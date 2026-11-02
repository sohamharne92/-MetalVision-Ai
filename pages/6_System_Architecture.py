"""
METALVISION AI — Page 6: System Architecture
Accurate hardware specification, motor mathematics, integration status,
and Dual-Channel CNN architecture.
"""
import streamlit as st
import plotly.graph_objects as go

from config import (
    PROJECT_TITLE, PRODUCT_NAME, VERSION,
    MOTOR_FULL_STEP_ANGLE, MOTOR_STEPS_PER_REV, MOTOR_MICROSTEPPING,
    INSPECTION_ANGLE_STEP, TOTAL_POSITIONS,
    CAMERA_MODEL, CAMERA_INTERFACE, CAMERA_SETTLE_DELAY_S,
    STM32_BAUD_RATE,
    INTEGRATION_STATUS,
    DECISION_ACCEPT, DECISION_REJECT, DECISION_REVIEW,
)
from modules.cnn_pipeline import DualChannelCNNVisualizer

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623"
TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24";INDIGO="#818cf8"

PL = dict(paper_bgcolor=BG2, plot_bgcolor=BG2,
          font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
          margin=dict(l=10,r=10,t=10,b=10))

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def spec_card(title, items, accent=CL, note=""):
    li = "".join(f'<li>{i}</li>' for i in items)
    footer = (f'<div style="margin-top:10px;padding-top:8px;border-top:1px solid {BORDER2};'
              f'font-family:JetBrains Mono,monospace;font-size:0.7rem;color:{TEXT3};">'
              f'{note}</div>') if note else ""
    return (f'<div class="v-spec-card" style="border-left-color:{accent};">'
            f'<div class="v-spec-title" style="color:{accent};">{title}</div>'
            f'<ul class="v-spec-list">{li}</ul>'
            f'{footer}</div>')

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">System Architecture</div>
  <div class="v-hero-sub">{PROJECT_TITLE}</div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">NEMA 17 · {MOTOR_FULL_STEP_ANGLE}°/STEP · {MOTOR_STEPS_PER_REV} STEPS/REV</span>
    <span class="v-hero-pill">STM32 + DRV8825</span>
    <span class="v-hero-pill">DUAL-CHANNEL CNN</span>
    <span class="v-hero-pill">{TOTAL_POSITIONS} POSITIONS · {INSPECTION_ANGLE_STEP}° INTERVAL</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "System Overview",
    "Hardware Spec",
    "Architecture Diagram",
    "CNN Pipeline",
    "Integration Status",
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — System Overview
# ════════════════════════════════════════════════════════════════
with tab1:
    sec("What This System Does")
    st.markdown(f"""
    <div style="padding:16px 20px;background:{PANEL};border:1px solid {BORDER2};
                border-radius:8px;margin-bottom:16px;
                font-family:'Space Grotesk',sans-serif;font-size:0.95rem;
                color:{TEXT};line-height:1.7;">
      A metal component is placed on a <b style="color:{CL};">rotating platform</b>.
      A <b style="color:{CL};">stepper motor</b> (NEMA 17, controlled by an STM32 via DRV8825)
      rotates the platform through <b style="color:{AMBER};">{TOTAL_POSITIONS} positions
      at {INSPECTION_ANGLE_STEP}° intervals</b>.
      At each position the motor stops, vibration settles, and the
      <b style="color:{CL};">{CAMERA_MODEL}</b> captures a frame via {CAMERA_INTERFACE}.
      The frame is processed by a <b style="color:{AMBER};">Dual-Channel CNN</b>
      (grayscale image + Sobel edge map) to classify the visible surface as
      Normal, Crack, Dent, or Scratch.
      The component receives a final verdict: <b style="color:{ACCEPT};">{DECISION_ACCEPT}</b>,
      <b style="color:{REJECT};">{DECISION_REJECT}</b>, or
      <b style="color:{WARN};">{DECISION_REVIEW}</b>.
    </div>
    """, unsafe_allow_html=True)

    sec("Current vs Intended System")
    cc, cp = st.columns(2)
    with cc:
        st.markdown(spec_card("Manual Inspection (Problem)", [
            "Operator turns component by hand",
            "Inconsistent lighting and viewing angle",
            "Result varies with operator fatigue",
            "No photographic record by default",
            "Time-consuming for every component",
            "Cannot detect micro-cracks reliably",
        ], accent=REJECT), unsafe_allow_html=True)
    with cp:
        st.markdown(spec_card("Automated System (Solution)", [
            f"Stepper motor rotates to {TOTAL_POSITIONS} fixed positions",
            "Consistent LED illumination every capture",
            "Same trained CNN applied to every image",
            f"Image saved against part ID at each {INSPECTION_ANGLE_STEP}° position",
            "Defect class + confidence returned per image",
            "Accept / Reject / Review decision with traceability",
        ], accent=ACCEPT), unsafe_allow_html=True)

    st.divider()
    sec("Inspection Workflow (Intended Final System)")
    steps = [
        ("1", "Place component on platform, enter Part ID in dashboard", AMBER),
        ("2", "Dashboard sends 'rotate' command to STM32 via serial (UART)", CL),
        ("3", f"STM32 generates {MOTOR_MICROSTEPPING*int(INSPECTION_ANGLE_STEP/MOTOR_FULL_STEP_ANGLE)} pulse(s) to DRV8825 — platform moves {INSPECTION_ANGLE_STEP}°", CL),
        ("4", "STM32 sends 'position confirmed' message back to laptop", CL),
        ("5", f"Wait {CAMERA_SETTLE_DELAY_S}s for vibration to settle, flush camera buffer", CL),
        ("6", f"Capture fresh frame from {CAMERA_MODEL} (DroidCam → OpenCV)", CL),
        ("7", "Check frame quality: blur score, brightness, overexposure", CL),
        ("8", "Preprocess: crop ROI, resize to CNN input, normalise pixels", CL),
        ("9", "Run Dual-Channel CNN — output: class + confidence score", AMBER),
        ("10","Record result against angle and part ID", CL),
        ("11",f"Repeat steps 2–10 for all {TOTAL_POSITIONS} positions", CL),
        ("12","Compute final decision: ACCEPT / REJECT / REVIEW", ACCEPT),
        ("13","Generate report — save images, classes, decision as evidence", ACCEPT),
    ]
    for num, desc, color in steps:
        st.markdown(f"""
        <div style="display:flex;gap:12px;align-items:flex-start;
                    padding:8px 12px;background:{BG2};
                    border-bottom:1px solid {BORDER2};">
          <div style="font-family:'Bebas Neue',cursive;font-size:1rem;
                      color:{color};min-width:28px;">{num}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                      color:{TEXT2};line-height:1.5;">{desc}</div>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 2 — Hardware Spec
# ════════════════════════════════════════════════════════════════
with tab2:
    sec("Hardware Components")
    hw_rows = [
        ("Rotary Platform & Fixture",  "Holds the component centred and secured during rotation"),
        ("NEMA 17 Stepper Motor",      f"{MOTOR_FULL_STEP_ANGLE}°/step full-step · {MOTOR_STEPS_PER_REV} steps/rev · direct-drive to platform"),
        ("DRV8825 Motor Driver",       "Controls current through motor coils; supports microstepping up to 1/32"),
        ("STM32 Microcontroller",      f"Generates step/direction pulses for DRV8825; UART to laptop at {STM32_BAUD_RATE} baud"),
        (CAMERA_MODEL,                 f"Captures visible surface; connected via {CAMERA_INTERFACE}"),
        ("LED Illumination",           "Provides consistent, repeatable lighting at each capture position"),
        ("Power Supply & Electronics", "Powers stepper motor, driver, STM32, and LED ring"),
        ("Laptop",                     "Runs dashboard, coordinates motor commands, processes images, stores results"),
    ]
    for part, job in hw_rows:
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 2fr;gap:8px;
                    padding:9px 14px;background:{BG2};
                    border-bottom:1px solid {BORDER2};">
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                      font-weight:700;color:{CL};">{part}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.85rem;
                      color:{TEXT2};line-height:1.5;">{job}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    sec("Motor Mathematics")
    st.markdown(f"""
    <div style="background:{PANEL};border:1px solid {BORDER2};border-radius:8px;
                padding:20px 24px;font-family:'JetBrains Mono',monospace;">
      <div style="font-size:0.88rem;color:{TEXT2};line-height:2;">
        <b style="color:{CL};">Motor type:</b> NEMA 17 stepper — confirmed full-step angle: {MOTOR_FULL_STEP_ANGLE}°<br>
        <b style="color:{CL};">Steps per revolution:</b>
          360° ÷ {MOTOR_FULL_STEP_ANGLE}° = <b style="color:{AMBER};">{MOTOR_STEPS_PER_REV} steps</b><br>
        <b style="color:{CL};">Current inspection interval:</b>
          {INSPECTION_ANGLE_STEP}° → {int(INSPECTION_ANGLE_STEP/MOTOR_FULL_STEP_ANGLE)} step(s) per move<br>
        <b style="color:{CL};">Full-resolution mode:</b>
          1.8° interval → {MOTOR_STEPS_PER_REV} positions per revolution<br>
        <b style="color:{CL};">Microstepping:</b>
          {MOTOR_MICROSTEPPING}× (full step) — DRV8825 supports up to 1/32<br>
        <b style="color:{CL};">Note:</b>
          Commanding an angle does not verify actual position.
          Slipping or missed steps cause cumulative error.
          A home-position reference and mechanical design are critical.
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    sec("Three-Responsibility Model")
    r1, r2, r3 = st.columns(3)
    for col, who, job, color in [
        (r1, "Laptop",    "Decides when to move, sends commands, processes images, stores results", CL),
        (r2, "STM32",     "Generates step/direction pulses at the correct timing and count",         AMBER),
        (r3, "DRV8825",   "Supplies controlled current through the motor coils in the right sequence", INDIGO),
    ]:
        col.markdown(f"""
        <div style="background:{color}12;border:2px solid {color};border-radius:8px;
                    padding:16px;text-align:center;">
          <div style="font-family:'Bebas Neue',cursive;font-size:1.3rem;
                      color:{color};margin-bottom:8px;">{who}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;
                      color:{TEXT2};line-height:1.5;">{job}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    sec("Image Capture Sequence")
    st.markdown(f"""
    <div style="padding:14px 18px;background:{PANEL};border:1px solid {BORDER2};
                border-radius:8px;font-family:'Space Grotesk',sans-serif;
                font-size:0.9rem;color:{TEXT2};line-height:1.8;">
      <b style="color:{CL};">Critical consideration:</b> even after the motor stops,
      the camera video buffer may still contain a frame from the previous position.
      The capture sequence must:<br>
      &nbsp;&nbsp;1. Wait for STM32 confirmation that movement is complete<br>
      &nbsp;&nbsp;2. Wait an additional {CAMERA_SETTLE_DELAY_S}s for mechanical vibration to settle<br>
      &nbsp;&nbsp;3. Flush the camera buffer to discard stale frames<br>
      &nbsp;&nbsp;4. Capture a fresh frame<br>
      &nbsp;&nbsp;5. Check image quality (blur, brightness, overexposure)<br>
      &nbsp;&nbsp;6. Request a retake if quality fails — do not classify a blurry image<br>
      The exact settling delay must be determined by testing with the actual platform and phone.
    </div>
    """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 3 — Architecture Diagram
# ════════════════════════════════════════════════════════════════
with tab3:
    sec("System Architecture Diagram")
    NODES = [
        ("Metal\nComponent",  0.50, 0.90, CL),
        ("Rotary\nPlatform",  0.30, 0.75, CL),
        ("NEMA 17\nStepper",  0.14, 0.58, AMBER),
        ("DRV8825\nDriver",   0.14, 0.40, AMBER),
        ("STM32\nController", 0.14, 0.22, AMBER),
        (f"{CAMERA_MODEL}\n(DroidCam)", 0.86, 0.58, INDIGO),
        ("OpenCV\nCapture",   0.86, 0.40, INDIGO),
        ("Image\nQuality Chk",0.86, 0.22, INDIGO),
        ("Dual-CH\nCNN",      0.50, 0.45, "#c084fc"),
        ("Decision\nEngine",  0.50, 0.26, "#c084fc"),
        ("Dashboard\n(Laptop)",0.70, 0.08, ACCEPT),
        ("History\n& Reports", 0.50, 0.08, ACCEPT),
        ("Alert /\nOutput",   0.30, 0.08, REJECT),
    ]
    EDGES = [
        (0,1),(1,2),(2,3),(3,4),(4,1),   # motor chain
        (0,5),(5,6),(6,7),(7,8),          # camera chain
        (4,9),(8,9),                       # CNN inputs
        (9,10),(9,11),(9,12),              # outputs
    ]
    fig = go.Figure()
    for s, d in EDGES:
        x0,y0 = NODES[s][1], NODES[s][2]
        x1,y1 = NODES[d][1], NODES[d][2]
        fig.add_annotation(x=x1,y=y1,ax=x0,ay=y0,
            xref="x",yref="y",axref="x",ayref="y",
            showarrow=True,arrowhead=2,arrowsize=1,
            arrowwidth=1.5,arrowcolor=BORDER)
    for label,x,y,color in NODES:
        fig.add_trace(go.Scatter(
            x=[x],y=[y],mode="markers+text",
            marker=dict(size=54,color=color,opacity=0.9,
                        line=dict(color=BG,width=2)),
            text=[f"<b>{label}</b>"],
            textfont=dict(color="white",size=7.5,family="Space Grotesk"),
            textposition="middle center",
            showlegend=False,hoverinfo="skip"))
    fig.update_layout(**PL,
        xaxis=dict(range=[-0.05,1.05],visible=False),
        yaxis=dict(range=[-0.04,1.02],visible=False),
        height=540)
    st.plotly_chart(fig, use_container_width=True)

    # Legend
    leg = st.columns(4)
    for col, label, color in [
        (leg[0],"Component & Platform",CL),
        (leg[1],"Motion Control (STM32 + DRV8825)",AMBER),
        (leg[2],"Camera & Image Processing",INDIGO),
        (leg[3],"CNN & Decision / Output",ACCEPT),
    ]:
        col.markdown(f"""
        <div style="display:flex;align-items:center;gap:8px;padding:6px 10px;
                    background:{BG2};border:1px solid {BORDER2};border-radius:4px;">
          <div style="width:10px;height:10px;border-radius:50%;
                      background:{color};box-shadow:0 0 6px {color};"></div>
          <span style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;
                       color:{TEXT2};text-transform:uppercase;">{label}</span>
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 4 — CNN Pipeline
# ════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(f"""
    <div style="padding:12px 16px;background:{WARN}18;border:1px solid {WARN};
                border-radius:6px;margin-bottom:16px;
                font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{WARN};">
      <b>Dual-channel does not mean two cameras.</b> One camera provides the source image.
      The application creates two versions: a grayscale image (channel 1) and a
      Sobel edge-detection image (channel 2). Both enter the CNN simultaneously.
      The model learns features from each branch independently, then combines them
      to predict: Normal, Crack, Dent, or Scratch.
      Trained model weights are not yet integrated — the pipeline shown is the intended architecture.
    </div>
    """, unsafe_allow_html=True)
    DualChannelCNNVisualizer().display_cnn_pipeline_visualization()

    st.divider()
    sec("Why Dual-Channel?")
    dc1, dc2 = st.columns(2)
    dc1.markdown(spec_card("Channel 1 — Grayscale Image", [
        "Preserves surface texture and brightness variation",
        "Dents produce subtle shading differences",
        "Scratches may show surface roughness change",
        "Cracks appear as dark linear regions",
        "Normal machining marks also produce texture",
    ], accent=CL, note="Source: original camera frame converted to grayscale"), unsafe_allow_html=True)
    dc2.markdown(spec_card("Channel 2 — Edge Detection (Sobel)", [
        "Highlights intensity boundaries and transitions",
        "Cracks produce strong linear edge responses",
        "Scratches produce parallel edge lines",
        "Dents produce curved boundary edges",
        "Combined with channel 1 to reduce false positives",
    ], accent=INDIGO, note="Source: same frame — Sobel gradient magnitude applied"), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# TAB 5 — Integration Status
# ════════════════════════════════════════════════════════════════
with tab5:
    sec("Current Integration Status")
    for component, info in INTEGRATION_STATUS.items():
        color = ACCEPT if info["integrated"] else WARN
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:14px;padding:12px 16px;
                    background:{PANEL};border:1px solid {BORDER2};
                    border-left:4px solid {color};border-radius:6px;margin-bottom:6px;">
          <div style="width:10px;height:10px;border-radius:50%;
                      background:{color};box-shadow:0 0 6px {color};flex-shrink:0;"></div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.9rem;
                      font-weight:700;color:{TEXT};min-width:180px;">{component}</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                      color:{color};">{info['status']}</div>
        </div>""", unsafe_allow_html=True)

    st.divider()
    sec("What Will Prove the Project Works")
    proof_items = [
        ("Platform repeatability",    "Rotates to the same reference position every time — verified by physical measurement", ACCEPT),
        ("Settled capture timing",    f"Images captured after vibration settles — settling delay confirmed with actual hardware", CL),
        ("Defect visibility",         "Smallest targeted defects (crack width, scratch depth) are visible in captured images", CL),
        ("CNN detection on new parts","Model correctly identifies defects on components not seen during training", AMBER),
        ("Normal component handling", "Normal components are not rejected — false reject rate measured and acceptable", AMBER),
        ("Incomplete inspection flag","Failed captures (blur, disconnect, timeout) produce REVIEW, not ACCEPT or REJECT", WARN),
        ("Traceable records",         "Each rejection can be reviewed: images, angle, confidence, and decision criteria present", ACCEPT),
        ("Measured performance",      "Defect precision, recall, false-accept rate, false-reject rate, and inspection time measured", AMBER),
    ]
    for item, desc, color in proof_items:
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:220px 1fr;gap:12px;
                    padding:9px 14px;background:{BG2};border-bottom:1px solid {BORDER2};">
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.85rem;
                      font-weight:700;color:{color};">{item}</div>
          <div style="font-family:'Space Grotesk',sans-serif;font-size:0.85rem;
                      color:{TEXT2};line-height:1.5;">{desc}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="margin-top:20px;padding:12px 16px;background:{PANEL};
                border:1px solid {BORDER2};border-radius:6px;text-align:center;">
      <span style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;
                   color:{TEXT3};letter-spacing:0.08em;">
        {PRODUCT_NAME} &nbsp;·&nbsp; {VERSION}
      </span>
    </div>""", unsafe_allow_html=True)
