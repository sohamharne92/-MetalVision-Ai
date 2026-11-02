"""
METALVISION AI — Page 7: Quality Control
Statistical Process Control (SPC) charts, Cpk, control limits, defect rate monitoring
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from config import PRODUCT_NAME, INSPECTION_POSITIONS, SIMULATION_WARNING
from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp

# ── Palette ───────────────────────────────────────────────────────────────────
BG="#12100a"; BG2="#1c1710"; PANEL="#241d12"; PANEL2="#2c2416"
BORDER="#4a3018"; BORDER2="#2e1e0c"
CL="#e8a85a"; CD="#8a5520"; AMBER="#f5a623"
TEXT="#f5ead8"; TEXT2="#c8a878"; TEXT3="#8a6840"
ACCEPT="#34d399"; REJECT="#fb7185"; WARN="#fbbf24"; INDIGO="#818cf8"

PL = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
          margin=dict(l=14, r=14, t=38, b=14))

dm    = InspectionDataManager()
rows  = dm.get_all_inspections()
stats = dm.get_statistics()

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def kpi(icon, label, value, color, sub=""):
    return f"""<div class="v-kpi">
      <span class="v-kpi-icon">{icon}</span>
      <div class="v-kpi-label">{label}</div>
      <div class="v-kpi-value" style="color:{color};font-size:1.8rem;">{value}</div>
      <div class="v-kpi-sub">{sub}</div>
    </div>"""

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">◉</span><span class="rivet tr">◉</span>
  <span class="rivet bl">◉</span><span class="rivet br">◉</span>
  <div class="v-hero-title">Quality Control Centre</div>
  <div class="v-hero-sub">Statistical Process Control · Cpk Analysis · Control Charts</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">SPC CHARTS</span>
    <span class="v-hero-pill">Cpk INDEX</span>
    <span class="v-hero-pill">CONTROL LIMITS</span>
    <span class="v-hero-pill">DEFECT RATE</span>
  </div>
</div>""", unsafe_allow_html=True)

if not rows:
    st.markdown(f"""<div class="v-plate" style="text-align:center;padding:48px;">
      <div style="font-family:'Bebas Neue',cursive;font-size:2rem;color:{TEXT3};">
        No Inspection Data</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;
                  color:{TEXT3};margin-top:8px;">
        Run inspections on the Live 360° page first
      </div></div>""", unsafe_allow_html=True)
    st.stop()

# ── Compute SPC metrics ───────────────────────────────────────────────────────
confidences = [r.get("confidence", 0) * 100 for r in rows]
n = len(confidences)
mean_conf   = np.mean(confidences) if n else 0
std_conf    = np.std(confidences)  if n > 1 else 0

# Control limits (3-sigma)
UCL = mean_conf + 3 * std_conf
LCL = max(0, mean_conf - 3 * std_conf)

# Cpk — process capability (USL=100%, LSL=70%)
USL, LSL = 100.0, 70.0
cpu = (USL - mean_conf) / (3 * std_conf) if std_conf > 0 else 999
cpl = (mean_conf - LSL) / (3 * std_conf) if std_conf > 0 else 999
cpk = min(cpu, cpl)

# Defect rate
total       = stats["total"]
rejected    = stats["rejected"]
defect_rate = round(rejected / total * 100, 2) if total else 0
dpmo        = round(defect_rate * 10000)   # defects per million opportunities (approx)

# Sigma level (simplified)
sigma_map = [(3.4,6),(233,5),(6210,4),(66807,3),(308537,2),(690000,1)]
sigma_level = 1
for threshold, level in sigma_map:
    if dpmo <= threshold:
        sigma_level = level
        break

# Trend — last 20 in time order
trend_data = dm.get_trend_data(20)

# ── KPI strip ─────────────────────────────────────────────────────────────────
sec("Process Quality Metrics")
k1, k2, k3, k4, k5 = st.columns(5)
for col, icon, label, val, color, sub in [
    (k1, "", "Mean Confidence",  f"{mean_conf:.1f}%",   AMBER,   "process centre"),
    (k2, "", "Std Deviation",    f"{std_conf:.2f}%",    CL,      "process spread"),
    (k3, "", "Cpk Index",        f"{cpk:.2f}",          ACCEPT if cpk>=1.33 else WARN if cpk>=1.0 else REJECT,
                                                                    "≥1.33 = capable"),
    (k4, "", "Defect Rate",      f"{defect_rate:.1f}%", REJECT if defect_rate>10 else WARN if defect_rate>5 else ACCEPT,
                                                                    f"{dpmo:,} DPMO"),
    (k5, "⭐", "Sigma Level",      f"{sigma_level}σ",     ACCEPT if sigma_level>=4 else WARN if sigma_level>=3 else REJECT,
                                                                    "process sigma"),
]:
    col.markdown(kpi(icon, label, val, color, sub), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Cpk gauge ─────────────────────────────────────────────────────────────────
col_cpk, col_sigma = st.columns(2)

with col_cpk:
    sec("Process Capability (Cpk)")
    cpk_clamped = min(max(cpk, 0), 2.5)
    fig_cpk = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=round(cpk, 3),
        delta={"reference": 1.33, "valueformat": ".2f",
               "increasing": {"color": ACCEPT}, "decreasing": {"color": REJECT}},
        gauge={
            "axis": {"range": [0, 2.5], "tickwidth": 1,
                     "tickcolor": TEXT2, "tickfont": {"color": TEXT2, "size": 10}},
            "bar":  {"color": ACCEPT if cpk >= 1.33 else WARN if cpk >= 1.0 else REJECT},
            "bgcolor": BG2,
            "borderwidth": 1, "bordercolor": BORDER,
            "steps": [
                {"range": [0,    1.0],  "color": "rgba(251,113,133,0.13)"},
                {"range": [1.0,  1.33], "color": "rgba(251,191,36,0.13)"},
                {"range": [1.33, 2.5],  "color": "rgba(52,211,153,0.13)"},
            ],
            "threshold": {"line": {"color": AMBER, "width": 3}, "value": 1.33},
        },
        number={"font": {"color": TEXT, "size": 40, "family": "JetBrains Mono"}},
        title={"text": "Cpk — Process Capability Index",
               "font": {"color": TEXT2, "size": 12, "family": "Space Grotesk"}},
    ))
    fig_cpk.update_layout(paper_bgcolor=BG2, font=dict(color=TEXT),
                          height=280, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_cpk, use_container_width=True)
    cpk_status = "CAPABLE " if cpk >= 1.33 else "MARGINAL " if cpk >= 1.0 else "NOT CAPABLE "
    cpk_color  = ACCEPT if cpk >= 1.33 else WARN if cpk >= 1.0 else REJECT
    st.markdown(f"""<div style="text-align:center;padding:10px;background:{cpk_color}18;
        border:1px solid {cpk_color};border-radius:6px;
        font-family:'Bebas Neue',cursive;font-size:1.4rem;color:{cpk_color};
        letter-spacing:0.1em;">{cpk_status}</div>""", unsafe_allow_html=True)

with col_sigma:
    sec("Sigma Level & DPMO")
    sigma_colors = {1: REJECT, 2: REJECT, 3: WARN, 4: WARN, 5: ACCEPT, 6: ACCEPT}
    sigma_labels = {
        1: "68.3% yield",  2: "95.5% yield",  3: "99.73% yield",
        4: "99.994% yield", 5: "99.99994% yield", 6: "99.9999998% yield"
    }
    bars = go.Figure(go.Bar(
        x=[f"{i}σ" for i in range(1, 7)],
        y=[690000, 308537, 66807, 6210, 233, 3.4],
        marker_color=[sigma_colors.get(i, CL) for i in range(1, 7)],
        text=[f"{v:,.0f}" for v in [690000, 308537, 66807, 6210, 233, 3.4]],
        textposition="outside",
        textfont=dict(color=TEXT2, size=9, family="JetBrains Mono"),
    ))
    # Mark current sigma
    bars.add_vline(x=sigma_level - 1, line_color=AMBER, line_width=3,
                   annotation_text=f"Current: {sigma_level}σ",
                   annotation_font=dict(color=AMBER, size=11))
    bars.update_layout(**PL, height=280,
        xaxis=dict(tickfont=dict(color=TEXT2, family="Space Grotesk", size=11)),
        yaxis=dict(title="DPMO (log)", type="log", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        title=dict(text="Sigma Level vs DPMO", font=dict(color=CL, size=12), x=0.5))
    st.plotly_chart(bars, use_container_width=True)

st.divider()

# ── X-bar (Individuals) Control Chart ─────────────────────────────────────────
sec("X-Chart — Individual Confidence Values (Control Chart)")
if len(confidences) >= 3:
    x_axis = list(range(1, n + 1))
    out_of_control = [i for i, v in enumerate(confidences) if v > UCL or v < LCL]

    marker_colors = [REJECT if i in out_of_control else ACCEPT for i in range(n)]

    fig_xbar = go.Figure()
    fig_xbar.add_trace(go.Scatter(
        x=x_axis, y=confidences, mode="lines+markers",
        name="Confidence", line=dict(color=CL, width=1.5),
        marker=dict(color=marker_colors, size=7, line=dict(color=BG, width=1)),
        hovertemplate="Inspection #%{x}<br>Confidence: %{y:.1f}%<extra></extra>",
    ))
    # UCL / Mean / LCL lines
    for val, color, name, dash in [
        (UCL, REJECT, f"UCL ({UCL:.1f}%)", "dash"),
        (mean_conf, AMBER, f"Mean ({mean_conf:.1f}%)", "solid"),
        (LCL, REJECT, f"LCL ({LCL:.1f}%)", "dash"),
    ]:
        fig_xbar.add_hline(y=val, line_color=color, line_dash=dash, line_width=1.5,
                           annotation_text=name,
                           annotation_font=dict(color=color, size=10))
    # Mark OOC points
    if out_of_control:
        ooc_x = [x_axis[i] for i in out_of_control]
        ooc_y = [confidences[i] for i in out_of_control]
        fig_xbar.add_trace(go.Scatter(
            x=ooc_x, y=ooc_y, mode="markers",
            name="Out of Control", marker=dict(color=REJECT, size=12, symbol="x"),
        ))
    fig_xbar.update_layout(**PL, height=320,
        xaxis=dict(title="Inspection #", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        yaxis=dict(title="Confidence (%)", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        legend=dict(font=dict(color=TEXT2, size=10, family="Space Grotesk"),
                    orientation="h", x=0.5, xanchor="center", y=-0.12))
    st.plotly_chart(fig_xbar, use_container_width=True)

    ooc_count = len(out_of_control)
    if ooc_count:
        st.markdown(f"""<div style="padding:10px 16px;background:{REJECT}18;
            border:1px solid {REJECT};border-radius:6px;
            font-family:'Space Grotesk',sans-serif;font-size:0.92rem;color:{REJECT};">
            {ooc_count} inspection(s) out of control limits — investigate assignable causes.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="padding:10px 16px;background:{ACCEPT}18;
            border:1px solid {ACCEPT};border-radius:6px;
            font-family:'Space Grotesk',sans-serif;font-size:0.92rem;color:{ACCEPT};">
             All points within control limits — process is in statistical control.
        </div>""", unsafe_allow_html=True)
else:
    st.info("Need at least 3 inspections to compute control chart.")

st.divider()

# ── Moving Range Chart ─────────────────────────────────────────────────────────
sec("MR-Chart — Moving Range (Process Variability)")
if len(confidences) >= 3:
    mr = [abs(confidences[i] - confidences[i-1]) for i in range(1, n)]
    mr_mean = np.mean(mr)
    mr_ucl  = 3.267 * mr_mean  # D4 factor for n=2

    fig_mr = go.Figure()
    fig_mr.add_trace(go.Bar(
        x=list(range(2, n+1)), y=mr,
        marker_color=[REJECT if v > mr_ucl else CL for v in mr],
        name="Moving Range",
        hovertemplate="Inspection #%{x}<br>Moving Range: %{y:.2f}%<extra></extra>",
    ))
    fig_mr.add_hline(y=mr_ucl, line_color=REJECT, line_dash="dash",
                     annotation_text=f"UCL-MR ({mr_ucl:.2f}%)",
                     annotation_font=dict(color=REJECT, size=10))
    fig_mr.add_hline(y=mr_mean, line_color=AMBER, line_width=1.5,
                     annotation_text=f"Mean-MR ({mr_mean:.2f}%)",
                     annotation_font=dict(color=AMBER, size=10))
    fig_mr.update_layout(**PL, height=260,
        xaxis=dict(title="Inspection #", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        yaxis=dict(title="Moving Range (%)", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)))
    st.plotly_chart(fig_mr, use_container_width=True)

st.divider()

# ── P-Chart (Defect proportion) ───────────────────────────────────────────────
sec("P-Chart — Defect Proportion by Inspection")
if len(rows) >= 5:
    defect_props = []
    for r in rows:
        total_pos = r.get("positions_inspected", 12) or 12
        defects   = r.get("defects_found", 0)
        defect_props.append(defects / total_pos)

    p_bar  = np.mean(defect_props)
    p_ucl  = [p_bar + 3 * np.sqrt(p_bar * (1 - p_bar) / 12) for _ in defect_props]
    p_lcl  = [max(0, p_bar - 3 * np.sqrt(p_bar * (1 - p_bar) / 12)) for _ in defect_props]
    x_p    = list(range(1, len(defect_props) + 1))

    fig_p = go.Figure()
    fig_p.add_trace(go.Scatter(
        x=x_p, y=[v * 100 for v in defect_props],
        mode="lines+markers", name="Defect %",
        line=dict(color=CL, width=1.5),
        marker=dict(
            color=[REJECT if v * 100 > uc * 100 else ACCEPT
                   for v, uc in zip(defect_props, p_ucl)],
            size=7),
        hovertemplate="Inspection #%{x}<br>Defect Rate: %{y:.1f}%<extra></extra>",
    ))
    fig_p.add_trace(go.Scatter(
        x=x_p, y=[v * 100 for v in p_ucl],
        mode="lines", name="UCL", line=dict(color=REJECT, dash="dash", width=1),
    ))
    fig_p.add_trace(go.Scatter(
        x=x_p, y=[v * 100 for v in p_lcl],
        mode="lines", name="LCL", fill="tonexty", fillcolor="rgba(251,113,133,0.03)",
        line=dict(color=REJECT, dash="dash", width=1),
    ))
    fig_p.add_hline(y=p_bar * 100, line_color=AMBER,
                    annotation_text=f"p̄ = {p_bar*100:.1f}%",
                    annotation_font=dict(color=AMBER, size=10))
    fig_p.update_layout(**PL, height=280,
        xaxis=dict(title="Inspection #", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        yaxis=dict(title="Defect Rate (%)", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        legend=dict(font=dict(color=TEXT2, size=10), orientation="h",
                    x=0.5, xanchor="center", y=-0.14))
    st.plotly_chart(fig_p, use_container_width=True)

st.divider()

# ── Specification summary table ───────────────────────────────────────────────
sec("Process Capability Summary")
summary_data = {
    "Parameter":        ["USL", "LSL", "Mean (X̄)", "Std Dev (σ)", "UCL (3σ)", "LCL (3σ)", "Cpu", "Cpl", "Cpk"],
    "Value":            [f"{USL:.1f}%", f"{LSL:.1f}%",
                         f"{mean_conf:.2f}%", f"{std_conf:.2f}%",
                         f"{UCL:.2f}%", f"{LCL:.2f}%",
                         f"{cpu:.3f}", f"{cpl:.3f}", f"{cpk:.3f}"],
    "Status":           ["Spec limit","Spec limit",
                         "In control" if LCL<=mean_conf<=UCL else "Out of range",
                         "Normal" if std_conf < 5 else "High",
                         "Control limit","Control limit",
                         "Good" if cpu>=1.33 else "Marginal" if cpu>=1.0 else "Poor",
                         "Good" if cpl>=1.33 else "Marginal" if cpl>=1.0 else "Poor",
                         "Capable" if cpk>=1.33 else "Marginal" if cpk>=1.0 else "Not Capable"],
}
for param, val, status in zip(summary_data["Parameter"], summary_data["Value"], summary_data["Status"]):
    s_color = ACCEPT if "Good" in status or "Capable" in status or "control" in status or "Normal" in status or "limit" in status \
              else WARN if "Marginal" in status or "range" in status \
              else REJECT
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
                padding:8px 16px;background:{BG2};border-bottom:1px solid {BORDER2};">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                   font-weight:600;color:{TEXT2};text-transform:uppercase;
                   letter-spacing:0.06em;">{param}</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.92rem;
                   color:{TEXT};">{val}</span>
      <span class="v-badge" style="background:{s_color}22;color:{s_color};
             border:1px solid {s_color};font-size:0.72rem;">{status}</span>
    </div>""", unsafe_allow_html=True)
