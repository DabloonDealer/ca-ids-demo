import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.feature_contract import FEATURE_ORDER

REGIMES = {
    "idle": {"speed": 0.0, "throttle": 0.0, "brake": 0.0, "rpm": 800.0, "gear": 0.0, "steering_angle": 0.0},
    "accelerate": {"speed": 50.0, "throttle": 60.0, "brake": 0.0, "rpm": 2800.0, "gear": 3.0, "steering_angle": 0.0},
    "cruise": {"speed": 80.0, "throttle": 30.0, "brake": 0.0, "rpm": 2500.0, "gear": 5.0, "steering_angle": 0.0},
    "brake": {"speed": 30.0, "throttle": 0.0, "brake": 60.0, "rpm": 1200.0, "gear": 2.0, "steering_angle": 0.0},
    "turn": {"speed": 40.0, "throttle": 20.0, "brake": 10.0, "rpm": 2000.0, "gear": 3.0, "steering_angle": 180.0},
    "shift": {"speed": 60.0, "throttle": 50.0, "brake": 0.0, "rpm": 3200.0, "gear": 3.0, "steering_angle": 0.0},
}

NOISE_STD = {
    "speed": 1.5,
    "throttle": 1.0,
    "brake": 0.5,
    "rpm": 80.0,
    "gear": 0.0,
    "steering_angle": 2.0,
}


class VehicleSimulator:
    def __init__(self, regime: str = "cruise", seed: int | None = None):
        self.rng = np.random.default_rng(seed)
        self.target = REGIMES[regime].copy()
        self.state = self._initial_state(self.target)
        self.regime = regime
        self._steer_phase = float(self.rng.uniform(0.0, 2.0 * np.pi))

    def _initial_state(self, target: dict[str, float]) -> dict[str, float]:
        state: dict[str, float] = {}
        for key, value in target.items():
            if key == "gear":
                state[key] = value
            else:
                state[key] = value * float(self.rng.uniform(0.75, 1.25))
        return state

    def set_regime(self, regime: str) -> None:
        self.target = REGIMES[regime].copy()
        self.regime = regime

    def step(self, alpha: float = 0.15) -> np.ndarray:
        for key in FEATURE_ORDER:
            if key == "gear":
                self.state[key] = self.target[key]
            else:
                noise = self.rng.normal(0.0, NOISE_STD[key])
                self.state[key] += alpha * (self.target[key] - self.state[key]) + noise
        if self.regime == "turn":
            self._steer_phase += 0.45
            self.state["steering_angle"] = self.target["steering_angle"] * np.sin(self._steer_phase) + self.rng.normal(0.0, 5.0)
        elif self.regime == "cruise":
            self.state["steering_angle"] = self.rng.normal(0.0, 4.0)
            self.state["speed"] += self.rng.normal(0.4, 0.2)
            self.state["rpm"] += self.rng.normal(25.0, 10.0)
        self.state["speed"] = float(np.clip(self.state["speed"], 0.0, 160.0))
        self.state["throttle"] = float(np.clip(self.state["throttle"], 0.0, 100.0))
        self.state["brake"] = float(np.clip(self.state["brake"], 0.0, 100.0))
        self.state["rpm"] = float(np.clip(self.state["rpm"], 600.0, 7000.0))
        self.state["steering_angle"] = float(np.clip(self.state["steering_angle"], -180.0, 180.0))
        return np.array([self.state[key] for key in FEATURE_ORDER], dtype=np.float32)

    def window(self, n: int = 10) -> np.ndarray:
        return np.stack([self.step() for _ in range(n)], axis=0)


class AttackInjector:
    @staticmethod
    def dos(sim: VehicleSimulator) -> np.ndarray:
        window = sim.window()
        window[:, 3] += sim.rng.uniform(4000.0, 6000.0, window.shape[0])
        return window

    @staticmethod
    def spoofing(sim: VehicleSimulator) -> np.ndarray:
        window = sim.window()
        window[:, 0] += 150.0
        window[:, 4] = 1.0
        return window

    @staticmethod
    def replay(sim: VehicleSimulator) -> np.ndarray:
        first_half = np.stack([sim.step(alpha=0.35) for _ in range(5)], axis=0)
        _ = sim.window(5)
        return np.concatenate([first_half, first_half], axis=0).astype(np.float32)

    @staticmethod
    def fuzzing(sim: VehicleSimulator) -> np.ndarray:
        window = sim.window()
        window += sim.rng.uniform(-50.0, 50.0, window.shape)
        return window.astype(np.float32)
