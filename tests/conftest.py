"""
Shared pytest fixtures for METALVISION AI test suite.
"""
import os
import sys
import csv
import uuid
import tempfile
import pytest
from datetime import datetime
from pathlib import Path

# Add project root to sys.path so imports work without installation
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Sample inspection result (matches simulator output) ───────────────────────
SAMPLE_POSITIONS = {
    a: {"angle": a, "class": "Normal", "confidence": 0.95,
        "timestamp": datetime.now().isoformat()}
    for a in [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330]
}

SAMPLE_WITH_DEFECT = {
    **SAMPLE_POSITIONS,
    90: {"angle": 90, "class": "Crack", "confidence": 0.89,
         "timestamp": datetime.now().isoformat()},
}


@pytest.fixture
def sample_inspection():
    """Minimal valid inspection summary dict (all normal)."""
    return {
        "inspection_id":    str(uuid.uuid4())[:8],
        "timestamp":        datetime.now().isoformat(),
        "positions":        dict(SAMPLE_POSITIONS),
        "overall_confidence": 0.95,
        "defect_count":     0,
        "final_decision":   "ACCEPT",
        "total_positions":  12,
    }


@pytest.fixture
def sample_inspection_with_defect():
    """Inspection summary with one crack at 90°."""
    return {
        "inspection_id":    str(uuid.uuid4())[:8],
        "timestamp":        datetime.now().isoformat(),
        "positions":        dict(SAMPLE_WITH_DEFECT),
        "overall_confidence": 0.91,
        "defect_count":     1,
        "final_decision":   "REJECT",
        "total_positions":  12,
    }


@pytest.fixture
def tmp_csv(tmp_path):
    """Temporary CSV file path for data_manager tests."""
    return str(tmp_path / "test_history.csv")


@pytest.fixture
def csv_with_records(tmp_csv):
    """CSV pre-populated with 3 inspection records."""
    from modules.data_manager import InspectionDataManager, CSV_COLUMNS
    dm = InspectionDataManager(csv_path=tmp_csv)
    records = [
        {
            "inspection_id":       str(uuid.uuid4())[:8],
            "timestamp":           datetime.now().isoformat(),
            "part_id":             f"PART-001",
            "scenario":            "Scenario 1: Normal Product",
            "decision":            "ACCEPT",
            "confidence":          0.96,
            "defects_found":       0,
            "defect_types":        [],
            "positions_inspected": 12,
            "defect_positions":    [],
            "notes":               "",
        },
        {
            "inspection_id":       str(uuid.uuid4())[:8],
            "timestamp":           datetime.now().isoformat(),
            "part_id":             "PART-002",
            "scenario":            "Scenario 2: Scratch Defect",
            "decision":            "REJECT",
            "confidence":          0.88,
            "defects_found":       1,
            "defect_types":        ["Scratch"],
            "positions_inspected": 12,
            "defect_positions":    [90],
            "notes":               "",
        },
        {
            "inspection_id":       str(uuid.uuid4())[:8],
            "timestamp":           datetime.now().isoformat(),
            "part_id":             "PART-003",
            "scenario":            "Scenario 4: Multiple Defects",
            "decision":            "REJECT",
            "confidence":          0.82,
            "defects_found":       2,
            "defect_types":        ["Crack", "Dent"],
            "positions_inspected": 12,
            "defect_positions":    [60, 330],
            "notes":               "",
        },
    ]
    for r in records:
        dm.add_inspection(r)
    return dm, records
