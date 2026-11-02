"""
METALVISION AI — Page 3: Inspection History  v2
Advanced filter bar · colour-coded table · stats strip
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp, format_confidence

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623"
TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185"

dm = InspectionDataManager()

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Inspection Logbook</div>
  <div class="v-hero-sub">Complete record of all past inspection sessions</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">FILTERABLE</span>
    <span class="v-hero-pill">EXPORTABLE</span>
    <span class="v-hero-pill">CSV · JSON</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Filter bar ────────────────────────────────────────────────────────────────
sec("Filter Controls")
st.markdown('<div class="v-filter-bar">', unsafe_allow_html=True)
fc1,fc2,fc3,fc4 = st.columns([1,1,1,2])
with fc1:
    dec_f = st.selectbox("Decision", ["All","ACCEPT","REJECT"], key="hist_dec")
with fc2:
    def_f = st.selectbox("Defect Type", ["All","Normal","Crack","Dent","Scratch"], key="hist_def")
with fc3:
    conf_min = st.slider("Min Conf %", 0, 100, 0, key="hist_conf")
with fc4:
    search = st.text_input("Search ID", placeholder="Type partial inspection ID…", key="hist_search")
st.markdown('</div>', unsafe_allow_html=True)

results = dm.get_inspections_filtered(
    decision=None if dec_f=="All" else dec_f,
    defect_type=None if def_f=="All" else def_f,
    min_confidence=conf_min/100,
    search_id=search.strip(),
)

# ── Summary strip ─────────────────────────────────────────────────────────────
total_f = len(results)
acc_f   = sum(1 for r in results if r.get("decision")=="ACCEPT")
rej_f   = total_f - acc_f
avg_cf  = (sum(r.get("confidence",0) for r in results)/total_f*100) if total_f else 0
rate_f  = round(acc_f/total_f*100,1) if total_f else 0

sec("Summary")
s1,s2,s3,s4,s5 = st.columns(5)
for col,icon,label,val,color,sub in [
    (s1,"","Showing",  total_f,         AMBER,  "filtered records"),
    (s2,"","Accepted", acc_f,            ACCEPT, f"{rate_f}% of shown"),
    (s3,"","Rejected", rej_f,            REJECT, "defect found"),
    (s4,"","Avg Conf", f"{avg_cf:.1f}%", CL,     "certainty"),
    (s5,"","All Time", dm.get_statistics()['total'], TEXT2, "total records"),
]:
    col.markdown(f"""
    <div class="v-kpi">
      <span class="v-kpi-icon">{icon}</span>
      <div class="v-kpi-label">{label}</div>
      <div class="v-kpi-value" style="color:{color};font-size:1.6rem;">{val}</div>
      <div class="v-kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Table ─────────────────────────────────────────────────────────────────────
sec(f"Records ({total_f} shown)")
if results:
    # Column headers
    st.markdown(f"""
    <div style="display:grid;
         grid-template-columns:1.8fr 1.8fr 1.5fr 0.9fr 0.9fr 0.8fr 1.4fr;
         gap:4px;padding:6px 10px;background:{PANEL2};
         border:1px solid {BORDER2};border-radius:3px 3px 0 0;">
      {''.join(f'<div style="font-family:Oswald,sans-serif;font-size:0.6rem;'
               f'letter-spacing:0.16em;text-transform:uppercase;color:{CD};">{h}</div>'
               for h in ['ID','Timestamp','Scenario','Decision','Confidence','Defects','Types'])}
    </div>""", unsafe_allow_html=True)

    for i,r in enumerate(results):
        dec  = r.get("decision","—")
        dc   = ACCEPT if dec=="ACCEPT" else REJECT
        bg   = BG2 if i%2==0 else PANEL
        dtypes = ", ".join(r.get("defect_types",[])) or "—"
        st.markdown(f"""
        <div style="display:grid;
             grid-template-columns:1.8fr 1.8fr 1.5fr 0.9fr 0.9fr 0.8fr 1.4fr;
             gap:4px;padding:7px 10px;background:{bg};
             border-left:1px solid {BORDER2};border-right:1px solid {BORDER2};
             border-bottom:1px solid {BORDER2};
             transition:background 0.15s;"
             onmouseover="this.style.background='{PANEL2}'"
             onmouseout="this.style.background='{bg}'">
          <div style="font-family:Share Tech Mono,monospace;font-size:0.68rem;
                      color:{AMBER};">INS-{r.get('inspection_id','')[:8].upper()}</div>
          <div style="font-family:Share Tech Mono,monospace;font-size:0.66rem;
                      color:{TEXT2};">{format_timestamp(r.get('timestamp',''))}</div>
          <div style="font-family:Rajdhani,sans-serif;font-size:0.75rem;
                      color:{TEXT2};">{r.get('scenario','')[:20]}</div>
          <div><span class="v-badge {'v-badge-accept' if dec=='ACCEPT' else 'v-badge-reject'}"
               style="font-size:0.62rem;">{'' if dec=='ACCEPT' else ''} {dec}</span></div>
          <div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;
                      color:{CL};">{format_confidence(r.get('confidence',0))}</div>
          <div style="font-family:Share Tech Mono,monospace;font-size:0.7rem;
                      color:{'#f87171' if r.get('defects_found',0)>0 else '#4ade80'};">
            {r.get('defects_found',0)}</div>
          <div style="font-family:Rajdhani,sans-serif;font-size:0.72rem;
                      color:{TEXT2};">{dtypes}</div>
        </div>""", unsafe_allow_html=True)

    # Pagination info
    st.markdown(f"<p style='font-family:Share Tech Mono,monospace;font-size:0.62rem;"
                f"color:{TEXT3};text-align:right;margin-top:4px;'>"
                f"Showing {total_f} records · {acc_f} accepted · {rej_f} rejected</p>",
                unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Export row ────────────────────────────────────────────────────────────
    sec("Export")
    ec1,ec2,ec3 = st.columns(3)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with ec1:
        st.download_button("Export CSV", dm.export_to_csv(),
            f"metalvision_{ts}.csv","text/csv",use_container_width=True)
    with ec2:
        st.download_button("Export JSON", dm.export_to_json(),
            f"metalvision_{ts}.json","application/json",use_container_width=True)

    st.divider()

    # ── Detail expanders ──────────────────────────────────────────────────────
    sec("Detailed View")
    for r in results[:10]:
        dec = r.get("decision","—")
        dc  = ACCEPT if dec=="ACCEPT" else REJECT
        with st.expander(
            f"INS-{r.get('inspection_id','')[:8].upper()}  |  "
            f"{format_timestamp(r.get('timestamp',''))}  |  {dec}"):
            d1,d2,d3,d4 = st.columns(4)
            d1.metric("Decision",   dec)
            d2.metric("Confidence", f"{float(r.get('confidence',0))*100:.1f}%")
            d3.metric("Defects",    r.get("defects_found",0))
            d4.metric("Positions",  r.get("positions_inspected",12))
            st.write(f"**Scenario:** {r.get('scenario','—')}")
            st.write(f"**Defect Types:** {', '.join(r.get('defect_types',[])) or 'None'}")
            st.write(f"**Defect Positions:** {r.get('defect_positions',[])}")
else:
    st.markdown(f"""
    <div class="v-plate" style="text-align:center;padding:36px;">
      <div style="font-family:Special Elite,cursive;font-size:1.5rem;
                  color:{TEXT3};margin-bottom:8px;">No Matching Records</div>
      <div style="font-family:Share Tech Mono,monospace;font-size:0.74rem;color:{TEXT3};">
        Adjust filters to see results
      </div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── Danger zone ───────────────────────────────────────────────────────────────
with st.expander("DANGER ZONE — Clear All History"):
    st.markdown('<div class="v-tape" style="margin-bottom:10px;">WARNING: IRREVERSIBLE ACTION</div>',
                unsafe_allow_html=True)
    st.warning("This will permanently delete all inspection records from the CSV. There is no undo.")
    confirm_text = st.text_input(
        'Type  DELETE  to confirm',
        placeholder="DELETE",
        key="clear_confirm_input"
    )
    if confirm_text == "DELETE":
        if st.button("CLEAR ALL RECORDS", type="primary"):
            dm.clear_history()
            st.success("All records cleared.")
            st.rerun()
    else:
        st.button("CLEAR ALL RECORDS", disabled=True)
