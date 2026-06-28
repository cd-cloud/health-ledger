import json
import logging
import uuid
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import BinaryIO, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import UPLOAD_DIR
from app.database import get_db
from app.services.auth import get_current_user
from app.services.export import (
    add_csv_and_json_to_zip,
    biomarker_value_to_dict,
    format_datetime,
    user_biomarker_values_query,
)
from app.services.report_parser import parse_report

router = APIRouter(prefix="/reports", tags=["reports"])
logger = logging.getLogger(__name__)

# 单文件大小限制：50 MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024

# 上传文件允许的 MIME 类型
ALLOWED_PDF_MIME_TYPES = {
    "application/pdf",
    "application/x-pdf",
}

# PDF 文件头魔数（%PDF-）
PDF_MAGIC = b"%PDF-"


def _is_pdf_content(data: bytes) -> bool:
    """通过文件头魔数判断是否为 PDF 格式。"""
    return data.startswith(PDF_MAGIC)


def _stream_to_temp(
    source: BinaryIO,
    temp_path: Path,
    max_size: int,
    chunk_size: int = 8192,
) -> int:
    """将上传流分块写入临时文件，超过限额时立即抛出异常。

    返回实际写入字节数。
    """
    total = 0
    with open(temp_path, "wb") as buffer:
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_size:
                raise ValueError(
                    f"文件大小超过 {max_size // 1024 // 1024} MB 限制"
                )
            buffer.write(chunk)
    return total


def _safe_unlink(path: Path) -> None:
    """安全删除文件，忽略不存在等异常。"""
    try:
        path.unlink()
    except FileNotFoundError:
        pass
    except Exception:
        logger.exception("删除临时文件失败：%s", path)


def _get_user_report(db: Session, report_id: int, user_id: int) -> models.Report:
    report = (
        db.query(models.Report)
        .filter(models.Report.id == report_id, models.Report.user_id == user_id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/upload", response_model=schemas.ReportOut, status_code=status.HTTP_201_CREATED)
def upload_report(
    file: UploadFile = File(...),
    report_date: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请选择要上传的文件",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 PDF 文件，请上传 .pdf 格式的体检报告",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_PDF_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的文件类型 {content_type}，请上传 PDF 文件",
        )

    ext = Path(file.filename).suffix
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / stored_filename
    temp_path = Path(f"{stored_path}.tmp")

    try:
        # 流式写入临时文件，边写边校验大小，避免大文件完整落地
        file_size = _stream_to_temp(file.file, temp_path, MAX_UPLOAD_SIZE)
    except ValueError as exc:
        # 超过限额或读取失败，清理临时文件
        _safe_unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        _safe_unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败：{exc}",
        ) from exc
    finally:
        file.file.close()

    # 空文件检查
    if file_size == 0:
        _safe_unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件为空，请检查文件是否损坏",
        )

    # 文件头魔数校验：防止仅修改扩展名的伪装文件
    with open(temp_path, "rb") as f:
        header = f.read(len(PDF_MAGIC))
    if not _is_pdf_content(header):
        _safe_unlink(temp_path)
        logger.warning(
            "上传文件扩展名为 .pdf 但文件头不匹配，可能为恶意或损坏文件：%s",
            file.filename,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件不是有效的 PDF，请检查文件是否损坏或被篡改",
        )

    # 校验通过，移动到正式路径
    try:
        temp_path.rename(stored_path)
    except Exception as exc:
        _safe_unlink(temp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档文件失败：{exc}",
        ) from exc

    parsed_date = None
    if report_date:
        try:
            parsed_date = datetime.fromisoformat(report_date)
        except ValueError:
            pass

    report = models.Report(
        user_id=current_user.id,
        filename=stored_filename,
        original_name=file.filename,
        stored_path=str(stored_path),
        report_date=parsed_date,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@router.get("", response_model=schemas.ReportListOut)
def list_reports(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = (
        db.query(models.Report)
        .filter(models.Report.user_id == current_user.id)
        .order_by(models.Report.created_at.desc())
    )
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/export")
def export_reports_archive(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """导出当前用户的全部历史报告（PDF 原始文件 + 指标 CSV/JSON）为 ZIP。

    注意：导出的 ZIP 包含用户敏感健康数据，下载后请妥善保管。
    """
    reports = (
        db.query(models.Report)
        .filter(models.Report.user_id == current_user.id)
        .order_by(models.Report.created_at.desc())
        .all()
    )
    values = (
        user_biomarker_values_query(db, current_user.id)
        .order_by(models.BiomarkerValue.created_at.desc())
        .all()
    )
    biomarkers = db.query(models.Biomarker).order_by(models.Biomarker.code).all()

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        add_csv_and_json_to_zip(
            zf, "reports", [_report_to_dict(r) for r in reports]
        )
        add_csv_and_json_to_zip(
            zf, "biomarker_values", [biomarker_value_to_dict(v) for v in values]
        )
        add_csv_and_json_to_zip(
            zf, "biomarkers", [_biomarker_to_dict(b) for b in biomarkers]
        )

        seen_names: Dict[str, int] = {}
        for report in reports:
            pdf_path = Path(report.stored_path)
            arc_name = f"pdfs/{_unique_pdf_name(report.original_name, seen_names)}"
            if pdf_path.exists():
                zf.write(pdf_path, arc_name)
            else:
                logger.warning("报告 PDF 文件缺失，已跳过: %s", pdf_path)

        manifest = {
            "version": "0.4.0",
            "exported_at": format_datetime(datetime.now()),
            "username": current_user.username,
            "report_count": len(reports),
            "biomarker_value_count": len(values),
            "biomarker_count": len(biomarkers),
        }
        zf.writestr(
            "manifest.json",
            json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        )

    buffer.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"health_export_{current_user.username}_{timestamp}.zip"
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{report_id}", response_model=schemas.ReportDetailOut)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_user_report(db, report_id, current_user.id)


@router.post("/{report_id}/parse", response_model=schemas.ParseReportResponse)
def parse_report_endpoint(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user.id)

    try:
        result = parse_report(db, report_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"报告解析失败：{exc}",
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"服务暂时不可用：{exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"报告解析失败：{exc}",
        ) from exc

    return result


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    report = _get_user_report(db, report_id, current_user.id)

    try:
        Path(report.stored_path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(report)
    db.commit()
    return None


def _report_to_dict(report: models.Report) -> Dict[str, object]:
    return {
        "id": report.id,
        "user_id": report.user_id,
        "original_name": report.original_name,
        "filename": report.filename,
        "report_date": format_datetime(report.report_date),
        "status": report.status,
        "error_message": report.error_message,
        "created_at": format_datetime(report.created_at),
        "updated_at": format_datetime(report.updated_at),
    }


def _biomarker_to_dict(biomarker: models.Biomarker) -> Dict[str, object]:
    return {
        "id": biomarker.id,
        "code": biomarker.code,
        "name": biomarker.name,
        "unit_standard": biomarker.unit_standard,
        "category": biomarker.category,
        "reference_low": biomarker.reference_low,
        "reference_high": biomarker.reference_high,
        "direction": biomarker.direction,
        "description": biomarker.description,
    }


def _unique_pdf_name(original_name: str, seen_names: Dict[str, int]) -> str:
    base = Path(original_name).name
    if base not in seen_names:
        seen_names[base] = 0
        return base
    seen_names[base] += 1
    stem = Path(base).stem
    suffix = Path(base).suffix
    return f"{stem}_{seen_names[base]}{suffix}"
