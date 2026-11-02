"""
METALVISION AI — Page 1: Overview Dashboard
Real-time summary of inspection activity, component pass/fail rates,
and system integration status.
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

from config import (
    PROJECT_TITLE, PRODUCT_NAME, SIMULATION_WARNING,
    SYSTEM_STATUS, INTEGRATION_STATUS,
    MOTOR_FULL_STEP_ANGLE, MOTOR_STEPS_PER_REV, INSPECTION_ANGLE_STEP, TOTAL_POSITIONS,
    CAMERA_MODEL, CAMERA_INTERFACE,
)
from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp, format_confidence

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623"
TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24";REVIEW="#fbbf24"

PL = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
          margin=dict(l=12, r=12, t=36, b=12))

dm    = InspectionDataManager()
stats = dm.get_statistics()
dist  = dm.get_defect_distribution()
rows  = dm.get_all_inspections()
trend = dm.get_trend_data(20)

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def kpi(label, value, color, sub="", pct=None):
    bar = ""
    if pct is not None:
        bar = (f'<div class="v-kpi-bar">'
               f'<div class="v-kpi-bar-fill" style="width:{min(pct,100):.0f}%;"></div>'
               f'</div>')
    return (f'<div class="v-kpi v-fade-in">'
            f'<div class="v-kpi-label">{label}</div>'
            f'<div class="v-kpi-value v-count-up" style="color:{color};">{value}</div>'
            f'<div class="v-kpi-sub">{sub}</div>'
            f'{bar}</div>')

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div style="display:flex;justify-content:space-between;align-items:flex-start;
              flex-wrap:wrap;gap:12px;">
    <div>
      <div class="v-hero-title">Overview Dashboard</div>
      <div class="v-hero-sub">{PROJECT_TITLE}</div>
      <div class="v-hero-meta">
        <span class="v-hero-pill">{TOTAL_POSITIONS} POSITIONS · {INSPECTION_ANGLE_STEP}° INTERVAL</span>
        <span class="v-hero-pill">NEMA 17 · {MOTOR_FULL_STEP_ANGLE}° STEP · {MOTOR_STEPS_PER_REV} STEPS/REV</span>
        <span class="v-hero-pill">DUAL-CHANNEL CNN</span>
      </div>
    </div>
    <div style="text-align:right;">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:{TEXT3};">
        {datetime.now().strftime('%Y-%m-%d  %H:%M')}</div>
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.62rem;
                  letter-spacing:0.16em;color:{TEXT3};margin-top:4px;text-transform:uppercase;">
        Simulation Mode</div>
    </div>
  </div>
  <div style="margin-top:12px;padding:8px 14px;background:rgba(251,191,36,0.1);
              border:1px solid {WARN};border-radius:4px;
              font-family:'Space Grotesk',sans-serif;font-size:0.85rem;color:{WARN};">
    {SIMULATION_WARNING}
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPI row ───────────────────────────────────────────────────────────────────
sec("Inspection Summary")
k1, k2, k3, k4 = st.columns(4)
accept_pct = stats["acceptance_rate"]
conf_pct   = stats["avg_confidence"]
for col, label, val, color, sub, pct in [
    (k1, "Total Inspected",   stats["total"],   AMBER,  "all records",          100),
    (k2, "Accepted",          stats["accepted"],ACCEPT, f"{accept_pct}% pass rate", accept_pct),
    (k3, "Rejected",          stats["rejected"],REJECT, "defect detected",       100 - accept_pct),
    (k4, "Avg CNN Confidence",f"{conf_pct}%",   CL,     "simulated score",       conf_pct),
]:
    col.markdown(kpi(label, val, color, sub, pct), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Charts ────────────────────────────────────────────────────────────────────
sec("Defect & Acceptance Analysis")
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown(f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.72rem;"
                f"letter-spacing:0.16em;color:{CD};text-transform:uppercase;"
                f"margin:0 0 6px;'>Defect Distribution</p>", unsafe_allow_html=True)
    if dist:
        cmap = {"Normal": ACCEPT, "Crack": REJECT, "Dent": AMBER, "Scratch": "#c084fc"}
        labels = list(dist.keys()); vals = list(dist.values())
        fig = go.Figure(go.Pie(
            labels=labels, values=vals,
            marker=dict(colors=[cmap.get(l, CL) for l in labels],
                        line=dict(color=BG, width=2)),
            hole=0.52,
            textfont=dict(color="white", family="Space Grotesk", size=11),
            hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>",
        ))
        fig.add_annotation(text=f"<b>{sum(vals)}</b><br>total",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(color=TEXT, size=14, family="JetBrains Mono"))
        fig.update_layout(**PL, height=300,
                          legend=dict(font=dict(color=TEXT2, size=10, family="Space Grotesk"),
                                      orientation="h", x=0.5, xanchor="center", y=-0.08))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.markdown(f'<div class="v-plate" style="padding:28px;text-align:center;'
                    f'font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{TEXT3};">'
                    f'No inspection data yet</div>', unsafe_allow_html=True)

with ch2:
    st.markdown(f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.72rem;"
                f"letter-spacing:0.16em;color:{CD};text-transform:uppercase;"
                f"margin:0 0 6px;'>Acceptance Trend — last 20</p>", unsafe_allow_html=True)
    if trend:
        ids  = [r.get("inspection_id", "")[-5:] for r in trend]
        acc  = [1 if r.get("decision") == "ACCEPT" else 0 for r in trend]
        rej  = [1 if r.get("decision") == "REJECT" else 0 for r in trend]
        rev  = [1 if r.get("decision") == "REVIEW" else 0 for r in trend]
        cf   = [r.get("confidence", 0) * 100 for r in trend]
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(name="ACCEPT", x=ids, y=acc, marker_color=ACCEPT))
        fig2.add_trace(go.Bar(name="REJECT", x=ids, y=rej, marker_color=REJECT))
        fig2.add_trace(go.Bar(name="REVIEW", x=ids, y=rev, marker_color=REVIEW))
        fig2.add_trace(go.Scatter(name="Confidence", x=ids, y=cf,
                                   yaxis="y2", mode="lines+markers",
                                   line=dict(color=AMBER, width=1.5),
                                   marker=dict(size=4, color=AMBER)))
        fig2.update_layout(**PL, barmode="stack", height=300,
            xaxis=dict(showticklabels=False, gridcolor=BORDER2),
            yaxis=dict(gridcolor=BORDER2, range=[0, 1.4]),
            yaxis2=dict(overlaying="y", side="right", range=[0, 110],
                        gridcolor="rgba(0,0,0,0)",
                        tickfont=dict(color=AMBER, size=9, family="JetBrains Mono")),
            legend=dict(font=dict(color=TEXT2, size=10, family="Space Grotesk"),
                        orientation="h", x=0.5, xanchor="center", y=-0.08))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.markdown(f'<div class="v-plate" style="padding:28px;text-align:center;'
                    f'font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{TEXT3};">'
                    f'No trend data yet</div>', unsafe_allow_html=True)

st.divider()

# ── Recent inspections ────────────────────────────────────────────────────────
sec("Recent Inspection Log")
recent = rows[:8]
if recent:
    # Header
    h1,h2,h3,h4,h5,h6,h7 = st.columns([1.6,1.2,1.8,1,0.9,0.8,0.8])
    for col, lbl in [(h1,"Part ID"),(h2,"Insp. ID"),(h3,"Timestamp"),
                     (h4,"Scenario"),(h5,"Decision"),(h6,"Confidence"),(h7,"Defects")]:
        col.markdown(
            f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.66rem;"
            f"letter-spacing:0.14em;text-transform:uppercase;color:{CD};"
            f"margin:0;padding:5px 2px;'>{lbl}</p>", unsafe_allow_html=True)
    st.markdown(f"<hr style='margin:0 0 4px;background:{BORDER2};'>", unsafe_allow_html=True)

    for r in recent:
        dec = r.get("decision", "—")
        dc  = ACCEPT if dec == "ACCEPT" else REJECT if dec == "REJECT" else REVIEW
        r1,r2,r3,r4,r5,r6,r7 = st.columns([1.6,1.2,1.8,1,0.9,0.8,0.8])
        r1.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.72rem;"
                    f"color:{AMBER};margin:0;padding:5px 2px;'>"
                    f"{r.get('part_id','—')[:14]}</p>", unsafe_allow_html=True)
        r2.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.68rem;"
                    f"color:{CL};margin:0;padding:5px 2px;'>"
                    f"INS-{r.get('inspection_id','')[:6].upper()}</p>", unsafe_allow_html=True)
        r3.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.68rem;"
                    f"color:{TEXT2};margin:0;padding:5px 2px;'>"
                    f"{format_timestamp(r.get('timestamp',''))}</p>", unsafe_allow_html=True)
        r4.markdown(f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.7rem;"
                    f"color:{TEXT2};margin:0;padding:5px 2px;'>"
                    f"{r.get('scenario','')[:16]}</p>", unsafe_allow_html=True)
        r5.markdown(
            f"<span class='v-badge "
            f"{'v-badge-accept' if dec=='ACCEPT' else 'v-badge-reject' if dec=='REJECT' else 'v-badge-warn'}'>"
            f"{dec}</span>", unsafe_allow_html=True)
        r6.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.7rem;"
                    f"color:{CL};margin:0;padding:5px 2px;'>"
                    f"{format_confidence(r.get('confidence',0))}</p>", unsafe_allow_html=True)
        r7.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.7rem;"
                    f"color:{'#fb7185' if r.get('defects_found',0)>0 else '#34d399'};"
                    f"margin:0;padding:5px 2px;'>{r.get('defects_found',0)}</p>",
                    unsafe_allow_html=True)
        st.markdown(f"<div style='border-top:1px solid {BORDER2};'></div>",
                    unsafe_allow_html=True)

    st.markdown(f"<p style='font-family:JetBrains Mono,monospace;font-size:0.65rem;"
                f"color:{TEXT3};text-align:right;margin-top:4px;'>"
                f"Showing 8 of {len(rows)} records — see History for full view</p>",
                unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="v-plate" style="text-align:center;padding:32px;">
      <div style="font-family:'Bebas Neue',cursive;font-size:1.6rem;color:{TEXT3};">
        No Records Yet</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;
                  color:{TEXT3};margin-top:6px;">
        Run an inspection on the Live Inspection page to begin collecting data.
      </div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── System integration status ─────────────────────────────────────────────────
sec("System Integration Status")
cols = st.columns(3)
for i, (comp, info) in enumerate(SYSTEM_STATUS.items()):
    sc = info["color"]
    with cols[i % 3]:
        st.markdown(f"""
        <div class="v-status-row" style="border-left-color:{sc};margin-bottom:6px;">
          <div class="v-status-dot" style="background:{sc};color:{sc};"></div>
          <span class="v-status-label">{comp}</span>
          <span class="v-status-value" style="color:{sc};">{info['status']}</span>
        </div>""", unsafe_allow_html=True)

# ── What this system does ─────────────────────────────────────────────────────
st.divider()
sec("About This System")
a1, a2 = st.columns(2)
with a1:
    st.markdown(f"""
    <div class="v-spec-card" style="border-left-color:{CL};">
      <div class="v-spec-title" style="color:{CL};">What This System Does</div>
      <ul class="v-spec-list">
        <li>Rotates metal component through {TOTAL_POSITIONS} positions ({INSPECTION_ANGLE_STEP}° intervals) using NEMA 17 stepper + DRV8825 + STM32</li>
        <li>Captures images at each position using OpenCV under controlled LED illumination</li>
        <li>Generates grayscale image (texture + intensity) and Sobel edge image (defect boundaries)</li>
        <li>Dual-Channel CNN classifies each view: Normal, Crack, Dent, or Scratch</li>
        <li>Returns ACCEPT / REJECT / REVIEW with confidence score per component</li>
        <li>Stores images, classifications, and reports for full traceability</li>
      </ul>
    </div>""", unsafe_allow_html=True)
with a2:
    st.markdown(f"""
    <div class="v-spec-card" style="border-left-color:{WARN};">
      <div class="v-spec-title" style="color:{WARN};">Current Status</div>
      <ul class="v-spec-list">
        <li>Dashboard, analytics, reporting — fully live</li>
        <li>OpenCV image capture — live (USB webcam)</li>
        <li>Dual-Channel CNN — trained, 93.70% test accuracy on NEU dataset</li>
        <li>CNN framework: PyTorch 2.10, 3.1M parameters</li>
        <li>STM32 motor control — not yet integrated (manual rotation)</li>
        <li>Normal class — not in NEU dataset; to be collected from physical components</li>
      </ul>
    </div>""", unsafe_allow_html=True)
