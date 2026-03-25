import sys
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.feature_contract import CLASS_NAMES, N_CLASSES, normalize
from training.simulator import AttackInjector, VehicleSimulator

REGIMES = ["idle", "accelerate", "cruise", "brake", "turn", "shift"]
INJECTORS = [
    None,
    AttackInjector.dos,
    AttackInjector.spoofing,
    AttackInjector.replay,
    AttackInjector.fuzzing,
]
CLASS_REGIMES = {
    0: REGIMES,
    1: ["accelerate", "cruise", "shift"],
    2: ["accelerate", "cruise", "turn"],
    3: ["accelerate", "turn", "shift"],
    4: REGIMES,
}
NORMAL_REGIME_WEIGHTS = {
    "idle": 0.25,
    "accelerate": 0.10,
    "cruise": 0.25,
    "brake": 0.20,
    "turn": 0.15,
    "shift": 0.05,
}


class CANDataset(Dataset):
    def __init__(self, n_samples: int = 10000, regimes: list[str] | None = None, seed: int = 0):
        self.rng = np.random.default_rng(seed)
        self.regimes = regimes or REGIMES
        self.X, self.y = [], []
        per_class = n_samples // N_CLASSES

        for label, injector in enumerate(INJECTORS):
            for _ in range(per_class):
                if label == 0:
                    regime = self.rng.choice(
                        list(NORMAL_REGIME_WEIGHTS.keys()),
                        p=list(NORMAL_REGIME_WEIGHTS.values()),
                    ).item()
                else:
                    regime_pool = CLASS_REGIMES.get(label, self.regimes)
                    regime = self.rng.choice(regime_pool).item()
                sim = VehicleSimulator(regime=regime, seed=int(self.rng.integers(0, 1_000_000)))
                raw_window = injector(sim) if injector else sim.window()
                norm_window = normalize(raw_window)
                self.X.append(norm_window)
                self.y.append(label)

        self.X = np.asarray(self.X, dtype=np.float32)
        self.y = np.asarray(self.y, dtype=np.int64)

    def __len__(self) -> int:
        return len(self.y)

    def __getitem__(self, i: int):
        return torch.from_numpy(self.X[i]), torch.tensor(self.y[i], dtype=torch.long)


__all__ = ["CANDataset", "CLASS_NAMES", "REGIMES"]
