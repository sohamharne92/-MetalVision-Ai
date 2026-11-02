"""
METALVISION AI — Camera Utility
Reliable frame capture that auto-detects the best backend per camera index.
Works for DSHOW cameras (most USB) and MSMF cameras (some built-in / virtual).
"""

import os
import cv2
import numpy as np
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

# Backend preference order per camera index
# Key: camera index, Value: list of backends to try in order
_BACKEND_MAP = {
    0: [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY],
    1: [cv2.CAP_MSMF,  cv2.CAP_DSHOW, cv2.CAP_ANY],
    2: [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY],
    3: [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY],
    4: [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY],
}
_DEFAULT_BACKENDS = [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]


def open_camera(cam_index: int, width: int = 1280, height: int = 720):
    """
    Open a camera, trying multiple backends until one delivers a real frame.
    Returns (cap, backend_name) on success, or (None, '') on failure.
    """
    backends = _BACKEND_MAP.get(cam_index, _DEFAULT_BACKENDS)

    for backend in backends:
        try:
            cap = cv2.VideoCapture(cam_index, backend)
            if not cap.isOpened():
                cap.release()
                continue

            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # Flush 4 stale frames
            for _ in range(4):
                cap.grab()

            # Verify actual frame
            ret, frame = cap.read()
            if ret and frame is not None:
                backend_name = {
                    cv2.CAP_DSHOW: "DSHOW",
                    cv2.CAP_MSMF:  "MSMF",
                    cv2.CAP_ANY:   "AUTO",
                }.get(backend, str(backend))
                return cap, backend_name

            cap.release()
        except Exception:
            try: cap.release()
            except Exception: pass

    return None, ""


def capture_frame(cam_index: int, width: int = 1280, height: int = 720):
    """
    Open camera, capture one frame, close.
    Returns (success, bgr_frame, actual_w, actual_h, backend_used, error_msg)
    """
    cap, backend = open_camera(cam_index, width, height)
    if cap is None:
        return False, None, 0, 0, "", f"No working backend found for camera {cam_index}"

    try:
        ret, frame = cap.read()
        aw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        ah = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()
        if ret and frame is not None:
            return True, frame, aw, ah, backend, ""
        return False, None, 0, 0, backend, "read() returned no frame"
    except Exception as e:
        try: cap.release()
        except Exception: pass
        return False, None, 0, 0, backend, str(e)


def image_quality(bgr: np.ndarray) -> dict:
    """Compute blur score, brightness, and quality flags."""
    if bgr is None:
        return {"blur_score":0, "brightness":0, "flags":["no frame"], "quality_ok":False}
    gray       = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(gray.mean())
    flags = []
    if blur_score < 20:  flags.append("blurry")
    if brightness < 30:  flags.append("too dark")
    if brightness > 230: flags.append("overexposed")
    return {
        "blur_score": round(blur_score, 1),
        "brightness": round(brightness, 1),
        "flags":      flags,
        "quality_ok": len(flags) == 0,
    }


def bgr_to_pil(bgr: np.ndarray):
    """Convert BGR numpy array to PIL Image."""
    from PIL import Image
    return Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
