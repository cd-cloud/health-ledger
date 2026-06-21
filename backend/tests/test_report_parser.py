import json
from datetime import datetime
from pathlib import Path

import pytest

from app import models
from app.services.auth import hash_password
from app.services.llm_provider import LLMProvider
from app.services.normalizer import BiomarkerNormalizer
from app.services.report_parser import parse_report


class FakeLLMProvider(LLMProvider):
    """用于测试的 LLM Provider，返回固定结果。"""

    def __init__(self, extracted=None):
        self._extracted = extracted or []

    def is_available(self) -> bool:
        return True

    def extract_biomarkers(self, report_text, biomarker_dictionary):
        return self._extracted

    def analyze_trend(self, biomarker_name, unit, reference_low, reference_high, trend_points):
        return "趋势平稳。"


@pytest.fixture
def test_user(db):
    user = models.User(
        username="parseruser",
        hashed_password=hash_password("testpass"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def sample_report(db, tmp_path, test_user):
    """创建一份测试用的 PDF 报告。"""
    report = models.Report(
        user_id=test_user.id,
        filename="test.pdf",
        original_name="test.pdf",
        stored_path=str(tmp_path / "test.pdf"),
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    # 创建一个最小有效的 PDF 文件
    Path(report.stored_path).write_bytes(
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n"
        b"4 0 obj<</Length 21>>stream\nBT /F1 12 Tf 100 700 Td (HGB 14.0 g/dL) Tj ET\nendstream\nendobj\n"
        b"xref\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    return report


class TestParseReport:
    def test_parse_report_not_found(self, db):
        with pytest.raises(ValueError, match="Report 99999 not found"):
            parse_report(db, 99999)

    def test_parse_report_with_llm_provider(self, db, sample_report, sample_biomarkers):
        provider = FakeLLMProvider(
            extracted=[
                {
                    "original_name": "血红蛋白",
                    "original_value": "14.0",
                    "original_unit": "g/dL",
                    "confidence": 0.9,
                }
            ]
        )
        normalizer = BiomarkerNormalizer()

        result = parse_report(db, sample_report.id, normalizer=normalizer, provider=provider)

        assert result["status"] == "parsed"
        assert result["extracted_count"] == 1

        db.refresh(sample_report)
        assert sample_report.status == "parsed"
        assert len(sample_report.values) == 1
        value = sample_report.values[0]
        assert value.biomarker.code == "HGB"
        assert value.value == 140.0  # g/dL -> g/L
        assert value.unit == "g/L"

    def test_parse_report_fallback_when_llm_unavailable(self, db, sample_report, sample_biomarkers):
        provider = FakeLLMProvider(extracted=[])
        provider.is_available = lambda: False
        normalizer = BiomarkerNormalizer()

        result = parse_report(db, sample_report.id, normalizer=normalizer, provider=provider)

        assert result["status"] == "parsed"
        # 最小 PDF 中无法可靠提取，但至少应完成解析流程
        assert sample_report.status == "parsed"

    def test_parse_report_date_extraction(self, db, tmp_path, sample_biomarkers, test_user):
        stored_path = tmp_path / "dated.pdf"
        stored_path.write_bytes(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj\n"
            b"4 0 obj<</Length 50>>stream\nBT /F1 12 Tf 100 700 Td (Report Date: 2024-05-12 HGB 14.0 g/dL) Tj ET\nendstream\nendobj\n"
            b"xref\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        report = models.Report(
            user_id=test_user.id,
            filename="dated.pdf",
            original_name="dated.pdf",
            stored_path=str(stored_path),
            status="pending",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        provider = FakeLLMProvider(
            extracted=[
                {
                    "original_name": "血红蛋白",
                    "original_value": "14.0",
                    "original_unit": "g/dL",
                    "confidence": 0.9,
                }
            ]
        )
        parse_report(db, report.id, provider=provider)

        db.refresh(report)
        assert report.report_date is not None
        assert report.report_date.date().isoformat() == "2024-05-12"

    def test_parse_report_error_status(self, db, sample_report, sample_biomarkers):
        """空 PDF 或无法提取文本时应标记为 error。"""
        provider = FakeLLMProvider(extracted=[])
        provider.is_available = lambda: True
        # 将文件替换为空文件
        Path(sample_report.stored_path).write_bytes(b"")

        with pytest.raises(Exception):
            parse_report(db, sample_report.id, provider=provider)

        db.refresh(sample_report)
        assert sample_report.status == "error"
        assert sample_report.error_message is not None
