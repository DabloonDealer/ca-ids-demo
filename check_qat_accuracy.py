import sys

import torch

sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware")
sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training")

from shared.feature_contract import CLASS_NAMES, normalize
from training.simulator import AttackInjector, VehicleSimulator


checkpoint = torch.load(
    r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\logs\caids_ai8x_qat40_lr1e3___2026.03.23-170254\caids_ai8x_qat40_lr1e3_qat_best.pth.tar",
    map_location="cpu",
    weights_only=False,
)
print("Checkpoint keys:", list(checkpoint.keys()))
print("Best top-1 accuracy:", checkpoint.get("best_top1", "not found"))
print("Epoch:", checkpoint.get("epoch", "not found"))

# Also run inference on the QAT model if the arch is available
if "state_dict" in checkpoint:
    print("\nState dict keys (first 10):", list(checkpoint["state_dict"].keys())[:10])
