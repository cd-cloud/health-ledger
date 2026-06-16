import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import DOCS_DIR

logger = logging.getLogger(__name__)

# 原始单位 -> 标准单位的换算系数（乘以该系数）
# 系数基于临床常用换算关系，保留足够精度。
UNIT_CONVERSIONS: Dict[str, Dict[str, float]] = {
    "HGB": {"g/dL": 10.0},  # g/dL -> g/L
    "TC": {"mg/dL": 1.0 / 38.67},  # mg/dL -> mmol/L
    "TG": {"mg/dL": 1.0 / 88.57},
    "HDL-C": {"mg/dL": 1.0 / 38.67},
    "LDL-C": {"mg/dL": 1.0 / 38.67},
    "GLU": {"mg/dL": 1.0 / 18.0},
    "FBG": {"mg/dL": 1.0 / 18.0},
    "CREA": {"mg/dL": 88.42},
    "BUN": {"mg/dL": 1.0 / 2.8},
    "UA": {"mg/dL": 59.48},
    "CA": {"mg/dL": 1.0 / 4.0},
    "TBIL": {"mg/dL": 17.1},
    "DBIL": {"mg/dL": 17.1},
    "TP": {"g/dL": 10.0},
    "ALB": {"g/dL": 10.0},
}


def _load_dictionary(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    if path is None:
        path = DOCS_DIR / "biomarker_dictionary.example.json"
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("biomarkers", [])
    except Exception as exc:
        logger.warning("Failed to load biomarker dictionary: %s", exc)
        return []


class BiomarkerNormalizer:
    def __init__(self, dictionary: Optional[List[Dict[str, Any]]] = None):
        self.dictionary = dictionary or _load_dictionary()
        self._by_code: Dict[str, Dict[str, Any]] = {b["code"]: b for b in self.dictionary}
        self._alias_map: Dict[str, str] = {}
        for b in self.dictionary:
            for alias in b.get("aliases", []):
                self._alias_map[self._normalize_text(alias)] = b["code"]
            self._alias_map[self._normalize_text(b["name"])] = b["code"]
            self._alias_map[self._normalize_text(b["code"])] = b["code"]

    @staticmethod
    def _normalize_text(text: str) -> str:
        """统一文本：小写、去空白、去括号、去星号、统一希腊字母 μ。"""
        return (
            text.lower()
            .replace(" ", "")
            .replace("(", "")
            .replace(")", "")
            .replace("*", "")
            .replace("μ", "u")
        )

    def match_biomarker(self, original_name: str) -> Optional[Dict[str, Any]]:
        key = self._normalize_text(original_name)
        code = self._alias_map.get(key)
        if code:
            return self._by_code.get(code)
        # 模糊前缀匹配
        for alias, code in self._alias_map.items():
            if key in alias or alias in key:
                return self._by_code.get(code)
        return None

    def normalize_value(
        self,
        biomarker_code: str,
        value_text: str,
        original_unit: str,
    ) -> Tuple[Optional[float], Optional[str]]:
        try:
            value = float(str(value_text).replace(",", ""))
        except (ValueError, TypeError):
            return None, None

        definition = self._by_code.get(biomarker_code)
        if not definition:
            return value, original_unit

        standard_unit = definition["unit_standard"]
        matched_unit = self._match_unit(original_unit, definition)

        # 如果原始单位不是标准单位，尝试按 UNIT_CONVERSIONS 换算
        if matched_unit != standard_unit:
            conversion = UNIT_CONVERSIONS.get(biomarker_code, {}).get(matched_unit)
            if conversion is not None:
                value = value * conversion
            else:
                # 没有换算系数时保留原值，但日志记录单位不一致
                logger.debug(
                    "No conversion factor for %s from %s to %s",
                    biomarker_code,
                    matched_unit,
                    standard_unit,
                )
        return value, standard_unit

    def _match_unit(self, original_unit: str, definition: Dict[str, Any]) -> str:
        """返回与 original_unit 匹配的单位别名（未匹配则返回 original_unit）。"""
        unit_key = self._normalize_text(original_unit)
        if not unit_key:
            return definition["unit_standard"]

        standard_unit = definition["unit_standard"]
        if unit_key == self._normalize_text(standard_unit):
            return standard_unit

        for alias in definition.get("unit_aliases", []):
            if unit_key == self._normalize_text(alias):
                return alias
        return original_unit

    def determine_status(
        self,
        biomarker_code: str,
        value: float,
    ) -> Optional[str]:
        definition = self._by_code.get(biomarker_code)
        if not definition:
            return None

        low = definition.get("reference_low")
        high = definition.get("reference_high")
        direction = definition.get("direction", "both")

        if low is not None and value < low:
            if direction in ("both", "low"):
                return "low"
        if high is not None and value > high:
            if direction in ("both", "high"):
                return "high"
        return "normal"

    def normalize_extracted(
        self,
        extracted: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        results = []
        for item in extracted:
            original_name = item.get("original_name", "")
            original_value = item.get("original_value", "")
            original_unit = item.get("original_unit", "")
            matched = self.match_biomarker(original_name)
            if not matched:
                logger.debug("No biomarker match for: %s", original_name)
                continue

            value, unit = self.normalize_value(
                matched["code"], original_value, original_unit
            )
            if value is None:
                continue

            status = self.determine_status(matched["code"], value)
            results.append(
                {
                    "biomarker_code": matched["code"],
                    "original_name": original_name,
                    "original_value_text": str(original_value),
                    "original_unit": original_unit,
                    "value": value,
                    "unit": unit,
                    "reference_low": matched.get("reference_low"),
                    "reference_high": matched.get("reference_high"),
                    "status": status,
                    "is_reviewed": False,
                }
            )
        return results

    def get_biomarker_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        return self._by_code.get(code)

    def list_biomarkers(self) -> List[Dict[str, Any]]:
        return self.dictionary
