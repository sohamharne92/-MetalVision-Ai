"""
Tests for modules/utils.py — formatting helpers, color helpers, HTML builders.
"""
import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.utils import (
    format_timestamp, format_confidence, format_inspection_id,
    get_defect_color, get_decision_color, get_position_status_color,
    get_chart_colors_defects, get_chart_colors_custom,
    validate_inspection_data, validate_position_result,
    get_defect_summary_text, get_defect_severity_rank,
    create_badge_html, create_status_indicator_html, create_metric_html,
)


class TestFormatTimestamp:
    def test_valid_iso_returns_formatted(self):
        result = format_timestamp("2024-06-15T14:30:00")
        assert "2024-06-15" in result
        assert "14:30:00" in result

    def test_invalid_returns_original(self):
        result = format_timestamp("not-a-date")
        assert result == "not-a-date"

    def test_empty_string(self):
        result = format_timestamp("")
        assert isinstance(result, str)


class TestFormatConfidence:
    def test_zero_returns_zero_percent(self):
        assert format_confidence(0) == "0.0%"

    def test_one_returns_100_percent(self):
        assert format_confidence(1.0) == "100.0%"

    def test_decimal_rounded_to_one_place(self):
        assert format_confidence(0.856) == "85.6%"

    def test_string_float_works(self):
        assert format_confidence("0.75") == "75.0%"


class TestFormatInspectionId:
    def test_prepends_ins(self):
        result = format_inspection_id("abc12345")
        assert result == "INS-ABC12345"


class TestColorHelpers:
    def test_get_defect_color_normal(self):
        c = get_defect_color("Normal")
        assert c.startswith("#")

    def test_get_defect_color_crack(self):
        c = get_defect_color("Crack")
        assert c.startswith("#")

    def test_get_defect_color_unknown_returns_hex(self):
        c = get_defect_color("Unknown")
        assert c.startswith("#")

    def test_get_decision_color_accept(self):
        c = get_decision_color("ACCEPT")
        assert c.startswith("#")

    def test_get_decision_color_reject(self):
        c = get_decision_color("REJECT")
        assert c.startswith("#")

    def test_accept_and_reject_different_colors(self):
        assert get_decision_color("ACCEPT") != get_decision_color("REJECT")

    def test_get_position_status_colors_are_hex(self):
        for status in ["Pending", "Inspecting", "Normal", "Defect"]:
            c = get_position_status_color(status)
            assert c.startswith("#"), f"Color for {status} is not hex: {c}"

    def test_chart_colors_defects_has_four(self):
        colors = get_chart_colors_defects()
        assert len(colors) == 4
        assert all(c.startswith("#") for c in colors)

    def test_chart_colors_custom_respects_count(self):
        for n in [1, 3, 6, 10]:
            colors = get_chart_colors_custom(n)
            assert len(colors) == n


class TestValidation:
    def test_validate_inspection_data_valid(self, sample_inspection):
        assert validate_inspection_data(sample_inspection) is True

    def test_validate_inspection_data_missing_key(self, sample_inspection):
        del sample_inspection["final_decision"]
        assert validate_inspection_data(sample_inspection) is False

    def test_validate_inspection_data_wrong_position_count(self, sample_inspection):
        sample_inspection["positions"] = {0: {"class": "Normal"}}
        assert validate_inspection_data(sample_inspection) is False

    def test_validate_position_result_valid(self):
        p = {"angle": 90, "class": "Normal", "confidence": 0.95}
        assert validate_position_result(p) is True

    def test_validate_position_result_missing_confidence(self):
        p = {"angle": 90, "class": "Normal"}
        assert validate_position_result(p) is False


class TestDefectAnalysis:
    def test_no_defects_returns_no_defects_text(self):
        summary = {"Normal": 12, "Crack": 0, "Dent": 0, "Scratch": 0}
        text = get_defect_summary_text(summary)
        assert text == "No defects detected"

    def test_one_defect_in_text(self):
        summary = {"Normal": 11, "Crack": 1, "Dent": 0, "Scratch": 0}
        text = get_defect_summary_text(summary)
        assert "Crack" in text

    def test_severity_rank_sorted_descending(self):
        summary = {"Crack": 3, "Dent": 1, "Scratch": 5}
        ranked  = get_defect_severity_rank(summary)
        counts  = [c for _, c in ranked]
        assert counts == sorted(counts, reverse=True)

    def test_severity_rank_excludes_normal(self):
        summary = {"Normal": 10, "Crack": 2}
        ranked  = get_defect_severity_rank(summary)
        names   = [n for n, _ in ranked]
        assert "Normal" not in names


class TestHtmlBuilders:
    def test_create_badge_html_contains_text(self):
        html = create_badge_html("ACCEPT")
        assert "ACCEPT" in html

    def test_create_badge_html_contains_color(self):
        html = create_badge_html("TEST", color="#34d399")
        assert "#34d399" in html

    def test_create_status_indicator_html_contains_status(self):
        html = create_status_indicator_html("Online", "#34d399")
        assert "Online" in html

    def test_create_metric_html_contains_label_and_value(self):
        html = create_metric_html("Total", 42, color="#f5a623")
        assert "Total" in html
        assert "42" in html
