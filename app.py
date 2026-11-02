"""
METALVISION AI — Main Application
Professional Vintage Industrial Dashboard v4.0
"""

import os
os.environ["PYTHONUTF8"] = "1"
import sys
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="METALVISION AI",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "METALVISION AI v4.0 | College Major Project | Prototype"},
)

from config import (
    PRODUCT_NAME, PRODUCT_SUBTITLE,
    SIMULATION_WARNING, CURRENT_YEAR, VERSION,
)
from modules.utils import init_session_state
from modules.data_manager import InspectionDataManager

init_session_state()

# ── CSS ───────────────────────────────────────────────────────────────────────
css_file = Path("assets/styles/custom.css")
if css_file.exists():
    with open(css_file, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Live stats ────────────────────────────────────────────────────────────────
dm    = InspectionDataManager()
stats = dm.get_statistics()

# ── Navigation ────────────────────────────────────────────────────────────────
NAV = {
    "Overview":        "pages/1_Overview_Dashboard.py",
    "Live Inspection": "pages/2_Live_360_Inspection.py",
    "History":         "pages/3_Inspection_History.py",
    "Analytics":       "pages/4_Analytics.py",
    "Reports":         "pages/5_Digital_Reports.py",
    "Architecture":    "pages/6_System_Architecture.py",
    "Quality Control": "pages/7_Quality_Control.py",
    "Predictions":     "pages/8_Predictions.py",
    "Maintenance":     "pages/9_Maintenance.py",
    "Admin Panel":     "pages/10_Admin_Panel.py",
    "Camera Test":     "pages/11_Camera_Test.py",
    "Motor Control":   "pages/12_Motor_Control.py",
}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:

    # Brand plate
    st.markdown(f"""
    <div style="padding:20px 14px 0;text-align:center;">
      <div style="position:relative;background:linear-gradient(145deg,#2c2416,#12100a);
                  border:1px solid #6a4820;border-radius:8px;padding:20px 24px 16px;
                  box-shadow:0 0 32px rgba(192,120,48,0.2),inset 0 1px 0 rgba(255,255,255,0.04);">
        <span style="position:absolute;top:8px;left:10px;color:#6a3810;font-size:9px;">◉</span>
        <span style="position:absolute;top:8px;right:10px;color:#6a3810;font-size:9px;">◉</span>
        <span style="position:absolute;bottom:8px;left:10px;color:#6a3810;font-size:9px;">◉</span>
        <span style="position:absolute;bottom:8px;right:10px;color:#6a3810;font-size:9px;">◉</span>
        <div class="v-shimmer" style="font-family:'Bebas Neue','Special Elite',cursive;
                    font-size:1.9rem;letter-spacing:0.12em;line-height:1.1;">
          METALVISION AI
        </div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.68rem;font-weight:600;
                    letter-spacing:0.24em;color:#6a4820;margin-top:5px;text-transform:uppercase;">
          Defect Detection System
        </div>
      </div>
    </div>
    <div class="v-tape" style="margin:10px 0 0;">PROTOTYPE · SIMULATION</div>
    """, unsafe_allow_html=True)

    # Live stats strip
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;padding:14px 10px 0;">
      <div style="background:#1c1710;border:1px solid #2e1e0c;border-radius:6px;
                  padding:11px 6px;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;
                    font-weight:600;color:#f5a623;line-height:1.1;">{stats['total']}</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.65rem;font-weight:700;
                    letter-spacing:0.14em;color:#5a4428;text-transform:uppercase;
                    margin-top:3px;">Total</div>
      </div>
      <div style="background:#1c1710;border:1px solid #2e1e0c;border-radius:6px;
                  padding:11px 6px;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;
                    font-weight:600;color:#34d399;line-height:1.1;">{stats['accepted']}</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.65rem;font-weight:700;
                    letter-spacing:0.14em;color:#5a4428;text-transform:uppercase;
                    margin-top:3px;">Accept</div>
      </div>
      <div style="background:#1c1710;border:1px solid #2e1e0c;border-radius:6px;
                  padding:11px 6px;text-align:center;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;
                    font-weight:600;color:#fb7185;line-height:1.1;">{stats['rejected']}</div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.65rem;font-weight:700;
                    letter-spacing:0.14em;color:#5a4428;text-transform:uppercase;
                    margin-top:3px;">Reject</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Navigation — clean text buttons, no radio, no emoji
    st.markdown('<div class="v-section" style="margin:16px 10px 8px;">Navigation</div>',
                unsafe_allow_html=True)

    if "current_page" not in st.session_state:
        st.session_state.current_page = list(NAV.keys())[0]

    for label in NAV.keys():
        is_active = st.session_state.current_page == label
        btn_style = (
            f"width:100%;text-align:left;padding:9px 14px;"
            f"background:{'rgba(245,166,35,0.14)' if is_active else 'transparent'};"
            f"border:1px solid {'#6a4820' if is_active else 'transparent'};"
            f"border-radius:6px;cursor:pointer;"
            f"font-family:'Space Grotesk',sans-serif;font-size:0.88rem;font-weight:600;"
            f"letter-spacing:0.05em;text-transform:uppercase;"
            f"color:{'#f5a623' if is_active else '#8a6840'};"
            f"margin-bottom:2px;display:block;transition:all 0.15s;"
        )
        if st.sidebar.button(
            label,
            key=f"nav_{label}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        ):
            if label != st.session_state.current_page:
                st.session_state.current_page = label
                st.rerun()

    page_selection = st.session_state.current_page
    page_file = NAV[page_selection]

    # Last inspection result
    insp_data = st.session_state.get("inspection_data")
    if insp_data:
        dec = insp_data.get("final_decision", "")
        dc  = "#34d399" if dec == "ACCEPT" else "#fb7185"
        st.markdown(f"""
        <div style="margin:14px 10px 0;padding:12px 16px;background:#1c1710;
                    border:1px solid {dc}44;border-left:4px solid {dc};border-radius:6px;
                    display:flex;align-items:center;gap:12px;">
          <div style="font-family:'Bebas Neue','Special Elite',cursive;font-size:1.4rem;
                      color:{dc};text-shadow:0 0 12px {dc};letter-spacing:0.08em;">{dec}</div>
          <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-size:0.68rem;font-weight:700;
                        letter-spacing:0.14em;color:#5a4428;text-transform:uppercase;">
              Last Result</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                        color:#c8a878;margin-top:2px;">
              Conf: {float(insp_data.get('overall_confidence', 0)) * 100:.1f}%</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # System info
    st.markdown('<div class="v-section" style="margin:18px 10px 8px;">System Info</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div style="margin:0 0 6px;padding:12px 14px;background:#1c1710;
                border:1px solid #2e1e0c;border-radius:6px;">
      <div style="display:flex;justify-content:space-between;align-items:center;
                  padding:6px 0;border-bottom:1px solid #241d12;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;font-weight:700;
                     letter-spacing:0.1em;text-transform:uppercase;color:#5a4428;">Version</span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                     color:#c8a878;">v{VERSION.split()[0]}</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;
                  padding:6px 0;border-bottom:1px solid #241d12;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;font-weight:700;
                     letter-spacing:0.1em;text-transform:uppercase;color:#5a4428;">Mode</span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                     color:#f5a623;">Simulation</span>
      </div>
      <div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;">
        <span style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;font-weight:700;
                     letter-spacing:0.1em;text-transform:uppercase;color:#5a4428;">Year</span>
        <span style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                     color:#c8a878;">{CURRENT_YEAR}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Online indicator
    st.markdown("""
    <div style="margin:8px 0 14px;padding:10px 14px;background:#1c1710;
                border:1px solid #2e1e0c;border-radius:6px;
                display:flex;align-items:center;gap:10px;">
      <div class="v-flicker" style="width:9px;height:9px;border-radius:50%;
           background:#f5a623;box-shadow:0 0 10px #f5a623;flex-shrink:0;"></div>
      <span style="font-family:'Space Grotesk',sans-serif;font-size:0.75rem;font-weight:700;
                   letter-spacing:0.14em;color:#5a4428;text-transform:uppercase;">
        System Online</span>
      <span style="margin-left:auto;font-family:'JetBrains Mono',monospace;
                   font-size:0.68rem;color:#3a2818;">● LIVE</span>
    </div>
    """, unsafe_allow_html=True)

# ── Breadcrumb ────────────────────────────────────────────────────────────────
page_label = page_selection.split("  ", 1)[-1].strip()
st.markdown(f"""
<div class="v-breadcrumb">
  <span style="font-family:'Space Grotesk',sans-serif;font-size:0.78rem;font-weight:600;
               letter-spacing:0.12em;color:#5a4428;text-transform:uppercase;">
    METALVISION AI</span>
  <span style="color:#3a2818;font-size:1rem;">›</span>
  <span style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;font-weight:700;
               letter-spacing:0.1em;color:#e8a85a;text-transform:uppercase;">
    {page_label}</span>
  <span style="margin-left:auto;font-family:'JetBrains Mono',monospace;
               font-size:0.72rem;color:#3a2818;letter-spacing:0.06em;">
    {stats['total']} records &nbsp;·&nbsp; {stats['acceptance_rate']}% pass rate</span>
</div>
""", unsafe_allow_html=True)

# ── Page routing ──────────────────────────────────────────────────────────────
# Read page file fresh on each run — no cache so switching always loads correctly
Path("pages").mkdir(exist_ok=True)
page_path = Path(page_file)

if page_path.exists():
    try:
        with open(page_file, "r", encoding="utf-8") as f:
            page_code = f.read()
        # Compile with the page file path so tracebacks show correct filenames
        exec(compile(page_code, page_file, "exec"), globals())
    except Exception as e:
        st.error(f"Error loading page: {e}")
        st.exception(e)
else:
    st.error(f"Page file not found: {page_file}")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:48px;padding:12px 0 6px;border-top:1px solid #2e1e0c;
            display:flex;justify-content:space-between;align-items:center;
            flex-wrap:wrap;gap:8px;">
  <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
               color:#3a2818;letter-spacing:0.06em;">
    METALVISION AI &copy; {CURRENT_YEAR} &nbsp;·&nbsp; FOR EDUCATIONAL PURPOSES ONLY
  </span>
  <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#3a2818;">
    PROTOTYPE / SIMULATION MODE &nbsp;·&nbsp; v{VERSION.split()[0]}
  </span>
</div>
""", unsafe_allow_html=True)
