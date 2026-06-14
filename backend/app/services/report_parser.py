import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app import models
from app.config import UPLOAD_DIR
from app.services.kimi_provider import KimiProvider
from app.services.llm_provider import LLMProvider
from app.services.normalizer import BiomarkerNormalizer
from app.services.pdf_extractor import extract_report_date, extract_text_from_pdf

logger = logging.getLogger(__name__)


def get_llm_provider() -> LLMProvider:
    from app.config import LLM_PROVIDER
    if LLM_PROVIDER == "kimi":
        return KimiProvider()
    raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")


def ensure_biomarkers_in_db(db: Session, normalizer: BiomarkerNormalizer) -> None:
    """将字典中的指标写入数据库（如不存在）。"""
    existing = {b.code for b in db.query(models.Biomarker).all()}
    for b in normalizer.list_biomarkers():
        if b["code"] in existing:
            continue
        import json as _json
        db.add(
            models.Biomarker(
                code=b["code"],
                name=b["name"],
                aliases=_json.dumps(b.get("aliases", []), ensure_ascii=False),
                unit_standard=b["unit_standard"],
                unit_aliases=_json.dumps(b.get("unit_aliases", []), ensure_ascii=False),
                category=b.get("category"),
                reference_low=b.get("reference_low"),
                reference_high=b.get("reference_high"),
                direction=b.get("direction"),
                description=b.get("description"),
            )
        )
    db.commit()


def parse_report(
    db: Session,
    report_id: int,
    normalizer: Optional[BiomarkerNormalizer] = None,
    provider: Optional[LLMProvider] = None,
) -> Dict[str, Any]:
    normalizer = normalizer or BiomarkerNormalizer()
    provider = provider or get_llm_provider()

    report = db.query(models.Report).filter(models.Report.id == report_id).first()
    if not report:
        raise ValueError(f"Report {report_id} not found")

    ensure_biomarkers_in_db(db, normalizer)

    try:
        text = extract_text_from_pdf(report.stored_path)
        if not text.strip():
            raise ValueError("PDF text is empty")

        # 尝试提取报告日期
        date_str = extract_report_date(text)
        if date_str and not report.report_date:
            report.report_date = datetime.fromisoformat(date_str)

        if not provider.is_available():
            logger.warning("LLM provider not available; using fallback demo extraction")
            extracted = _fallback_extract(text, normalizer)
        else:
            extracted = provider.extract_biomarkers(
                text, normalizer.list_biomarkers()
            )

        normalized = normalizer.normalize_extracted(extracted)

        # 写入数据库
        for item in normalized:
            biomarker = (
                db.query(models.Biomarker)
                .filter(models.Biomarker.code == item["biomarker_code"])
                .first()
            )
            if not biomarker:
                continue
            db.add(
                models.BiomarkerValue(
                    report_id=report.id,
                    biomarker_id=biomarker.id,
                    original_name=item["original_name"],
                    original_value_text=item["original_value_text"],
                    original_unit=item["original_unit"],
                    value=item["value"],
                    unit=item["unit"],
                    reference_low=item["reference_low"],
                    reference_high=item["reference_high"],
                    status=item["status"],
                    is_reviewed=False,
                )
            )

        report.status = "parsed"
        db.commit()
        return {
            "report_id": report.id,
            "status": "parsed",
            "extracted_count": len(normalized),
        }
    except Exception as exc:
        logger.exception("Report parsing failed for report %s", report_id)
        report.status = "error"
        report.error_message = str(exc)
        db.commit()
        raise


def _fallback_extract(
    text: str, normalizer: BiomarkerNormalizer
) -> List[Dict[str, Any]]:
    """当 LLM 不可用时，使用简单关键字匹配做演示提取（准确率有限）。"""
    import re

    results = []
    matched_names = set()
    for b in normalizer.list_biomarkers():
        # 优先用中文名称匹配，再尝试 aliases（如 WBC、RBC 等英文缩写）
        candidates = [b["name"]] + b.get("aliases", [])
        for name in candidates:
            if name in matched_names:
                continue
            pattern = re.compile(
                rf"{re.escape(name)}[\s:：]*([0-9]+\.?[0-9]*)\s*([A-Za-zμ^/0-9]+)",
                re.IGNORECASE,
            )
            match = pattern.search(text)
            if match:
                matched_names.add(name)
                results.append(
                    {
                        "original_name": name,
                        "original_value": match.group(1),
                        "original_unit": match.group(2),
                        "confidence": 0.6,
                    }
                )
                break
    return results
