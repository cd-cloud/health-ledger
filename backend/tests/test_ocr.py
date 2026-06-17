"""扫描件 PDF 的 OCR 端到端与兜底路径测试。

这些测试依赖系统级 OCR 工具（poppler + tesseract/paddleocr）以及 img2pdf，
在未安装相关依赖的环境中会被自动跳过。可通过以下命令在 Docker 中一键运行：

    docker compose -f backend/docker-compose.ocr-test.yml up --build
"""

from pathlib import Path
from typing import Optional

import pytest

from app.services.ocr_extractor import extract_text_with_ocr, is_ocr_available
from app.services.pdf_extractor import extract_text_from_pdf

# 可选依赖：用于生成测试用扫描件 PDF
try:
    import img2pdf
except ImportError:  # pragma: no cover
    img2pdf = None  # type: ignore

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    Image = None  # type: ignore
    ImageDraw = None  # type: ignore
    ImageFont = None  # type: ignore

pytestmark = pytest.mark.skipif(
    not is_ocr_available() or img2pdf is None or Image is None,
    reason="OCR runtime dependencies not available (poppler, tesseract/paddleocr, PIL, img2pdf)",
)


def _make_scanned_pdf(text: str, tmp_path: Path) -> Path:
    """将纯文本渲染为图片后封装成单页扫描件 PDF。"""
    image_path = tmp_path / "scan.png"
    pdf_path = tmp_path / "scan.pdf"

    # 高分辨率、大字体，提升 Tesseract 识别率
    img = Image.new("RGB", (1600, 500), color="white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 96)
    except Exception:  # pragma: no cover
        font = ImageFont.load_default()
    draw.text((80, 180), text, fill="black", font=font)
    img.save(image_path, "PNG", dpi=(300, 300))

    with open(pdf_path, "wb") as f:
        img2pdf.convert([str(image_path)], outputstream=f)

    return pdf_path


def _contains_any(text: str, candidates: list[str]) -> bool:
    return any(candidate in text for candidate in candidates)


class TestOCRExtractor:
    def test_ocr_extracts_text_from_scanned_pdf(self, tmp_path):
        pdf_path = _make_scanned_pdf("HGB 14.0 g/dL", tmp_path)
        text = extract_text_with_ocr(pdf_path, use_paddle=False, use_tesseract=True)

        assert text and text.strip()
        assert _contains_any(text.upper(), ["HGB"])
        assert _contains_any(text, ["14.0", "14"])


class TestPDFOCRFallback:
    def test_extract_text_from_pdf_falls_back_to_ocr(self, tmp_path, monkeypatch):
        # 禁用 PaddleOCR，确保测试走 Tesseract 快速路径
        from app.services import ocr_extractor

        monkeypatch.setattr(ocr_extractor, "PaddleOCR", None)

        pdf_path = _make_scanned_pdf("HGB 14.0 g/dL", tmp_path)
        text = extract_text_from_pdf(pdf_path)

        assert text and text.strip()
        assert _contains_any(text.upper(), ["HGB"])


class TestScannedReportEndToEnd:
    def test_upload_and_parse_scanned_report(self, client, tmp_path, monkeypatch):
        from app.services import ocr_extractor

        monkeypatch.setattr(ocr_extractor, "PaddleOCR", None)

        pdf_path = _make_scanned_pdf("HGB 14.0 g/dL", tmp_path)

        with open(pdf_path, "rb") as f:
            response = client.post(
                "/reports/upload",
                files={"file": ("scanned_report.pdf", f, "application/pdf")},
            )
        assert response.status_code == 201
        report_id = response.json()["id"]

        response = client.post(f"/reports/{report_id}/parse")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "parsed"

        values_response = client.get("/biomarkers/values", params={"report_id": report_id})
        assert values_response.status_code == 200
        values = values_response.json()
        codes = {v["biomarker"]["code"] for v in values}
        assert "HGB" in codes

        hgb = next(v for v in values if v["biomarker"]["code"] == "HGB")
        assert hgb["value"] == 140.0  # g/dL -> g/L
        assert hgb["unit"] == "g/L"
