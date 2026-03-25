import sys

import numpy as np

sys.path.insert(0, ".")

from shared.feature_contract import FEATURE_ORDER, INPUT_SHAPE, normalize

RAW_SAMPLE = np.array(
    [
        [62.1, 28.5, 0.0, 2050.0, 3.0, 5.0],
        [63.4, 29.1, 0.0, 2110.0, 3.0, 4.2],
        [64.0, 30.2, 0.0, 2090.0, 3.0, 3.8],
        [64.5, 31.0, 0.0, 2120.0, 3.0, 2.1],
        [65.0, 30.8, 0.0, 2200.0, 3.0, 1.5],
        [65.2, 30.5, 0.0, 2180.0, 3.0, 0.8],
        [65.1, 30.0, 0.0, 2150.0, 3.0, -0.5],
        [64.8, 29.8, 0.0, 2100.0, 3.0, -1.2],
        [64.2, 29.5, 0.0, 2080.0, 3.0, -2.0],
        [63.8, 29.2, 0.0, 2060.0, 3.0, -2.5],
    ],
    dtype=np.float32,
)


def test_output_shape():
    out = normalize(RAW_SAMPLE)
    assert out.shape == INPUT_SHAPE, f"Expected {INPUT_SHAPE}, got {out.shape}"


def test_output_dtype():
    out = normalize(RAW_SAMPLE)
    assert out.dtype == np.float32


def test_clip_range():
    out = normalize(RAW_SAMPLE)
    assert out.min() >= -3.0 and out.max() <= 3.0


def test_training_bridge_parity():
    training_side = normalize(RAW_SAMPLE.copy())
    bridge_side = normalize(RAW_SAMPLE.copy())
    diff = np.abs(training_side - bridge_side).max()
    assert diff < 1e-5, f"Parity failed - max abs diff: {diff}"


def test_feature_order():
    assert FEATURE_ORDER[0] == "speed"
    assert FEATURE_ORDER[3] == "rpm"
    assert len(FEATURE_ORDER) == 6
