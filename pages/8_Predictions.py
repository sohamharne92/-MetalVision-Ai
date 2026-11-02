"""
METALVISION AI — Page 8: Predictions
Trend forecasting, anomaly detection, defect probability modelling
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from config import INSPECTION_POSITIONS
from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp

BG="#12100a"; BG2="#1c1710"; PANEL="#241d12"; PANEL2="#2c2416"
BORDER="#4a3018"; BORDER2="#2e1e0c"
CL="#e8a85a"; CD="#8a5520"; AMBER="#f5a623"
TEXT="#f5ead8"; TEXT2="#c8a878"; TEXT3="#8a6840"
ACCEPT="#34d399"; REJECT="#fb7185"; WARN="#fbbf24"; INDIGO="#818cf8"

PL = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
          margin=dict(l=14, r=14, t=38, b=14))

dm   = InspectionDataManager()
rows = dm.get_all_inspections()
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
  <div class="v-hero-title">Predictive Intelligence</div>
  <div class="v-hero-sub">Trend Forecasting · Anomaly Detection · Defect Probability</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">LINEAR REGRESSION</span>
    <span class="v-hero-pill">ANOMALY DETECTION</span>
    <span class="v-hero-pill">NEXT-N FORECAST</span>
    <span class="v-hero-pill">RISK SCORING</span>
  </div>
</div>""", unsafe_allow_html=True)

if len(rows) < 5:
    st.markdown(f"""<div class="v-plate" style="text-align:center;padding:48px;">
      <div style="font-family:'Bebas Neue',cursive;font-size:2rem;color:{TEXT3};">
        Insufficient Data</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.85rem;
                  color:{TEXT3};margin-top:8px;">
        At least 5 inspections needed for predictions.<br>
        Currently have {len(rows)} record(s).
      </div></div>""", unsafe_allow_html=True)
    st.stop()

# ── Prepare data ──────────────────────────────────────────────────────────────
# Reverse to chronological order for trend
chron = list(reversed(rows))
n     = len(chron)
confs = np.array([r.get("confidence", 0) * 100 for r in chron])
defect_flags = np.array([1 if r.get("decision") == "REJECT" else 0 for r in chron])
x_idx = np.arange(n)

# Linear regression on confidence
coeffs        = np.polyfit(x_idx, confs, 1)
trend_line    = np.polyval(coeffs, x_idx)
slope         = coeffs[0]
trend_dir     = "↑ Improving" if slope > 0.05 else "↓ Declining" if slope < -0.05 else "→ Stable"
trend_color   = ACCEPT if slope > 0.05 else REJECT if slope < -0.05 else WARN

# Forecast next 5
forecast_idx  = np.arange(n, n + 5)
forecast_vals = np.polyval(coeffs, forecast_idx)
forecast_vals = np.clip(forecast_vals, 0, 100)

# Anomaly detection — Z-score > 2.5
mean_c = np.mean(confs); std_c = np.std(confs)
z_scores = np.abs((confs - mean_c) / std_c) if std_c > 0 else np.zeros(n)
anomalies = np.where(z_scores > 2.5)[0]

# Rolling defect rate (window=5)
rolling_reject = []
window = min(5, n)
for i in range(n):
    start = max(0, i - window + 1)
    rolling_reject.append(np.mean(defect_flags[start:i+1]) * 100)

# Risk score: weighted combination
risk_score = min(100, max(0,
    (1 - stats["acceptance_rate"] / 100) * 60 +
    max(0, (80 - mean_c) / 80) * 30 +
    len(anomalies) / n * 10
))
risk_label = "HIGH RISK" if risk_score > 60 else "MEDIUM RISK" if risk_score > 30 else "LOW RISK"
risk_color = REJECT if risk_score > 60 else WARN if risk_score > 30 else ACCEPT

# ── KPIs ──────────────────────────────────────────────────────────────────────
sec("Predictive Metrics")
k1, k2, k3, k4 = st.columns(4)
for col, icon, label, val, color, sub in [
    (k1, "", "Trend Direction",   trend_dir,           trend_color,  f"{slope:+.3f}% / inspection"),
    (k2, "", "Anomalies Found",   len(anomalies),      REJECT if anomalies.size > 0 else ACCEPT,
                                                                        f"Z > 2.5 threshold"),
    (k3, "", "Risk Score",        f"{risk_score:.0f}%", risk_color,  risk_label),
    (k4, "", "Next Forecast",     f"{forecast_vals[0]:.1f}%", INDIGO, "confidence prediction"),
]:
    col.markdown(kpi(icon, label, val, color, sub), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Forecast chart ────────────────────────────────────────────────────────────
sec("Confidence Trend & 5-Step Forecast")
fig_fc = go.Figure()

# Historical
fig_fc.add_trace(go.Scatter(
    x=list(x_idx), y=list(confs), mode="lines+markers",
    name="Historical", line=dict(color=CL, width=1.8),
    marker=dict(color=[REJECT if i in anomalies else CL for i in range(n)],
                size=[10 if i in anomalies else 5 for i in range(n)],
                symbol=["x" if i in anomalies else "circle" for i in range(n)],
                line=dict(color=BG, width=1)),
    hovertemplate="Inspection %{x}<br>Confidence: %{y:.1f}%<extra></extra>",
))
# Trend line
fig_fc.add_trace(go.Scatter(
    x=list(x_idx), y=list(trend_line), mode="lines",
    name=f"Trend ({slope:+.3f}%/insp)",
    line=dict(color=trend_color, width=1.5, dash="dot"),
))
# Forecast
fig_fc.add_trace(go.Scatter(
    x=list(forecast_idx), y=list(forecast_vals), mode="lines+markers",
    name="Forecast (next 5)",
    line=dict(color=INDIGO, width=2, dash="dash"),
    marker=dict(color=INDIGO, size=8, symbol="diamond"),
    hovertemplate="Forecast #%{x}<br>Predicted: %{y:.1f}%<extra></extra>",
))
# Uncertainty band
upper = np.clip(forecast_vals + 1.5 * std_c, 0, 100)
lower = np.clip(forecast_vals - 1.5 * std_c, 0, 100)
fig_fc.add_trace(go.Scatter(
    x=list(forecast_idx) + list(reversed(forecast_idx)),
    y=list(upper) + list(reversed(lower)),
    fill="toself", fillcolor="rgba(129,140,248,0.09)",
    line=dict(color="rgba(0,0,0,0)"), name="Uncertainty Band",
))
# Anomaly markers
if anomalies.size > 0:
    fig_fc.add_trace(go.Scatter(
        x=[int(i) for i in anomalies],
        y=[confs[i] for i in anomalies],
        mode="markers", name="Anomalies",
        marker=dict(color=REJECT, size=14, symbol="x",
                    line=dict(color=REJECT, width=2)),
        hovertemplate="ANOMALY at #%{x}<br>Conf: %{y:.1f}%<extra></extra>",
    ))

fig_fc.add_vline(x=n - 0.5, line_color=AMBER, line_dash="dash",
                 annotation_text="Forecast →",
                 annotation_font=dict(color=AMBER, size=10))
fig_fc.update_layout(**PL, height=360,
    xaxis=dict(title="Inspection #", gridcolor=BORDER2,
               tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
    yaxis=dict(title="Confidence (%)", gridcolor=BORDER2, range=[50, 105],
               tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
    legend=dict(font=dict(color=TEXT2, size=9, family="Space Grotesk"),
                orientation="h", x=0.5, xanchor="center", y=-0.12))
st.plotly_chart(fig_fc, use_container_width=True)

st.divider()

# ── Rolling defect rate ───────────────────────────────────────────────────────
col_roll, col_risk = st.columns(2)

with col_roll:
    sec("Rolling Defect Rate (5-inspection window)")
    fig_roll = go.Figure()
    fig_roll.add_trace(go.Scatter(
        x=list(x_idx), y=rolling_reject, mode="lines+markers",
        name="Defect Rate %", line=dict(color=REJECT, width=2),
        marker=dict(color=REJECT, size=5),
        fill="tozeroy", fillcolor="rgba(251,113,133,0.08)",
        hovertemplate="Inspection %{x}<br>Rolling Defect Rate: %{y:.1f}%<extra></extra>",
    ))
    fig_roll.add_hline(y=10, line_color=WARN, line_dash="dash",
                       annotation_text="10% warning",
                       annotation_font=dict(color=WARN, size=10))
    fig_roll.update_layout(**PL, height=280,
        xaxis=dict(title="Inspection #", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
        yaxis=dict(title="Defect Rate (%)", gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)))
    st.plotly_chart(fig_roll, use_container_width=True)

with col_risk:
    sec("Composite Risk Score")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(risk_score, 1),
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickfont": {"color": TEXT2, "size": 9}},
            "bar":  {"color": risk_color},
            "bgcolor": BG2,
            "borderwidth": 1, "bordercolor": BORDER,
            "steps": [
                {"range": [0,  30], "color": "rgba(52,211,153,0.09)"},
                {"range": [30, 60], "color": "rgba(251,191,36,0.09)"},
                {"range": [60, 100],"color": "rgba(251,113,133,0.09)"},
            ],
            "threshold": {"line": {"color": AMBER, "width": 3}, "value": 60},
        },
        number={"suffix": "%", "font": {"color": risk_color, "size": 42,
                                         "family": "JetBrains Mono"}},
        title={"text": risk_label,
               "font": {"color": risk_color, "size": 14, "family": "Space Grotesk"}},
    ))
    fig_gauge.update_layout(paper_bgcolor=BG2, font=dict(color=TEXT),
                             height=280, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_gauge, use_container_width=True)

st.divider()

# ── Defect type prediction ────────────────────────────────────────────────────
sec("Defect Type Probability Model")
st.markdown(f"""
<div style="padding:12px 16px;background:{PANEL};border:1px solid {BORDER2};
            border-left:3px solid {INDIGO};border-radius:6px;
            font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{TEXT2};
            margin-bottom:14px;">
  Based on historical frequency distribution. Higher counts increase
  probability of that defect type recurring.
</div>""", unsafe_allow_html=True)

defect_dist = dm.get_defect_distribution()
total_defects = sum(defect_dist.values()) or 1
defect_types  = ["Crack", "Dent", "Scratch"]
d_colors      = {"Crack": REJECT, "Dent": WARN, "Scratch": "#c084fc"}

dcols = st.columns(3)
for col, dtype in zip(dcols, defect_types):
    count   = defect_dist.get(dtype, 0)
    prob    = count / total_defects * 100
    dc      = d_colors[dtype]
    with col:
        st.markdown(f"""
        <div style="background:{dc}18;border:2px solid {dc};border-radius:8px;
                    padding:20px;text-align:center;">
          <div style="font-family:'Bebas Neue',cursive;font-size:1.6rem;
                      color:{dc};letter-spacing:0.08em;">{dtype}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;
                      font-weight:600;color:{dc};margin:8px 0;">{prob:.1f}%</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.78rem;
                      color:{TEXT2};text-transform:uppercase;letter-spacing:0.1em;">
            {count} occurrences
          </div>
          <div style="height:4px;background:{BORDER2};border-radius:2px;margin-top:12px;">
            <div style="width:{min(prob,100):.0f}%;height:100%;background:{dc};
                        border-radius:2px;box-shadow:0 0 8px {dc};"></div>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Forecast table ────────────────────────────────────────────────────────────
sec("5-Step Forecast Values")
st.markdown(f"""
<div style="background:{PANEL};border:1px solid {BORDER2};border-radius:8px;overflow:hidden;">
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;
              padding:8px 16px;background:{PANEL2};border-bottom:1px solid {BORDER2};">
    {''.join(f'<div style="font-family:Space Grotesk,sans-serif;font-size:0.72rem;font-weight:700;'
             f'letter-spacing:0.14em;text-transform:uppercase;color:{CD};">{h}</div>'
             for h in ["Step", "Predicted Confidence", "Expected Decision", "Confidence Band"])}
  </div>""", unsafe_allow_html=True)

for i, (fv, fu, fl) in enumerate(zip(forecast_vals, upper, lower), 1):
    exp_dec   = "ACCEPT" if fv >= 75 else "REJECT"
    dec_color = ACCEPT if exp_dec == "ACCEPT" else REJECT
    bg        = BG2 if i % 2 == 0 else PANEL
    st.markdown(f"""
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;
              padding:9px 16px;background:{bg};border-bottom:1px solid {BORDER2};">
    <div style="font-family:JetBrains Mono,monospace;font-size:0.88rem;color:{AMBER};">
      +{i}</div>
    <div style="font-family:JetBrains Mono,monospace;font-size:0.88rem;color:{TEXT};">
      {fv:.1f}%</div>
    <div><span class="v-badge {'v-badge-accept' if exp_dec=='ACCEPT' else 'v-badge-reject'}"
         style="font-size:0.72rem;">{'' if exp_dec=='ACCEPT' else ''} {exp_dec}</span></div>
    <div style="font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{TEXT2};">
      {fl:.1f}% – {fu:.1f}%</div>
  </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)
