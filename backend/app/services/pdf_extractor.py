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

from app.services.ocr_extractor import extract_text_with_ocr

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: str | Path, use_ocr_fallback: bool = True) -> str:
    """优先使用 pdfplumber 提取文本，失败则回退到 pypdf；若文本为空则尝试 OCR。"""
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

    if not text.strip() and use_ocr_fallback:
        logger.info("No text extracted from PDF; trying OCR fallback")
        ocr_text = extract_text_with_ocr(path)
        if ocr_text:
            return ocr_text
        logger.warning("OCR fallback produced no text")

    return text


def extract_report_date(text: str) -> Optional[str]:
    """从文本中尝试提取报告日期（YYYY-MM-DD）。

    优先匹配带报告日期关键词的日期；其次返回首个不紧邻出生日期
    关键词的日期，减少误取出生日期的概率。
    """
    import re
    from datetime import datetime

    report_date_keywords_cn = "报告日期|报告时间|检查日期|体检日期|采样日期|送检日期|检验日期|检测日期"
    report_date_keywords_en = "report date|test date|exam date|checkup date|report time"

    birth_date_keywords = [
        "出生日期",
        "出生",
        "birth",
        "date of birth",
        "dob",
    ]

    def _parse_date(groups):
        year, month, day = groups
        try:
            return datetime(int(year), int(month), int(day)).date().isoformat()
        except ValueError:
            return None

    def _is_birth_date(match_start: int, match_end: int, window: int = 18) -> bool:
        """检查日期前后小窗口内是否出现出生日期关键词（忽略空格）。"""
        ws = max(0, match_start - window)
        we = min(len(text), match_end + window)
        snippet = text[ws:we].lower().replace(" ", "")
        return any(kw.lower().replace(" ", "") in snippet for kw in birth_date_keywords)

    # 第一轮：显式匹配报告日期关键词 + 日期（中英文，支持带空格中文格式）
    explicit_patterns = [
        rf"(?:{report_date_keywords_cn})\s*[：:\s]\s*(\d{{4}})\s*年\s*(\d{{1,2}})\s*月\s*(\d{{1,2}})\s*日?",
        rf"(?:{report_date_keywords_cn})\s*[：:\s]\s*(\d{{4}})[\-/](\d{{1,2}})[\-/](\d{{1,2}})",
        rf"(?:{report_date_keywords_en})\s*[：:\s]\s*(\d{{4}})[\-/](\d{{1,2}})[\-/](\d{{1,2}})",
    ]
    for pattern in explicit_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            iso_date = _parse_date(match.groups())
            if iso_date:
                return iso_date

    # 第二轮：通用日期扫描，跳过紧邻出生日期关键词的日期
    generic_patterns = [
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?",
        r"(\d{4})[\-/](\d{1,2})[\-/](\d{1,2})",
        r"(\d{4})(\d{2})(\d{2})",
    ]
    for pattern in generic_patterns:
        for match in re.finditer(pattern, text):
            iso_date = _parse_date(match.groups())
            if iso_date and not _is_birth_date(match.start(), match.end()):
                return iso_date

    return None
