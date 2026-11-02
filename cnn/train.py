"""
METALVISION AI — CNN Training Script
Trains the Dual-Channel CNN on the prepared NEU-DET dataset.
Automatically detects available classes — works with 3 classes
(Crack/Dent/Scratch) or 4 classes (+ Normal) depending on what
is present in dataset/NEU-DET/prepared/train/.

USAGE (from project root):
  python cnn/train.py

OUTPUTS:
  models/dual_channel_cnn.pth   — best model weights (by val accuracy)
  models/training_log.json      — per-epoch metrics
  models/model_info.json        — class names, accuracy, config
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import ReduceLROnPlateau

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from cnn.dataset import get_dataloaders, IMG_SIZE

# ── Auto-detect available classes from prepared directory ─────────────────────
PREPARED_DIR = ROOT / "dataset" / "NEU-DET" / "prepared"
ALL_CLASSES  = ["Normal", "Crack", "Dent", "Scratch"]

def detect_classes(prepared_dir: Path) -> list:
    """Return only the classes that have images in train/."""
    train_dir = prepared_dir / "train"
    if not train_dir.exists():
        return []
    found = []
    for cls in ALL_CLASSES:
        cls_dir = train_dir / cls
        if cls_dir.exists():
            imgs = list(cls_dir.glob("*"))
            if len(imgs) > 0:
                found.append(cls)
    return found

# ── Training configuration ────────────────────────────────────────────────────
CONFIG = {
    "prepared_dir": str(PREPARED_DIR),
    "model_dir":    str(ROOT / "models"),
    "model_name":   "dual_channel_cnn.pth",
    "epochs":       50,
    "batch_size":   32,
    "lr":           1e-3,
    "weight_decay": 1e-4,
    "dropout":      0.5,
    "num_workers":  0,
    "patience":     10,
    "min_delta":    0.001,
}

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_one_epoch(model, loader, criterion, optimizer):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for gray, edge, labels in loader:
        gray, edge, labels = gray.to(DEVICE), edge.to(DEVICE), labels.to(DEVICE)
        optimizer.zero_grad()
        logits = model(gray, edge)
        loss   = criterion(logits, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
        optimizer.step()
        total_loss += loss.item() * labels.size(0)
        correct    += (logits.argmax(1) == labels).sum().item()
        total      += labels.size(0)
    return total_loss / total, correct / total


def evaluate(model, loader, criterion, num_classes):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    confusion = [[0]*num_classes for _ in range(num_classes)]
    with torch.no_grad():
        for gray, edge, labels in loader:
            gray, edge, labels = gray.to(DEVICE), edge.to(DEVICE), labels.to(DEVICE)
            logits = model(gray, edge)
            loss   = criterion(logits, labels)
            preds  = logits.argmax(1)
            total_loss += loss.item() * labels.size(0)
            correct    += (preds == labels).sum().item()
            total      += labels.size(0)
            for t, p in zip(labels.cpu().tolist(), preds.cpu().tolist()):
                confusion[t][p] += 1
    return total_loss / total, correct / total, confusion


def class_metrics(confusion, class_names):
    metrics = {}
    n = len(class_names)
    for i, cls in enumerate(class_names):
        tp = confusion[i][i]
        fp = sum(confusion[j][i] for j in range(n) if j != i)
        fn = sum(confusion[i][j] for j in range(n) if j != i)
        pr = tp / (tp + fp) if (tp + fp) else 0.0
        rc = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2*pr*rc/(pr+rc) if (pr+rc) else 0.0
        metrics[cls] = {"precision": round(pr,4), "recall": round(rc,4), "f1": round(f1,4)}
    return metrics


def compute_class_weights(loader, num_classes):
    counts = torch.zeros(num_classes)
    for _, _, labels in loader:
        for l in labels: counts[l] += 1
    total   = counts.sum()
    weights = total / (num_classes * counts)
    weights[counts == 0] = 0.0
    return weights.to(DEVICE)


def train():
    print("\n" + "=" * 62)
    print("  METALVISION AI — Dual-Channel CNN Training")
    print("=" * 62)
    print(f"  Device     : {DEVICE}")
    print(f"  Epochs     : {CONFIG['epochs']}")
    print(f"  Batch size : {CONFIG['batch_size']}")

    # ── Auto-detect classes ───────────────────────────────────────────────────
    class_names = detect_classes(PREPARED_DIR)
    if not class_names:
        print(f"\nERROR: No classes found in {PREPARED_DIR}/train/")
        print("Run: python dataset/prepare_dataset.py")
        return

    num_classes = len(class_names)
    print(f"\n  Detected {num_classes} classes: {class_names}")
    if "Normal" not in class_names:
        print("  NOTE: Normal class not found — add clean metal images to train it.")
        print("        Training with defect classes only.\n")

    # ── Patch dataset CLASS_TO_IDX to match detected classes ─────────────────
    import cnn.dataset as ds_module
    ds_module.CLASS_NAMES  = class_names
    ds_module.CLASS_TO_IDX = {c: i for i, c in enumerate(class_names)}

    # ── Load data ─────────────────────────────────────────────────────────────
    print(f"\nLoading dataset from: {CONFIG['prepared_dir']}")
    loaders = get_dataloaders(CONFIG["prepared_dir"],
                               batch_size=CONFIG["batch_size"],
                               num_workers=CONFIG["num_workers"])
    if "train" not in loaders:
        print("ERROR: No training data found after loading.")
        return

    # ── Build model ───────────────────────────────────────────────────────────
    from cnn.model import build_model, count_parameters
    model = build_model(num_classes=num_classes, dropout=CONFIG["dropout"]).to(DEVICE)
    # Override CLASS_NAMES on the model instance
    model.CLASS_NAMES = class_names
    print(f"  Parameters : {count_parameters(model):,}")

    weights   = compute_class_weights(loaders["train"], num_classes)
    criterion = nn.CrossEntropyLoss(weight=weights)
    optimizer = optim.AdamW(model.parameters(),
                             lr=CONFIG["lr"], weight_decay=CONFIG["weight_decay"])
    scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=5)

    # ── Training loop ─────────────────────────────────────────────────────────
    best_val_acc   = 0.0
    patience_count = 0
    log            = []
    model_dir      = Path(CONFIG["model_dir"])
    model_dir.mkdir(exist_ok=True)
    model_path     = model_dir / CONFIG["model_name"]

    print(f"\n{'Epoch':>6}  {'Tr Loss':>8}  {'Tr Acc':>7}  "
          f"{'Val Loss':>8}  {'Val Acc':>7}  {'LR':>8}  Note")
    print("-" * 66)

    for epoch in range(1, CONFIG["epochs"] + 1):
        t0 = time.time()
        tr_loss, tr_acc = train_one_epoch(model, loaders["train"], criterion, optimizer)

        if "val" in loaders:
            val_loss, val_acc, _ = evaluate(model, loaders["val"], criterion, num_classes)
        else:
            val_loss, val_acc = tr_loss, tr_acc

        lr_now = optimizer.param_groups[0]["lr"]
        note   = ""

        if val_acc > best_val_acc + CONFIG["min_delta"]:
            best_val_acc   = val_acc
            patience_count = 0
            torch.save(model.state_dict(), model_path)
            note = "saved"
        else:
            patience_count += 1
            note = f"p {patience_count}/{CONFIG['patience']}"

        log.append({"epoch": epoch, "tr_loss": round(tr_loss,4),
                    "tr_acc": round(tr_acc,4), "val_loss": round(val_loss,4),
                    "val_acc": round(val_acc,4), "lr": lr_now})

        print(f"{epoch:>6}  {tr_loss:>8.4f}  {tr_acc:>6.1%}  "
              f"{val_loss:>8.4f}  {val_acc:>6.1%}  {lr_now:>8.2e}  "
              f"{note}  ({time.time()-t0:.1f}s)")

        scheduler.step(val_acc)

        if patience_count >= CONFIG["patience"]:
            print(f"\nEarly stopping at epoch {epoch}.")
            break

    # ── Final test evaluation ─────────────────────────────────────────────────
    test_acc = None
    metrics  = {}
    if "test" in loaders and model_path.exists():
        print("\nFinal test evaluation...")
        model.load_state_dict(torch.load(model_path, map_location=DEVICE,
                                          weights_only=True))
        test_loss, test_acc, confusion = evaluate(
            model, loaders["test"], criterion, num_classes)
        metrics = class_metrics(confusion, class_names)

        print(f"Test Acc : {test_acc:.1%}")
        print(f"\n{'Class':<10}  Precision  Recall     F1")
        print("-" * 44)
        for cls, m in metrics.items():
            print(f"{cls:<10}  {m['precision']:.3f}      "
                  f"{m['recall']:.3f}    {m['f1']:.3f}")

        print("\nConfusion Matrix (rows=actual, cols=predicted):")
        header = "         " + "".join(f"{c[:6]:>8}" for c in class_names)
        print(header)
        for i, cls in enumerate(class_names):
            row = f"{cls[:8]:<8} " + "".join(f"{confusion[i][j]:>8}"
                                               for j in range(num_classes))
            print(row)

    # ── Save training log + model info ────────────────────────────────────────
    (model_dir / "training_log.json").write_text(json.dumps(log, indent=2))

    model_info = {
        "model_name":    "DualChannelCNN",
        "class_names":   class_names,
        "num_classes":   num_classes,
        "input_size":    IMG_SIZE,
        "best_val_acc":  round(best_val_acc, 4),
        "test_acc":      round(test_acc, 4) if test_acc else None,
        "class_metrics": metrics,
        "trained_on":    datetime.now().isoformat(),
        "dataset":       "NEU Metal Surface Defects",
        "config":        CONFIG,
        "device":        str(DEVICE),
        "status":        "trained",
    }
    (model_dir / "model_info.json").write_text(json.dumps(model_info, indent=2))

    print(f"\nBest val acc  : {best_val_acc:.1%}")
    print(f"Model saved   : {model_path}")
    print(f"Classes       : {class_names}")
    print("Training complete. Run the dashboard to use real CNN inference.")


if __name__ == "__main__":
    train()
