"""Benchmark each step of the inspection pipeline."""
import os, sys, time, cv2, numpy as np
sys.path.insert(0, ".")
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
os.environ["PYTHONUTF8"] = "1"

POSITIONS = 12

print("=" * 55)
print("  MetalVision AI — Inspection Pipeline Benchmark")
print("=" * 55)

# ── Find working camera ───────────────────────────────────────────────────────
cap = None
cam_index = 0
for idx in [0, 1, 2, 3, 4]:
    for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
        try:
            c = cv2.VideoCapture(idx, backend)
            if not c.isOpened(): c.release(); continue
            c.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
            c.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            for _ in range(4): c.grab()
            ret, fr = c.read()
            if ret and fr is not None:
                cap = c
                cam_index = idx
                frame = fr
                print(f"\nUsing Camera {idx} [{backend}]  {fr.shape[1]}x{fr.shape[0]}")
                break
        except Exception:
            pass
    if cap is not None:
        break

if cap is None or frame is None:
    print("ERROR: No camera found. Using synthetic frame.")
    frame = np.random.randint(80, 200, (720, 1280, 3), dtype=np.uint8)

# ── 1. Camera open time (already measured above) ─────────────────────────────
t0 = time.time()
for _ in range(4): cap.grab()
ret, _ = cap.read()
t_open = (time.time() - t0) * 1000
print(f"\n[1] Camera flush + 1 frame    : {t_open:.0f} ms  (one-time cost)")

# ── 2. Per-frame capture (camera open) ───────────────────────────────────────
times_cap = []
for _ in range(POSITIONS):
    t0 = time.time()
    ret, fr = cap.read()
    if ret and fr is not None:
        frame = fr
    times_cap.append((time.time() - t0) * 1000)
cap.release()
avg_cap = sum(times_cap) / len(times_cap)
print(f"[2] Per-frame capture avg     : {avg_cap:.0f} ms  (min={min(times_cap):.0f} max={max(times_cap):.0f})")

# ── 3. JPEG save ──────────────────────────────────────────────────────────────
os.makedirs("data/captures/bench_test", exist_ok=True)
times_save = []
for i in range(POSITIONS):
    fpath = f"data/captures/bench_test/pos_{i*30:03d}deg.jpg"
    t0 = time.time()
    cv2.imwrite(fpath, frame, [cv2.IMWRITE_JPEG_QUALITY, 82])
    times_save.append((time.time() - t0) * 1000)
avg_save = sum(times_save) / len(times_save)
print(f"[3] JPEG save per frame avg   : {avg_save:.0f} ms")
import shutil; shutil.rmtree("data/captures/bench_test", ignore_errors=True)

# ── 4. Quality check ─────────────────────────────────────────────────────────
times_qc = []
for _ in range(POSITIONS):
    t0 = time.time()
    g  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bl = float(cv2.Laplacian(g, cv2.CV_64F).var())
    br = float(g.mean())
    times_qc.append((time.time() - t0) * 1000)
avg_qc = sum(times_qc) / len(times_qc)
print(f"[4] Quality check per frame   : {avg_qc:.1f} ms")

# ── 5. Thumbnail + base64 ─────────────────────────────────────────────────────
from PIL import Image
import base64, io as _io
times_b64 = []
for _ in range(POSITIONS):
    t0 = time.time()
    small = cv2.resize(frame, (200, 150))
    pil   = Image.fromarray(cv2.cvtColor(small, cv2.COLOR_BGR2RGB))
    buf   = _io.BytesIO()
    pil.save(buf, format="JPEG", quality=70)
    base64.b64encode(buf.getvalue())
    times_b64.append((time.time() - t0) * 1000)
avg_b64 = sum(times_b64) / len(times_b64)
print(f"[5] Thumb+base64 per frame    : {avg_b64:.1f} ms")

# ── 6. CNN inference ──────────────────────────────────────────────────────────
t_cnn = 40.0   # default estimate
try:
    import cnn.dataset as ds
    ds.CLASS_NAMES  = ["Crack","Dent","Scratch"]
    ds.CLASS_TO_IDX = {c:i for i,c in enumerate(ds.CLASS_NAMES)}
    from cnn.inference import MetalVisionInference
    engine = MetalVisionInference()
    if engine.is_ready:
        for _ in range(3): engine.predict_from_array(frame)   # warmup
        t0 = time.time()
        for _ in range(POSITIONS): engine.predict_from_array(frame)
        t_cnn = (time.time() - t0) * 1000 / POSITIONS
        print(f"[6] CNN inference per frame   : {t_cnn:.0f} ms  (real model)")
    else:
        print(f"[6] CNN inference             : ~{t_cnn:.0f} ms  (estimated, sim mode)")
except Exception as e:
    print(f"[6] CNN inference             : ~{t_cnn:.0f} ms  (estimated)")

# ── 7. Streamlit HTML update overhead ─────────────────────────────────────────
t_html = 30    # ~30ms per st.empty().markdown() call (from profiling)
print(f"[7] Streamlit update per pos  : ~{t_html} ms  (estimated)")

# ── Summary ───────────────────────────────────────────────────────────────────
per_pos   = avg_cap + avg_save + avg_qc + avg_b64 + t_cnn + t_html
total_est = t_open + per_pos * POSITIONS

print()
print("=" * 55)
print("  TIME BUDGET ANALYSIS  (target: 45-50 s)")
print("=" * 55)
print(f"  Camera open (once)      : {t_open:.0f} ms")
print(f"  Per-position breakdown  :")
print(f"    Capture               : {avg_cap:.0f} ms")
print(f"    JPEG save             : {avg_save:.0f} ms")
print(f"    Quality check         : {avg_qc:.1f} ms")
print(f"    Thumbnail + base64    : {avg_b64:.1f} ms")
print(f"    CNN inference         : {t_cnn:.0f} ms")
print(f"    Streamlit render      : {t_html} ms")
print(f"    ─────────────────────")
print(f"    Per-position total    : {per_pos:.0f} ms  ({per_pos/1000:.2f} s)")
print()
print(f"  12 positions total est  : {total_est/1000:.1f} s")
print(f"  Target                  : 45-50 s")

needed_per_pos = (47000 - t_open) / POSITIONS
needed_delay   = max(0, needed_per_pos - per_pos)
print(f"  Needed per-position     : {needed_per_pos:.0f} ms")
print(f"  Required sleep/delay    : {needed_delay:.0f} ms  ({needed_delay/1000:.2f} s)")
print("=" * 55)
