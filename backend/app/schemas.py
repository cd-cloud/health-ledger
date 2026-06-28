from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)


class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(UserBase):
    password: str = Field(..., min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    created_at: datetime


class BiomarkerBase(BaseModel):
    code: str
    name: str
    unit_standard: str
    category: Optional[str] = None
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    direction: Optional[str] = None
    description: Optional[str] = None


class BiomarkerOut(BiomarkerBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class BiomarkerValueBase(BaseModel):
    value: float
    unit: str
    reference_low: Optional[float] = None
    reference_high: Optional[float] = None
    status: Optional[str] = None
    parse_version: int = 1
    is_reviewed: bool = False


class BiomarkerValueCreate(BaseModel):
    biomarker_code: str
    value: float
    unit: str
    original_name: Optional[str] = None
    original_value_text: Optional[str] = None
    original_unit: Optional[str] = None


class BiomarkerValueUpdate(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    is_reviewed: Optional[bool] = None


class BiomarkerValueBatchItem(BaseModel):
    id: int
    value: Optional[float] = None
    unit: Optional[str] = None
    status: Optional[str] = None
    is_reviewed: Optional[bool] = None


class BiomarkerValueBatchUpdate(BaseModel):
    items: List[BiomarkerValueBatchItem]


class BiomarkerValueOut(BiomarkerValueBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    report_id: int
    biomarker_id: int
    biomarker: BiomarkerOut
    original_name: Optional[str] = None
    original_value_text: Optional[str] = None
    original_unit: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ReportBase(BaseModel):
    filename: str
    original_name: str
    report_date: Optional[datetime] = None
    status: str = "pending"
    parse_version: int = 1


class ReportCreate(BaseModel):
    original_name: str
    report_date: Optional[datetime] = None


class ReportOut(ReportBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    stored_path: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ReportDetailOut(ReportOut):
    values: List[BiomarkerValueOut] = []


class ReportListOut(BaseModel):
    items: List[ReportOut]
    total: int


class TrendPoint(BaseModel):
    report_id: int
    report_date: Optional[datetime]
    value: float
    unit: str
    status: Optional[str]
    is_reviewed: bool


class TrendOut(BaseModel):
    biomarker: BiomarkerOut
    points: List[TrendPoint]


class TrendAnalysisRequest(BaseModel):
    biomarker_code: str


class TrendAnalysisOut(BaseModel):
    biomarker_code: str
    biomarker_name: str
    analysis: str
    disclaimer: str


class ParseReportResponse(BaseModel):
    report_id: int
    status: str
    extracted_count: int
    message: Optional[str] = None


class AbnormalFilter(BaseModel):
    biomarker_code: Optional[str] = None
    status: Optional[str] = None  # high / low


class ErrorResponse(BaseModel):
    detail: str
