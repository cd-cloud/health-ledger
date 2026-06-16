import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import UPLOAD_DIR
from app.database import get_db
from app.services.report_parser import parse_report

router = APIRouter(prefix="/reports", tags=["reports"])

# 单文件大小限制：50 MB
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


@router.post("/upload", response_model=schemas.ReportOut, status_code=status.HTTP_201_CREATED)
def upload_report(
    file: UploadFile = File(...),
    report_date: str | None = Form(None),
    db: Session = Depends(get_db),
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

    ext = Path(file.filename).suffix
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / stored_filename

    try:
        with open(stored_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存文件失败：{exc}",
        ) from exc
    finally:
        file.file.close()

    # 空文件检查
    file_size = stored_path.stat().st_size
    if file_size == 0:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件为空，请检查文件是否损坏",
        )

    if file_size > MAX_UPLOAD_SIZE:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"文件大小超过 {MAX_UPLOAD_SIZE // 1024 // 1024} MB 限制",
        )

    parsed_date = None
    if report_date:
        try:
            parsed_date = datetime.fromisoformat(report_date)
        except ValueError:
            pass

    report = models.Report(
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
def list_reports(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    query = db.query(models.Report).order_by(models.Report.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"items": items, "total": total}


@router.get("/{report_id}", response_model=schemas.ReportDetailOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/{report_id}/parse", response_model=schemas.ParseReportResponse)
def parse_report_endpoint(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

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
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    try:
        Path(report.stored_path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(report)
    db.commit()
    return None
