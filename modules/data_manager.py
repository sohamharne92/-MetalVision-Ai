"""
METALVISION AI - Data Manager Module
Handles CSV persistence, filtering, statistics, and session management.
"""

import csv
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st

# ---------------------------------------------------------------------------
# Defaults (overridden by config.py when available)
# ---------------------------------------------------------------------------
_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
_CSV_PATH = os.path.join(_DATA_DIR, "inspection_history.csv")

CSV_COLUMNS = [
    "inspection_id",
    "timestamp",
    "part_id",
    "scenario",
    "decision",
    "confidence",
    "defects_found",
    "defect_types",
    "positions_inspected",
    "defect_positions",
    "notes",
]


# ===========================================================================
# InspectionDataManager – CSV-backed persistence
# ===========================================================================

class InspectionDataManager:
    """
    Manages persistent inspection records stored in a CSV file.

    All public methods are safe to call before the CSV is created;
    ``ensure_csv_exists()`` is called automatically when needed.
    """

    def __init__(self, csv_path: str = _CSV_PATH):
        self.csv_path = csv_path
        self.ensure_csv_exists()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def ensure_csv_exists(self) -> None:
        """Create the data directory and CSV file with headers if missing."""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        if not os.path.exists(self.csv_path):
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()

    def _read_all_rows(self) -> List[Dict[str, str]]:
        """Return all rows as a list of dicts (raw strings)."""
        self.ensure_csv_exists()
        try:
            with open(self.csv_path, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception:
            return []

    @staticmethod
    def _parse_row(row: Dict[str, str]) -> Dict[str, Any]:
        """Cast string values from CSV into proper Python types."""
        parsed = dict(row)
        try:
            parsed["confidence"] = float(row.get("confidence", 0))
        except (ValueError, TypeError):
            parsed["confidence"] = 0.0
        try:
            parsed["defects_found"] = int(row.get("defects_found", 0))
        except (ValueError, TypeError):
            parsed["defects_found"] = 0
        try:
            raw = row.get("defect_types", "[]")
            parsed["defect_types"] = json.loads(raw) if raw.startswith("[") else []
        except (ValueError, json.JSONDecodeError):
            parsed["defect_types"] = []
        try:
            raw = row.get("defect_positions", "[]")
            parsed["defect_positions"] = json.loads(raw) if raw.startswith("[") else []
        except (ValueError, json.JSONDecodeError):
            parsed["defect_positions"] = []
        return parsed

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def add_inspection(self, inspection: Dict[str, Any]) -> bool:
        """
        Append a single inspection record to the CSV.

        Parameters
        ----------
        inspection : dict
            Must contain at minimum ``inspection_id``, ``decision``,
            ``confidence``, and ``timestamp``.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        self.ensure_csv_exists()
        try:
            row = {col: "" for col in CSV_COLUMNS}
            for key in CSV_COLUMNS:
                val = inspection.get(key, "")
                if isinstance(val, (list, dict)):
                    val = json.dumps(val)
                row[key] = str(val)
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writerow(row)
            return True
        except Exception as exc:
            st.error(f"Failed to save inspection: {exc}")
            return False

    def clear_history(self) -> bool:
        """
        Delete all inspection records (rewrites headers only).

        Returns
        -------
        bool
            True on success.
        """
        try:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
                writer.writeheader()
            return True
        except Exception as exc:
            st.error(f"Failed to clear history: {exc}")
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_all_inspections(self) -> List[Dict[str, Any]]:
        """Return all inspections sorted newest-first."""
        rows = self._read_all_rows()
        parsed = [self._parse_row(r) for r in rows]
        parsed.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return parsed

    def get_inspection_by_id(self, inspection_id: str) -> Optional[Dict[str, Any]]:
        """Return the first inspection matching ``inspection_id``, or None."""
        for row in self._read_all_rows():
            if row.get("inspection_id") == inspection_id:
                return self._parse_row(row)
        return None

    def get_inspections_filtered(
        self,
        decision: Optional[str] = None,
        defect_type: Optional[str] = None,
        min_confidence: float = 0.0,
        max_confidence: float = 1.0,
        search_id: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Return inspections matching all supplied filters.

        Parameters
        ----------
        decision : str | None
            "ACCEPT", "REJECT", or None for all.
        defect_type : str | None
            Match records that contain this defect type.
        min_confidence / max_confidence : float
            Inclusive confidence range [0, 1].
        search_id : str
            Substring match against ``inspection_id``.
        """
        results = self.get_all_inspections()
        if decision:
            results = [r for r in results if r.get("decision") == decision]
        if defect_type and defect_type != "All":
            results = [
                r for r in results
                if defect_type in r.get("defect_types", [])
            ]
        results = [
            r for r in results
            if min_confidence <= r.get("confidence", 0) <= max_confidence
        ]
        if search_id:
            results = [
                r for r in results
                if search_id.lower() in r.get("inspection_id", "").lower()
            ]
        return results

    # ------------------------------------------------------------------
    # Aggregation / statistics
    # ------------------------------------------------------------------

    def get_statistics(self) -> Dict[str, Any]:
        """Return a summary statistics dict for the Overview Dashboard."""
        rows = self.get_all_inspections()
        total = len(rows)
        if total == 0:
            return {
                "total": 0, "accepted": 0, "rejected": 0,
                "acceptance_rate": 0.0, "avg_confidence": 0.0,
                "total_defects": 0,
            }
        accepted = sum(1 for r in rows if r.get("decision") == "ACCEPT")
        rejected = total - accepted
        avg_conf = sum(r.get("confidence", 0) for r in rows) / total
        total_defects = sum(r.get("defects_found", 0) for r in rows)
        return {
            "total": total,
            "accepted": accepted,
            "rejected": rejected,
            "acceptance_rate": round(accepted / total * 100, 1),
            "avg_confidence": round(avg_conf * 100, 1),
            "total_defects": total_defects,
        }

    def get_defect_distribution(self) -> Dict[str, int]:
        """Return a dict mapping defect type → occurrence count."""
        distribution: Dict[str, int] = {}
        for row in self.get_all_inspections():
            for dtype in row.get("defect_types", []):
                distribution[dtype] = distribution.get(dtype, 0) + 1
        return distribution

    def get_trend_data(self, last_n: int = 20) -> List[Dict[str, Any]]:
        """
        Return the most recent ``last_n`` inspections in chronological
        order for trend charts.
        """
        rows = self.get_all_inspections()[:last_n]
        rows.reverse()
        return rows

    # ------------------------------------------------------------------
    # Export helpers
    # ------------------------------------------------------------------

    def export_to_csv(self) -> str:
        """Return the raw CSV content as a string."""
        try:
            with open(self.csv_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def export_to_json(self) -> str:
        """Return all inspections serialised as a JSON string."""
        rows = self.get_all_inspections()
        return json.dumps(rows, indent=2, default=str)


# ===========================================================================
# SessionDataManager – in-memory / Streamlit session_state
# ===========================================================================

class SessionDataManager:
    """
    Thin wrapper around ``st.session_state`` for managing the current
    inspection session without touching the CSV.
    """

    _SESSION_KEY = "_metalvision_session"

    def _get_store(self) -> Dict[str, Any]:
        if self._SESSION_KEY not in st.session_state:
            st.session_state[self._SESSION_KEY] = {
                "inspections": [],
                "current": None,
            }
        return st.session_state[self._SESSION_KEY]

    def init_inspection_session(self) -> None:
        """Reset the in-session inspection list."""
        st.session_state[self._SESSION_KEY] = {
            "inspections": [],
            "current": None,
        }

    def save_current_inspection(self, inspection: Dict[str, Any]) -> None:
        """Save ``inspection`` as the current record and append to session list."""
        store = self._get_store()
        store["current"] = inspection
        store["inspections"].append(inspection)

    def get_current_inspection(self) -> Optional[Dict[str, Any]]:
        """Return the most recently saved inspection, or None."""
        return self._get_store().get("current")

    def get_inspection_list(self) -> List[Dict[str, Any]]:
        """Return all inspections saved this session."""
        return self._get_store().get("inspections", [])

    def clear_session(self) -> None:
        """Clear all in-session inspections."""
        self.init_inspection_session()
