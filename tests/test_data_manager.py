"""
Tests for modules/data_manager.py — InspectionDataManager & SessionDataManager.
"""
import pytest
import uuid
import json
import sys
from pathlib import Path
from datetime import datetime
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.data_manager import InspectionDataManager, SessionDataManager, CSV_COLUMNS


# ── Helpers ───────────────────────────────────────────────────────────────────
def make_record(**overrides):
    base = {
        "inspection_id":       str(uuid.uuid4())[:8],
        "timestamp":           datetime.now().isoformat(),
        "part_id":             "PART-TEST",
        "scenario":            "Scenario 1: Normal Product",
        "decision":            "ACCEPT",
        "confidence":          0.95,
        "defects_found":       0,
        "defect_types":        [],
        "positions_inspected": 12,
        "defect_positions":    [],
        "notes":               "",
    }
    base.update(overrides)
    return base


# ══════════════════════════════════════════════════════════════════════════════
# InspectionDataManager
# ══════════════════════════════════════════════════════════════════════════════
class TestCSVCreation:
    def test_csv_created_on_init(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        assert Path(tmp_csv).exists()

    def test_csv_has_header(self, tmp_csv):
        InspectionDataManager(csv_path=tmp_csv)
        with open(tmp_csv) as f:
            header = f.readline().strip().split(",")
        for col in CSV_COLUMNS:
            assert col in header


class TestAddInspection:
    def test_add_returns_true(self, tmp_csv):
        dm  = InspectionDataManager(csv_path=tmp_csv)
        rec = make_record()
        assert dm.add_inspection(rec) is True

    def test_record_retrievable_after_add(self, tmp_csv):
        dm  = InspectionDataManager(csv_path=tmp_csv)
        rec = make_record()
        dm.add_inspection(rec)
        rows = dm.get_all_inspections()
        assert len(rows) == 1
        assert rows[0]["inspection_id"] == rec["inspection_id"]

    def test_multiple_records_accumulate(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        for _ in range(5):
            dm.add_inspection(make_record())
        assert len(dm.get_all_inspections()) == 5

    def test_list_fields_serialised_as_json(self, tmp_csv):
        dm  = InspectionDataManager(csv_path=tmp_csv)
        rec = make_record(defect_types=["Crack", "Dent"], defect_positions=[90, 180])
        dm.add_inspection(rec)
        row = dm.get_all_inspections()[0]
        assert row["defect_types"]     == ["Crack", "Dent"]
        assert row["defect_positions"] == [90, 180]


class TestGetAllInspections:
    def test_empty_returns_empty_list(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        assert dm.get_all_inspections() == []

    def test_sorted_newest_first(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        r1 = make_record(timestamp="2024-01-01T10:00:00")
        r2 = make_record(timestamp="2024-06-01T10:00:00")
        dm.add_inspection(r1)
        dm.add_inspection(r2)
        rows = dm.get_all_inspections()
        assert rows[0]["timestamp"] > rows[1]["timestamp"]


class TestGetInspectionById:
    def test_finds_existing_record(self, tmp_csv):
        dm  = InspectionDataManager(csv_path=tmp_csv)
        rec = make_record()
        dm.add_inspection(rec)
        found = dm.get_inspection_by_id(rec["inspection_id"])
        assert found is not None
        assert found["inspection_id"] == rec["inspection_id"]

    def test_returns_none_for_missing(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        assert dm.get_inspection_by_id("nonexistent") is None


class TestGetInspectionsFiltered:
    def test_filter_by_accept(self, csv_with_records):
        dm, _ = csv_with_records
        results = dm.get_inspections_filtered(decision="ACCEPT")
        assert all(r["decision"] == "ACCEPT" for r in results)
        assert len(results) == 1

    def test_filter_by_reject(self, csv_with_records):
        dm, _ = csv_with_records
        results = dm.get_inspections_filtered(decision="REJECT")
        assert all(r["decision"] == "REJECT" for r in results)
        assert len(results) == 2

    def test_filter_by_defect_type(self, csv_with_records):
        dm, _ = csv_with_records
        results = dm.get_inspections_filtered(defect_type="Scratch")
        assert len(results) == 1
        assert "Scratch" in results[0]["defect_types"]

    def test_filter_by_min_confidence(self, csv_with_records):
        dm, _ = csv_with_records
        results = dm.get_inspections_filtered(min_confidence=0.90)
        assert all(r["confidence"] >= 0.90 for r in results)

    def test_filter_by_search_id(self, csv_with_records):
        dm, records = csv_with_records
        target_id = records[0]["inspection_id"]
        results = dm.get_inspections_filtered(search_id=target_id[:4])
        assert any(r["inspection_id"] == target_id for r in results)

    def test_no_filter_returns_all(self, csv_with_records):
        dm, records = csv_with_records
        results = dm.get_inspections_filtered()
        assert len(results) == len(records)


class TestGetStatistics:
    def test_empty_db_returns_zeros(self, tmp_csv):
        dm    = InspectionDataManager(csv_path=tmp_csv)
        stats = dm.get_statistics()
        assert stats["total"]     == 0
        assert stats["accepted"]  == 0
        assert stats["rejected"]  == 0

    def test_correct_counts(self, csv_with_records):
        dm, _ = csv_with_records
        stats = dm.get_statistics()
        assert stats["total"]    == 3
        assert stats["accepted"] == 1
        assert stats["rejected"] == 2

    def test_acceptance_rate_correct(self, csv_with_records):
        dm, _ = csv_with_records
        stats = dm.get_statistics()
        assert abs(stats["acceptance_rate"] - 33.3) < 1.0

    def test_avg_confidence_in_range(self, csv_with_records):
        dm, _ = csv_with_records
        stats = dm.get_statistics()
        assert 0 < stats["avg_confidence"] <= 100


class TestGetDefectDistribution:
    def test_returns_dict(self, csv_with_records):
        dm, _ = csv_with_records
        dist  = dm.get_defect_distribution()
        assert isinstance(dist, dict)

    def test_scratch_counted(self, csv_with_records):
        dm, _ = csv_with_records
        dist  = dm.get_defect_distribution()
        assert dist.get("Scratch", 0) >= 1

    def test_crack_counted(self, csv_with_records):
        dm, _ = csv_with_records
        dist  = dm.get_defect_distribution()
        assert dist.get("Crack", 0) >= 1


class TestExport:
    def test_export_csv_has_header(self, csv_with_records):
        dm, _ = csv_with_records
        csv_str = dm.export_to_csv()
        assert "inspection_id" in csv_str.splitlines()[0]

    def test_export_json_valid(self, csv_with_records):
        dm, _ = csv_with_records
        data = json.loads(dm.export_to_json())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_export_csv_all_rows(self, csv_with_records):
        dm, _ = csv_with_records
        lines = dm.export_to_csv().strip().splitlines()
        assert len(lines) == 4   # 1 header + 3 records


class TestClearHistory:
    def test_clear_removes_all_records(self, csv_with_records):
        dm, _ = csv_with_records
        assert len(dm.get_all_inspections()) == 3
        dm.clear_history()
        assert len(dm.get_all_inspections()) == 0

    def test_can_add_after_clear(self, csv_with_records):
        dm, _ = csv_with_records
        dm.clear_history()
        dm.add_inspection(make_record())
        assert len(dm.get_all_inspections()) == 1


class TestGetTrendData:
    def test_returns_list(self, csv_with_records):
        dm, _ = csv_with_records
        trend = dm.get_trend_data(10)
        assert isinstance(trend, list)

    def test_respects_limit(self, tmp_csv):
        dm = InspectionDataManager(csv_path=tmp_csv)
        for _ in range(10):
            dm.add_inspection(make_record())
        trend = dm.get_trend_data(5)
        assert len(trend) <= 5
