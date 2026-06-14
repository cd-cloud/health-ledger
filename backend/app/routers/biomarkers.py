from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/biomarkers", tags=["biomarkers"])


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
):
    query = db.query(models.BiomarkerValue).join(models.Biomarker)

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


@router.patch("/values/{value_id}", response_model=schemas.BiomarkerValueOut)
def update_biomarker_value(
    value_id: int,
    payload: schemas.BiomarkerValueUpdate,
    db: Session = Depends(get_db),
):
    value = (
        db.query(models.BiomarkerValue)
        .filter(models.BiomarkerValue.id == value_id)
        .first()
    )
    if not value:
        raise HTTPException(status_code=404, detail="Biomarker value not found")

    if payload.value is not None:
        value.value = payload.value
    if payload.unit is not None:
        value.unit = payload.unit
    if payload.status is not None:
        value.status = payload.status
    if payload.is_reviewed is not None:
        value.is_reviewed = payload.is_reviewed
        value.reviewed_at = datetime.utcnow() if payload.is_reviewed else None

    db.commit()
    db.refresh(value)
    return value


@router.get("/summary/abnormal", response_model=List[schemas.BiomarkerValueOut])
def abnormal_summary(db: Session = Depends(get_db)):
    """返回每个指标最新一次已校对的异常值（用于 Dashboard）。"""
    subq = (
        db.query(
            models.BiomarkerValue.biomarker_id,
            func.max(models.BiomarkerValue.created_at).label("latest_at"),
        )
        .filter(models.BiomarkerValue.is_reviewed.is_(True))
        .filter(models.BiomarkerValue.status.in_(["high", "low"]))
        .group_by(models.BiomarkerValue.biomarker_id)
        .subquery()
    )
    query = (
        db.query(models.BiomarkerValue)
        .join(
            subq,
            (models.BiomarkerValue.biomarker_id == subq.c.biomarker_id)
            & (models.BiomarkerValue.created_at == subq.c.latest_at),
        )
        .order_by(models.BiomarkerValue.status)
    )
    return query.all()
