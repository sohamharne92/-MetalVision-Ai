"""
METALVISION AI — Dataset & DataLoader
Loads prepared images from dataset/NEU-DET/prepared/
and produces (gray_tensor, edge_tensor, label) tuples.

Directory structure expected:
  prepared/
    train/
      Crack/    *.bmp or *.jpg or *.png
      Dent/
      Scratch/
      Normal/
    val/
    test/
"""

import os
import numpy as np
from pathlib import Path
from PIL import Image

import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T


# ── Class mapping ─────────────────────────────────────────────────────────────
CLASS_NAMES  = ["Normal", "Crack", "Dent", "Scratch"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASS_NAMES)}
IMG_SIZE     = 200   # resize all images to 200×200


# ── Sobel edge detection (NumPy, no OpenCV dependency) ───────────────────────
def sobel_edge(gray_arr: np.ndarray) -> np.ndarray:
    """
    Compute Sobel gradient magnitude on a (H, W) uint8 grayscale array.
    Returns normalised float32 array in [0, 1].
    """
    img = gray_arr.astype(np.float32) / 255.0

    # Simple 3×3 Sobel kernels via convolution
    kx = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
    ky = kx.T

    # Pad and convolve manually (avoids scipy/OpenCV dependency)
    padded = np.pad(img, 1, mode="reflect")
    gx = np.zeros_like(img)
    gy = np.zeros_like(img)
    for i in range(3):
        for j in range(3):
            patch = padded[i:i + img.shape[0], j:j + img.shape[1]]
            gx += kx[i, j] * patch
            gy += ky[i, j] * patch

    magnitude = np.hypot(gx, gy)
    # Normalise to [0, 1]
    max_val = magnitude.max()
    if max_val > 0:
        magnitude /= max_val
    return magnitude.astype(np.float32)


# ── Dataset class ─────────────────────────────────────────────────────────────
class MetalDefectDataset(Dataset):
    """
    PyTorch Dataset for the prepared NEU-DET directory.

    Returns a tuple:
      gray_tensor  : FloatTensor (1, IMG_SIZE, IMG_SIZE) — normalised grayscale
      edge_tensor  : FloatTensor (1, IMG_SIZE, IMG_SIZE) — Sobel edge map
      label        : int (0=Normal, 1=Crack, 2=Dent, 3=Scratch)
    """

    SUPPORTED_EXTS = {".bmp", ".jpg", ".jpeg", ".png"}

    def __init__(self, root_dir: str, split: str = "train", augment: bool = False):
        """
        Args:
            root_dir : path to prepared/ directory
            split    : "train", "val", or "test"
            augment  : apply random augmentation (train only)
        """
        self.split   = split
        self.augment = augment and (split == "train")
        self.samples = []   # list of (path, label_idx)

        split_dir = Path(root_dir) / split
        if not split_dir.exists():
            raise FileNotFoundError(
                f"Split directory not found: {split_dir}\n"
                "Run  python dataset/prepare_dataset.py  first."
            )

        for class_name in CLASS_NAMES:
            class_dir = split_dir / class_name
            if not class_dir.exists():
                continue
            for img_path in class_dir.iterdir():
                if img_path.suffix.lower() in self.SUPPORTED_EXTS:
                    self.samples.append((img_path, CLASS_TO_IDX[class_name]))

        if len(self.samples) == 0:
            raise RuntimeError(
                f"No images found in {split_dir}.\n"
                "Check that prepare_dataset.py ran successfully."
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        img_path, label = self.samples[idx]

        # Load and resize to IMG_SIZE × IMG_SIZE
        img  = Image.open(img_path).convert("L")   # grayscale
        img  = img.resize((IMG_SIZE, IMG_SIZE), Image.BILINEAR)
        arr  = np.array(img, dtype=np.uint8)        # (H, W)

        # Augmentation (training only)
        if self.augment:
            arr = self._augment(arr)

        # Channel 1 — normalised grayscale float32
        gray = arr.astype(np.float32) / 255.0
        gray_tensor = torch.tensor(gray, dtype=torch.float32).unsqueeze(0)  # (1,H,W)

        # Channel 2 — Sobel edge map
        edge       = sobel_edge(arr)
        edge_tensor = torch.tensor(edge, dtype=torch.float32).unsqueeze(0)  # (1,H,W)

        return gray_tensor, edge_tensor, label

    @staticmethod
    def _augment(arr: np.ndarray) -> np.ndarray:
        """Apply random flip, rotation, and brightness jitter."""
        # Horizontal flip
        if np.random.rand() > 0.5:
            arr = np.fliplr(arr).copy()
        # Vertical flip
        if np.random.rand() > 0.5:
            arr = np.flipud(arr).copy()
        # 90° rotation (k = 0,1,2,3)
        k = np.random.randint(0, 4)
        arr = np.rot90(arr, k).copy()
        # Brightness jitter ±30 pixel values
        delta = np.random.randint(-30, 31)
        arr   = np.clip(arr.astype(np.int16) + delta, 0, 255).astype(np.uint8)
        return arr

    def class_counts(self) -> dict:
        """Return {class_name: count} for this split."""
        counts = {c: 0 for c in CLASS_NAMES}
        for _, label_idx in self.samples:
            counts[CLASS_NAMES[label_idx]] += 1
        return counts


# ── DataLoader builders ───────────────────────────────────────────────────────
def get_dataloaders(
    prepared_dir: str,
    batch_size:   int  = 32,
    num_workers:  int  = 0,
) -> dict:
    """
    Returns a dict with keys "train", "val", "test" — each a DataLoader.

    Args:
        prepared_dir : path to dataset/NEU-DET/prepared/
        batch_size   : images per batch
        num_workers  : parallel workers (0 = main process, safe on Windows)
    """
    loaders = {}
    for split in ("train", "val", "test"):
        augment = split == "train"
        try:
            ds = MetalDefectDataset(prepared_dir, split=split, augment=augment)
            loaders[split] = DataLoader(
                ds,
                batch_size=batch_size,
                shuffle=(split == "train"),
                num_workers=num_workers,
                pin_memory=False,
                drop_last=(split == "train"),
            )
            print(f"  {split:5s}: {len(ds):5d} images  "
                  f"({', '.join(f'{k}:{v}' for k,v in ds.class_counts().items())})")
        except FileNotFoundError as e:
            print(f"  WARNING: {e}")
    return loaders


if __name__ == "__main__":
    import sys
    prepared = Path(__file__).parent.parent / "dataset" / "NEU-DET" / "prepared"
    print(f"Loading from: {prepared}")
    loaders = get_dataloaders(str(prepared), batch_size=8)
    if "train" in loaders:
        gray, edge, labels = next(iter(loaders["train"]))
        print(f"Batch shapes — gray: {gray.shape}  edge: {edge.shape}  labels: {labels}")
