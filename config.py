"""
METALVISION AI - Configuration File
Project: AI-Based 360° Automated Metal Forming Defect Detection System Using Dual-Channel CNN
Maharashtra Institute of Technology — Department of Electronics and Computer Engineering
Major Project II (2026-27) — Aditya Deshpande, Soham Harne, Bhairu Salunke
Guide: Prof. R. N. Patil
"""

from datetime import datetime

# ==================== PROJECT METADATA ====================
PROJECT_TITLE    = "AI-Based 360° Automated Metal Forming Defect Detection System Using Dual-Channel CNN"
PRODUCT_NAME     = "METALVISION AI"
PRODUCT_SUBTITLE = "360° Automated Metal Forming Defect Detection"
VERSION          = "2.0 — Prototype"
CURRENT_YEAR     = datetime.now().year

# ==================== INTEGRATION STATUS ====================
INTEGRATION_STATUS = {
    "Dashboard & UI":         {"status": "Live",                           "integrated": True},
    "OpenCV Image Capture":   {"status": "Live — USB Webcam",             "integrated": True},
    "Dual-Channel CNN":       {"status": "Trained — 93.70% test accuracy", "integrated": True},
    "STM32 Motor Control":    {"status": "Hardware connected — firmware pending flash", "integrated": False},
    "DRV8825 Motor Driver":   {"status": "Hardware connected — CH340 on COM3",          "integrated": False},
}

# ==================== SIMULATION MODE MARKER ====================
SIMULATION_MODE    = "PROTOTYPE MODE"
SIMULATION_WARNING = (
    "Prototype mode: CNN classification is active (trained on NEU dataset, 93.70% accuracy). "
    "STM32 motor control is not yet integrated — platform rotation is manual."
)

# ==================== HARDWARE SPECIFICATION ====================
# Physical setup — NEMA 17 stepper motor, DRV8825 driver, STM32 controller
MOTOR_FULL_STEP_ANGLE   = 1.8          # degrees per full step (confirmed NEMA 17)
MOTOR_STEPS_PER_REV     = int(360 / MOTOR_FULL_STEP_ANGLE)   # 200 steps
MOTOR_MICROSTEPPING     = 1            # 1 = full step; 2/4/8/16 = microstepping
MOTOR_PULSES_PER_STEP   = MOTOR_MICROSTEPPING  # pulses needed per 1.8° move

# Camera
CAMERA_MODEL            = "USB Webcam / Built-in camera"
CAMERA_INTERFACE        = "OpenCV (auto-detects DSHOW / MSMF backend)"
CAMERA_SETTLE_DELAY_S   = 0.3

# Detected camera map — index → (label, best_backend)
# Update this map manually if connected devices change
CAMERA_DEVICES = {
    0: ("Camera 0 — Laptop built-in",    "DSHOW"),
    1: ("Camera 1 — External device",    "MSMF"),
    2: ("Camera 2 — External device",    "DSHOW"),
    3: ("Camera 3 — External / DroidCam","DSHOW"),
    4: ("Camera 4 — Additional device",  "DSHOW"),
}

# STM32
STM32_BAUD_RATE         = 9600         # CH340 board default; firmware uses 9600
STM32_PORT              = "COM3"       # default; configurable

# ==================== INSPECTION PARAMETERS ====================
# Default: 12 positions every 30°.
# Full resolution: 200 positions every 1.8° (MOTOR_STEPS_PER_REV).
# Change INSPECTION_ANGLE_STEP to 1.8 for full-resolution mode.
INSPECTION_ANGLE_STEP   = 30          # degrees between captures (configurable)
INSPECTION_POSITIONS    = [
    round(i * INSPECTION_ANGLE_STEP, 1)
    for i in range(int(360 / INSPECTION_ANGLE_STEP))
]
TOTAL_POSITIONS         = len(INSPECTION_POSITIONS)
INSPECTION_STEP_DELAY   = 0.8         # seconds per position during simulation

# ==================== DEFECT CLASSES ====================
# Phase 1 active classes (trained on NEU Metal Surface Defects dataset):
#   Crack, Dent, Scratch — 420 images each, 93.70% test accuracy
# Phase 2 planned (requires additional labelled data):
#   Fold, Wrinkle, Burr — to be added after data collection
DEFECT_CLASSES = {
    "Normal":  "Normal",
    "Crack":   "Crack",
    "Dent":    "Dent",
    "Scratch": "Scratch",
}

DEFECT_DESCRIPTIONS = {
    "Normal":  "No surface irregularity detected — component surface is intact",
    "Crack":   "Linear fracture or break in the metal surface (mapped from NEU: Crazing + Inclusion)",
    "Dent":    "Localised deformation or indentation from forming pressure (mapped from NEU: Patches + Pitted Surface)",
    "Scratch": "Surface mark or groove without depth penetration (mapped from NEU: Rolled-in Scale + Scratches)",
}

DEFECT_SEVERITY = {
    "Normal":  "None",
    "Crack":   "High — linear fracture indicates structural risk",
    "Dent":    "Medium — localised deformation from forming process",
    "Scratch": "Low — surface mark without depth penetration",
}

# CNN is trained on 3 classes (Normal class not in NEU dataset)
CNN_ACTIVE_CLASSES   = ["Normal", "Crack", "Dent", "Scratch"]
CNN_NUM_CLASSES      = 4
CNN_TEST_ACCURACY    = 0.9370   # 93.70% on 270 test images
CNN_FRAMEWORK        = "PyTorch 2.10"
CNN_PARAMETERS       = 3_098_947
CNN_INFERENCE_MS     = 38.6     # ms per image on CPU

# ==================== DECISION OUTCOMES ====================
# Three-outcome model (spec section 10):
#   ACCEPT  — all views usable, no defect meets rejection criteria
#   REJECT  — at least one defect meets validated rejection criteria
#   REVIEW  — images missing, quality poor, or result uncertain
DECISION_ACCEPT = "ACCEPT"
DECISION_REJECT = "REJECT"
DECISION_REVIEW = "REVIEW"

# Confidence threshold below which a result is flagged for REVIEW
CONFIDENCE_REVIEW_THRESHOLD = 0.70

# ==================== IMAGE QUALITY THRESHOLDS ====================
# Used by image quality simulation (and future real capture pipeline)
IQ_BLUR_THRESHOLD        = 20.0      # Laplacian variance — below = blurry
IQ_BRIGHTNESS_MIN        = 30        # 0–255 mean pixel value
IQ_BRIGHTNESS_MAX        = 230       # above = overexposed
IQ_QUALITY_FLAGS         = ["blur", "dark", "overexposed"]

# ==================== CONFIDENCE SCORE RANGES ====================
CONFIDENCE_NORMAL_RANGE  = (0.92, 0.99)
CONFIDENCE_DEFECT_RANGE  = (0.78, 0.95)

# ==================== COLOR SCHEME ====================
# Backgrounds
COLOR_BACKGROUND  = "#12100a"
COLOR_CARD_BG     = "#241d12"
COLOR_SURFACE     = "#2c2416"
COLOR_BORDER      = "#4a3018"

# Text
COLOR_TEXT_PRIMARY   = "#f5ead8"
COLOR_TEXT_SECONDARY = "#c8a878"

# Status
COLOR_ACCEPT    = "#34d399"
COLOR_REJECT    = "#fb7185"
COLOR_REVIEW    = "#fbbf24"
COLOR_WARNING   = "#f5a623"
COLOR_ACCENT    = "#e8a85a"
COLOR_SUCCESS   = "#34d399"
COLOR_DANGER    = "#fb7185"

# Position status
COLOR_PENDING    = "#4a3010"
COLOR_INSPECTING = "#f5a623"
COLOR_NORMAL     = "#34d399"
COLOR_DEFECT     = "#fb7185"

# Chart colors
CHART_COLOR_NORMAL  = "#34d399"
CHART_COLOR_CRACK   = "#fb7185"
CHART_COLOR_DENT    = "#f5a623"
CHART_COLOR_SCRATCH = "#c084fc"

# Backwards-compatible aliases
COLOR_CRACK   = CHART_COLOR_CRACK
COLOR_DENT    = CHART_COLOR_DENT
COLOR_SCRATCH = CHART_COLOR_SCRATCH

# ==================== DEMO SCENARIOS ====================
DEMO_SCENARIOS = {
    "Scenario 1: Normal Component": {
        "name":            "Scenario 1: Normal Component",
        "description":     "All 12 positions — no surface defects detected. Component ACCEPTED.",
        "defects":         {},
        "expected_result": "ACCEPT",
    },
    "Scenario 2: Scratch at 90°": {
        "name":            "Scenario 2: Scratch at 90°",
        "description":     "Surface scratch detected at 90° position. Component REJECTED.",
        "defects":         {90: ("Scratch", 0.92)},
        "expected_result": "REJECT",
    },
    "Scenario 3: Crack at 180°": {
        "name":            "Scenario 3: Crack at 180°",
        "description":     "Linear crack detected at 180° position. Component REJECTED.",
        "defects":         {180: ("Crack", 0.89)},
        "expected_result": "REJECT",
    },
    "Scenario 4: Multiple Defects": {
        "name":            "Scenario 4: Multiple Defects",
        "description":     "Dent at 60°, Scratch at 210°, Crack at 330°. Component REJECTED.",
        "defects":         {60: ("Dent", 0.85), 210: ("Scratch", 0.88), 330: ("Crack", 0.91)},
        "expected_result": "REJECT",
    },
    "Scenario 5: Random Test": {
        "name":            "Scenario 5: Random Test",
        "description":     "Random defect distribution — result varies each run.",
        "defects":         "random",
        "expected_result": "varies",
    },
}

# ==================== SYSTEM STATUS ====================
SYSTEM_STATUS = {
    "Dashboard":            {"status": "Online",                     "color": COLOR_ACCEPT},
    "OpenCV Image Capture": {"status": "Live — USB Webcam",         "color": COLOR_ACCEPT},
    "Dual-Channel CNN":     {"status": "Trained — 93.70% accuracy", "color": COLOR_ACCEPT},
    "STM32 Controller":     {"status": "Not Integrated",            "color": COLOR_WARNING},
    "DRV8825 Motor Driver": {"status": "Not Integrated",            "color": COLOR_WARNING},
    "LED Illumination":     {"status": "Manual Setup",              "color": COLOR_WARNING},
}

# ==================== DECISION LOGIC ====================
def get_final_decision(inspection_data: dict) -> str:
    """
    Determine ACCEPT, REJECT, or REVIEW from position-level results.

    ACCEPT  — all positions Normal, all confidences above threshold
    REJECT  — any position contains Crack, Dent, or Scratch
    REVIEW  — any position confidence below CONFIDENCE_REVIEW_THRESHOLD
    """
    has_low_confidence = False
    for angle, data in inspection_data.items():
        if not isinstance(data, dict):
            continue
        defect_class = data.get("class", "Normal")
        confidence   = data.get("confidence", 1.0)
        if defect_class != "Normal":
            return DECISION_REJECT
        if confidence < CONFIDENCE_REVIEW_THRESHOLD:
            has_low_confidence = True
    return DECISION_REVIEW if has_low_confidence else DECISION_ACCEPT


def get_defect_color(defect_class: str) -> str:
    return {
        "Normal":  CHART_COLOR_NORMAL,
        "Crack":   CHART_COLOR_CRACK,
        "Dent":    CHART_COLOR_DENT,
        "Scratch": CHART_COLOR_SCRATCH,
    }.get(defect_class, COLOR_TEXT_SECONDARY)


def get_status_color(status: str) -> str:
    return {
        "Normal":     COLOR_NORMAL,
        "Defect":     COLOR_DEFECT,
        "Pending":    COLOR_PENDING,
        "Inspecting": COLOR_INSPECTING,
        "ACCEPT":     COLOR_ACCEPT,
        "REJECT":     COLOR_REJECT,
        "REVIEW":     COLOR_REVIEW,
    }.get(status, COLOR_TEXT_SECONDARY)


def get_decision_color(decision: str) -> str:
    return {
        DECISION_ACCEPT: COLOR_ACCEPT,
        DECISION_REJECT: COLOR_REJECT,
        DECISION_REVIEW: COLOR_REVIEW,
    }.get(decision, COLOR_ACCENT)


def simulate_image_quality(angle: int, defect_class: str) -> dict:
    """
    Simulate per-position image quality metrics.
    In the real system these come from the captured frame.
    Returns blur_score, brightness, overexposed flag, and quality_ok.
    """
    import numpy as np
    rng = np.random.default_rng(angle + 42)

    # Most images are good; occasional quality issues
    blur_score  = float(rng.uniform(80, 300))
    brightness  = float(rng.uniform(60, 200))
    overexposed = bool(brightness > IQ_BRIGHTNESS_MAX)
    blurry      = bool(blur_score < IQ_BLUR_THRESHOLD)
    dark        = bool(brightness < IQ_BRIGHTNESS_MIN)

    flags       = []
    if blurry:      flags.append("blur")
    if dark:        flags.append("dark")
    if overexposed: flags.append("overexposed")

    return {
        "blur_score":   round(blur_score, 1),
        "brightness":   round(brightness, 1),
        "overexposed":  overexposed,
        "blurry":       blurry,
        "dark":         dark,
        "flags":        flags,
        "quality_ok":   len(flags) == 0,
    }
