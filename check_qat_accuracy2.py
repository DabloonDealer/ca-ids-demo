import sys

import torch

sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware")
sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training")

checkpoint = torch.load(
    r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\logs\caids_ai8x_qat40_lr1e3___2026.03.23-170254\caids_ai8x_qat40_lr1e3_qat_best.pth.tar",
    map_location="cpu",
    weights_only=False,
)

print("Extras:", checkpoint.get("extras", "not found"))
print("Arch:", checkpoint.get("arch", "not found"))
print("Epoch:", checkpoint.get("epoch", "not found"))

# Check all log files from this training run
import os

log_dir = r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\logs\caids_ai8x_qat40_lr1e3___2026.03.23-170254"
for f in os.listdir(log_dir):
    print(f"  {f}")
