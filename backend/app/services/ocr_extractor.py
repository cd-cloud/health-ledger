import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from pdf2image import convert_from_path
except ImportError:  # pragma: no cover
    convert_from_path = None  # type: ignore

try:
    from paddleocr import PaddleOCR
except ImportError:  # pragma: no cover
    PaddleOCR = None  # type: ignore

try:
    import pytesseract
    from PIL import Image
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore
    Image = None  # type: ignore


def _paddle_ocr_image(ocr: "PaddleOCR", image_path: str) -> str:
    """使用 PaddleOCR 识别单张图片，返回拼接文本。"""
    result = ocr.ocr(image_path, cls=True)
    texts: list[str] = []
    if result and result[0]:
        for line in result[0]:
            if line:
                texts.append(line[1][0])
    return "\n".join(texts)


def _tesseract_ocr_image(image: "Image.Image") -> str:
    """使用 Tesseract 识别单张图片。"""
    if pytesseract is None or Image is None:
        raise RuntimeError("Tesseract or PIL not installed")
    return pytesseract.image_to_string(image, lang="chi_sim+eng")


def extract_text_with_ocr(
    file_path: str | Path,
    dpi: int = 300,
    use_paddle: bool = True,
    use_tesseract: bool = True,
) -> Optional[str]:
    """将 PDF 页面转为图片后使用 OCR 提取文本。

    优先尝试 PaddleOCR（中文场景效果较好），不可用则回退到 Tesseract。
    若 pdf2image 或所有 OCR 引擎均不可用，返回 None。
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    if convert_from_path is None:
        logger.warning("pdf2image not installed; cannot perform OCR fallback")
        return None

    try:
        images = convert_from_path(str(path), dpi=dpi)
    except Exception as exc:
        logger.warning("Failed to convert PDF pages to images: %s", exc)
        return None

    if not images:
        return None

    text_parts: list[str] = []

    # PaddleOCR 实例化开销较大，尽量复用一次
    paddle_ocr = None
    if use_paddle and PaddleOCR is not None:
        try:
            paddle_ocr = PaddleOCR(
                use_angle_cls=True,
                lang="ch",
                show_log=False,
            )
        except Exception as exc:
            logger.warning("Failed to initialize PaddleOCR: %s", exc)

    for idx, image in enumerate(images):
        page_text = ""
        if paddle_ocr is not None:
            try:
                import tempfile

                with tempfile.NamedTemporaryFile(
                    suffix=".png", delete=False
                ) as tmp:
                    tmp_path = tmp.name
                image.save(tmp_path, "PNG")
                page_text = _paddle_ocr_image(paddle_ocr, tmp_path)
                Path(tmp_path).unlink(missing_ok=True)
            except Exception as exc:
                logger.warning("PaddleOCR failed on page %s: %s", idx + 1, exc)

        if not page_text.strip() and use_tesseract and pytesseract is not None:
            try:
                page_text = _tesseract_ocr_image(image)
            except Exception as exc:
                logger.warning("Tesseract failed on page %s: %s", idx + 1, exc)

        if page_text.strip():
            text_parts.append(page_text.strip())

    return "\n".join(text_parts) if text_parts else None


def is_ocr_available() -> bool:
    """检查当前环境是否具备 OCR 兜底能力。"""
    if convert_from_path is None:
        return False
    return PaddleOCR is not None or pytesseract is not None
