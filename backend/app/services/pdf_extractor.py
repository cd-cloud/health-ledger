import logging
from pathlib import Path
from typing import Optional

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None  # type: ignore

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    from PyPDF2 import PdfReader  # type: ignore

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str | Path) -> str:
    """优先使用 pdfplumber 提取文本，失败则回退到 pypdf。"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    text = ""
    if pdfplumber is not None:
        try:
            with pdfplumber.open(path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            if text.strip():
                return text
        except Exception as exc:
            logger.warning("pdfplumber extraction failed: %s", exc)

    try:
        reader = PdfReader(str(path))
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as exc:
        logger.exception("pypdf extraction failed")
        raise RuntimeError(f"Failed to extract text from PDF: {exc}") from exc

    return text


def extract_report_date(text: str) -> Optional[str]:
    """从文本中尝试提取报告日期（YYYY-MM-DD），预留接口。"""
    import re
    patterns = [
        r"(\d{4})[\-/年](\d{1,2})[\-/月](\d{1,2})",
        r"(\d{4})(\d{2})(\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            year, month, day = match.groups()
            try:
                from datetime import datetime
                return datetime(int(year), int(month), int(day)).date().isoformat()
            except ValueError:
                continue
    return None
