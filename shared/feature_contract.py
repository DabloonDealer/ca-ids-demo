import struct

import numpy as np

# SOURCE OF TRUTH - do not duplicate these constants anywhere else.
# Frozen once Phase A training begins.

FEATURE_ORDER = ["speed", "throttle", "brake", "rpm", "gear", "steering_angle"]
N_FEATURES = 6
N_TIMESTEPS = 10
INPUT_SHAPE = (N_FEATURES, N_TIMESTEPS)

FEATURE_MEAN = np.array([60.0, 30.0, 0.0, 2000.0, 3.0, 0.0], dtype=np.float32)
FEATURE_STD = np.array([15.0, 10.0, 5.0, 800.0, 1.0, 60.0], dtype=np.float32)
CLIP_RANGE = (-3.0, 3.0)

CLASS_NAMES = ["Normal", "DoS", "Spoofing", "Replay", "Fuzzing"]
N_CLASSES = len(CLASS_NAMES)

UART_SOF = bytes([0xA5, 0x5A])
UART_PAYLOAD_BYTES = N_TIMESTEPS * N_FEATURES
UART_PACKET_SIZE = 2 + 1 + UART_PAYLOAD_BYTES + 1


def normalize(window: np.ndarray) -> np.ndarray:
    """Normalize a raw (10, 6) float window and return channels-first (6, 10)."""
    window = np.asarray(window, dtype=np.float32)
    normalized = (window - FEATURE_MEAN) / (FEATURE_STD + 1e-8)
    normalized = np.clip(normalized, *CLIP_RANGE)
    return normalized.T.astype(np.float32)


def to_int8(norm_window: np.ndarray) -> np.ndarray:
    """Map a normalized (6, 10) float window in [-3, 3] to signed int8."""
    scaled = np.asarray(norm_window, dtype=np.float32) * (127.0 / 3.0)
    return np.clip(np.round(scaled), -128, 127).astype(np.int8)


def build_packet(seq: int, norm_window: np.ndarray) -> bytes:
    """Build a 64-byte UART packet from one normalized (6, 10) window."""
    payload = to_int8(norm_window).flatten(order="C")
    crc = seq & 0xFF
    for value in payload:
        crc ^= int(value) & 0xFF
    return UART_SOF + struct.pack("B", seq & 0xFF) + bytes(payload.tolist()) + struct.pack("B", crc)
