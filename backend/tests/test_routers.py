import io
from pathlib import Path

import pytest

from app import models


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestBiomarkers:
    def test_list_biomarkers(self, client, sample_biomarkers):
        response = client.get("/biomarkers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_biomarkers)
        codes = {b["code"] for b in data}
        assert "HGB" in codes

    def test_batch_update(self, client, db, sample_biomarkers):
        report = models.Report(
            filename="test.pdf",
            original_name="test.pdf",
            stored_path="/tmp/test.pdf",
            status="parsed",
        )
        db.add(report)
        db.flush()

        biomarker = db.query(models.Biomarker).filter(models.Biomarker.code == "HGB").first()
        value = models.BiomarkerValue(
            report_id=report.id,
            biomarker_id=biomarker.id,
            value=140.0,
            unit="g/L",
            status="normal",
            is_reviewed=False,
        )
        db.add(value)
        db.commit()
        db.refresh(value)

        response = client.patch(
            "/biomarkers/values/batch",
            json={"items": [{"id": value.id, "is_reviewed": True}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_reviewed"] is True

    def test_export_csv(self, client, db, sample_biomarkers):
        response = client.get("/biomarkers/values/export?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "biomarker_values.csv" in response.headers["content-disposition"]

    def test_export_json(self, client, db, sample_biomarkers):
        response = client.get("/biomarkers/values/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, list)

    def test_export_invalid_format(self, client):
        response = client.get("/biomarkers/values/export?format=xml")
        assert response.status_code == 422


class TestReports:
    def test_upload_non_pdf_rejected(self, client):
        response = client.post(
            "/reports/upload",
            files={"file": ("test.txt", io.BytesIO(b"not pdf"), "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_empty_pdf_rejected(self, client):
        response = client.post(
            "/reports/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400
        assert "空" in response.json()["detail"]

    def test_upload_pdf_success(self, client, tmp_path):
        pdf_path = tmp_path / "report.pdf"
        pdf_path.write_bytes(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
            b"xref\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        with open(pdf_path, "rb") as f:
            response = client.post(
                "/reports/upload",
                files={"file": ("report.pdf", f, "application/pdf")},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["original_name"] == "report.pdf"
        assert data["status"] == "pending"

    def test_parse_report_not_found(self, client):
        response = client.post("/reports/99999/parse")
        assert response.status_code == 404

    def test_delete_report(self, client, db, tmp_path):
        pdf_path = tmp_path / "delete.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntrailer<</Root 1 0 R>>\n%%EOF")
        report = models.Report(
            filename="delete.pdf",
            original_name="delete.pdf",
            stored_path=str(pdf_path),
            status="pending",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        response = client.delete(f"/reports/{report.id}")
        assert response.status_code == 204

        response = client.get(f"/reports/{report.id}")
        assert response.status_code == 404


class TestTrends:
    def test_get_trend_no_data(self, client, sample_biomarkers):
        response = client.get("/trends/HGB")
        assert response.status_code == 200
        data = response.json()
        assert data["biomarker"]["code"] == "HGB"
        assert data["points"] == []
