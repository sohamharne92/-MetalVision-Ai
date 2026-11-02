"""
METALVISION AI — Dual-Channel CNN Model
Architecture: two parallel CNN branches (grayscale + edge map) whose
feature maps are concatenated and passed through fully-connected layers
to classify into 4 defect classes.

Input:
  channel_1 — grayscale image  (1, H, W)
  channel_2 — Sobel edge map   (1, H, W)

Output:
  logits of shape (batch, 4)  →  [Normal, Crack, Dent, Scratch]
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBnRelu(nn.Module):
    """Conv → BatchNorm → ReLU block — reused in both branches."""
    def __init__(self, in_ch: int, out_ch: int, kernel: int = 3, stride: int = 1):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel, stride=stride,
                      padding=kernel // 2, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class CNNBranch(nn.Module):
    """
    Single-channel feature extractor.
    Input:  (batch, 1, 200, 200)
    Output: (batch, 128, 12, 12)  — feature vector for this channel
    """
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            # Block 1
            ConvBnRelu(1, 32, 3),
            ConvBnRelu(32, 32, 3),
            nn.MaxPool2d(2, 2),          # 200 → 100
            nn.Dropout2d(0.1),

            # Block 2
            ConvBnRelu(32, 64, 3),
            ConvBnRelu(64, 64, 3),
            nn.MaxPool2d(2, 2),          # 100 → 50
            nn.Dropout2d(0.1),

            # Block 3
            ConvBnRelu(64, 128, 3),
            ConvBnRelu(128, 128, 3),
            nn.MaxPool2d(2, 2),          # 50 → 25
            nn.Dropout2d(0.1),

            # Block 4
            ConvBnRelu(128, 128, 3),
            nn.MaxPool2d(2, 2),          # 25 → 12
        )

    def forward(self, x):
        return self.features(x)


class DualChannelCNN(nn.Module):
    """
    Dual-Channel CNN for metal surface defect classification.

    Two CNNBranch instances process the grayscale image and the edge map
    independently. Their outputs are concatenated and passed through
    fully-connected layers to produce class logits.

    Classes (index 0–3): Normal, Crack, Dent, Scratch
    """

    CLASS_NAMES = ["Normal", "Crack", "Dent", "Scratch"]
    INPUT_SIZE  = 200   # images are resized to 200×200 before feeding

    def __init__(self, num_classes: int = 4, dropout: float = 0.5):
        super().__init__()
        self.num_classes = num_classes

        # Two parallel branches — one per channel
        self.branch_gray = CNNBranch()
        self.branch_edge = CNNBranch()

        # After concat: 128 * 2 = 256 feature maps, 12×12 spatial
        self.pool = nn.AdaptiveAvgPool2d((4, 4))   # → 256 × 4 × 4 = 4096

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout * 0.6),
            nn.Linear(256, num_classes),
        )

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.xavier_normal_(m.weight)
                nn.init.constant_(m.bias, 0)

    def forward(self, gray: torch.Tensor, edge: torch.Tensor) -> torch.Tensor:
        """
        Args:
            gray : (batch, 1, H, W) — normalised grayscale image
            edge : (batch, 1, H, W) — normalised Sobel edge map
        Returns:
            logits: (batch, num_classes)
        """
        feat_gray = self.branch_gray(gray)   # (B, 128, 12, 12)
        feat_edge = self.branch_edge(edge)   # (B, 128, 12, 12)
        combined  = torch.cat([feat_gray, feat_edge], dim=1)  # (B, 256, 12, 12)
        pooled    = self.pool(combined)       # (B, 256, 4, 4)
        return self.classifier(pooled)        # (B, 4)

    def predict(self, gray: torch.Tensor, edge: torch.Tensor):
        """
        Run inference and return (class_name, confidence).
        Accepts unbatched tensors (C, H, W) or batched (B, C, H, W).
        """
        self.eval()
        with torch.no_grad():
            if gray.dim() == 3:
                gray = gray.unsqueeze(0)
                edge = edge.unsqueeze(0)
            logits = self.forward(gray, edge)
            probs  = F.softmax(logits, dim=1)
            conf, idx = probs.max(dim=1)
            return self.CLASS_NAMES[idx.item()], round(conf.item(), 4)


def build_model(num_classes: int = 4, dropout: float = 0.5) -> DualChannelCNN:
    """Factory function — returns a new DualChannelCNN instance."""
    return DualChannelCNN(num_classes=num_classes, dropout=dropout)


def count_parameters(model: nn.Module) -> int:
    """Return the number of trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


if __name__ == "__main__":
    # Quick sanity check
    model = build_model()
    gray  = torch.randn(4, 1, 200, 200)
    edge  = torch.randn(4, 1, 200, 200)
    out   = model(gray, edge)
    print(f"Model output shape : {out.shape}")          # (4, 4)
    print(f"Trainable params   : {count_parameters(model):,}")
    cls, conf = model.predict(gray[0], edge[0])
    print(f"Single prediction  : {cls}  ({conf:.4f})")
