from datetime import datetime, timezone
from functools import partial

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=partial(datetime.now, timezone.utc), nullable=False)

    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    stored_path = Column(Text, nullable=False)
    report_date = Column(DateTime, nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending / parsed / error
    error_message = Column(Text, nullable=True)
    parse_version = Column(Integer, default=1, nullable=False)
    _utc_now = partial(datetime.now, timezone.utc)

    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)

    user = relationship("User", back_populates="reports")
    values = relationship("BiomarkerValue", back_populates="report", cascade="all, delete-orphan")


class Biomarker(Base):
    __tablename__ = "biomarkers"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    aliases = Column(Text, nullable=False, default="")  # JSON array as string
    unit_standard = Column(String(50), nullable=False)
    unit_aliases = Column(Text, nullable=False, default="")  # JSON array as string
    category = Column(String(50), nullable=True)
    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    direction = Column(String(20), nullable=True)  # both / high / low
    description = Column(Text, nullable=True)

    values = relationship("BiomarkerValue", back_populates="biomarker")


class BiomarkerValue(Base):
    __tablename__ = "biomarker_values"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=False, index=True)
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"), nullable=False, index=True)

    original_name = Column(String(200), nullable=True)
    original_value_text = Column(String(100), nullable=True)
    original_unit = Column(String(50), nullable=True)

    value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=False)

    reference_low = Column(Float, nullable=True)
    reference_high = Column(Float, nullable=True)
    status = Column(String(20), nullable=True)  # normal / high / low
    parse_version = Column(Integer, default=1, nullable=False)

    is_reviewed = Column(Boolean, default=False, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=partial(datetime.now, timezone.utc), nullable=False)

    report = relationship("Report", back_populates="values")
    biomarker = relationship("Biomarker", back_populates="values")

    __table_args__ = (
        Index("idx_value_report_biomarker", "report_id", "biomarker_id"),
    )
