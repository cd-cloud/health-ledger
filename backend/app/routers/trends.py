import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.config import MEDICAL_DISCLAIMER
from app.database import get_db
from app.services.auth import get_current_user
from app.services.kimi_provider import KimiProvider
from app.services.llm_provider import LLMProvider
from app.services.report_parser import get_llm_provider

router = APIRouter(prefix="/trends", tags=["trends"])


def _user_values_for_trend(db: Session, user_id: int, biomarker_id: int):
    return (
        db.query(models.BiomarkerValue)
        .filter(models.BiomarkerValue.biomarker_id == biomarker_id)
        .filter(models.BiomarkerValue.is_reviewed.is_(True))
        .join(models.Report)
        .filter(models.Report.user_id == user_id)
        .order_by(models.Report.report_date.asc())
    )


@router.get("/{biomarker_code}", response_model=schemas.TrendOut)
def get_trend(
    biomarker_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    biomarker = (
        db.query(models.Biomarker).filter(models.Biomarker.code == biomarker_code).first()
    )
    if not biomarker:
        raise HTTPException(status_code=404, detail="Biomarker not found")

    values = _user_values_for_trend(db, current_user.id, biomarker.id).all()

    points = [
        schemas.TrendPoint(
            report_id=v.report_id,
            report_date=v.report.report_date if v.report else None,
            value=v.value,
            unit=v.unit,
            status=v.status,
            is_reviewed=v.is_reviewed,
        )
        for v in values
    ]

    return schemas.TrendOut(biomarker=biomarker, points=points)


@router.post("/{biomarker_code}/analyze", response_model=schemas.TrendAnalysisOut)
def analyze_trend(
    biomarker_code: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    provider: LLMProvider = Depends(get_llm_provider),
):
    biomarker = (
        db.query(models.Biomarker).filter(models.Biomarker.code == biomarker_code).first()
    )
    if not biomarker:
        raise HTTPException(status_code=404, detail="Biomarker not found")

    values = _user_values_for_trend(db, current_user.id, biomarker.id).all()

    if len(values) < 2:
        analysis = "当前已校对的指标记录不足 2 条，暂无法生成趋势分析。请上传更多报告并完成校对。"
    elif not provider.is_available():
        # 本地简单趋势描述
        first, last = values[0], values[-1]
        direction = "上升" if last.value > first.value else "下降" if last.value < first.value else "持平"
        analysis = (
            f"从 {first.report.report_date.date() if first.report else '最早'} 到 "
            f"{last.report.report_date.date() if last.report else '最近'}，"
            f"{biomarker.name} 整体呈{direction}趋势（{first.value} -> {last.value} {biomarker.unit_standard}）。"
            "建议结合临床情况由医生进一步评估。"
        )
    else:
        trend_points = [
            {
                "report_date": str(v.report.report_date.date()) if v.report and v.report.report_date else None,
                "value": v.value,
                "status": v.status,
            }
            for v in values
        ]
        try:
            analysis = provider.analyze_trend(
                biomarker_name=biomarker.name,
                unit=biomarker.unit_standard,
                reference_low=biomarker.reference_low,
                reference_high=biomarker.reference_high,
                trend_points=trend_points,
            )
        except Exception as exc:
            logger = logging.getLogger(__name__)
            logger.warning("AI trend analysis failed: %s; using local fallback", exc)
            first, last = values[0], values[-1]
            direction = "上升" if last.value > first.value else "下降" if last.value < first.value else "持平"
            analysis = (
                f"从 {first.report.report_date.date() if first.report else '最早'} 到 "
                f"{last.report.report_date.date() if last.report else '最近'}，"
                f"{biomarker.name} 整体呈{direction}趋势（{first.value} -> {last.value} {biomarker.unit_standard}）。"
                "AI 分析暂时不可用，已切换为本地摘要。建议结合临床情况由医生进一步评估。"
            )

    return schemas.TrendAnalysisOut(
        biomarker_code=biomarker.code,
        biomarker_name=biomarker.name,
        analysis=analysis,
        disclaimer=MEDICAL_DISCLAIMER,
    )
