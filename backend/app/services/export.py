import csv
import io
import json
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app import models


def user_biomarker_values_query(db: Session, user_id: int):
    """返回仅属于当前用户的指标数值查询（关联报告与指标字典）。"""
    return (
        db.query(models.BiomarkerValue)
        .join(models.Report)
        .filter(models.Report.user_id == user_id)
        .join(models.Biomarker)
    )


def biomarker_value_to_dict(value: models.BiomarkerValue) -> Dict[str, Any]:
    """将 BiomarkerValue ORM 对象序列化为字典。"""
    return {
        "id": value.id,
        "report_id": value.report_id,
        "biomarker_code": value.biomarker.code,
        "biomarker_name": value.biomarker.name,
        "original_name": value.original_name,
        "original_value": value.original_value_text,
        "original_unit": value.original_unit,
        "value": value.value,
        "unit": value.unit,
        "reference_low": value.reference_low,
        "reference_high": value.reference_high,
        "status": value.status,
        "is_reviewed": value.is_reviewed,
        "reviewed_at": value.reviewed_at.isoformat() if value.reviewed_at else None,
        "created_at": value.created_at.isoformat() if value.created_at else None,
    }


def format_datetime(dt: Any) -> str | None:
    """统一将 datetime 对象格式化为 ISO 字符串。"""
    return dt.isoformat() if dt else None


def records_to_csv(records: List[Dict[str, Any]]) -> bytes:
    """将字典列表转换为带 UTF-8 BOM 的 CSV 字节。"""
    if not records:
        return "\ufeff".encode("utf-8")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue().encode("utf-8-sig")


def records_to_json(records: List[Dict[str, Any]]) -> bytes:
    """将字典列表格式化为可读的 JSON 字节。"""
    return json.dumps(records, ensure_ascii=False, indent=2).encode("utf-8")


def add_csv_and_json_to_zip(
    zf, name: str, records: List[Dict[str, Any]]
) -> None:
    """在 ZIP 中同时写入 CSV 与 JSON 两种格式的数据文件。"""
    zf.writestr(f"{name}.csv", records_to_csv(records))
    zf.writestr(f"{name}.json", records_to_json(records))
