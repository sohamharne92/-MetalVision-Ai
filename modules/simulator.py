"""
METALVISION AI — Inspection Simulator
Simulates the 360° stepper-motor-driven inspection workflow.
In the real system: motor rotates platform → STM32 confirms stop →
camera captures frame → CNN classifies image.
Currently: all results are synthetic demonstration data.
"""

import numpy as np
import uuid
from datetime import datetime

from config import (
    INSPECTION_POSITIONS,
    DEFECT_CLASSES,
    CONFIDENCE_NORMAL_RANGE,
    CONFIDENCE_DEFECT_RANGE,
    CONFIDENCE_REVIEW_THRESHOLD,
    DEMO_SCENARIOS,
    get_final_decision,
    simulate_image_quality,
    DECISION_ACCEPT, DECISION_REJECT, DECISION_REVIEW,
)


class MetalPartSimulator:
    """
    Simulates the inspection of a metal component at configurable positions.
    Step-driven mode (inspect_one + finalise) supports animated scanning.
    """

    def __init__(self):
        self.inspection_id      = str(uuid.uuid4())[:8].upper()
        self.inspection_results = {}
        self.overall_confidence = 0.0
        self.final_decision     = None
        self.defect_count       = 0
        self.part_id            = ""
        self.quality_flags      = {}   # angle → image quality dict

    # ── Full run (non-animated) ───────────────────────────────────────────────
    def run_inspection(self, scenario_name: str = "Scenario 5: Random Test") -> dict:
        """Run all positions at once and return the full summary."""
        scenario = DEMO_SCENARIOS.get(scenario_name, DEMO_SCENARIOS["Scenario 5: Random Test"])
        for position in INSPECTION_POSITIONS:
            self.inspection_results[position] = self._inspect_position(position, scenario)
            self.quality_flags[position]      = simulate_image_quality(
                position, self.inspection_results[position]["class"]
            )
        self._calculate_overall_metrics()
        self.final_decision = get_final_decision(self.inspection_results)
        return self.get_inspection_summary()

    # ── Step-driven (animated) ────────────────────────────────────────────────
    def inspect_one(self, angle: int, scenario_name: str = "Scenario 5: Random Test") -> dict:
        """
        Inspect a single position. Call this inside the animation loop.
        Returns the result dict for this angle.
        """
        scenario = DEMO_SCENARIOS.get(scenario_name, DEMO_SCENARIOS["Scenario 5: Random Test"])
        result   = self._inspect_position(angle, scenario)
        self.inspection_results[angle] = result
        self.quality_flags[angle]      = simulate_image_quality(angle, result["class"])
        return result

    def finalise(self) -> dict:
        """
        Call after all angles have been inspected via inspect_one().
        Computes overall metrics and final decision, then returns the full summary.
        """
        self._calculate_overall_metrics()
        self.final_decision = get_final_decision(self.inspection_results)
        return self.get_inspection_summary()

    # ── Internal helpers ──────────────────────────────────────────────────────
    def _inspect_position(self, angle: int, scenario: dict) -> dict:
        """
        Simulate inspection at one angle using the selected scenario.
        Real system: STM32 stops motor here, camera captures frame,
        Dual-Channel CNN classifies the image.
        """
        defects = scenario["defects"]

        if isinstance(defects, dict) and angle in defects:
            defect_class, confidence = defects[angle]
        elif defects == "random":
            defect_class, confidence = self._generate_random_defect()
        else:
            defect_class = "Normal"
            confidence   = float(np.random.uniform(*CONFIDENCE_NORMAL_RANGE))

        return {
            "angle":      angle,
            "class":      defect_class,
            "confidence": round(float(confidence), 4),
            "timestamp":  datetime.now().isoformat(),
            "source":     "simulation",   # "real_cnn" when model is integrated
        }

    def _generate_random_defect(self) -> tuple:
        """
        Random defect with realistic probability distribution.
        70% Normal, 10% each Crack / Dent / Scratch.
        """
        rand = np.random.random()
        if rand < 0.70:
            return "Normal",  float(np.random.uniform(*CONFIDENCE_NORMAL_RANGE))
        elif rand < 0.80:
            return "Crack",   float(np.random.uniform(*CONFIDENCE_DEFECT_RANGE))
        elif rand < 0.90:
            return "Dent",    float(np.random.uniform(*CONFIDENCE_DEFECT_RANGE))
        else:
            return "Scratch", float(np.random.uniform(*CONFIDENCE_DEFECT_RANGE))

    def _calculate_overall_metrics(self) -> None:
        if not self.inspection_results:
            self.overall_confidence = 0.0
            self.defect_count       = 0
            return
        total_conf   = sum(r["confidence"] for r in self.inspection_results.values())
        defect_count = sum(1 for r in self.inspection_results.values()
                           if r["class"] != "Normal")
        self.overall_confidence = total_conf / len(self.inspection_results)
        self.defect_count       = defect_count

    # ── Public accessors ──────────────────────────────────────────────────────
    def get_inspection_summary(self) -> dict:
        quality_issues = sum(1 for q in self.quality_flags.values() if not q["quality_ok"])
        return {
            "inspection_id":      self.inspection_id,
            "part_id":            self.part_id,
            "timestamp":          datetime.now().isoformat(),
            "positions":          self.inspection_results,
            "quality_flags":      self.quality_flags,
            "overall_confidence": round(self.overall_confidence, 4),
            "defect_count":       self.defect_count,
            "quality_issues":     quality_issues,
            "final_decision":     self.final_decision,
            "total_positions":    len(INSPECTION_POSITIONS),
        }

    def get_position_result(self, angle: int) -> dict:
        return self.inspection_results.get(angle, {})

    def get_defect_summary(self) -> dict:
        summary = {k: 0 for k in DEFECT_CLASSES}
        for r in self.inspection_results.values():
            summary[r["class"]] = summary.get(r["class"], 0) + 1
        return summary

    def reset(self) -> None:
        self.inspection_id      = str(uuid.uuid4())[:8].upper()
        self.inspection_results = {}
        self.quality_flags      = {}
        self.overall_confidence = 0.0
        self.final_decision     = None
        self.defect_count       = 0
        self.part_id            = ""


# ── Mock image helpers (used by CNN pipeline visualiser) ─────────────────────
def create_mock_image_for_position(angle: int, defect_class: str):
    """Return a 200×200 NumPy uint8 grayscale array with a synthetic defect pattern."""
    image = np.random.randint(100, 200, (200, 200), dtype=np.uint8)
    if defect_class == "Crack":
        image[95:105, :] = 50
    elif defect_class == "Dent":
        y, x = np.ogrid[:200, :200]
        image[(x - 100)**2 + (y - 100)**2 <= 30**2] //= 2
    elif defect_class == "Scratch":
        for i in range(0, 200, 5):
            image[i:i+2, i:min(i+100, 200)] = 80
    return image


def create_edge_image_from_original(image):
    """Return a Sobel-style edge image from a NumPy grayscale array."""
    gx = np.gradient(image.astype(float), axis=0)
    gy = np.gradient(image.astype(float), axis=1)
    mag = np.sqrt(gx**2 + gy**2)
    if mag.max() > 0:
        return (mag / mag.max() * 255).astype(np.uint8)
    return np.zeros_like(image, dtype=np.uint8)
