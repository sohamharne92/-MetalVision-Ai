"""
METALVISION AI - Utility Functions
Vintage Industrial Theme helpers
"""

from datetime import datetime

# ── Vintage palette (keeps utils self-contained) ──────────────────────────────
_COPPER   = "#b87333"
_COPPER_L = "#d4904a"
_AMBER    = "#f59e0b"
_ACCEPT   = "#4ade80"
_REJECT   = "#f87171"
_WARN     = "#fbbf24"
_TEXT2    = "#a08060"
_BG2      = "#221608"
_BORDER   = "#5a3a18"

# Also expose via config names so old imports still work
try:
    from config import (
        COLOR_ACCEPT, COLOR_REJECT, COLOR_WARNING, COLOR_ACCENT,
        COLOR_NORMAL, COLOR_DEFECT, COLOR_PENDING, COLOR_INSPECTING,
        CHART_COLOR_NORMAL, CHART_COLOR_CRACK, CHART_COLOR_DENT, CHART_COLOR_SCRATCH,
    )
except ImportError:
    COLOR_ACCEPT   = _ACCEPT
    COLOR_REJECT   = _REJECT
    COLOR_WARNING  = _AMBER
    COLOR_ACCENT   = _COPPER_L
    COLOR_NORMAL   = _ACCEPT
    COLOR_DEFECT   = _REJECT
    COLOR_PENDING  = "#6b5035"
    COLOR_INSPECTING = _AMBER
    CHART_COLOR_NORMAL  = _ACCEPT
    CHART_COLOR_CRACK   = _REJECT
    CHART_COLOR_DENT    = _AMBER
    CHART_COLOR_SCRATCH = "#c084fc"


# ── Formatting ────────────────────────────────────────────────────────────────

def format_timestamp(iso_timestamp: str) -> str:
    try:
        return datetime.fromisoformat(iso_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return iso_timestamp


def format_confidence(score) -> str:
    return f"{float(score) * 100:.1f}%"


def format_inspection_id(inspection_id: str) -> str:
    return f"INS-{inspection_id.upper()}"


def format_product_id(index: int) -> str:
    return f"PROD-2024-{str(index).zfill(5)}"


# ── Color helpers ─────────────────────────────────────────────────────────────

def get_defect_color(defect_class: str) -> str:
    return {
        "Normal":  CHART_COLOR_NORMAL,
        "Crack":   CHART_COLOR_CRACK,
        "Dent":    CHART_COLOR_DENT,
        "Scratch": CHART_COLOR_SCRATCH,
    }.get(defect_class, _COPPER_L)


def get_decision_color(decision: str) -> str:
    return {
        "ACCEPT": COLOR_ACCEPT,
        "REJECT": COLOR_REJECT,
        "REVIEW": _WARN,
    }.get(decision, _COPPER_L)


def get_position_status_color(status: str) -> str:
    return {
        "Pending":    COLOR_PENDING,
        "Inspecting": COLOR_INSPECTING,
        "Normal":     COLOR_NORMAL,
        "Defect":     COLOR_DEFECT,
    }.get(status, _COPPER_L)


def get_chart_colors_defects() -> list:
    return [CHART_COLOR_NORMAL, CHART_COLOR_CRACK, CHART_COLOR_DENT, CHART_COLOR_SCRATCH]


def get_chart_colors_custom(num_colors: int) -> list:
    palette = [_COPPER_L, _ACCEPT, _REJECT, _AMBER,
               "#818cf8", "#c084fc", "#22d3ee", "#fb923c"]
    return (palette * ((num_colors // len(palette)) + 1))[:num_colors]


# ── Data validation ───────────────────────────────────────────────────────────

def validate_inspection_data(inspection_data: dict) -> bool:
    required = ["inspection_id", "timestamp", "positions", "final_decision"]
    if not all(f in inspection_data for f in required):
        return False
    return len(inspection_data["positions"]) == 12


def validate_position_result(position_result: dict) -> bool:
    return all(f in position_result for f in ["angle", "class", "confidence"])


# ── Defect analysis ───────────────────────────────────────────────────────────

def get_defect_summary_text(defect_summary: dict) -> str:
    items = [f"{c} {n}" for n, c in defect_summary.items() if c > 0 and n != "Normal"]
    return ", ".join(items) if items else "No defects detected"


def get_defect_severity_rank(defect_summary: dict) -> list:
    return sorted(
        [(n, c) for n, c in defect_summary.items() if c > 0 and n != "Normal"],
        key=lambda x: x[1], reverse=True,
    )


# ── Vintage HTML components ───────────────────────────────────────────────────

def create_badge_html(text: str, color: str = _COPPER_L) -> str:
    """Vintage copper-style badge."""
    return (
        f'<span class="v-badge" '
        f'style="background:{color}22;color:{color};border:1px solid {color};">'
        f'{text}</span>'
    )


def create_status_indicator_html(status: str, color: str = _AMBER) -> str:
    """Dot + label status row."""
    return (
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'<div style="width:9px;height:9px;background:{color};border-radius:50%;'
        f'box-shadow:0 0 6px {color};flex-shrink:0;"></div>'
        f'<span style="font-family:Oswald,sans-serif;font-size:0.78rem;'
        f'letter-spacing:0.06em;color:{color};">{status}</span>'
        f'</div>'
    )


def create_metric_html(label: str, value, unit: str = "", color: str = _COPPER_L) -> str:
    """Vintage KPI card (matches .v-kpi CSS class style)."""
    return (
        f'<div class="v-kpi">'
        f'<div class="v-kpi-label">{label}</div>'
        f'<div class="v-kpi-value" style="color:{color};">{value}'
        f'{"<span style=\'font-size:1rem;margin-left:4px;\'>"+unit+"</span>" if unit else ""}'
        f'</div>'
        f'</div>'
    )


# ── Streamlit session state ───────────────────────────────────────────────────

def init_session_state() -> None:
    import streamlit as st
    defaults = {
        "inspection_data":         None,
        "inspection_history":      [],
        "current_inspection_id":   None,
        "inspection_in_progress":  False,
        "current_position_index":  0,
        "selected_scenario":       "Scenario 1: Normal Component",
        "last_saved_id":           None,
        "trigger_inspection":      False,
        "part_id_input":           "",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def add_to_inspection_history(inspection_data: dict) -> None:
    import streamlit as st
    if "inspection_history" not in st.session_state:
        st.session_state.inspection_history = []
    st.session_state.inspection_history.append(inspection_data)
    st.session_state.current_inspection_id = inspection_data["inspection_id"]


def get_inspection_history() -> list:
    import streamlit as st
    return st.session_state.get("inspection_history", [])


def get_latest_inspection():
    import streamlit as st
    history = st.session_state.get("inspection_history", [])
    return history[-1] if history else None
