"""
Tests for config.py — constants, decision logic, color helpers.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    INSPECTION_POSITIONS, TOTAL_POSITIONS,
    DEFECT_CLASSES, CONFIDENCE_NORMAL_RANGE, CONFIDENCE_DEFECT_RANGE,
    COLOR_ACCEPT, COLOR_REJECT, COLOR_WARNING,
    CHART_COLOR_NORMAL, CHART_COLOR_CRACK, CHART_COLOR_DENT, CHART_COLOR_SCRATCH,
    COLOR_CRACK, COLOR_DENT, COLOR_SCRATCH,
    get_final_decision, get_defect_color, get_status_color,
    DEMO_SCENARIOS, PRODUCT_NAME, VERSION,
)


class TestConstants:
    def test_inspection_positions_count(self):
        assert len(INSPECTION_POSITIONS) == 12

    def test_inspection_positions_values(self):
        assert INSPECTION_POSITIONS == list(range(0, 360, 30))

    def test_total_positions_matches(self):
        assert TOTAL_POSITIONS == len(INSPECTION_POSITIONS)

    def test_defect_classes_has_four(self):
        assert set(DEFECT_CLASSES.keys()) == {"Normal", "Crack", "Dent", "Scratch"}

    def test_confidence_ranges_valid(self):
        lo, hi = CONFIDENCE_NORMAL_RANGE
        assert 0 < lo < hi <= 1.0
        lo2, hi2 = CONFIDENCE_DEFECT_RANGE
        assert 0 < lo2 < hi2 <= 1.0

    def test_version_is_string(self):
        assert isinstance(VERSION, str)
        assert len(VERSION) > 0

    def test_product_name_is_metalvision(self):
        assert "METALVISION" in PRODUCT_NAME

    def test_color_aliases_match_chart_colors(self):
        assert COLOR_CRACK   == CHART_COLOR_CRACK
        assert COLOR_DENT    == CHART_COLOR_DENT
        assert COLOR_SCRATCH == CHART_COLOR_SCRATCH

    def test_demo_scenarios_has_five(self):
        assert len(DEMO_SCENARIOS) == 5

    def test_demo_scenarios_have_required_keys(self):
        for name, sc in DEMO_SCENARIOS.items():
            assert "description"    in sc
            assert "defects"        in sc
            assert "expected_result" in sc


class TestGetFinalDecision:
    def test_all_normal_returns_accept(self):
        data = {
            a: {"angle": a, "class": "Normal", "confidence": 0.95}
            for a in INSPECTION_POSITIONS
        }
        assert get_final_decision(data) == "ACCEPT"

    def test_one_crack_returns_reject(self):
        data = {
            a: {"angle": a, "class": "Normal", "confidence": 0.95}
            for a in INSPECTION_POSITIONS
        }
        data[90] = {"angle": 90, "class": "Crack", "confidence": 0.88}
        assert get_final_decision(data) == "REJECT"

    def test_one_dent_returns_reject(self):
        data = {a: {"class": "Normal"} for a in INSPECTION_POSITIONS}
        data[180] = {"class": "Dent"}
        assert get_final_decision(data) == "REJECT"

    def test_one_scratch_returns_reject(self):
        data = {a: {"class": "Normal"} for a in INSPECTION_POSITIONS}
        data[270] = {"class": "Scratch"}
        assert get_final_decision(data) == "REJECT"

    def test_multiple_defects_returns_reject(self):
        data = {a: {"class": "Normal"} for a in INSPECTION_POSITIONS}
        data[60]  = {"class": "Dent"}
        data[210] = {"class": "Scratch"}
        data[330] = {"class": "Crack"}
        assert get_final_decision(data) == "REJECT"

    def test_empty_dict_returns_accept(self):
        assert get_final_decision({}) == "ACCEPT"

    def test_non_dict_values_ignored(self):
        data = {0: "Normal", 30: None, 60: 42}
        assert get_final_decision(data) == "ACCEPT"


class TestGetDefectColor:
    def test_normal_returns_green(self):
        assert get_defect_color("Normal") == CHART_COLOR_NORMAL

    def test_crack_returns_red(self):
        assert get_defect_color("Crack") == CHART_COLOR_CRACK

    def test_dent_returns_amber(self):
        assert get_defect_color("Dent") == CHART_COLOR_DENT

    def test_scratch_returns_purple(self):
        assert get_defect_color("Scratch") == CHART_COLOR_SCRATCH

    def test_unknown_returns_fallback(self):
        result = get_defect_color("Unknown")
        assert isinstance(result, str)
        assert result.startswith("#")


class TestGetStatusColor:
    def test_accept_returns_color(self):
        assert get_status_color("ACCEPT") == COLOR_ACCEPT

    def test_reject_returns_color(self):
        assert get_status_color("REJECT") == COLOR_REJECT

    def test_unknown_returns_fallback(self):
        result = get_status_color("UNKNOWN")
        assert isinstance(result, str)
        assert result.startswith("#")
