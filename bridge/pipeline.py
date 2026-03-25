import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.feature_contract import INPUT_SHAPE, N_FEATURES, N_TIMESTEPS, build_packet, normalize


class FeaturePipeline:
    """Convert raw (6,) feature rows into normalized tensors or UART packets."""

    def __init__(self):
        self._buf: list[np.ndarray] = []
        self._seq = 0

    def push(self, row: np.ndarray) -> None:
        row = np.asarray(row, dtype=np.float32)
        if row.shape != (N_FEATURES,):
            raise ValueError(f"Expected row shape ({N_FEATURES},), got {row.shape}")
        self._buf.append(row)
        if len(self._buf) > N_TIMESTEPS:
            self._buf.pop(0)

    def ready(self) -> bool:
        return len(self._buf) == N_TIMESTEPS

    def _current_window(self) -> np.ndarray:
        if not self.ready():
            raise RuntimeError("Feature window is incomplete; call ready() before requesting output.")
        return np.stack(self._buf, axis=0)

    def get_packet(self) -> bytes:
        norm = normalize(self._current_window())
        packet = build_packet(self._seq, norm)
        self._seq = (self._seq + 1) & 0xFF
        return packet

    def get_tensor(self):
        import torch

        norm = normalize(self._current_window())
        if norm.shape != INPUT_SHAPE:
            raise RuntimeError(f"Expected normalized shape {INPUT_SHAPE}, got {norm.shape}")
        return torch.from_numpy(norm).unsqueeze(0)
