"""
METALVISION AI — Page 11: Camera Test & Live Feed
Switch between front/back cameras, select resolution,
capture frames, check image quality, preview dual-channel CNN input.
"""
import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

import cv2
import numpy as np
from PIL import Image
from datetime import datetime
from pathlib import Path
import streamlit as st

from config import (
    CHART_COLOR_NORMAL, CHART_COLOR_CRACK,
    CHART_COLOR_DENT, CHART_COLOR_SCRATCH,
)

# ── Palette ───────────────────────────────────────────────────────────────────
BG    = "#12100a"; BG2   = "#1c1710"; PANEL  = "#241d12"; PANEL2 = "#2c2416"
BORDER = "#4a3018"; BORDER2 = "#2e1e0c"
CL    = "#e8a85a"; CD    = "#8a5520"; AMBER  = "#f5a623"
TEXT  = "#f5ead8"; TEXT2 = "#c8a878"; TEXT3  = "#8a6840"
ACCEPT = "#34d399"; REJECT = "#fb7185"; WARN = "#fbbf24"

CAPTURE_DIR = Path("data/captures")
CAPTURE_DIR.mkdir(parents=True, exist_ok=True)

# ── Camera map — front/back labels based on scan results ─────────────────────
# Camera 0 = built-in front (laptop webcam)
# Camera 2 = secondary (could be front of phone via DroidCam)
# Camera 3 = DroidCam virtual (phone camera — set back/front in DroidCam app)
# Camera 4 = additional device
CAMERA_MAP = {
    "Front Camera  (index 0 — built-in / laptop)": 0,
    "Back Camera   (index 2 — external / USB)":    2,
    "Phone Camera  (index 3 — DroidCam)":          3,
    "Extra Device  (index 4)":                     4,
}

RESOLUTION_MAP = {
    "640 × 480   (SD  — fast)":             (640,  480),
    "1280 × 720  (HD  — recommended)":      (1280, 720),
    "1920 × 1080 (Full HD — high quality)": (1920, 1080),
}

def sec(label):
    st.markdown(f'<div class="v-section">{label}</div>', unsafe_allow_html=True)

# ── Core capture function ─────────────────────────────────────────────────────
def capture_frame(cam_index: int, width: int, height: int):
    """
    Open camera at requested resolution, flush buffer, grab fresh frame.
    Returns (success, bgr_frame, actual_width, actual_height, error_msg)
    """
    try:
        cap = cv2.VideoCapture(cam_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(cam_index)   # fallback backend
        if not cap.isOpened():
            return False, None, 0, 0, f"Cannot open camera index {cam_index}"

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Flush stale buffer frames
        for _ in range(4):
            cap.grab()

        ret, frame = cap.read()
        aw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ah = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if not ret or frame is None:
            return False, None, 0, 0, "Camera opened but returned no frame"

        return True, frame, aw, ah, ""
    except Exception as e:
        return False, None, 0, 0, str(e)

# ── Image quality check ───────────────────────────────────────────────────────
def quality_check(bgr: np.ndarray) -> dict:
    gray       = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    flags = []
    if blur_score  < 20:  flags.append("blurry")
    if brightness  < 30:  flags.append("too dark")
    if brightness  > 230: flags.append("overexposed")
    return {
        "blur_score": round(blur_score, 1),
        "brightness": round(brightness, 1),
        "flags":      flags,
        "ok":         len(flags) == 0,
    }

# ── Dual-channel builder ──────────────────────────────────────────────────────
def dual_channel(bgr: np.ndarray):
    gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    g200  = cv2.resize(gray, (200, 200))
    gx    = cv2.Sobel(g200, cv2.CV_32F, 1, 0, ksize=3)
    gy    = cv2.Sobel(g200, cv2.CV_32F, 0, 1, ksize=3)
    mag   = cv2.magnitude(gx, gy)
    mag   = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return Image.fromarray(g200), Image.fromarray(mag)

def to_pil(bgr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))

# ══════════════════════════════════════════════════════════════════
#  PAGE
# ══════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="v-hero">
  <span class="rivet tl">●</span><span class="rivet tr">●</span>
  <span class="rivet bl">●</span><span class="rivet br">●</span>
  <div class="v-hero-title">Camera Test &amp; Live Feed</div>
  <div class="v-hero-sub">
    Switch camera · Change resolution · Capture · Quality check · Dual-channel preview
  </div>
  <div class="v-hero-meta">
    <span class="v-hero-pill">FRONT / BACK SWITCH</span>
    <span class="v-hero-pill">SD / HD / FULL HD</span>
    <span class="v-hero-pill">QUALITY CHECK</span>
    <span class="v-hero-pill">DUAL-CHANNEL PREVIEW</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Controls ──────────────────────────────────────────────────────────────────
sec("Camera & Resolution")

ctrl1, ctrl2 = st.columns(2)

with ctrl1:
    cam_label = st.radio(
        "Select Camera",
        options=list(CAMERA_MAP.keys()),
        index=0,
        key="cam_label_radio",
    )
    cam_index = CAMERA_MAP[cam_label]

with ctrl2:
    res_label = st.radio(
        "Resolution",
        options=list(RESOLUTION_MAP.keys()),
        index=1,   # default HD 1280×720
        key="res_label_radio",
    )
    req_w, req_h = RESOLUTION_MAP[res_label]

# Current selection info bar
st.markdown(f"""
<div style="background:{PANEL};border:1px solid {BORDER2};border-radius:6px;
            padding:10px 16px;margin-top:4px;
            display:flex;gap:32px;flex-wrap:wrap;
            font-family:'JetBrains Mono',monospace;font-size:0.82rem;">
  <div><span style="color:{TEXT3};">Camera index</span>
       <span style="color:{AMBER};margin-left:8px;">{cam_index}</span></div>
  <div><span style="color:{TEXT3};">Requested res</span>
       <span style="color:{CL};margin-left:8px;">{req_w} × {req_h}</span></div>
  <div><span style="color:{TEXT3};">Captures saved to</span>
       <span style="color:{TEXT2};margin-left:8px;">data/captures/</span></div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Capture buttons ───────────────────────────────────────────────────────────
sec("Capture Controls")
b1, b2, b3 = st.columns(3)
with b1:
    do_capture  = st.button("CAPTURE FRAME", type="primary", use_container_width=True)
with b2:
    do_save     = st.button("SAVE LAST FRAME", use_container_width=True)
with b3:
    auto_refresh = st.toggle("Auto-refresh (2s live view)", value=False)

# ── Trigger capture ───────────────────────────────────────────────────────────
if do_capture or auto_refresh:
    with st.spinner(f"Capturing from camera {cam_index} at {req_w}×{req_h}..."):
        ok, frame, aw, ah, err = capture_frame(cam_index, req_w, req_h)

    if ok:
        st.session_state["cam_frame"]    = frame
        st.session_state["cam_actual_w"] = aw
        st.session_state["cam_actual_h"] = ah
        st.session_state["cam_ts"]       = datetime.now()
        st.session_state["cam_err"]      = ""
    else:
        st.session_state["cam_err"] = err

# ── Error display ─────────────────────────────────────────────────────────────
if st.session_state.get("cam_err"):
    st.markdown(f"""
    <div style="padding:14px 18px;background:{REJECT}18;border:1px solid {REJECT};
                border-radius:8px;margin:8px 0;
                font-family:'Space Grotesk',sans-serif;font-size:0.9rem;color:{REJECT};">
      <b>Capture failed:</b> {st.session_state['cam_err']}<br><br>
      <b>Fix:</b>
      <ul style="margin:6px 0 0 18px;color:{TEXT2};">
        <li>Make sure no other app (Teams, Zoom) is using this camera</li>
        <li>Try a different camera index from the selector above</li>
        <li>Reconnect the camera and restart the app</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

# ── Display frame ─────────────────────────────────────────────────────────────
frame = st.session_state.get("cam_frame")
ts    = st.session_state.get("cam_ts")
aw    = st.session_state.get("cam_actual_w", req_w)
ah    = st.session_state.get("cam_actual_h", req_h)

if frame is not None:
    ts_str = ts.strftime("%Y-%m-%d  %H:%M:%S") if ts else ""

    sec("Live Preview")
    st.image(
        to_pil(frame),
        caption=f"Camera {cam_index} — {aw}×{ah} — {ts_str}",
        use_container_width=True,
    )

    # ── Quality metrics ───────────────────────────────────────────────────────
    qm = quality_check(frame)
    qc = ACCEPT if qm["ok"] else REJECT

    st.markdown(f"""
    <div style="background:{qc}12;border:1px solid {qc};border-radius:8px;
                padding:14px 20px;margin:10px 0;
                display:flex;flex-wrap:wrap;gap:28px;align-items:center;">
      <div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:0.68rem;
                    font-weight:700;letter-spacing:0.18em;text-transform:uppercase;
                    color:{TEXT3};margin-bottom:4px;">Image Quality</div>
        <div style="font-family:'Bebas Neue',cursive;font-size:1.5rem;color:{qc};">
          {'GOOD — ready for inspection' if qm['ok'] else 'ISSUES — retake recommended'}
        </div>
        {f'<div style="font-family:JetBrains Mono,monospace;font-size:0.8rem;color:{REJECT};">Issues: {", ".join(qm["flags"])}</div>'
         if qm["flags"] else ""}
      </div>
      <div style="display:flex;gap:28px;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">
        <div>
          <div style="color:{TEXT3};font-size:0.62rem;text-transform:uppercase;margin-bottom:2px;">
            Blur (Laplacian)</div>
          <div style="color:{'#34d399' if qm['blur_score']>=20 else '#fb7185'};">
            {qm['blur_score']}  {'OK' if qm['blur_score']>=20 else 'LOW'}</div>
        </div>
        <div>
          <div style="color:{TEXT3};font-size:0.62rem;text-transform:uppercase;margin-bottom:2px;">
            Brightness</div>
          <div style="color:{'#34d399' if 30<=qm['brightness']<=230 else '#fb7185'};">
            {qm['brightness']} / 255</div>
        </div>
        <div>
          <div style="color:{TEXT3};font-size:0.62rem;text-transform:uppercase;margin-bottom:2px;">
            Actual Size</div>
          <div style="color:{CL};">{aw} × {ah}</div>
        </div>
        <div>
          <div style="color:{TEXT3};font-size:0.62rem;text-transform:uppercase;margin-bottom:2px;">
            Requested</div>
          <div style="color:{TEXT2};">{req_w} × {req_h}</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Dual-channel preview ──────────────────────────────────────────────────
    st.divider()
    sec("Dual-Channel CNN Input Preview")
    st.markdown(f"""
    <div style="padding:10px 14px;background:{WARN}18;border:1px solid {WARN};
                border-radius:6px;margin-bottom:14px;
                font-family:'Space Grotesk',sans-serif;font-size:0.88rem;color:{WARN};">
      Same frame — two CNN inputs. Grayscale preserves texture.
      Sobel edge map highlights boundaries and defect lines.
      Both are resized to 200×200 before entering the CNN.
    </div>
    """, unsafe_allow_html=True)

    gray_pil, edge_pil = dual_channel(frame)
    dc1, dc2, dc3 = st.columns(3)
    for col, img, label in [
        (dc1, to_pil(frame), "Original (RGB)"),
        (dc2, gray_pil,      "Channel 1 — Grayscale  200×200"),
        (dc3, edge_pil,      "Channel 2 — Sobel Edge  200×200"),
    ]:
        col.markdown(
            f"<p style='font-family:Space Grotesk,sans-serif;font-size:0.72rem;"
            f"letter-spacing:0.14em;color:{CD};text-transform:uppercase;"
            f"margin-bottom:4px;'>{label}</p>",
            unsafe_allow_html=True,
        )
        col.image(img, use_container_width=True)

else:
    # Empty state
    st.markdown(f"""
    <div class="v-plate" style="text-align:center;padding:64px 20px;margin-top:12px;">
      <div style="font-family:'Bebas Neue',cursive;font-size:2.2rem;
                  color:{TEXT3};margin-bottom:10px;">No Frame Captured</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.88rem;color:{TEXT3};">
        Select camera and resolution above, then press CAPTURE FRAME
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Save ──────────────────────────────────────────────────────────────────────
if do_save:
    if frame is None:
        st.warning("Capture a frame first.")
    else:
        ts_file = datetime.now().strftime("%Y%m%d_%H%M%S")
        fpath   = CAPTURE_DIR / f"cam{cam_index}_{req_w}x{req_h}_{ts_file}.jpg"
        cv2.imwrite(str(fpath), frame)
        st.success(f"Saved: {fpath}")

st.divider()

# ── Gallery ───────────────────────────────────────────────────────────────────
sec("Saved Captures")
saved = sorted(CAPTURE_DIR.glob("*.jpg"), reverse=True)

if saved:
    total = len(saved)
    show  = saved[:12]
    st.markdown(
        f"<p style='font-family:JetBrains Mono,monospace;font-size:0.78rem;"
        f"color:{TEXT3};'>{total} saved — showing last {len(show)}</p>",
        unsafe_allow_html=True,
    )
    with open(show[0], "rb") as f:
        st.download_button(
            "Download Latest Capture",
            f.read(),
            file_name=show[0].name,
            mime="image/jpeg",
        )
    for i in range(0, len(show), 4):
        cols = st.columns(4)
        for col, p in zip(cols, show[i:i+4]):
            col.image(Image.open(p), caption=p.stem[-16:], use_container_width=True)
else:
    st.markdown(f"""
    <div style="padding:20px;background:{BG2};border:1px solid {BORDER2};
                border-radius:6px;text-align:center;
                font-family:'JetBrains Mono',monospace;font-size:0.82rem;color:{TEXT3};">
      No saved captures yet. Click SAVE LAST FRAME after capturing.
    </div>
    """, unsafe_allow_html=True)

# ── Auto-refresh ──────────────────────────────────────────────────────────────
if auto_refresh:
    import time
    time.sleep(2)
    st.rerun()
