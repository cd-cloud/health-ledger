import csv
import io
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.auth import get_current_user

router = APIRouter(prefix="/biomarkers", tags=["biomarkers"])


def _user_values_query(db: Session, user_id: int):
    """返回仅属于当前用户的指标数值查询。"""
    return (
        db.query(models.BiomarkerValue)
        .join(models.Report)
        .filter(models.Report.user_id == user_id)
        .join(models.Biomarker)
    )


@router.get("", response_model=List[schemas.BiomarkerOut])
def list_biomarkers(db: Session = Depends(get_db)):
    return db.query(models.Biomarker).order_by(models.Biomarker.code).all()


@router.get("/values", response_model=List[schemas.BiomarkerValueOut])
def list_biomarker_values(
    report_id: Optional[int] = None,
    biomarker_code: Optional[str] = None,
    status: Optional[str] = None,
    abnormal_only: bool = False,
    reviewed_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = _user_values_query(db, current_user.id)

    if report_id is not None:
        query = query.filter(models.BiomarkerValue.report_id == report_id)
    if biomarker_code:
        query = query.filter(models.Biomarker.code == biomarker_code)
    if status:
        query = query.filter(models.BiomarkerValue.status == status)
    if abnormal_only:
        query = query.filter(models.BiomarkerValue.status.in_(["high", "low"]))
    if reviewed_only:
        query = query.filter(models.BiomarkerValue.is_reviewed.is_(True))

    return query.order_by(models.BiomarkerValue.created_at.desc()).all()


@router.get("/values/export")
def export_biomarker_values(
    format: str = Query("csv", pattern="^(csv|json)$"),
    report_id: Optional[int] = None,
    biomarker_code: Optional[str] = None,
    status: Optional[str] = None,
    abnormal_only: bool = False,
    reviewed_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """导出当前用户的指标数值为 CSV 或 JSON。"""
    query = _user_values_query(db, current_user.id)

    if report_id is not None:
        query = query.filter(models.BiomarkerValue.report_id == report_id)
    if biomarker_code:
        query = query.filter(models.Biomarker.code == biomarker_code)
    if status:
        query = query.filter(models.BiomarkerValue.status == status)
    if abnormal_only:
        query = query.filter(models.BiomarkerValue.status.in_(["high", "low"]))
    if reviewed_only:
        query = query.filter(models.BiomarkerValue.is_reviewed.is_(True))

    values = query.order_by(models.BiomarkerValue.created_at.desc()).all()

    records = [
        {
            "id": v.id,
            "report_id": v.report_id,
            "biomarker_code": v.biomarker.code,
            "biomarker_name": v.biomarker.name,
            "original_name": v.original_name,
            "original_value": v.original_value_text,
            "original_unit": v.original_unit,
            "value": v.value,
            "unit": v.unit,
            "reference_low": v.reference_low,
            "reference_high": v.reference_high,
            "status": v.status,
            "is_reviewed": v.is_reviewed,
            "reviewed_at": v.reviewed_at.isoformat() if v.reviewed_at else None,
            "created_at": v.created_at.isoformat() if v.created_at else None,
        }
        for v in values
    ]

    if format == "json":
        return Response(
            content=json.dumps(records, ensure_ascii=False, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=biomarker_values.json"},
        )

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys() if records else [])
    writer.writeheader()
    writer.writerows(records)
    return Response(
        content=output.getvalue().encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=biomarker_values.csv"},
    )


@router.patch("/values/batch", response_model=List[schemas.BiomarkerValueOut])
def batch_update_biomarker_values(
    payload: schemas.BiomarkerValueBatchUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """批量更新当前用户的指标数值，常用于报告详情页的批量校对。"""
    updated = []
    for item in payload.items:
        value = (
            _user_values_query(db, current_user.id)
            .filter(models.BiomarkerValue.id == item.id)
            .first()
        )
        if not value:
            continue
        _apply_value_update(value, item)
        updated.append(value)

    db.commit()
    for value in updated:
        db.refresh(value)
    return updated


@router.patch("/values/{value_id}", response_model=schemas.BiomarkerValueOut)
def update_biomarker_value(
    value_id: int,
    payload: schemas.BiomarkerValueUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    value = (
        _user_values_query(db, current_user.id)
        .filter(models.BiomarkerValue.id == value_id)
        .first()
    )
    if not value:
        raise HTTPException(status_code=404, detail="Biomarker value not found")

    _apply_value_update(value, payload)

    db.commit()
    db.refresh(value)
    return value


def _apply_value_update(value: models.BiomarkerValue, payload: schemas.BiomarkerValueUpdate) -> None:
    if payload.value is not None:
        value.value = payload.value
    if payload.unit is not None:
        value.unit = payload.unit
    if payload.status is not None:
        value.status = payload.status
    if payload.is_reviewed is not None:
        value.is_reviewed = payload.is_reviewed
        value.reviewed_at = datetime.utcnow() if payload.is_reviewed else None


@router.get("/summary/abnormal", response_model=List[schemas.BiomarkerValueOut])
def abnormal_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """返回当前用户每个指标最新一次已校对的异常值（用于 Dashboard）。"""
    subq = (
        db.query(
            models.BiomarkerValue.biomarker_id,
            func.max(models.BiomarkerValue.created_at).label("latest_at"),
        )
        .join(models.Report)
        .filter(models.Report.user_id == current_user.id)
        .filter(models.BiomarkerValue.is_reviewed.is_(True))
        .filter(models.BiomarkerValue.status.in_(["high", "low"]))
        .group_by(models.BiomarkerValue.biomarker_id)
        .subquery()
    )
    query = (
        db.query(models.BiomarkerValue)
        .join(models.Report)
        .filter(models.Report.user_id == current_user.id)
        .join(
            subq,
            (models.BiomarkerValue.biomarker_id == subq.c.biomarker_id)
            & (models.BiomarkerValue.created_at == subq.c.latest_at),
        )
        .order_by(models.BiomarkerValue.status)
    )
    return query.all()
