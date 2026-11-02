"""
METALVISION AI — CNN Inference Engine
Loads the trained model and classifies a single captured image.
Used by the dashboard when real camera integration is active.

USAGE:
  from cnn.inference import MetalVisionInference
  engine = MetalVisionInference()
  result = engine.predict_from_path("path/to/image.jpg")
  # → {"class": "Crack", "confidence": 0.934, "all_probs": {...}}

  # Or from a numpy array (e.g. from OpenCV frame):
  result = engine.predict_from_array(frame_bgr)
"""

import json
import numpy as np
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image

ROOT = Path(__file__).parent.parent


class MetalVisionInference:
    """
    Loads a trained DualChannelCNN and runs inference on captured images.
    Falls back gracefully if model weights are not yet available.
    """

    MODEL_PATH = ROOT / "models" / "dual_channel_cnn.pth"
    INFO_PATH  = ROOT / "models" / "model_info.json"
    IMG_SIZE   = 200

    CLASS_NAMES = ["Normal", "Crack", "Dent", "Scratch"]

    def __init__(self):
        self.device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model     = None
        self.model_info = {}
        self._load()

    def _load(self) -> None:
        """Load model weights.

        Class names and count are read from models/model_info.json when it is
        available and readable, so inference stays consistent with whatever
        train.py produced. Falls back to the 3-class default (Crack, Dent,
        Scratch) when model_info.json is missing or unreadable.
        """
        if not self.MODEL_PATH.exists():
            return

        try:
            # ── Resolve class names + count from model_info.json (fallback 3) ──
            class_names = ["Crack", "Dent", "Scratch"]   # 3-class default
            if self.INFO_PATH.exists():
                try:
                    with open(self.INFO_PATH) as f:
                        self.model_info = json.load(f)
                    info_classes = self.model_info.get("class_names")
                    if info_classes:
                        class_names = list(info_classes)
                except (json.JSONDecodeError, OSError):
                    # Unreadable info file — keep the 3-class default
                    self.model_info = {}
            num_classes      = len(class_names)
            self.CLASS_NAMES = class_names

            from cnn.model import build_model
            self.model = build_model(num_classes=num_classes).to(self.device)
            self.model.load_state_dict(
                torch.load(self.MODEL_PATH, map_location=self.device,
                           weights_only=True)
            )
            self.model.eval()
        except Exception as e:
            print(f"[MetalVisionInference] Could not load model: {e}")
            self.model = None

    @property
    def is_ready(self) -> bool:
        """True if model weights are loaded and inference is available."""
        return self.model is not None

    def _preprocess(self, gray_arr: np.ndarray):
        """
        Convert a (H, W) uint8 grayscale array into
        (gray_tensor, edge_tensor) ready for the model.
        """
        from cnn.dataset import sobel_edge

        # Resize
        img  = Image.fromarray(gray_arr).resize(
            (self.IMG_SIZE, self.IMG_SIZE), Image.BILINEAR)
        arr  = np.array(img, dtype=np.uint8)

        gray = arr.astype(np.float32) / 255.0
        edge = sobel_edge(arr)

        gray_t = torch.tensor(gray).unsqueeze(0).unsqueeze(0).to(self.device)
        edge_t = torch.tensor(edge).unsqueeze(0).unsqueeze(0).to(self.device)
        return gray_t, edge_t

    def predict_from_array(self, image_array: np.ndarray) -> dict:
        """
        Classify a captured frame.

        Args:
            image_array: np.ndarray — BGR (from OpenCV) or grayscale (H, W)

        Returns:
            dict with keys:
              class       — predicted class name
              confidence  — confidence score 0–1
              all_probs   — {class_name: probability} for all 4 classes
              source      — "real_cnn" or "not_available"
        """
        if not self.is_ready:
            return {
                "class":      "Unknown",
                "confidence": 0.0,
                "all_probs":  {c: 0.0 for c in self.CLASS_NAMES},
                "source":     "not_available",
                "error":      "Model weights not found. Run  python cnn/train.py  first.",
            }

        # Convert BGR→Gray if needed
        if image_array.ndim == 3 and image_array.shape[2] == 3:
            gray_arr = np.dot(image_array[..., ::-1],
                              [0.2989, 0.5870, 0.1140]).astype(np.uint8)
        elif image_array.ndim == 2:
            gray_arr = image_array.astype(np.uint8)
        else:
            gray_arr = image_array[:, :, 0].astype(np.uint8)

        try:
            gray_t, edge_t = self._preprocess(gray_arr)
            with torch.no_grad():
                logits = self.model(gray_t, edge_t)
                probs  = F.softmax(logits, dim=1).squeeze().cpu().numpy()

            pred_idx   = int(probs.argmax())
            class_name = self.CLASS_NAMES[pred_idx]
            confidence = float(probs[pred_idx])
            all_probs  = {c: round(float(probs[i]), 4)
                          for i, c in enumerate(self.CLASS_NAMES)}

            return {
                "class":      class_name,
                "confidence": round(confidence, 4),
                "all_probs":  all_probs,
                "source":     "real_cnn",
            }
        except Exception as e:
            return {
                "class":      "Unknown",
                "confidence": 0.0,
                "all_probs":  {c: 0.0 for c in self.CLASS_NAMES},
                "source":     "error",
                "error":      str(e),
            }

    def predict_from_path(self, image_path: str) -> dict:
        """Classify an image file. Returns same dict as predict_from_array."""
        try:
            img      = Image.open(image_path).convert("L")
            arr      = np.array(img, dtype=np.uint8)
            return self.predict_from_array(arr)
        except Exception as e:
            return {
                "class":      "Unknown",
                "confidence": 0.0,
                "all_probs":  {c: 0.0 for c in self.CLASS_NAMES},
                "source":     "error",
                "error":      str(e),
            }

    def get_model_info(self) -> dict:
        """Return model metadata (accuracy, training date, etc.)."""
        if not self.MODEL_PATH.exists():
            return {"status": "not_trained",
                    "message": "Run python cnn/train.py to train the model."}
        if self.model_info:
            return self.model_info
        return {"status": "weights_found_no_info",
                "model_path": str(self.MODEL_PATH)}


# ── Convenience singleton ─────────────────────────────────────────────────────
# Import this anywhere in the dashboard:
#   from cnn.inference import engine
#   result = engine.predict_from_array(frame)
engine = MetalVisionInference()


if __name__ == "__main__":
    print(f"Model ready : {engine.is_ready}")
    print(f"Model info  : {json.dumps(engine.get_model_info(), indent=2)}")
