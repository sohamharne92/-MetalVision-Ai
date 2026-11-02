"""
METALVISION AI — Page 2: Live 360° Inspection
Operator enters Part ID, selects scenario, runs animated scan.
Displays per-position results, image quality flags, and 3-outcome verdict.
"""
import streamlit as st
import plotly.graph_objects as go
import math, time
from datetime import datetime

from config import (
    INSPECTION_POSITIONS, DEMO_SCENARIOS, SIMULATION_WARNING,
    INSPECTION_STEP_DELAY, TOTAL_POSITIONS, INSPECTION_ANGLE_STEP,
    MOTOR_FULL_STEP_ANGLE, MOTOR_STEPS_PER_REV,
    CAMERA_MODEL, CAMERA_INTERFACE, CAMERA_SETTLE_DELAY_S,
    DECISION_ACCEPT, DECISION_REJECT, DECISION_REVIEW,
    get_decision_color, simulate_image_quality,
)
from modules.simulator import MetalPartSimulator
from modules.data_manager import InspectionDataManager
from modules.cnn_pipeline import DualChannelCNNVisualizer
from modules.utils import init_session_state, add_to_inspection_history, format_confidence

init_session_state()
dm = InspectionDataManager()

BG="#12100a";BG2="#1c1710";PANEL="#241d12";PANEL2="#2c2416"
BORDER="#4a3018";BORDER2="#2e1e0c"
CL="#e8a85a";CD="#8a5520";AMBER="#f5a623"
TEXT="#f5ead8";TEXT2="#c8a878";TEXT3="#8a6840"
ACCEPT="#34d399";REJECT="#fb7185";WARN="#fbbf24"

STATUS_COLORS = {"Pending":"#4a3010","Inspecting":AMBER,"Normal":ACCEPT,"Defect":REJECT}
STATUS_SIZES  = {"Pending":18,"Inspecting":32,"Normal":24,"Defect":28}

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

def decision_color(dec):
    return ACCEPT if dec == DECISION_ACCEPT else REJECT if dec == DECISION_REJECT else WARN

def build_ring(statuses: dict) -> go.Figure:
    r = 1.0
    xs,ys,colors,sizes,hovers,labels = [],[],[],[],[],[]
    for a in INSPECTION_POSITIONS:
        rad = math.radians(90 - a)
        xs.append(r * math.cos(rad)); ys.append(r * math.sin(rad))
        s = statuses.get(a, "Pending")
        colors.append(STATUS_COLORS.get(s, "#4a3010"))
        sizes.append(STATUS_SIZES.get(s, 18))
        hovers.append(f"<b>{a}°</b> — {s}")
        labels.append(f"{a}°")

    fig = go.Figure()
    ang = [math.radians(90 - a) for a in range(0, 361, 2)]
    fig.add_trace(go.Scatter(x=[0.94*math.cos(a) for a in ang],
                              y=[0.94*math.sin(a) for a in ang],
                              mode="lines", line=dict(color=BORDER, width=28),
                              hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.94*math.cos(a) for a in ang],
                              y=[0.94*math.sin(a) for a in ang],
                              mode="lines", line=dict(color=CL, width=1.5),
                              hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[0.72*math.cos(a) for a in ang],
                              y=[0.72*math.sin(a) for a in ang],
                              mode="lines", line=dict(color=BORDER2, width=1, dash="dot"),
                              hoverinfo="skip", showlegend=False))
    for a in INSPECTION_POSITIONS:
        rad = math.radians(90 - a)
        fig.add_shape(type="line",
                      x0=0.78*math.cos(rad), y0=0.78*math.sin(rad),
                      x1=0.88*math.cos(rad), y1=0.88*math.sin(rad),
                      line=dict(color=CD, width=1.5))
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text",
        marker=dict(size=sizes, color=colors, line=dict(color=BG, width=2)),
        text=labels, textfont=dict(color="white", size=7, family="JetBrains Mono"),
        textposition="middle center",
        hovertext=hovers, hoverinfo="text", showlegend=False))
    fig.add_annotation(x=0, y=0, text=f"<b>360°</b><br>{TOTAL_POSITIONS} views",
        font=dict(color=AMBER, size=12, family="JetBrains Mono"), showarrow=False)
    for s, c in STATUS_COLORS.items():
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
            marker=dict(size=9, color=c), name=s, showlegend=True))
    fig.update_layout(
        paper_bgcolor=BG2, plot_bgcolor=BG2,
        font=dict(color=TEXT, family="Space Grotesk"),
        legend=dict(orientation="h", x=0.5, y=-0.05, xanchor="center",
                    font=dict(color=TEXT2, size=9, family="Space Grotesk")),
        xaxis=dict(range=[-1.3,1.3], visible=False, scaleanchor="y"),
        yaxis=dict(range=[-1.3,1.3], visible=False),
        height=460, margin=dict(l=10,r=10,t=10,b=30))
    return fig

def statuses_from_session():
    data = st.session_state.get("inspection_data")
    if not data: return {a: "Pending" for a in INSPECTION_POSITIONS}
    return {a: "Normal" if data["positions"].get(a,{}).get("class","Normal")=="Normal"
              else "Defect" for a in INSPECTION_POSITIONS}

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    sec("Inspection Setup")

    part_id_input = st.text_input(
        "Component Part ID",
        value=st.session_state.get("part_id_input", ""),
        placeholder="e.g. MC-2024-0001",
        key="part_id_input",
    )

    scenario_names = list(DEMO_SCENARIOS.keys())
    selected = st.selectbox(
        "Inspection Scenario",
        scenario_names,
        index=scenario_names.index(
            st.session_state.get("selected_scenario", scenario_names[0])),
        key="selected_scenario",
    )
    sc_info = DEMO_SCENARIOS[selected]
    st.markdown(f"""
    <div style="background:{BG2};border:1px solid {BORDER2};border-left:3px solid {AMBER};
                border-radius:4px;padding:10px 12px;margin-top:6px;
                font-family:'Space Grotesk',sans-serif;font-size:0.85rem;color:{TEXT2};">
      {sc_info['description']}
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="v-section" style="margin:14px 0 6px;">Storage Settings</div>',
                unsafe_allow_html=True)
    retention = st.selectbox(
        "Auto-delete captures after",
        options=["1 hour", "6 hours", "24 hours", "48 hours", "7 days", "Never"],
        index=2,   # default 24 hours
        key="capture_retention",
    )
    retention_map = {
        "1 hour": 1, "6 hours": 6, "24 hours": 24,
        "48 hours": 48, "7 days": 168, "Never": 999999,
    }
    st.session_state["capture_retention_hours"] = retention_map[retention]
    st.markdown(f"""
    <div style="padding:7px 10px;background:{BG2};border:1px solid {BORDER2};
                border-radius:4px;font-family:'JetBrains Mono',monospace;
                font-size:0.72rem;color:{TEXT3};">
      Captures saved to: data/captures/&lt;insp_id&gt;/<br>
      Auto-deleted after: {retention}
    </div>""", unsafe_allow_html=True)

# ── Page header ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Live 360° Inspection</div>
  <div class="v-hero-sub">
    Stepper-motor-driven surface defect detection — {TOTAL_POSITIONS} positions at {INSPECTION_ANGLE_STEP}° intervals
  </div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">{TOTAL_POSITIONS} POSITIONS</span>
    <span class="v-hero-pill">DUAL-CHANNEL CNN</span>
    <span class="v-hero-pill">ACCEPT / REJECT / REVIEW</span>
    <span class="v-hero-pill">REAL CAMERA CAPTURE</span>
  </div>
</div>""", unsafe_allow_html=True)

# ── Camera & Resolution — on main page so always visible ─────────────────────
sec("Camera Setup")
cam_col, res_col, info_col = st.columns([1, 1, 1.2])

CAM_OPTIONS = {
    0: "Camera 0 — Default webcam",
    1: "Camera 1 — Secondary",
    2: "Camera 2 — External USB",
    3: "Camera 3 — DroidCam / Phone",
    4: "Camera 4 — Additional",
}
RES_OPTIONS = {
    "640 × 480  (SD — fast)":              (640,  480),
    "1280 × 720  (HD — recommended)":      (1280, 720),
    "1920 × 1080 (Full HD — high detail)": (1920, 1080),
}

with cam_col:
    insp_cam = st.selectbox(
        "Camera",
        options=list(CAM_OPTIONS.keys()),
        format_func=lambda x: CAM_OPTIONS[x],
        index=st.session_state.get("insp_cam_index", 0),
        key="insp_cam_sel",
    )
    st.session_state["insp_cam_index"] = insp_cam

with res_col:
    insp_res_label = st.selectbox(
        "Resolution",
        options=list(RES_OPTIONS.keys()),
        index=st.session_state.get("insp_res_idx", 1),
        key="insp_res_sel",
    )
    st.session_state["insp_res_idx"] = list(RES_OPTIONS.keys()).index(insp_res_label)
    st.session_state["insp_cap_w"]   = RES_OPTIONS[insp_res_label][0]
    st.session_state["insp_cap_h"]   = RES_OPTIONS[insp_res_label][1]

with info_col:
    w = RES_OPTIONS[insp_res_label][0]
    h = RES_OPTIONS[insp_res_label][1]
    st.markdown(f"""
    <div style="background:{PANEL};border:1px solid {BORDER2};border-radius:6px;
                padding:12px 16px;font-family:'JetBrains Mono',monospace;
                font-size:0.78rem;color:{TEXT2};line-height:2;">
      <div><span style="color:{CD};">Active camera</span> : {CAM_OPTIONS[insp_cam]}</div>
      <div><span style="color:{CD};">Resolution    </span> : {w} × {h}</div>
      <div><span style="color:{CD};">Frames saved  </span> : data/captures/&lt;insp_id&gt;/</div>
      <div><span style="color:{WARN};">CNN status    </span> : {'Real CNN — 4 classes active' if st.session_state.get('cnn_engine') and st.session_state['cnn_engine'].is_ready else 'Simulation (model not loaded)'}</div>
    </div>
    """, unsafe_allow_html=True)

# ── Main layout ───────────────────────────────────────────────────────────────
if not st.session_state.get("inspection_in_progress"):
    ring_col, panel_col = st.columns([1.1, 0.9])

    with ring_col:
        sec("360° Scan Visualiser")
        st.plotly_chart(build_ring(statuses_from_session()), use_container_width=True)

    with panel_col:
        sec("Inspection Readout")
        data = st.session_state.get("inspection_data")

        if data:
            dec  = data.get("final_decision", "—")
            dc   = decision_color(dec)
            conf = float(data.get("overall_confidence", 0))
            qi   = data.get("quality_issues", 0)

            # 3-outcome verdict card
            st.markdown(f"""
            <div class="v-decision {'v-decision-accept' if dec==DECISION_ACCEPT
                                    else 'v-decision-reject'} v-fade-in">
              <div class="v-decision-label">
                {'Final Verdict' if dec != DECISION_REVIEW else 'Requires Review'}
              </div>
              <div class="v-decision-text" style="color:{dc};">{dec}</div>
              <div class="v-decision-conf">
                Simulated confidence: {conf*100:.1f}%
                &nbsp;|&nbsp; Defects: {data.get('defect_count',0)}
                &nbsp;|&nbsp; Quality issues: {qi}
                &nbsp;|&nbsp; Frames captured: {data.get('captured_count', 0)}/{TOTAL_POSITIONS}
              </div>
            </div>""", unsafe_allow_html=True)

            if dec == DECISION_REVIEW:
                st.markdown(f"""
                <div style="margin-top:8px;padding:10px 14px;background:{WARN}18;
                            border:1px solid {WARN};border-radius:6px;
                            font-family:'Space Grotesk',sans-serif;
                            font-size:0.85rem;color:{WARN};">
                  One or more positions returned low confidence. In the real system,
                  these would require a retake before a decision can be made.
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Defect list
            defects = [(a, p) for a, p in data["positions"].items()
                       if p.get("class") != "Normal"]
            if defects:
                sec("Defects Detected")
                dcmap = {"Crack": REJECT, "Dent": AMBER, "Scratch": "#c084fc"}
                for angle, pos in sorted(defects, key=lambda x: x[0]):
                    dc2 = dcmap.get(pos["class"], CL)
                    qf  = data.get("quality_flags", {}).get(angle, {})
                    qbadge = ""
                    if qf and not qf.get("quality_ok", True):
                        qbadge = (f'<span class="v-badge v-badge-warn" '
                                  f'style="font-size:0.65rem;">'
                                  f'Image: {", ".join(qf.get("flags", []))}</span>')
                    st.markdown(f"""
                    <div class="v-defect-row v-fade-in">
                      <div style="width:8px;height:8px;border-radius:50%;
                                  background:{dc2};box-shadow:0 0 6px {dc2};
                                  flex-shrink:0;"></div>
                      <span class="v-badge" style="background:{dc2}22;color:{dc2};
                            border:1px solid {dc2};">{pos['class']}</span>
                      <span style="font-family:JetBrains Mono,monospace;
                                   font-size:0.75rem;color:{TEXT2};">
                        Position {angle}°</span>
                      <span style="font-family:JetBrains Mono,monospace;
                                   font-size:0.72rem;color:{TEXT3};margin-left:auto;">
                        {format_confidence(pos['confidence'])} (sim)</span>
                      {qbadge}
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="padding:14px;background:{ACCEPT}12;
                            border:1px solid {ACCEPT};border-radius:6px;text-align:center;">
                  <span style="font-family:'Space Grotesk',sans-serif;font-size:0.88rem;
                               color:{ACCEPT};font-weight:600;">
                    All {TOTAL_POSITIONS} positions — Normal
                  </span>
                </div>""", unsafe_allow_html=True)

            # Position grid
            sec("Position Summary")
            cols_g = st.columns(6)
            for idx, a in enumerate(INSPECTION_POSITIONS):
                p   = data["positions"].get(a, {})
                cls = p.get("class", "Normal")
                pc  = ACCEPT if cls == "Normal" else REJECT
                qf  = data.get("quality_flags", {}).get(a, {})
                qi_border = f"border:1px solid {WARN};" if qf and not qf.get("quality_ok", True) else f"border:1px solid {pc}44;"
                with cols_g[idx % 6]:
                    st.markdown(f"""
                    <div style="background:{pc}18;{qi_border}border-radius:4px;
                                padding:6px 4px;text-align:center;margin-bottom:4px;">
                      <div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;
                                  color:{pc};">{a}°</div>
                      <div style="font-family:Space Grotesk,sans-serif;font-size:0.6rem;
                                  color:{pc};text-transform:uppercase;">
                        {'OK' if cls=='Normal' else cls[:3]}
                      </div>
                    </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="v-plate" style="text-align:center;padding:40px 20px;">
              <div style="font-family:'Bebas Neue',cursive;font-size:1.8rem;
                          color:{TEXT3};margin-bottom:8px;">
                Awaiting Inspection</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                          color:{TEXT3};">
                Enter Part ID · Select scenario · Press START
              </div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        b1, b2 = st.columns(2)
        with b1:
            if st.button("START INSPECTION", type="primary", use_container_width=True):
                st.session_state.trigger_inspection = True
                st.session_state.inspection_data    = None
                st.session_state.last_saved_id      = None
                st.rerun()
        with b2:
            if st.button("RESET", use_container_width=True):
                st.session_state.inspection_data        = None
                st.session_state.inspection_in_progress = False
                st.session_state.last_saved_id          = None
                st.session_state.trigger_inspection     = False
                st.rerun()

        if data and st.session_state.get("last_saved_id") != data.get("inspection_id"):
            if st.button("SAVE TO HISTORY", use_container_width=True):
                record = {
                    "inspection_id":       data["inspection_id"],
                    "timestamp":           data["timestamp"],
                    "part_id":             data.get("part_id") or part_id_input or "—",
                    "scenario":            st.session_state.get("selected_scenario", ""),
                    "decision":            data["final_decision"],
                    "confidence":          data["overall_confidence"],
                    "defects_found":       data["defect_count"],
                    "defect_types":        list({p["class"] for p in data["positions"].values()
                                                 if p["class"] != "Normal"}),
                    "positions_inspected": len(data["positions"]),
                    "defect_positions":    [a for a, p in data["positions"].items()
                                            if p["class"] != "Normal"],
                    "notes":               f"Quality issues: {data.get('quality_issues',0)} | Frames: data/captures/{data.get('inspection_id','')}/",
                }
                if dm.add_inspection(record):
                    add_to_inspection_history(data)
                    st.session_state.last_saved_id = data["inspection_id"]
                    st.success("Saved to history.")
                    st.rerun()

# ── Animated scan ─────────────────────────────────────────────────────────────
if st.session_state.get("trigger_inspection"):
    st.session_state.trigger_inspection     = False
    st.session_state.inspection_in_progress = True

if st.session_state.get("inspection_in_progress"):
    import os, cv2, numpy as np, base64
    from PIL import Image as PILImage
    from pathlib import Path
    import io as _io
    os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

    scenario_name = st.session_state.get("selected_scenario", "Scenario 5: Random Test")
    sim           = MetalPartSimulator()
    entered_pid   = st.session_state.get("part_id_input", "").strip()
    sim.part_id   = entered_pid if entered_pid else f"AUTO-{sim.inspection_id}"

    cam_index = st.session_state.get("insp_cam_index", 0)
    cap_w     = st.session_state.get("insp_cap_w",  1280)
    cap_h     = st.session_state.get("insp_cap_h",  720)

    # ── Absolute capture directory ─────────────────────────────────────────────
    # Derive project root relative to the running app (portable — no hardcoded path).
    # Page file lives in <project>/pages/, so go up one level to reach the project root.
    PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
    CAPTURE_DIR = os.path.join(PROJECT_ROOT, "data", "captures", sim.inspection_id)
    os.makedirs(CAPTURE_DIR, exist_ok=True)

    # ── Auto-cleanup: delete inspection folders older than 24 hours ────────────
    def auto_cleanup(base_dir, max_age_hours=24):
        import time
        base = os.path.join(PROJECT_ROOT, "data", "captures")
        if not os.path.exists(base):
            return
        now = time.time()
        deleted = 0
        for folder in os.listdir(base):
            fpath = os.path.join(base, folder)
            if not os.path.isdir(fpath):
                continue
            age_hours = (now - os.path.getmtime(fpath)) / 3600
            if age_hours > max_age_hours:
                import shutil
                shutil.rmtree(fpath, ignore_errors=True)
                deleted += 1
        return deleted

    cleanup_count = auto_cleanup(CAPTURE_DIR,
                                 max_age_hours=st.session_state.get("capture_retention_hours", 24))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _open_cam(idx, w, h):
        for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
            try:
                c = cv2.VideoCapture(idx, backend)
                if not c.isOpened(): c.release(); continue
                c.set(cv2.CAP_PROP_FRAME_WIDTH,  w)
                c.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
                c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                for _ in range(4): c.grab()
                ok, fr = c.read()
                if ok and fr is not None: return c, backend
                c.release()
            except Exception: pass
        return None, None

    def _quality(bgr):
        if bgr is None:
            return {"blur_score":0,"brightness":0,"flags":["no frame"],"quality_ok":False}
        g  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        bl = float(cv2.Laplacian(g, cv2.CV_64F).var())
        br = float(g.mean())
        fl = []
        if bl < 20:  fl.append("blurry")
        if br < 30:  fl.append("too dark")
        if br > 230: fl.append("overexposed")
        return {"blur_score":round(bl,1),"brightness":round(br,1),
                "flags":fl,"quality_ok":len(fl)==0}

    def _bgr_pil(bgr):
        return PILImage.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

    def _to_b64(pil_img, size=(200,150)):
        img  = pil_img.resize(size, PILImage.BILINEAR)
        buf  = _io.BytesIO()
        img.save(buf, format="JPEG", quality=75)
        return base64.b64encode(buf.getvalue()).decode()

    # ── Motor monitor ─────────────────────────────────────────────────────────
    if "motor_ctrl" not in st.session_state:
        try:
            from modules.motor import get_or_connect
            mc = get_or_connect()
            st.session_state["motor_ctrl"] = mc
        except Exception:
            st.session_state["motor_ctrl"] = None

    # Always get from module singleton (survives reruns)
    from modules.motor import get_singleton as _get_motor_singleton
    motor_ctrl = _get_motor_singleton() or st.session_state.get("motor_ctrl")
    use_motor  = motor_ctrl is not None and motor_ctrl.connected and motor_ctrl.is_ready

    # ── CNN engine ────────────────────────────────────────────────────────────
    # Always load fresh from the module singleton so model_info.json changes
    # are picked up without requiring a browser session restart.
    try:
        from cnn.inference import MetalVisionInference
        # Force a fresh instance every inspection run so stale cached
        # engines (from when weights were mis-matched) don't persist.
        _eng = MetalVisionInference()
        st.session_state["cnn_engine"] = _eng
    except Exception:
        st.session_state["cnn_engine"] = None
    cnn_engine = st.session_state.get("cnn_engine")
    use_cnn    = cnn_engine is not None and cnn_engine.is_ready

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 1 — CAPTURE ALL 12 IMAGES
    # ══════════════════════════════════════════════════════════════════════════
    st.markdown(f"""
    <div style="padding:10px 16px;background:{AMBER}18;border:1px solid {AMBER};
                border-radius:6px;margin-bottom:12px;
                font-family:'JetBrains Mono',monospace;font-size:0.88rem;color:{AMBER};">
      PHASE 1 / 2 &nbsp;·&nbsp; Capturing {TOTAL_POSITIONS} images
      &nbsp;·&nbsp; Camera {cam_index} &nbsp;·&nbsp; {cap_w}×{cap_h}
      &nbsp;·&nbsp; Part: {sim.part_id}
      &nbsp;·&nbsp; Motor: {'AUTO — {:.1f} RPM'.format(motor_ctrl.rpm) if use_motor else 'MANUAL ROTATION'}
    </div>""", unsafe_allow_html=True)

    # Layout: live preview | scan log
    col_live, col_log = st.columns([1.4, 0.6])
    with col_live:
        st.markdown(f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.75rem;"
                    f"letter-spacing:0.14em;color:{CD};text-transform:uppercase;"
                    f"margin:0 0 4px;'>Live Camera Feed</p>", unsafe_allow_html=True)
        live_ph  = st.empty()
        stat_ph  = st.empty()
        prog_ph  = st.empty()
    with col_log:
        st.markdown(f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.75rem;"
                    f"letter-spacing:0.14em;color:{CD};text-transform:uppercase;"
                    f"margin:0 0 4px;'>Capture Log</p>", unsafe_allow_html=True)
        caplog_ph = st.empty()

    # Full 12-image gallery placeholder (shown after all captures)
    st.markdown(f"<div class='v-section' style='margin:14px 0 8px;'>All Captured Images ({TOTAL_POSITIONS} positions)</div>",
                unsafe_allow_html=True)
    gallery_ph = st.empty()

    # Open camera once
    cap, backend = _open_cam(cam_index, cap_w, cap_h)
    camera_ok    = cap is not None
    if not camera_ok:
        live_ph.error(f"Cannot open camera {cam_index}. Check connection.")

    captured_frames = {}
    quality_flags   = {}
    cap_log_entries = []

    for idx, angle in enumerate(INSPECTION_POSITIONS):
        prog_ph.progress((idx + 1) / TOTAL_POSITIONS)
        stat_ph.markdown(
            f"<div style='padding:7px 12px;background:{AMBER}12;"
            f"border-left:3px solid {AMBER};border-radius:4px;"
            f"font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{AMBER};'>"
            f"Capturing position <b>{angle}°</b> &nbsp; ({idx+1}/{TOTAL_POSITIONS})</div>",
            unsafe_allow_html=True,
        )

        # ── Motor: wait for rotation to reach this angle ──────────────────────
        if use_motor:
            stat_ph.markdown(
                f"<div style='padding:7px 12px;background:{AMBER}12;"
                f"border-left:3px solid {AMBER};border-radius:4px;"
                f"font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{AMBER};'>"
                f"⟳ &nbsp; Motor spinning — waiting for <b>{angle}°</b> "
                f"&nbsp;({idx+1}/{TOTAL_POSITIONS}) "
                f"&nbsp; Now: {motor_ctrl.angle:.0f}° "
                f"&nbsp; {motor_ctrl.rpm:.1f} RPM</div>",
                unsafe_allow_html=True,
            )
            reached = motor_ctrl.wait_for_angle(angle, timeout_s=60.0)
            if not reached:
                stat_ph.warning(f"Timeout waiting for {angle}° — capturing anyway")
        else:
            # Manual rotation prompt when motor not connected
            if idx > 0:
                stat_ph.markdown(
                    f"<div style='padding:7px 12px;background:{WARN}18;"
                    f"border:2px solid {WARN};border-radius:6px;"
                    f"font-family:JetBrains Mono,monospace;font-size:0.88rem;color:{WARN};'>"
                    f"⟳ &nbsp; Manually rotate component to <b>{angle}°</b>, then wait…"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                time.sleep(INSPECTION_STEP_DELAY)

        # ── Read frame — flush camera buffer for a fresh frame ────────────────
        bgr = None
        if camera_ok:
            # Drain stale buffered frames before reading
            for _ in range(4):
                cap.grab()
            time.sleep(CAMERA_SETTLE_DELAY_S)   # let sensor settle
            ok, fr = cap.read()
            if ok and fr is not None: bgr = fr

        qf = _quality(bgr)
        quality_flags[angle] = qf

        if bgr is not None:
            fpath = os.path.join(CAPTURE_DIR, f"pos_{angle:03d}deg.jpg")
            saved = cv2.imwrite(fpath, bgr, [cv2.IMWRITE_JPEG_QUALITY, 82])
            captured_frames[angle] = bgr

            # Live frame display
            live_ph.image(_bgr_pil(bgr),
                caption=f"{angle}° | {bgr.shape[1]}×{bgr.shape[0]} | "
                        f"Blur:{qf['blur_score']} | Brt:{qf['brightness']} | "
                        f"{'OK' if qf['quality_ok'] else ' '.join(qf['flags'])}",
                use_container_width=True,
            )
        else:
            live_ph.markdown(
                f"<div style='padding:32px;background:{REJECT}18;border:1px solid {REJECT};"
                f"border-radius:6px;text-align:center;"
                f"font-family:JetBrains Mono,monospace;color:{REJECT};'>"
                f"No frame at {angle}°</div>", unsafe_allow_html=True)

        # Capture log entry
        qc = ACCEPT if qf["quality_ok"] else WARN
        cap_log_entries.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:5px 8px;'
            f'border-bottom:1px solid {BORDER2};font-family:JetBrains Mono,monospace;font-size:0.75rem;">'
            f'<span style="min-width:36px;color:{AMBER};font-weight:700;">{angle}°</span>'
            f'<span style="color:{"#34d399" if bgr is not None else "#fb7185"};">'
            f'{"Captured" if bgr is not None else "FAILED"}</span>'
            f'<span style="color:{qc};margin-left:auto;">'
            f'{"OK" if qf["quality_ok"] else " ".join(qf["flags"])}</span>'
            f'</div>'
        )
        caplog_ph.markdown(
            f'<div style="background:{BG2};border:1px solid {BORDER2};border-radius:6px;'
            f'max-height:380px;overflow-y:auto;">'
            + "".join(cap_log_entries) + "</div>",
            unsafe_allow_html=True,
        )

        # Update the full gallery after EVERY capture
        # Build a 4-column grid showing all captured images so far
        if captured_frames:
            angles_done = sorted(captured_frames.keys())
            # Build HTML grid of all captured images
            html_cells = ""
            for a in angles_done:
                b64   = _to_b64(_bgr_pil(captured_frames[a]))
                qf_a  = quality_flags.get(a, {})
                border_color = ACCEPT if qf_a.get("quality_ok", True) else WARN
                html_cells += f"""
                <div style="text-align:center;">
                  <img src="data:image/jpeg;base64,{b64}"
                       style="width:100%;border-radius:4px;
                              border:2px solid {border_color};" />
                  <div style="font-family:JetBrains Mono,monospace;font-size:0.68rem;
                               color:{AMBER};margin-top:2px;">{a}°</div>
                  <div style="font-family:Space Grotesk,sans-serif;font-size:0.6rem;
                               color:{"#34d399" if qf_a.get("quality_ok",True) else "#f5a623"};">
                    {"OK" if qf_a.get("quality_ok",True) else " | ".join(qf_a.get("flags",[]))}</div>
                </div>"""

            gallery_ph.markdown(
                f'<div style="display:grid;grid-template-columns:repeat(4,1fr);'
                f'gap:8px;background:{BG2};border:1px solid {BORDER2};'
                f'border-radius:8px;padding:12px;">'
                + html_cells + "</div>",
                unsafe_allow_html=True,
            )

    # Close camera
    if camera_ok and cap is not None:
        cap.release()

    n_captured = len(captured_frames)
    prog_ph.progress(1.0)
    stat_ph.markdown(
        f"<div style='padding:7px 12px;background:{ACCEPT}12;"
        f"border-left:3px solid {ACCEPT};border-radius:4px;"
        f"font-family:JetBrains Mono,monospace;font-size:0.82rem;color:{ACCEPT};'>"
        f"Capture complete — {n_captured}/{TOTAL_POSITIONS} images saved "
        f"&nbsp;·&nbsp; Stored for 24 hours in data/captures/{sim.inspection_id}/</div>",
        unsafe_allow_html=True,
    )

    # ══════════════════════════════════════════════════════════════════════════
    # PHASE 2 — CLASSIFY ALL CAPTURED IMAGES
    # ══════════════════════════════════════════════════════════════════════════
    cnn_status_color = "#34d399" if use_cnn else "#818cf8"
    cnn_status_label = (
        f"Real CNN — {', '.join(cnn_engine.CLASS_NAMES)} — 4 classes"
        if use_cnn else "Simulation mode (CNN not loaded)"
    )
    st.markdown(f"""
    <div style="padding:10px 16px;background:{cnn_status_color}18;
                border:1px solid {cnn_status_color};
                border-radius:6px;margin:12px 0;
                font-family:'JetBrains Mono',monospace;font-size:0.88rem;
                color:{cnn_status_color};">
      PHASE 2 / 2 &nbsp;·&nbsp; Classifying {n_captured} images
      &nbsp;·&nbsp; {cnn_status_label}
    </div>""", unsafe_allow_html=True)

    cls_prog = st.empty()
    cls_stat = st.empty()
    cls_log  = st.empty()

    statuses    = {a: "Pending" for a in INSPECTION_POSITIONS}
    log_entries = []

    for idx, angle in enumerate(INSPECTION_POSITIONS):
        cls_prog.progress((idx + 1) / TOTAL_POSITIONS)
        cls_stat.markdown(
            f"<div style='padding:6px 12px;background:#818cf812;"
            f"border-left:3px solid #818cf8;border-radius:4px;"
            f"font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#818cf8;'>"
            f"Classifying <b>{angle}°</b> ({idx+1}/{TOTAL_POSITIONS})</div>",
            unsafe_allow_html=True,
        )

        bgr = captured_frames.get(angle)
        qf  = quality_flags.get(angle, {"flags":["no frame"],"quality_ok":False,
                                          "blur_score":0,"brightness":0})

        if use_cnn and bgr is not None:
            res = cnn_engine.predict_from_array(bgr)
            cls = res["class"]; cf = res["confidence"]; src = "CNN"
        else:
            p   = sim.inspect_one(angle, scenario_name)
            cls = p["class"];  cf = p["confidence"];   src = "sim"

        sim.inspection_results[angle] = {
            "angle": angle, "class": cls,
            "confidence": round(float(cf), 4),
            "timestamp": datetime.now().isoformat(), "source": src,
        }
        sim.quality_flags[angle] = qf

        ok  = cls == "Normal"
        statuses[angle] = "Normal" if ok else "Defect"
        dc2   = ACCEPT if ok else REJECT
        qnote = f"[{','.join(qf['flags'])}] " if not qf["quality_ok"] else ""

        # Thumbnail + result row
        b64_img = ""
        if angle in captured_frames:
            b64_img = (f'<img src="data:image/jpeg;base64,{_to_b64(_bgr_pil(captured_frames[angle]), (56,42))}" '
                       f'style="width:56px;height:42px;object-fit:cover;border-radius:3px;flex-shrink:0;'
                       f'border:1px solid {dc2};"/>')

        log_entries.append(
            f'<div style="display:flex;align-items:center;gap:8px;padding:5px 8px;'
            f'border-bottom:1px solid {BORDER2};">'
            f'{b64_img}'
            f'<span style="min-width:38px;font-family:JetBrains Mono,monospace;"'
            f'font-size:0.78rem;color:{AMBER};font-weight:700;">{angle}°</span>'
            f'<span style="flex:1;font-family:Space Grotesk,sans-serif;font-size:0.82rem;'
            f'color:{dc2};">{qnote}{"Normal" if ok else cls}</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.78rem;'
            f'color:{dc2};font-weight:700;">{cf*100:.0f}%</span>'
            f'<span style="font-family:JetBrains Mono,monospace;font-size:0.65rem;'
            f'color:{TEXT3};">[{src}]</span>'
            f'</div>'
        )
        cls_log.markdown(
            f'<div style="background:{BG2};border:1px solid {BORDER2};"'
            f'border-radius:6px;max-height:400px;overflow-y:auto;">'
            + "".join(log_entries) + "</div>",
            unsafe_allow_html=True,
        )

    # ── Finalise ──────────────────────────────────────────────────────────────
    results = sim.finalise()
    results["capture_dir"]    = CAPTURE_DIR
    results["captured_count"] = n_captured

    final_dec = results.get("final_decision", "")
    fdc       = decision_color(final_dec)
    cls_prog.progress(1.0)
    cls_stat.empty()

    st.markdown(f"""
    <div style="padding:20px 24px;background:{fdc}12;border:3px solid {fdc};
                border-radius:8px;text-align:center;margin:16px 0;">
      <div style="font-family:'Space Grotesk',sans-serif;font-size:0.72rem;
                  font-weight:700;letter-spacing:0.22em;text-transform:uppercase;
                  color:{TEXT3};margin-bottom:6px;">FINAL VERDICT</div>
      <div style="font-family:'Bebas Neue',cursive;font-size:3.2rem;
                  color:{fdc};text-shadow:0 0 24px {fdc};letter-spacing:0.1em;line-height:1;">
        {final_dec}
      </div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.82rem;
                  color:{TEXT2};margin-top:10px;">
        {n_captured}/{TOTAL_POSITIONS} frames captured
        &nbsp;·&nbsp; {results.get('defect_count',0)} defect(s) found
        &nbsp;·&nbsp; {results.get('overall_confidence',0)*100:.1f}% confidence
        &nbsp;·&nbsp; {'Real CNN' if use_cnn else 'Simulation'}
        &nbsp;·&nbsp; Images stored 24h → data/captures/{sim.inspection_id}/
      </div>
    </div>""", unsafe_allow_html=True)

    st.plotly_chart(build_ring(statuses), use_container_width=True)

    st.session_state.inspection_data        = results
    st.session_state.inspection_in_progress = False
    st.rerun()

st.divider()
sec("Dual-Channel CNN Processing Pipeline")
st.markdown(f"""
<div style="padding:10px 14px;background:{ACCEPT}18;border:1px solid {ACCEPT};
            border-radius:6px;margin-bottom:14px;
            font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{ACCEPT};">
  <b>CNN Status: Trained and Active.</b> The Dual-Channel CNN was trained on the
  NEU Metal Surface Defects dataset (1,800 images, 3 classes) and achieves
  <b>93.70% test accuracy</b>. One camera provides the source image for both the
  grayscale channel (Channel 1) and the Sobel edge-detection channel (Channel 2).
  STM32 motor control is not yet integrated — rotate the component manually between captures.
</div>
""", unsafe_allow_html=True)
DualChannelCNNVisualizer().display_cnn_pipeline_visualization()
