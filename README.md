# METALVISION AI

**AI-Based 360° Automated Metal Forming Defect Detection System Using Dual-Channel CNN**

Maharashtra Institute of Technology — Department of Electronics & Computer Engineering
Major Project II (2026-27)

A **Streamlit** web dashboard that inspects a cylindrical metal component by
capturing images from **12 angular positions** (every 30°, full 360°), classifying
each surface image for defects with a trained **dual-channel CNN**, and producing a
final **ACCEPT / REJECT / REVIEW** verdict.

> **Prototype status.** The CNN defect classifier is real and trained (93.70% test
> accuracy on 3 classes). The motorised rotation hardware (STM32 + DRV8825 + NEMA 17
> stepper) is **not yet integrated** — the operator rotates the part by hand between
> captures.

---

## What the system does

- Captures one frame per position from a USB / built-in webcam via **OpenCV**
  (auto-detects DSHOW / MSMF backend), saving JPEGs under `data/captures/<inspection_id>/`.
- Classifies each frame with the trained **Dual-Channel CNN** — two parallel branches
  take a grayscale image and a Sobel **edge map**, fuse them, and classify the surface.
- Aggregates the 12 results into a final **ACCEPT / REJECT / REVIEW** decision
  (`config.get_final_decision`): any defect → REJECT; any sub-threshold confidence →
  REVIEW; otherwise ACCEPT.
- Renders a 360° Plotly ring of per-position statuses, a defect list, image-quality
  flags, and a final verdict, then optionally **saves to history**
  (`data/inspection_history.csv`).
- When the CNN weights are unavailable, classification falls back to a **simulation**
  engine driven by `config.DEMO_SCENARIOS`.

### Dual-Channel CNN

- **Architecture:** two VGG-style `CNNBranch` feature extractors (grayscale + Sobel
  edge) concatenated → adaptive pool → FC head. ~3,098,947 parameters.
- **Input:** 200×200 grayscale; channel 2 is a pure-NumPy Sobel edge map.
- **Classes:** `Crack`, `Dent`, `Scratch` (3 classes, mapped from 6 NEU-DET classes).
- **Trained on:** NEU Metal Surface Defects (NEU-DET) — 420 / 90 / 90 images per
  class (train / val / test), inverse-frequency class weights, AdamW +
  ReduceLROnPlateau, early stopping. **Test accuracy 93.70%**, ~38.6 ms / image on CPU.
- Whole-image **classification only** — no bounding-box / mask localization.

> The NEU-DET dataset has no defect-free images, so the model has no `Normal` class.
> In real-CNN mode a clean part is still labeled as a defect class; the all-`Normal`
> → ACCEPT path exists only in simulation mode.

---

## Project structure

```
AI-Metal-Defect-Detection-Prototype/
├── app.py                      # Streamlit entry point + custom page routing (11 pages)
├── config.py                   # Constants, classes, scenarios, decision logic
├── run.bat                     # streamlit run app.py
├── requirements.txt            # Pinned dependencies
├── benchmark.py                # Per-step pipeline timing vs a 45–50s budget
├── cnn/
│   ├── model.py                # DualChannelCNN, build_model
│   ├── dataset.py              # MetalDefectDataset, Sobel edge, DataLoaders
│   ├── train.py                # Training script (auto-detects classes)
│   └── inference.py            # MetalVisionInference engine
├── modules/
│   ├── camera.py               # OpenCV capture + image quality
│   ├── simulator.py            # Inspection simulation engine
│   ├── data_manager.py         # CSV history + session data
│   ├── cnn_pipeline.py         # Static CNN architecture visualizer
│   └── utils.py                # Session state + formatting helpers
├── pages/                      # 11 dashboard pages (see below)
├── assets/styles/custom.css    # Vintage industrial copper / amber theme
├── models/
│   ├── dual_channel_cnn.pth    # trained weights (3 classes)
│   └── model_info.json          # class names, accuracy, config
├── dataset/NEU-DET/            # training data (prepared splits)
└── data/inspection_history.csv  # inspection history
```

---

## The 11 pages

1. **Overview** — KPI cards from the history CSV.
2. **Live 360° Inspection** — the core workflow: Part ID, scenario, camera, capture, classify, verdict.
3. **Inspection History** — table + filters over the history CSV.
4. **Analytics** — charts over history.
5. **Digital Reports** — report export (PDF / TXT).
6. **System Architecture** — static diagrams + motor math.
7. **Quality Control** — image-quality thresholds + control charts.
8. **Predictions** — NumPy linear-regression forecasting / anomaly detection.
9. **Maintenance** — component health + maintenance log.
10. **Admin Panel** — admin tools.
11. **Camera Test** — OpenCV camera probe + dual-channel preview.

---

## Setup & running

### Prerequisites
- Python 3.10+
- A USB / built-in webcam (optional — simulation mode works without a camera)

### Install
```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

`requirements.txt` pins every dependency, including **opencv-python** (camera
capture), **torch** / **torchvision** (CNN), streamlit, plotly, pandas, Pillow,
reportlab, and scipy.

### Run
```bash
streamlit run app.py
```
or, on Windows, double-click **`run.bat`**. The app opens at `http://localhost:8501`.

### Train / retrain the model (optional)
```bash
python dataset/prepare_dataset.py   # prepare NEU-DET splits (already done)
python cnn/train.py                 # auto-detects classes → 3-class model
```
`train.py` auto-detects the classes present in `dataset/NEU-DET/prepared/train/`
and builds a model matching that count, keeping it consistent with `inference.py`,
which reads class names / count from `models/model_info.json`.

---

## Integration status

| Component | Status |
|---|---|
| Dashboard & UI (Streamlit, 11 pages) | Live |
| OpenCV image capture (USB webcam) | Live |
| Dual-Channel CNN classifier | Trained — 93.70% test accuracy |
| STM32 motor control / DRV8825 driver | Not integrated (firmware / hardware pending) |
| Platform rotation | Manual (operator rotates by hand between captures) |

---

## Tech stack

Python · Streamlit · PyTorch (Dual-Channel CNN) · OpenCV (camera) · Plotly ·
Pandas · NumPy · Pillow · reportlab.

---

## Notes & limitations

- **Hardware not integrated:** rotation is manual; the STM32 / DRV8825 / NEMA-17
  paths are placeholders in `config.py`.
- **No `Normal` class** in the real model (NEU-DET has no defect-free images).
- **No defect localization** — the live pipeline is whole-image classification only.

For educational / prototype purposes only.
