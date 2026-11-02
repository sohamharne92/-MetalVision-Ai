"""
METALVISION AI — Page 4: Analytics  v2
3×2 chart grid · summary row · heatmap
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import INSPECTION_POSITIONS
from modules.data_manager import InspectionDataManager

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
COPPER="#b87333";CL="#e8a85a";CD="#8a5520"
AMBER="#f5a623";TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24";INDIGO="#818cf8"
CNORMAL="#34d399";CCRACK="#fb7185";CDENT="#fbbf24";CSCRATCH="#c084fc"

PL=dict(paper_bgcolor=BG2,plot_bgcolor=BG2,
        font=dict(color=TEXT,family="Space Grotesk, sans-serif"),
        margin=dict(l=14,r=14,t=38,b=14))

dm    = InspectionDataManager()
rows  = dm.get_all_inspections()
stats = dm.get_statistics()
dist  = dm.get_defect_distribution()

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def chart_label(text):
    st.markdown(f"<p style='font-family:Oswald;font-size:0.68rem;letter-spacing:0.18em;"
                f"color:{CD};text-transform:uppercase;margin:0 0 4px;'>— {text}</p>",
                unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Analytics Workshop</div>
  <div class="v-hero-sub">Statistical analysis across all inspection records</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">{len(rows)} RECORDS</span>
    <span class="v-hero-pill">6 CHART VIEWS</span>
    <span class="v-hero-pill">INTERACTIVE</span>
  </div>
</div>""", unsafe_allow_html=True)

if not rows:
    st.markdown(f"""
    <div class="v-plate" style="text-align:center;padding:48px;">
      <div style="font-family:Special Elite,cursive;font-size:1.6rem;color:{TEXT3};
                  margin-bottom:8px;">No Data Available</div>
      <div style="font-family:Share Tech Mono,monospace;font-size:0.74rem;color:{TEXT3};">
        Run inspections on the Live 360° page first
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── KPI strip ─────────────────────────────────────────────────────────────────
sec("Key Metrics")
m1,m2,m3,m4,m5 = st.columns(5)
for col,icon,label,val,color in [
    (m1,"","Inspected",  stats["total"],               AMBER),
    (m2,"","Pass Rate",  f"{stats['acceptance_rate']}%",ACCEPT),
    (m3,"","Rejected",   stats["rejected"],             REJECT),
    (m4,"","Avg Conf",   f"{stats['avg_confidence']}%", CL),
    (m5,"","Defects",    stats["total_defects"],        WARN),
]:
    col.markdown(f"""
    <div class="v-kpi">
      <span class="v-kpi-icon">{icon}</span>
      <div class="v-kpi-label">{label}</div>
      <div class="v-kpi-value" style="color:{color};font-size:1.5rem;">{val}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Pie + Defect Bar ───────────────────────────────────────────────────
sec("Decision & Defect Breakdown")
r1a, r1b = st.columns(2)

with r1a:
    chart_label("Accept vs Reject")
    fig=go.Figure(go.Pie(
        labels=["ACCEPT","REJECT"],
        values=[stats["accepted"],stats["rejected"]],
        marker=dict(colors=[ACCEPT,REJECT],line=dict(color=BG,width=2)),
        hole=0.55,textfont=dict(color="white",family="Space Grotesk",size=11),
        hovertemplate="<b>%{label}</b><br>%{value} inspections (%{percent})<extra></extra>",
    ))
    fig.add_annotation(text=f"<b>{stats['acceptance_rate']}%</b><br>pass",
                       x=0.5,y=0.5,showarrow=False,
                       font=dict(color=ACCEPT,size=14,family="JetBrains Mono"))
    fig.update_layout(**PL,height=300,
                      legend=dict(font=dict(color=TEXT2,size=10,family="Space Grotesk"),
                                  orientation="h",x=0.5,xanchor="center",y=-0.06))
    st.plotly_chart(fig,use_container_width=True)

with r1b:
    chart_label("Defect Type Distribution")
    if dist:
        cmap={"Normal":CNORMAL,"Crack":CCRACK,"Dent":CDENT,"Scratch":CSCRATCH}
        labels=list(dist.keys()); vals=list(dist.values())
        fig2=go.Figure(go.Bar(
            x=labels,y=vals,
            marker_color=[cmap.get(l,CL) for l in labels],
            marker_line=dict(color=BG,width=0.5),
            text=vals,textposition="outside",
            textfont=dict(color=TEXT,family="JetBrains Mono",size=10),
            hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>",
        ))
        fig2.update_layout(**PL,height=300,
            xaxis=dict(gridcolor=BORDER2,tickfont=dict(color=TEXT2,family="Space Grotesk",size=10)),
            yaxis=dict(gridcolor=BORDER2,tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9)))
        st.plotly_chart(fig2,use_container_width=True)
    else:
        st.info("No defect data.")

st.divider()

# ── Row 2: Histogram + Trend ──────────────────────────────────────────────────
sec("Confidence & Trend Analysis")
r2a, r2b = st.columns(2)

with r2a:
    chart_label("Confidence Score Distribution")
    confs=[r.get("confidence",0)*100 for r in rows]
    fig3=go.Figure(go.Histogram(
        x=confs,nbinsx=20,
        marker_color=COPPER,marker_line=dict(color=BG,width=0.5),opacity=0.9,
        hovertemplate="Confidence: %{x:.1f}%<br>Count: %{y}<extra></extra>",
    ))
    fig3.update_layout(**PL,height=300,
        xaxis=dict(title="Confidence (%)",gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9)),
        yaxis=dict(title="Count",gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9)))
    st.plotly_chart(fig3,use_container_width=True)

with r2b:
    chart_label("Inspection Trend (last 30)")
    trend=dm.get_trend_data(30)
    if trend:
        xl=[r.get("inspection_id","")[-5:] for r in trend]
        cv=[r.get("confidence",0)*100 for r in trend]
        av=[1 if r.get("decision")=="ACCEPT" else 0 for r in trend]
        fig4=make_subplots(specs=[[{"secondary_y":True}]])
        fig4.add_trace(go.Scatter(
            x=xl,y=cv,name="Confidence %",
            line=dict(color=AMBER,width=2),mode="lines+markers",
            marker=dict(size=4,color=AMBER),
            hovertemplate="%{y:.1f}%<extra>Confidence</extra>"),secondary_y=False)
        fig4.add_trace(go.Bar(
            x=xl,y=av,name="ACCEPT",
            marker_color="rgba(52,211,153,0.33)",
            hovertemplate="%{y}<extra>ACCEPT</extra>"),secondary_y=True)
        fig4.update_layout(**PL,height=300,
            xaxis=dict(showticklabels=False,gridcolor=BORDER2),
            legend=dict(font=dict(color=TEXT2,size=9,family="Space Grotesk"),
                        orientation="h",x=0.5,xanchor="center",y=-0.08))
        fig4.update_yaxes(title_text="Confidence %",gridcolor=BORDER2,
                          tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9),
                          secondary_y=False)
        fig4.update_yaxes(title_text="Accept",gridcolor="rgba(0,0,0,0)",
                          tickfont=dict(color=ACCEPT,family="JetBrains Mono",size=9),
                          secondary_y=True)
        st.plotly_chart(fig4,use_container_width=True)

st.divider()

# ── Row 3: Scatter + Heatmap ──────────────────────────────────────────────────
sec("Defect Position Intelligence")
r3a, r3b = st.columns([1,1.4])

with r3a:
    chart_label("Confidence by Decision")
    acc_c=[r.get("confidence",0)*100 for r in rows if r.get("decision")=="ACCEPT"]
    rej_c=[r.get("confidence",0)*100 for r in rows if r.get("decision")=="REJECT"]
    fig5=go.Figure()
    fig5.add_trace(go.Box(y=acc_c,name="ACCEPT",marker_color=ACCEPT,
                          line=dict(color=ACCEPT),boxmean=True))
    fig5.add_trace(go.Box(y=rej_c,name="REJECT",marker_color=REJECT,
                          line=dict(color=REJECT),boxmean=True))
    fig5.update_layout(**PL,height=300,
        yaxis=dict(title="Confidence %",gridcolor=BORDER2,
                   tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9)),
        xaxis=dict(tickfont=dict(color=TEXT2,family="Space Grotesk",size=10)),
        legend=dict(font=dict(color=TEXT2,size=10,family="Space Grotesk")))
    st.plotly_chart(fig5,use_container_width=True)

with r3b:
    chart_label("Defect Frequency Heatmap by Position")
    defect_types_list = ["Crack", "Dent", "Scratch"]
    hmap = {d: {a: 0 for a in INSPECTION_POSITIONS} for d in defect_types_list}

    for r in rows:
        # Primary source: full positions dict (session-state inspections)
        positions_dict = r.get("positions") or {}
        if positions_dict:
            for angle, pos in positions_dict.items():
                if isinstance(pos, dict) and pos.get("class") in defect_types_list:
                    try:
                        ai = int(angle)
                        if ai in hmap[pos["class"]]:
                            hmap[pos["class"]][ai] += 1
                    except (ValueError, TypeError):
                        pass
        else:
            # Fallback: reconstruct from flat CSV columns.
            # defect_positions is a list of angles; defect_types is a list of class names.
            # They are parallel lists when there is exactly one defect type per record,
            # otherwise we spread counts equally across the defect types present.
            d_positions = r.get("defect_positions") or []
            d_types     = r.get("defect_types")     or []
            if d_positions and d_types:
                for angle in d_positions:
                    try:
                        ai = int(angle)
                    except (ValueError, TypeError):
                        continue
                    for dtype in d_types:
                        if dtype in hmap and ai in hmap[dtype]:
                            hmap[dtype][ai] += 1

    z = [[hmap[d][a] for a in INSPECTION_POSITIONS] for d in defect_types_list]
    fig6=go.Figure(go.Heatmap(
        z=z,x=[f"{a}°" for a in INSPECTION_POSITIONS],y=defect_types_list,
        colorscale=[[0,BG],[0.4,CD],[0.7,AMBER],[1,REJECT]],
        text=z,texttemplate="%{text}",
        textfont=dict(color="white",family="JetBrains Mono",size=11),
        showscale=True,
        hovertemplate="Pos: %{x}<br>Defect: %{y}<br>Count: %{z}<extra></extra>",
    ))
    fig6.update_layout(**PL,height=300,
        xaxis=dict(title="Inspection Position",
                   tickfont=dict(color=TEXT2,family="JetBrains Mono",size=9)),
        yaxis=dict(tickfont=dict(color=TEXT2,family="Space Grotesk",size=10)))
    st.plotly_chart(fig6,use_container_width=True)
