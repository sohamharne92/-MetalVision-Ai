"""
METALVISION AI — Page 5: Digital Reports
Inspection certificate with accurate language about what is real vs simulated.
"""
import streamlit as st
import json, io, csv
from datetime import datetime

from config import (
    PRODUCT_NAME, PROJECT_TITLE, VERSION, SIMULATION_WARNING,
    DECISION_ACCEPT, DECISION_REJECT, DECISION_REVIEW,
    MOTOR_FULL_STEP_ANGLE, INSPECTION_ANGLE_STEP, TOTAL_POSITIONS,
    CAMERA_MODEL,
)
from modules.data_manager import InspectionDataManager
from modules.utils import format_timestamp, format_confidence

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623"
TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24"
DCOLORS = {"Crack":"#fb7185","Dent":"#f5a623","Scratch":"#c084fc","Normal":"#34d399"}

dm   = InspectionDataManager()
rows = dm.get_all_inspections()

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def info_row(key, val, vc=None):
    vc = vc or TEXT
    return (f'<div class="v-info-row">'
            f'<span class="v-info-key">{key}</span>'
            f'<span class="v-info-val" style="color:{vc};">{val}</span>'
            f'</div>')

def decision_color(dec):
    return ACCEPT if dec == DECISION_ACCEPT else REJECT if dec == DECISION_REJECT else WARN

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Inspection Reports</div>
  <div class="v-hero-sub">{PROJECT_TITLE}</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">TXT · CSV · JSON · PDF</span>
    <span class="v-hero-pill">TRACEABLE RECORDS</span>
  </div>
</div>""", unsafe_allow_html=True)

if not rows:
    st.markdown(f"""
    <div class="v-plate" style="text-align:center;padding:48px;">
      <div style="font-family:'Bebas Neue',cursive;font-size:1.8rem;color:{TEXT3};">
        No Records Found</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                  color:{TEXT3};margin-top:6px;">
        Run an inspection on the Live Inspection page first.
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Simulation notice ─────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:12px 16px;background:{WARN}18;border:1px solid {WARN};
            border-radius:6px;margin-bottom:16px;
            font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{WARN};">
  <b>Simulation notice:</b> {SIMULATION_WARNING}
  These reports describe simulated defect classifications.
  When the CNN model and hardware are integrated, reports will contain
  real captured images, actual model predictions, and measured confidence scores.
</div>
""", unsafe_allow_html=True)

# ── Record selector ───────────────────────────────────────────────────────────
sec("Select Inspection Record")
ids = [r.get("inspection_id","") for r in rows]
sel = st.selectbox(
    "Record", ids,
    format_func=lambda x: (
        f"INS-{x.upper()[:8]}  |  "
        f"{format_timestamp(next((r.get('timestamp','') for r in rows if r.get('inspection_id')==x),''))}  |  "
        f"{next((r.get('decision','') for r in rows if r.get('inspection_id')==x),'')}  |  "
        f"Part: {next((r.get('part_id','—') for r in rows if r.get('inspection_id')==x),'—')}"
    ),
)
record = dm.get_inspection_by_id(sel)
if not record:
    st.error("Record not found."); st.stop()

dec      = record.get("decision","—")
dc       = decision_color(dec)
conf     = float(record.get("confidence",0)) * 100
deftypes = record.get("defect_types",[])
defpos   = record.get("defect_positions",[])

# ── Certificate ───────────────────────────────────────────────────────────────
sec("Inspection Certificate")
cert_left, cert_right = st.columns([1.6, 1])

with cert_left:
    st.markdown(f"""
    <div class="v-cert">
      <div class="v-cert-stamp" style="color:{dc};">{dec}</div>
      <span style="position:absolute;top:8px;left:10px;color:#6b4222;font-size:8px;">●</span>
      <span style="position:absolute;top:8px;right:10px;color:#6b4222;font-size:8px;">●</span>
      <span style="position:absolute;bottom:8px;left:10px;color:#6b4222;font-size:8px;">●</span>
      <span style="position:absolute;bottom:8px;right:10px;color:#6b4222;font-size:8px;">●</span>
      <div style="font-family:'Bebas Neue',cursive;font-size:1.3rem;
                  color:{CL};margin-bottom:14px;letter-spacing:0.06em;">
        {PRODUCT_NAME} — Inspection Certificate
      </div>
      {info_row("Record ID",     f"INS-{record.get('inspection_id','').upper()[:8]}", AMBER)}
      {info_row("Part ID",       record.get('part_id','—') or '—')}
      {info_row("Timestamp",     format_timestamp(record.get('timestamp','')))}
      {info_row("Scenario",      record.get('scenario','—'))}
      {info_row("Positions",     f"{record.get('positions_inspected',TOTAL_POSITIONS)} of {TOTAL_POSITIONS} ({INSPECTION_ANGLE_STEP}° intervals)")}
      {info_row("Defects Found", str(record.get('defects_found',0)),
                REJECT if record.get('defects_found',0)>0 else ACCEPT)}
      {info_row("CNN Confidence","Simulated — model not integrated", WARN)}
      {info_row("Image Source",  f"Simulated — {CAMERA_MODEL} not yet active", WARN)}
      <div style="margin-top:14px;padding-top:12px;border-top:1px solid {BORDER2};
                  font-family:'JetBrains Mono',monospace;font-size:0.7rem;
                  color:{TEXT3};line-height:1.7;">
        Classification source: simulation (synthetic data)<br>
        CNN model: not integrated — training required<br>
        STM32 motor control: not integrated<br>
        {SIMULATION_WARNING}
      </div>
    </div>""", unsafe_allow_html=True)

with cert_right:
    st.markdown(f"""
    <div class="v-decision {'v-decision-accept' if dec==DECISION_ACCEPT
                            else 'v-decision-reject'} v-fade-in"
         style="margin-bottom:14px;">
      <div class="v-decision-label">
        {'Final Verdict' if dec != DECISION_REVIEW else 'Requires Review'}
      </div>
      <div class="v-decision-text" style="color:{dc};">{dec}</div>
      <div class="v-decision-conf">Simulated confidence: {conf:.1f}%</div>
    </div>""", unsafe_allow_html=True)

    if dec == DECISION_REVIEW:
        st.markdown(f"""
        <div style="padding:10px 12px;background:{WARN}18;border:1px solid {WARN};
                    border-radius:6px;margin-bottom:10px;
                    font-family:'Space Grotesk',sans-serif;font-size:0.82rem;color:{WARN};">
          Review required — one or more positions had low confidence.
          In the real system, these positions would require retake.
        </div>""", unsafe_allow_html=True)

    if deftypes:
        st.markdown(f"""
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;
                    font-weight:700;letter-spacing:0.12em;text-transform:uppercase;
                    color:{CD};margin-bottom:8px;">
          Defect Types (Simulated)
        </div>""", unsafe_allow_html=True)
        for dt in deftypes:
            c = DCOLORS.get(dt, CL)
            st.markdown(f"""
            <div style="background:{c}18;border:1px solid {c};border-radius:4px;
                        padding:8px 12px;text-align:center;margin-bottom:6px;">
              <div style="font-family:'Bebas Neue',cursive;font-size:1.1rem;
                          color:{c};letter-spacing:0.06em;">{dt}</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;
                          color:{TEXT3};">Simulated classification</div>
            </div>""", unsafe_allow_html=True)
        if defpos:
            st.markdown(f"""
            <div style="padding:8px 12px;background:{BG2};border:1px solid {BORDER2};
                        border-left:3px solid {REJECT};border-radius:4px;
                        font-family:'JetBrains Mono',monospace;font-size:0.78rem;
                        color:{TEXT2};margin-top:6px;">
              Positions: {', '.join(str(p)+'°' for p in defpos)}
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="padding:14px;background:{ACCEPT}12;border:1px solid {ACCEPT};
                    border-radius:6px;text-align:center;">
          <span style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                       color:{ACCEPT};font-weight:600;">
            All positions — Normal (simulated)
          </span>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── Metrics ───────────────────────────────────────────────────────────────────
sec("Record Metrics")
g1, g2, g3, g4 = st.columns(4)
for col, label, val, color in [
    (g1, "Part ID",         record.get("part_id","—") or "—",     CL),
    (g2, "Confidence",      f"{conf:.1f}% (sim)",                  WARN),
    (g3, "Defects (sim)",   record.get("defects_found",0),
     REJECT if record.get("defects_found",0) > 0 else ACCEPT),
    (g4, "Positions",       f"{record.get('positions_inspected',TOTAL_POSITIONS)} / {TOTAL_POSITIONS}", TEXT2),
]:
    col.markdown(f"""
    <div class="v-kpi">
      <div class="v-kpi-label">{label}</div>
      <div class="v-kpi-value" style="color:{color};font-size:1.4rem;">{val}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ── TXT report builder ────────────────────────────────────────────────────────
def build_txt(r: dict) -> str:
    return "\n".join([
        "=" * 64,
        f"  {PRODUCT_NAME}",
        f"  {PROJECT_TITLE}",
        "=" * 64,
        f"  Record ID        : INS-{r.get('inspection_id','').upper()[:8]}",
        f"  Part ID          : {r.get('part_id','—') or '—'}",
        f"  Timestamp        : {format_timestamp(r.get('timestamp',''))}",
        f"  Scenario         : {r.get('scenario','—')}",
        f"  Positions checked: {r.get('positions_inspected',TOTAL_POSITIONS)} of {TOTAL_POSITIONS} ({INSPECTION_ANGLE_STEP}° intervals)",
        "",
        "-" * 64,
        f"  VERDICT          : {r.get('decision','—')}",
        f"  CNN Confidence   : SIMULATED — model not integrated",
        f"  Defects (sim)    : {r.get('defects_found',0)}",
        f"  Defect Types     : {', '.join(r.get('defect_types',[])) or 'None'}",
        f"  Defect Positions : {r.get('defect_positions',[])}",
        "",
        "-" * 64,
        "  IMPORTANT:",
        f"  {SIMULATION_WARNING}",
        "  CNN model not integrated — training and weights required.",
        "  STM32 motor control not integrated — firmware required.",
        "  Image source: simulated — Motorola Edge 20 not yet active.",
        "",
        f"  Version   : {VERSION}",
        f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 64,
    ])

# ── PDF builder ───────────────────────────────────────────────────────────────
def build_pdf(r: dict):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, HRFlowable,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=18*mm, bottomMargin=18*mm)

        C_BG     = colors.HexColor("#12100a")
        C_COPPER = colors.HexColor("#e8a85a")
        C_AMBER  = colors.HexColor("#f5a623")
        C_ACCEPT = colors.HexColor("#34d399")
        C_REJECT = colors.HexColor("#fb7185")
        C_WARN   = colors.HexColor("#fbbf24")
        C_TEXT   = colors.HexColor("#f5ead8")
        C_TEXT2  = colors.HexColor("#c8a878")
        C_TEXT3  = colors.HexColor("#8a6840")
        C_PANEL  = colors.HexColor("#241d12")

        decision = r.get("decision", "ACCEPT")
        dec_c    = (C_ACCEPT if decision == DECISION_ACCEPT
                    else C_REJECT if decision == DECISION_REJECT
                    else C_WARN)

        sty = getSampleStyleSheet()
        def S(name, **kw):
            return ParagraphStyle(name, parent=sty["Normal"], **kw)

        story = []

        # ── Header ─────────────────────────────────────────────────────────────
        htbl = Table(
            [[Paragraph(PRODUCT_NAME,
                S("hdr", fontSize=22, textColor=C_COPPER,
                  fontName="Helvetica-Bold", alignment=TA_CENTER))]],
            colWidths=[170*mm])
        htbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), C_BG),
            ("BOX",           (0,0), (-1,-1), 2, C_COPPER),
            ("TOPPADDING",    (0,0), (-1,-1), 12),
            ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(htbl)
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(PROJECT_TITLE,
            S("sub", fontSize=8, textColor=C_TEXT2,
              alignment=TA_CENTER, fontName="Helvetica")))
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=C_COPPER, spaceAfter=4))

        # ── Verdict ────────────────────────────────────────────────────────────
        vtbl = Table(
            [[Paragraph(decision,
                S("vrd", fontSize=28, textColor=dec_c,
                  fontName="Helvetica-Bold", alignment=TA_CENTER,
                  spaceBefore=6, spaceAfter=6))]],
            colWidths=[170*mm])
        vtbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1),
             colors.HexColor("#34d39920"
                             if decision == DECISION_ACCEPT
                             else "#fb718520")),
            ("BOX", (0,0), (-1,-1), 2, dec_c),
        ]))
        story.append(vtbl)
        story.append(Spacer(1, 4*mm))

        # ── Details table ──────────────────────────────────────────────────────
        conf_pct = f"{float(r.get('confidence', 0))*100:.1f}%"
        detail_rows = [
            ["Record ID",  f"INS-{r.get('inspection_id','').upper()[:8]}",
             "Part ID",    str(r.get('part_id', '-') or '-')],
            ["Timestamp",  format_timestamp(r.get('timestamp', '')),
             "Scenario",   str(r.get('scenario', '-'))[:35]],
            ["Positions",
             f"{r.get('positions_inspected', TOTAL_POSITIONS)}/{TOTAL_POSITIONS}",
             "Defects",    str(r.get('defects_found', 0))],
            ["Confidence", conf_pct,
             "Decision",   decision],
        ]
        dtbl = Table(detail_rows, colWidths=[28*mm, 54*mm, 28*mm, 60*mm])
        dtbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), C_PANEL),
            ("TEXTCOLOR",     (0,0), (0,-1),  C_TEXT3),
            ("TEXTCOLOR",     (2,0), (2,-1),  C_TEXT3),
            ("TEXTCOLOR",     (1,0), (1,-1),  C_TEXT),
            ("TEXTCOLOR",     (3,0), (3,-1),  C_AMBER),
            ("FONTNAME",      (0,0), (0,-1),  "Helvetica-Bold"),
            ("FONTNAME",      (2,0), (2,-1),  "Helvetica-Bold"),
            ("FONTNAME",      (1,0), (1,-1),  "Helvetica"),
            ("FONTNAME",      (3,0), (3,-1),  "Courier"),
            ("FONTSIZE",      (0,0), (-1,-1), 9),
            ("GRID",          (0,0), (-1,-1), 0.5,
             colors.HexColor("#2e1e0c")),
            ("TOPPADDING",    (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ]))
        story.append(dtbl)
        story.append(Spacer(1, 5*mm))

        # ── Defect list ────────────────────────────────────────────────────────
        defect_types = r.get('defect_types', [])
        defect_pos   = r.get('defect_positions', [])
        if defect_types:
            story.append(Paragraph("Defects Detected:",
                S("dl", fontSize=10, textColor=C_AMBER,
                  fontName="Helvetica-Bold")))
            story.append(Spacer(1, 2*mm))
            for dt in defect_types:
                story.append(Paragraph(
                    f"  \u2022  {dt}  \u2014  position(s): "
                    f"{', '.join(str(p)+'deg' for p in defect_pos)}",
                    S("di", fontSize=9, textColor=C_TEXT,
                      fontName="Helvetica")))
            story.append(Spacer(1, 3*mm))
        else:
            story.append(Paragraph(
                "All 12 positions: Normal \u2014 No defects detected.",
                S("ok", fontSize=10, textColor=C_ACCEPT,
                  fontName="Helvetica-Bold")))
            story.append(Spacer(1, 3*mm))

        # ── Notes ──────────────────────────────────────────────────────────────
        notes = r.get('notes', '')
        if notes:
            story.append(Paragraph(
                f"Notes: {notes}",
                S("nt", fontSize=8, textColor=C_TEXT2,
                  fontName="Helvetica-Oblique")))
            story.append(Spacer(1, 3*mm))

        # ── Simulation notice ──────────────────────────────────────────────────
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=C_COPPER, spaceAfter=3))
        story.append(Paragraph(
            f"NOTE: {SIMULATION_WARNING}",
            S("wn", fontSize=7, textColor=C_WARN,
              fontName="Helvetica-Oblique", alignment=TA_CENTER)))
        story.append(Spacer(1, 2*mm))
        story.append(HRFlowable(
            width="100%", thickness=0.5, color=C_COPPER, spaceAfter=2))

        # ── Footer ─────────────────────────────────────────────────────────────
        story.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            f"  |  {VERSION}  |  {PRODUCT_NAME}",
            S("ft", fontSize=7, textColor=C_TEXT3,
              fontName="Helvetica", alignment=TA_CENTER)))

        doc.build(story)
        return buf.getvalue()

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

# ── Export ────────────────────────────────────────────────────────────────────
sec("Export Options")
ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
rid = record.get("inspection_id","")[:8]
e1,e2,e3,e4,e5 = st.columns(5)
with e1:
    st.download_button("TXT Report", build_txt(record),
        f"cert_{rid}_{ts}.txt","text/plain",use_container_width=True)
with e2:
    cols = ["inspection_id","timestamp","part_id","decision","confidence","defects_found","scenario"]
    buf = io.StringIO()
    w   = csv.DictWriter(buf,fieldnames=cols,extrasaction="ignore"); w.writeheader()
    w.writerow({k:record.get(k,"") for k in cols})
    st.download_button("CSV (Single)",buf.getvalue(),
        f"record_{rid}_{ts}.csv","text/csv",use_container_width=True)
with e3:
    st.download_button("JSON (Single)",json.dumps(record,indent=2,default=str),
        f"record_{rid}_{ts}.json","application/json",use_container_width=True)
with e4:
    st.download_button("All Records CSV",dm.export_to_csv(),
        f"all_{ts}.csv","text/csv",use_container_width=True)
with e5:
    pdf = build_pdf(record)
    if pdf:
        st.download_button("PDF Certificate",data=pdf,
            file_name=f"cert_{rid}_{ts}.pdf",mime="application/pdf",
            use_container_width=True)
    else:
        st.markdown(f"""
        <div style="padding:8px;background:{WARN}22;border:1px solid {WARN};
                    border-radius:6px;font-family:'Space Grotesk',sans-serif;
                    font-size:0.78rem;color:{WARN};text-align:center;">
          PDF: install reportlab<br>
          <code>pip install reportlab</code>
        </div>""", unsafe_allow_html=True)

st.divider()
sec("Session Summary")
ss = dm.get_statistics()
s1,s2,s3,s4 = st.columns(4)
for col,label,val in [
    (s1,"Total Records",   ss["total"]),
    (s2,"Acceptance Rate", f"{ss['acceptance_rate']}%"),
    (s3,"Avg Confidence",  f"{ss['avg_confidence']}% (sim)"),
    (s4,"Total Defects",   ss["total_defects"]),
]:
    col.metric(label, val)
