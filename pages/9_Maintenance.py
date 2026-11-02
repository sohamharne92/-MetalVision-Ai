"""
METALVISION AI — Page 9: Maintenance
System health indicators, maintenance schedule, component lifetime tracking
"""
import streamlit as st
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

from config import PRODUCT_NAME, SIMULATION_WARNING
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

dm    = InspectionDataManager()
rows  = dm.get_all_inspections()
stats = dm.get_statistics()
total = stats["total"]

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

# ── Simulate component health based on inspection count ───────────────────────
# In a real system these would come from hardware sensors
def health_pct(max_cycles, used_cycles, wear_factor=1.0):
    """Return health percentage (0–100) with non-linear wear curve."""
    ratio = min(used_cycles / max_cycles, 1.0)
    return max(0, round((1 - ratio ** wear_factor) * 100, 1))

COMPONENTS = [
    # (name, icon, max_cycles, wear_factor, last_service_days_ago, service_interval_days)
    ("Camera Lens",        "", 5000, 0.8,  12, 90),
    ("LED Ring Light",     "", 8000, 1.2,  30, 180),
    ("Stepper Motor",      "",  10000, 1.5, 60, 365),
    ("Belt Drive",         "", 3000, 2.0,  45, 120),
    ("USB Interface",      "", 15000, 0.5, 5,  365),
    ("STM32 Controller",   "", 50000, 0.3, 90, 730),
    ("Power Supply",       "", 20000, 0.6, 15, 365),
    ("Inspection Platform","", 12000, 1.8, 28, 180),
]

now = datetime.now()

def component_data(name, icon, max_cycles, wear_factor, last_svc_days, svc_interval):
    used   = min(total * 12, max_cycles)          # 12 positions per inspection
    health = health_pct(max_cycles, used, wear_factor)
    next_svc_days = max(0, svc_interval - last_svc_days)
    status = "Critical" if health < 25 else "Warning" if health < 60 else "Good"
    color  = REJECT if status == "Critical" else WARN if status == "Warning" else ACCEPT
    next_svc_date = (now + timedelta(days=next_svc_days)).strftime("%Y-%m-%d")
    last_svc_date = (now - timedelta(days=last_svc_days)).strftime("%Y-%m-%d")
    return dict(name=name, icon=icon, health=health, status=status, color=color,
                used=used, max_cycles=max_cycles, next_svc_days=next_svc_days,
                next_svc_date=next_svc_date, last_svc_date=last_svc_date)

components = [component_data(*c) for c in COMPONENTS]

# Overall system health (weighted average)
system_health = round(np.mean([c["health"] for c in components]), 1)
critical_count = sum(1 for c in components if c["status"] == "Critical")
warning_count  = sum(1 for c in components if c["status"] == "Warning")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">◉</span><span class="rivet tr">◉</span>
  <span class="rivet bl">◉</span><span class="rivet br">◉</span>
  <div class="v-hero-title">Maintenance Control Centre</div>
  <div class="v-hero-sub">Component Health · Service Schedule · System Status</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">{len(components)} COMPONENTS</span>
    <span class="v-hero-pill">{critical_count} CRITICAL</span>
    <span class="v-hero-pill">{warning_count} WARNINGS</span>
    <span class="v-hero-pill">{total * 12:,} TOTAL CYCLES</span>
  </div>
  <div class="v-tape" style="margin-top:14px;">{SIMULATION_WARNING}</div>
</div>""", unsafe_allow_html=True)

# ── System health gauge + KPI strip ───────────────────────────────────────────
sec("System Overview")
g_col, k_col = st.columns([0.4, 0.6])

with g_col:
    sh_color = REJECT if system_health < 40 else WARN if system_health < 70 else ACCEPT
    fig_sys = go.Figure(go.Indicator(
        mode="gauge+number",
        value=system_health,
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1,
                     "tickfont": {"color": TEXT2, "size": 9}},
            "bar":  {"color": sh_color},
            "bgcolor": BG2, "borderwidth": 1, "bordercolor": BORDER,
            "steps": [
                {"range": [0,  40], "color": "rgba(251,113,133,0.13)"},
                {"range": [40, 70], "color": "rgba(251,191,36,0.09)"},
                {"range": [70, 100],"color": "rgba(52,211,153,0.09)"},
            ],
            "threshold": {"line": {"color": AMBER, "width": 3}, "value": 70},
        },
        number={"suffix": "%", "font": {"color": sh_color, "size": 46,
                                         "family": "JetBrains Mono"}},
        title={"text": "Overall System Health",
               "font": {"color": TEXT2, "size": 12, "family": "Space Grotesk"}},
    ))
    fig_sys.update_layout(paper_bgcolor=BG2, font=dict(color=TEXT),
                          height=270, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_sys, use_container_width=True)

with k_col:
    st.markdown("<br>", unsafe_allow_html=True)
    for icon, label, val, color in [
        ("", "Total Inspections",  total,             AMBER),
        ("", "Total Cycles Run",   f"{total*12:,}",   CL),
        ("", "Critical Components",critical_count,    REJECT if critical_count > 0 else ACCEPT),
        ("", "Warnings",           warning_count,     WARN if warning_count > 0 else ACCEPT),
    ]:
        st.markdown(f"""
        <div class="v-stat-card" style="margin-bottom:8px;">
          <div class="v-stat-icon" style="background:{color}22;">{icon}</div>
          <div class="v-stat-body">
            <div class="v-stat-label">{label}</div>
            <div class="v-stat-value" style="color:{color};">{val}</div>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Component health bars ─────────────────────────────────────────────────────
sec("Component Health Status")
c1, c2 = st.columns(2)
for i, comp in enumerate(components):
    col = c1 if i % 2 == 0 else c2
    with col:
        st.markdown(f"""
        <div style="background:{PANEL};border:1px solid {BORDER2};
                    border-left:4px solid {comp['color']};border-radius:6px;
                    padding:14px 16px;margin-bottom:10px;">
          <div style="display:flex;justify-content:space-between;align-items:center;
                      margin-bottom:8px;">
            <div style="display:flex;align-items:center;gap:10px;">
              <span style="font-size:1.2rem;">{comp['icon']}</span>
              <span style="font-family:'Space Grotesk',sans-serif;font-size:0.9rem;
                           font-weight:600;color:{TEXT};">{comp['name']}</span>
            </div>
            <span class="v-badge" style="background:{comp['color']}22;
                   color:{comp['color']};border:1px solid {comp['color']};
                   font-size:0.72rem;">{comp['status']}</span>
          </div>
          <!-- Health bar -->
          <div style="height:8px;background:{BORDER2};border-radius:4px;margin-bottom:8px;">
            <div style="width:{comp['health']}%;height:100%;
                        background:{comp['color']};border-radius:4px;
                        box-shadow:0 0 6px {comp['color']}66;
                        transition:width 0.6s ease;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;
                      font-family:'JetBrains Mono',monospace;font-size:0.75rem;
                      color:{TEXT2};">
            <span>Health: <b style="color:{comp['color']};">{comp['health']}%</b></span>
            <span>Cycles: {comp['used']:,} / {comp['max_cycles']:,}</span>
            <span style="color:{'#f87171' if comp['next_svc_days']<7 else '#fbbf24' if comp['next_svc_days']<30 else '#34d399'};">
              Next: {comp['next_svc_date']}
            </span>
          </div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Maintenance schedule timeline ─────────────────────────────────────────────
sec("Maintenance Schedule — Next 90 Days")
sorted_comps = sorted(components, key=lambda x: x["next_svc_days"])

fig_sched = go.Figure()
for i, comp in enumerate(sorted_comps):
    bar_color = REJECT if comp["next_svc_days"] < 7 else WARN if comp["next_svc_days"] < 30 else ACCEPT
    fig_sched.add_trace(go.Bar(
        x=[comp["next_svc_days"]],
        y=[comp["name"]],
        orientation="h",
        name=comp["name"],
        marker_color=bar_color,
        text=[f"{comp['next_svc_days']} days ({comp['next_svc_date']})"],
        textposition="outside",
        textfont=dict(color=TEXT2, size=10, family="JetBrains Mono"),
        hovertemplate=f"<b>{comp['name']}</b><br>Due in: {comp['next_svc_days']} days<br>"
                      f"Date: {comp['next_svc_date']}<extra></extra>",
        showlegend=False,
    ))

fig_sched.add_vline(x=7,  line_color=REJECT, line_dash="dash",
                    annotation_text="7d", annotation_font=dict(color=REJECT, size=10))
fig_sched.add_vline(x=30, line_color=WARN,   line_dash="dash",
                    annotation_text="30d", annotation_font=dict(color=WARN, size=10))
fig_sched.update_layout(**PL, height=380, barmode="overlay",
    xaxis=dict(title="Days Until Service", range=[0, 100], gridcolor=BORDER2,
               tickfont=dict(color=TEXT2, family="JetBrains Mono", size=9)),
    yaxis=dict(tickfont=dict(color=TEXT, family="Space Grotesk", size=11)),
    title=dict(text="Next Scheduled Maintenance (0 = overdue)",
               font=dict(color=CL, size=12), x=0.5))
st.plotly_chart(fig_sched, use_container_width=True)

st.divider()

# ── Maintenance log ───────────────────────────────────────────────────────────
sec("Simulated Maintenance Log")
log_events = []
for comp in components:
    log_events.append({
        "date":      comp["last_svc_date"],
        "component": comp["name"],
        "action":    "Routine Inspection & Calibration",
        "status":    "Completed",
        "tech":      "System Auto-Log",
    })
log_events.sort(key=lambda x: x["date"], reverse=True)

st.markdown(f'<div style="background:{PANEL};border:1px solid {BORDER2};border-radius:8px;overflow:hidden;">',
            unsafe_allow_html=True)
# Header
st.markdown(f"""<div style="display:grid;grid-template-columns:1.2fr 1.5fr 2fr 1fr 1.2fr;
    gap:4px;padding:8px 16px;background:{PANEL2};border-bottom:1px solid {BORDER2};">
  {''.join(f'<div style="font-family:Space Grotesk,sans-serif;font-size:0.7rem;'
           f'font-weight:700;letter-spacing:0.14em;text-transform:uppercase;'
           f'color:{CD};">{h}</div>'
           for h in ["Date","Component","Action","Status","Technician"])}
</div>""", unsafe_allow_html=True)

for i, ev in enumerate(log_events[:8]):
    bg = BG2 if i % 2 == 0 else PANEL
    st.markdown(f"""<div style="display:grid;grid-template-columns:1.2fr 1.5fr 2fr 1fr 1.2fr;
        gap:4px;padding:8px 16px;background:{bg};border-bottom:1px solid {BORDER2};">
      <div style="font-family:JetBrains Mono,monospace;font-size:0.78rem;color:{AMBER};">{ev['date']}</div>
      <div style="font-family:Space Grotesk,sans-serif;font-size:0.85rem;color:{TEXT};">{ev['component']}</div>
      <div style="font-family:Space Grotesk,sans-serif;font-size:0.82rem;color:{TEXT2};">{ev['action']}</div>
      <div><span class="v-badge v-badge-accept" style="font-size:0.68rem;"> {ev['status']}</span></div>
      <div style="font-family:JetBrains Mono,monospace;font-size:0.75rem;color:{TEXT3};">{ev['tech']}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

st.divider()

# ── Alerts panel ──────────────────────────────────────────────────────────────
critical_comps = [c for c in components if c["status"] == "Critical"]
warning_comps  = [c for c in components if c["status"] == "Warning"]

if critical_comps or warning_comps:
    sec("Active Alerts")
    for comp in critical_comps:
        st.markdown(f"""<div style="padding:12px 16px;background:{REJECT}18;
            border:1px solid {REJECT};border-radius:6px;margin-bottom:8px;
            display:flex;align-items:center;gap:12px;">
          <span style="font-size:1.2rem;"></span>
          <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                        font-size:0.92rem;color:{REJECT};">
              CRITICAL: {comp['name']}
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                        color:{TEXT2};">
              Health at {comp['health']}% — Immediate maintenance required
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    for comp in warning_comps:
        st.markdown(f"""<div style="padding:12px 16px;background:{WARN}18;
            border:1px solid {WARN};border-radius:6px;margin-bottom:8px;
            display:flex;align-items:center;gap:12px;">
          <span style="font-size:1.2rem;"></span>
          <div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;
                        font-size:0.92rem;color:{WARN};">
              WARNING: {comp['name']}
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                        color:{TEXT2};">
              Health at {comp['health']}% — Schedule maintenance soon
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
else:
    st.markdown(f"""<div style="padding:14px 18px;background:{ACCEPT}18;
        border:1px solid {ACCEPT};border-radius:6px;text-align:center;">
      <span style="font-family:'Space Grotesk',sans-serif;font-size:0.95rem;
                   color:{ACCEPT};font-weight:600;">
         All components within normal operating parameters
      </span>
    </div>""", unsafe_allow_html=True)
