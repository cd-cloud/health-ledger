import io
import json
import zipfile
from pathlib import Path

import pytest

from app import models


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestAuth:
    def test_register(self, client):
        response = client.post(
            "/auth/register",
            json={"username": "newuser", "password": "newpass123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"

    def test_register_duplicate_username(self, client, test_user):
        response = client.post(
            "/auth/register",
            json={"username": test_user.username, "password": "newpass123"},
        )
        assert response.status_code == 400

    def test_login_success(self, client, test_user):
        response = client.post(
            "/auth/login",
            json={"username": test_user.username, "password": "testpass"},
        )
        assert response.status_code == 200
        assert response.json()["username"] == test_user.username

    def test_login_failure(self, client, test_user):
        response = client.post(
            "/auth/login",
            json={"username": test_user.username, "password": "wrongpass"},
        )
        assert response.status_code == 401

    def test_me_requires_login(self, client):
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_me_authenticated(self, auth_client, test_user):
        response = auth_client.get("/auth/me")
        assert response.status_code == 200
        assert response.json()["username"] == test_user.username


class TestBiomarkers:
    def test_list_biomarkers(self, client, sample_biomarkers):
        response = client.get("/biomarkers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_biomarkers)
        codes = {b["code"] for b in data}
        assert "HGB" in codes

    def test_values_require_login(self, client):
        response = client.get("/biomarkers/values")
        assert response.status_code == 401

    def test_batch_update(self, auth_client, db, sample_biomarkers, test_user):
        report = models.Report(
            user_id=test_user.id,
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

        response = auth_client.patch(
            "/biomarkers/values/batch",
            json={"items": [{"id": value.id, "is_reviewed": True}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["is_reviewed"] is True

    def test_update_other_user_value_forbidden(self, auth_client, db, sample_biomarkers):
        other_user = models.User(
            username="otheruser",
            hashed_password="dummy",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        report = models.Report(
            user_id=other_user.id,
            filename="other.pdf",
            original_name="other.pdf",
            stored_path="/tmp/other.pdf",
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

        response = auth_client.patch(
            "/biomarkers/values/batch",
            json={"items": [{"id": value.id, "is_reviewed": True}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_export_csv(self, auth_client, db, sample_biomarkers, test_user):
        response = auth_client.get("/biomarkers/values/export?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        assert "biomarker_values.csv" in response.headers["content-disposition"]

    def test_export_json(self, auth_client, db, sample_biomarkers, test_user):
        response = auth_client.get("/biomarkers/values/export?format=json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, list)

    def test_export_invalid_format(self, auth_client):
        response = auth_client.get("/biomarkers/values/export?format=xml")
        assert response.status_code == 422


class TestReports:
    def test_upload_non_pdf_rejected(self, auth_client):
        response = auth_client.post(
            "/reports/upload",
            files={"file": ("test.txt", io.BytesIO(b"not pdf"), "text/plain")},
        )
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_upload_empty_pdf_rejected(self, auth_client):
        response = auth_client.post(
            "/reports/upload",
            files={"file": ("empty.pdf", io.BytesIO(b""), "application/pdf")},
        )
        assert response.status_code == 400
        assert "空" in response.json()["detail"]

    def test_upload_requires_login(self, client):
        response = client.post(
            "/reports/upload",
            files={"file": ("report.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert response.status_code == 401

    def test_upload_pdf_success(self, auth_client, tmp_path):
        pdf_path = tmp_path / "report.pdf"
        pdf_path.write_bytes(
            b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
            b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]>>endobj\n"
            b"xref\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        with open(pdf_path, "rb") as f:
            response = auth_client.post(
                "/reports/upload",
                files={"file": ("report.pdf", f, "application/pdf")},
            )
        assert response.status_code == 201
        data = response.json()
        assert data["original_name"] == "report.pdf"
        assert data["status"] == "pending"
        assert data["user_id"] == 1  # test_user.id

    def test_list_reports_isolated(self, auth_client, db, test_user):
        report = models.Report(
            user_id=test_user.id,
            filename="a.pdf",
            original_name="a.pdf",
            stored_path="/tmp/a.pdf",
            status="pending",
        )
        db.add(report)
        db.commit()

        response = auth_client.get("/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

    def test_list_reports_other_user_hidden(self, auth_client, db):
        other_user = models.User(
            username="otheruser2",
            hashed_password="dummy",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        report = models.Report(
            user_id=other_user.id,
            filename="other.pdf",
            original_name="other.pdf",
            stored_path="/tmp/other.pdf",
            status="pending",
        )
        db.add(report)
        db.commit()

        response = auth_client.get("/reports")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    def test_parse_report_not_found(self, auth_client):
        response = auth_client.post("/reports/99999/parse")
        assert response.status_code == 404

    def test_delete_report(self, auth_client, db, tmp_path, test_user):
        pdf_path = tmp_path / "delete.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntrailer<</Root 1 0 R>>\n%%EOF")
        report = models.Report(
            user_id=test_user.id,
            filename="delete.pdf",
            original_name="delete.pdf",
            stored_path=str(pdf_path),
            status="pending",
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        response = auth_client.delete(f"/reports/{report.id}")
        assert response.status_code == 204

        response = auth_client.get(f"/reports/{report.id}")
        assert response.status_code == 404

    def test_export_archive_requires_login(self, client):
        response = client.get("/reports/export")
        assert response.status_code == 401

    def test_export_archive_zip_contains_pdf_and_csv(self, auth_client, db, tmp_path, test_user, sample_biomarkers):
        pdf_path = tmp_path / "report.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n%%EOF")

        report = models.Report(
            user_id=test_user.id,
            filename="report.pdf",
            original_name="report.pdf",
            stored_path=str(pdf_path),
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
            is_reviewed=True,
        )
        db.add(value)
        db.commit()

        response = auth_client.get("/reports/export")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/zip"
        assert "health_export_" in response.headers["content-disposition"]

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
            assert "reports.csv" in names
            assert "reports.json" in names
            assert "biomarker_values.csv" in names
            assert "biomarker_values.json" in names
            assert "biomarkers.csv" in names
            assert "biomarkers.json" in names
            assert "manifest.json" in names
            assert "pdfs/report.pdf" in names

            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            assert manifest["username"] == test_user.username
            assert manifest["report_count"] == 1
            assert manifest["biomarker_value_count"] == 1

    def test_export_archive_is_user_isolated(self, auth_client, db, tmp_path):
        other_user = models.User(
            username="otheruser3",
            hashed_password="dummy",
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        pdf_path = tmp_path / "other_report.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%%EOF")
        report = models.Report(
            user_id=other_user.id,
            filename="other_report.pdf",
            original_name="other_report.pdf",
            stored_path=str(pdf_path),
            status="pending",
        )
        db.add(report)
        db.commit()

        response = auth_client.get("/reports/export")
        assert response.status_code == 200

        with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
            names = zf.namelist()
            assert "pdfs/other_report.pdf" not in names
            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            assert manifest["report_count"] == 0


class TestTrends:
    def test_get_trend_no_data(self, auth_client, sample_biomarkers):
        response = auth_client.get("/trends/HGB")
        assert response.status_code == 200
        data = response.json()
        assert data["biomarker"]["code"] == "HGB"
        assert data["points"] == []

    def test_get_trend_requires_login(self, client, sample_biomarkers):
        response = client.get("/trends/HGB")
        assert response.status_code == 401
