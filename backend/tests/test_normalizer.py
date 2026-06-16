import pytest

from app.services.normalizer import BiomarkerNormalizer, UNIT_CONVERSIONS


class TestBiomarkerMatching:
    def test_match_by_chinese_name(self, normalizer):
        matched = normalizer.match_biomarker("血红蛋白")
        assert matched is not None
        assert matched["code"] == "HGB"

    def test_match_by_english_alias(self, normalizer):
        matched = normalizer.match_biomarker("white blood cell")
        assert matched is not None
        assert matched["code"] == "WBC"

    def test_match_by_code(self, normalizer):
        matched = normalizer.match_biomarker("HDL-C")
        assert matched is not None
        assert matched["code"] == "HDL-C"

    def test_no_match(self, normalizer):
        matched = normalizer.match_biomarker("不存在的指标")
        assert matched is None


class TestUnitConversion:
    @pytest.mark.parametrize(
        "code,value,unit,expected_value,expected_unit",
        [
            ("HGB", "14.0", "g/dL", 140.0, "g/L"),
            ("TC", "200", "mg/dL", pytest.approx(5.17, 0.01), "mmol/L"),
            ("TG", "150", "mg/dL", pytest.approx(1.69, 0.01), "mmol/L"),
            ("CREA", "1.2", "mg/dL", pytest.approx(106.10, 0.01), "μmol/L"),
            ("UA", "6.0", "mg/dL", pytest.approx(356.88, 0.01), "μmol/L"),
            ("GLU", "90", "mg/dL", 5.0, "mmol/L"),
            ("HDL-C", "60", "mg/dL", pytest.approx(1.55, 0.01), "mmol/L"),
            ("LDL-C", "100", "mg/dL", pytest.approx(2.59, 0.01), "mmol/L"),
        ],
    )
    def test_common_conversions(self, normalizer, code, value, unit, expected_value, expected_unit):
        converted, std_unit = normalizer.normalize_value(code, value, unit)
        assert converted == expected_value
        assert std_unit == expected_unit

    def test_standard_unit_unchanged(self, normalizer):
        converted, std_unit = normalizer.normalize_value("WBC", "6.5", "10^9/L")
        assert converted == 6.5
        assert std_unit == "10^9/L"

    def test_unit_case_insensitive(self, normalizer):
        converted, std_unit = normalizer.normalize_value("HGB", "140", "g/l")
        assert converted == 140.0
        assert std_unit == "g/L"

    def test_invalid_value_returns_none(self, normalizer):
        converted, std_unit = normalizer.normalize_value("HGB", "N/A", "g/L")
        assert converted is None
        assert std_unit is None


class TestStatusDetermination:
    def test_high_status(self, normalizer):
        status = normalizer.determine_status("HGB", 200)
        assert status == "high"

    def test_low_status(self, normalizer):
        status = normalizer.determine_status("HGB", 50)
        assert status == "low"

    def test_normal_status(self, normalizer):
        status = normalizer.determine_status("HGB", 140)
        assert status == "normal"

    def test_direction_high_only(self, normalizer):
        # TC 只有 reference_high，direction=high，低于下限仍应视为 normal
        status = normalizer.determine_status("TC", 1.0)
        assert status == "normal"

    def test_direction_low_only(self, normalizer):
        # HDL-C 只有 reference_low，direction=low，高于上限仍应视为 normal
        status = normalizer.determine_status("HDL-C", 5.0)
        assert status == "normal"


class TestNormalizeExtracted:
    def test_normalize_extracted(self, normalizer):
        extracted = [
            {
                "original_name": "血红蛋白",
                "original_value": "140",
                "original_unit": "g/L",
            }
        ]
        results = normalizer.normalize_extracted(extracted)
        assert len(results) == 1
        assert results[0]["biomarker_code"] == "HGB"
        assert results[0]["value"] == 140.0
        assert results[0]["status"] == "normal"

    def test_normalize_extracted_skips_unknown(self, normalizer):
        extracted = [
            {"original_name": "未知指标", "original_value": "10", "original_unit": "U/L"}
        ]
        results = normalizer.normalize_extracted(extracted)
        assert len(results) == 0


class TestUnitConversionsCoverage:
    def test_conversion_keys_have_aliases(self, normalizer):
        """UNIT_CONVERSIONS 中的每个原始单位都应在对应指标的 unit_aliases 中出现。"""
        for code, conversions in UNIT_CONVERSIONS.items():
            definition = normalizer.get_biomarker_by_code(code)
            assert definition is not None, f"{code} not in dictionary"
            aliases = definition.get("unit_aliases", [])
            for source_unit in conversions.keys():
                normalized_aliases = {BiomarkerNormalizer._normalize_text(a) for a in aliases}
                assert (
                    BiomarkerNormalizer._normalize_text(source_unit) in normalized_aliases
                ), f"{source_unit} not in aliases for {code}"
