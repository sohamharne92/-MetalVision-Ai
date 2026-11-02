"""
METALVISION AI — Page 10: Admin Panel
System settings, data management, configuration, activity logs
"""
import streamlit as st
import json
import os
from datetime import datetime
from pathlib import Path

from config import (
    PRODUCT_NAME, VERSION, CURRENT_YEAR,
    INSPECTION_STEP_DELAY, TOTAL_POSITIONS,
    CONFIDENCE_NORMAL_RANGE, CONFIDENCE_DEFECT_RANGE,
    SIMULATION_WARNING,
)
from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp

BG="#12100a"; BG2="#1c1710"; PANEL="#241d12"; PANEL2="#2c2416"
BORDER="#4a3018"; BORDER2="#2e1e0c"
CL="#e8a85a"; CD="#8a5520"; AMBER="#f5a623"
TEXT="#f5ead8"; TEXT2="#c8a878"; TEXT3="#8a6840"
ACCEPT="#34d399"; REJECT="#fb7185"; WARN="#fbbf24"; INDIGO="#818cf8"

dm    = InspectionDataManager()
stats = dm.get_statistics()
rows  = dm.get_all_inspections()

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def info_row(key, val, color=None):
    vc = color or TEXT
    return f"""<div style="display:flex;justify-content:space-between;align-items:center;
        padding:9px 0;border-bottom:1px solid {BORDER2};">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:0.78rem;
                   font-weight:700;letter-spacing:0.1em;text-transform:uppercase;
                   color:{TEXT3};">{key}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.88rem;
                   color:{vc};">{val}</span>
    </div>"""

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">◉</span><span class="rivet tr">◉</span>
  <span class="rivet bl">◉</span><span class="rivet br">◉</span>
  <div class="v-hero-title">Admin Control Panel</div>
  <div class="v-hero-sub">System Configuration · Data Management · Activity Logs</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">v{VERSION.split()[0]}</span>
    <span class="v-hero-pill">SIMULATION MODE</span>
    <span class="v-hero-pill">{stats['total']} RECORDS</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    " System Info",
    " Data Management",
    " Configuration",
    " Activity Log",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — SYSTEM INFO
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    sec("System Information")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"""
        <div class="v-plate">
          <div style="font-family:'Bebas Neue',cursive;font-size:1.3rem;
                      color:{CL};margin-bottom:14px;letter-spacing:0.06em;">
            Application Details
          </div>
          {info_row("Product",      PRODUCT_NAME,                  CL)}
          {info_row("Version",      VERSION,                        AMBER)}
          {info_row("Mode",         "Prototype / Simulation",       WARN)}
          {info_row("Year",         str(CURRENT_YEAR),              TEXT)}
          {info_row("Framework",    "Streamlit",                    INDIGO)}
          {info_row("Python",       "3.10+",                        INDIGO)}
          {info_row("Charts",       "Plotly 5.x",                   INDIGO)}
        </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown(f"""
        <div class="v-plate">
          <div style="font-family:'Bebas Neue',cursive;font-size:1.3rem;
                      color:{CL};margin-bottom:14px;letter-spacing:0.06em;">
            Inspection Parameters
          </div>
          {info_row("Total Positions",     str(TOTAL_POSITIONS),             TEXT)}
          {info_row("Scan Delay",          f"{INSPECTION_STEP_DELAY}s / pos", TEXT)}
          {info_row("Normal Conf Range",   f"{CONFIDENCE_NORMAL_RANGE[0]}–{CONFIDENCE_NORMAL_RANGE[1]}", ACCEPT)}
          {info_row("Defect Conf Range",   f"{CONFIDENCE_DEFECT_RANGE[0]}–{CONFIDENCE_DEFECT_RANGE[1]}", WARN)}
          {info_row("Total Records",       str(stats['total']),               AMBER)}
          {info_row("Acceptance Rate",     f"{stats['acceptance_rate']}%",    ACCEPT if stats['acceptance_rate']>80 else REJECT)}
          {info_row("Avg Confidence",      f"{stats['avg_confidence']}%",     CL)}
        </div>""", unsafe_allow_html=True)

    sec("Data File Status")
    data_dir = Path("data")
    csv_path = data_dir / "inspection_history.csv"

    csv_exists   = csv_path.exists()
    csv_size     = csv_path.stat().st_size if csv_exists else 0
    csv_modified = datetime.fromtimestamp(csv_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S") \
                   if csv_exists else "—"

    f1, f2, f3 = st.columns(3)
    for col, icon, label, val, color in [
        (f1, "", "CSV File",      "Exists" if csv_exists else "Missing",
         ACCEPT if csv_exists else REJECT),
        (f2, "", "File Size",     f"{csv_size:,} bytes", CL),
        (f3, "", "Last Modified", csv_modified, TEXT2),
    ]:
        col.markdown(f"""
        <div class="v-kpi">
          <span class="v-kpi-icon">{icon}</span>
          <div class="v-kpi-label">{label}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;
                      color:{color};margin:4px 0;">{val}</div>
        </div>""", unsafe_allow_html=True)

    sec("Session State Monitor")
    import streamlit as _st
    session_keys = [
        "inspection_data", "inspection_in_progress", "inspection_history",
        "selected_scenario", "last_saved_id", "trigger_inspection",
    ]
    for key in session_keys:
        val = _st.session_state.get(key, "not set")
        if isinstance(val, dict):
            display = f"dict with {len(val)} keys"
        elif isinstance(val, list):
            display = f"list with {len(val)} items"
        else:
            display = str(val)[:60]
        color = ACCEPT if val not in (None, False, "not set", []) else TEXT3
        st.markdown(f"""
        <div style="display:flex;gap:12px;padding:7px 12px;
                    background:{BG2};border-bottom:1px solid {BORDER2};">
          <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;
                       color:{AMBER};min-width:220px;">{key}</span>
          <span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;
                       color:{color};">{display}</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DATA MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    sec("Data Overview")
    d1, d2, d3, d4 = st.columns(4)
    for col, icon, label, val, color in [
        (d1, "", "Total Records",   stats["total"],              AMBER),
        (d2, "", "Accepted",        stats["accepted"],           ACCEPT),
        (d3, "", "Rejected",        stats["rejected"],           REJECT),
        (d4, "", "Total Defects",   stats["total_defects"],      WARN),
    ]:
        col.markdown(f"""
        <div class="v-kpi">
          <span class="v-kpi-icon">{icon}</span>
          <div class="v-kpi-label">{label}</div>
          <div class="v-kpi-value" style="color:{color};font-size:1.8rem;">{val}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    sec("Export All Data")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ea, eb, ec = st.columns(3)
    with ea:
        st.download_button(" Full CSV Export", dm.export_to_csv(),
            f"metalvision_full_{ts}.csv", "text/csv", use_container_width=True)
    with eb:
        st.download_button(" Full JSON Export", dm.export_to_json(),
            f"metalvision_full_{ts}.json", "application/json", use_container_width=True)
    with ec:
        # System snapshot JSON
        snapshot = {
            "exported_at":   datetime.now().isoformat(),
            "version":       VERSION,
            "statistics":    stats,
            "defect_distribution": dm.get_defect_distribution(),
            "total_records": len(rows),
        }
        st.download_button(" System Snapshot",
            json.dumps(snapshot, indent=2, default=str),
            f"system_snapshot_{ts}.json", "application/json",
            use_container_width=True)

    sec("Data Integrity Check")
    issues = []
    for r in rows:
        if not r.get("inspection_id"):
            issues.append(f"Record missing inspection_id")
        if r.get("decision") not in ("ACCEPT", "REJECT"):
            issues.append(f"Record {r.get('inspection_id','?')[:8]}: invalid decision '{r.get('decision')}'")
        try:
            float(r.get("confidence", 0))
        except (TypeError, ValueError):
            issues.append(f"Record {r.get('inspection_id','?')[:8]}: invalid confidence value")

    if issues:
        for issue in issues[:10]:
            st.markdown(f"""<div style="padding:8px 14px;background:{REJECT}18;
                border:1px solid {REJECT};border-radius:4px;margin-bottom:5px;
                font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                color:{REJECT};">{issue}</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="padding:12px 16px;background:{ACCEPT}18;
            border:1px solid {ACCEPT};border-radius:6px;
            font-family:'Space Grotesk',sans-serif;font-size:0.92rem;color:{ACCEPT};">
             All {len(rows)} records passed integrity check — no issues found.
        </div>""", unsafe_allow_html=True)

    st.divider()

    # Danger zone
    with st.expander("DANGER ZONE — Permanent Data Operations"):
        st.markdown(f'<div class="v-tape" style="margin-bottom:12px;">IRREVERSIBLE — PROCEED WITH CAUTION</div>',
                    unsafe_allow_html=True)
        confirm = st.text_input("Type  DELETE  to enable destructive actions",
                                placeholder="DELETE", key="admin_delete_confirm")
        if confirm == "DELETE":
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button(" Clear All Inspection Records", type="primary",
                             use_container_width=True):
                    dm.clear_history()
                    st.success("All records cleared.")
                    st.rerun()
            with col_d2:
                if st.button(" Reset Session State", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.success("Session state reset.")
                    st.rerun()
        else:
            st.info("Enter DELETE above to enable data operations.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    sec("Runtime Configuration (Read-Only in Simulation Mode)")
    st.markdown(f"""<div style="padding:10px 14px;background:{WARN}18;
        border:1px solid {WARN};border-radius:6px;margin-bottom:16px;
        font-family:'Space Grotesk',sans-serif;font-size:0.9rem;color:{WARN};">
        These settings are read-only in simulation mode. In Phase 3 hardware integration,
        they would be writable and persisted to a configuration file.
    </div>""", unsafe_allow_html=True)

    ca, cb = st.columns(2)
    with ca:
        st.markdown(f"""
        <div class="v-spec-card" style="margin-bottom:12px;">
          <div class="v-spec-title" style="color:{CL};"> Inspection Settings</div>
          <ul class="v-spec-list">
            <li>Scan delay: {INSPECTION_STEP_DELAY}s per position</li>
            <li>Positions: {TOTAL_POSITIONS} (every 30°)</li>
            <li>Defect classes: Normal, Crack, Dent, Scratch</li>
            <li>Decision rule: ANY defect → REJECT</li>
            <li>Confidence threshold: 70% minimum</li>
          </ul>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="v-spec-card">
          <div class="v-spec-title" style="color:{ACCEPT};"> CNN Model Settings</div>
          <ul class="v-spec-list">
            <li>Architecture: Dual-Channel CNN</li>
            <li>Input: 640×480 RGB + Edge Map</li>
            <li>Filters: Conv1=32, Conv2=64</li>
            <li>FC Layer: 512 neurons, Dropout 0.5</li>
            <li>Output: 4-class Softmax</li>
            <li>Status: Simulation (no real model)</li>
          </ul>
        </div>""", unsafe_allow_html=True)

    with cb:
        st.markdown(f"""
        <div class="v-spec-card" style="margin-bottom:12px;">
          <div class="v-spec-title" style="color:{AMBER};"> Storage Settings</div>
          <ul class="v-spec-list">
            <li>Backend: CSV file (Phase 2)</li>
            <li>Path: data/inspection_history.csv</li>
            <li>Encoding: UTF-8</li>
            <li>Phase 3 target: PostgreSQL</li>
            <li>Auto-backup: Not configured</li>
          </ul>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div class="v-spec-card">
          <div class="v-spec-title" style="color:{INDIGO};"> Hardware Settings</div>
          <ul class="v-spec-list">
            <li>STM32: Not connected (future)</li>
            <li>Motor: NEMA 17 stepper (planned)</li>
            <li>Driver: A4988 module (planned)</li>
            <li>Camera: USB/CSI (planned)</li>
            <li>UART baud: 115200 (planned)</li>
            <li>Status: Phase 3 integration</li>
          </ul>
        </div>""", unsafe_allow_html=True)

    sec("Phase 3 Roadmap")
    phases = [
        ("3A", "Database Migration",    "CSV → PostgreSQL, user auth",  ACCEPT, "Planned"),
        ("3B", "Hardware Integration",  "STM32, camera, motor control", AMBER,  "Planned"),
        ("3C", "Real CNN Model",        "Train on NEU-DET dataset",     AMBER,  "Planned"),
        ("3D", "Advanced Analytics",    "PDF export, email alerts",     ACCEPT, "Partial"),
        ("3E", "REST API",              "FastAPI + authentication",     WARN,   "Planned"),
        ("3F", "Mobile App",            "React Native dashboard",       WARN,   "Future"),
        ("3G", "Cloud Deployment",      "Docker + Kubernetes + AWS",    WARN,   "Future"),
    ]
    for code, title, desc, color, status in phases:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;padding:10px 14px;
                    background:{PANEL};border:1px solid {BORDER2};
                    border-left:3px solid {color};border-radius:6px;margin-bottom:6px;">
          <div style="font-family:'Bebas Neue',cursive;font-size:1.1rem;
                      color:{color};min-width:32px;">{code}</div>
          <div style="flex:1;">
            <div style="font-family:'Space Grotesk',sans-serif;font-size:0.9rem;
                        font-weight:700;color:{TEXT};">{title}</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                        color:{TEXT2};margin-top:2px;">{desc}</div>
          </div>
          <span class="v-badge" style="background:{color}22;color:{color};
                 border:1px solid {color};font-size:0.72rem;">{status}</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — ACTIVITY LOG
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    sec("Recent Activity Log")
    st.markdown(f"""<div style="padding:10px 14px;background:{INDIGO}18;
        border:1px solid {INDIGO};border-radius:6px;margin-bottom:14px;
        font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{INDIGO};">
        Activity log shows the {min(len(rows), 20)} most recent inspection events
        from persistent storage.
    </div>""", unsafe_allow_html=True)

    if rows:
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER2};
                    border-radius:8px;overflow:hidden;">
          <div style="display:grid;grid-template-columns:1.4fr 1.2fr 1.2fr 0.8fr 0.8fr 1fr;
                      gap:4px;padding:8px 16px;background:{PANEL2};
                      border-bottom:1px solid {BORDER2};">
            {''.join(f'<div style="font-family:Space Grotesk,sans-serif;font-size:0.7rem;'
                     f'font-weight:700;letter-spacing:0.14em;text-transform:uppercase;'
                     f'color:{CD};">{h}</div>'
                     for h in ["Timestamp","Record ID","Scenario","Decision","Confidence","Defects"])}
          </div>""", unsafe_allow_html=True)

        for i, r in enumerate(rows[:20]):
            dec  = r.get("decision", "—")
            dc   = ACCEPT if dec == "ACCEPT" else REJECT
            bg   = BG2 if i % 2 == 0 else PANEL
            st.markdown(f"""
          <div style="display:grid;grid-template-columns:1.4fr 1.2fr 1.2fr 0.8fr 0.8fr 1fr;
                      gap:4px;padding:8px 16px;background:{bg};
                      border-bottom:1px solid {BORDER2};">
            <div style="font-family:JetBrains Mono,monospace;font-size:0.75rem;
                        color:{TEXT2};">{format_timestamp(r.get('timestamp',''))}</div>
            <div style="font-family:JetBrains Mono,monospace;font-size:0.78rem;
                        color:{AMBER};">INS-{r.get('inspection_id','')[:8].upper()}</div>
            <div style="font-family:Space Grotesk,sans-serif;font-size:0.8rem;
                        color:{TEXT2};">{r.get('scenario','')[:18]}</div>
            <div><span class="v-badge {'v-badge-accept' if dec=='ACCEPT' else 'v-badge-reject'}"
                 style="font-size:0.68rem;">{'' if dec=='ACCEPT' else ''} {dec}</span></div>
            <div style="font-family:JetBrains Mono,monospace;font-size:0.78rem;
                        color:{CL};">{float(r.get('confidence',0))*100:.1f}%</div>
            <div style="font-family:JetBrains Mono,monospace;font-size:0.78rem;
                        color:{'#fb7185' if r.get('defects_found',0)>0 else '#34d399'};">
              {r.get('defects_found',0)} found</div>
          </div>""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="v-plate" style="text-align:center;padding:32px;">
          <div style="font-family:'JetBrains Mono',monospace;color:{TEXT3};font-size:0.9rem;">
            No activity recorded yet
          </div></div>""", unsafe_allow_html=True)

    sec("Application Events")
    app_events = [
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO",    "Dashboard loaded successfully",       ACCEPT),
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO",    f"Database connected: {stats['total']} records", ACCEPT),
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO",    "CSS theme loaded: vintage-industrial v4", ACCEPT),
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "WARNING", "Hardware not connected (simulation mode)", WARN),
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "WARNING", "CNN model not loaded (simulation mode)",   WARN),
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO",    "Session state initialised",               ACCEPT),
    ]
    for ts_ev, level, msg, color in app_events:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:12px;padding:7px 14px;
                    background:{BG2};border-bottom:1px solid {BORDER2};">
          <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                       color:{TEXT3};min-width:160px;">{ts_ev}</span>
          <span class="v-badge" style="background:{color}22;color:{color};
                 border:1px solid {color};font-size:0.68rem;min-width:70px;
                 text-align:center;">{level}</span>
          <span style="font-family:'Space Grotesk',sans-serif;font-size:0.85rem;
                       color:{TEXT2};">{msg}</span>
        </div>""", unsafe_allow_html=True)
