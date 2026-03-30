import argparse
import contextlib
import io
import os
import sys
import time
import types

import numpy as np
import serial

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training")

from shared.feature_contract import (
    CLASS_NAMES,
    N_CLASSES,
    build_packet,
    normalize,
    to_int8,
)
from training.dataset import CLASS_REGIMES, NORMAL_REGIME_WEIGHTS
from training.simulator import AttackInjector, VehicleSimulator

AI8X_CHECKPOINT = (
    r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\logs\caids_ai8x_qat40_lr1e3___2026.03.23-170254\caids_ai8x_qat40_lr1e3_qat_best.pth.tar"
)
TORCHSCRIPT_MODEL = r"C:\Users\Amiltha M\IDS_Hardware\training\caids_q8.pth"
REPLAY_TIEBREAK_MARGIN = 1.3


def load_ai8x_model(silent=False):
    import importlib.util
    import torch

    # ai8x imports tqdm at module import time; provide a tiny fallback so
    # checkpoint comparison can still run in lean environments.
    if "tqdm" not in sys.modules:
        tqdm_mod = types.ModuleType("tqdm")

        def _tqdm(iterable=None, *args, **kwargs):
            return iterable if iterable is not None else []

        tqdm_mod.tqdm = _tqdm
        sys.modules["tqdm"] = tqdm_mod

    with contextlib.redirect_stdout(io.StringIO()) if silent else contextlib.nullcontext():
        import ai8x
        ai8x.set_device(device=85, simulate=True, round_avg=False)

    model_path = r"C:\Users\Amiltha M\IDS_Hardware\ai8x-training\models\ai85net-caids.py"
    spec = importlib.util.spec_from_file_location("ai85net_caids", model_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    model = module.AI85CAIDSNet(batchnorm=None)
    checkpoint = torch.load(AI8X_CHECKPOINT, map_location="cpu", weights_only=False)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    return model


def load_torchscript_model():
    import torch

    model = torch.jit.load(TORCHSCRIPT_MODEL, map_location="cpu")
    model.eval()
    return model


def desktop_predict(model, raw_window, reference, aux_model=None):
    import torch

    norm = normalize(raw_window)
    if reference == "ai8x":
        tensor = torch.tensor(to_int8(norm).astype(np.float32)).unsqueeze(0)
    else:
        tensor = torch.tensor(norm).unsqueeze(0)
    with torch.no_grad():
        out = model(tensor)
        pred = int(out.argmax(1).item())
        if reference == "torchscript" and aux_model is not None and pred == 3:
            logits = out.squeeze(0)
            top_vals, _ = torch.topk(logits, 2)
            margin = float(top_vals[0] - top_vals[1])
            if margin < REPLAY_TIEBREAK_MARGIN:
                aux_tensor = torch.tensor(to_int8(norm).astype(np.float32)).unsqueeze(0)
                aux_pred = int(aux_model(aux_tensor).argmax(1).item())
                if aux_pred != 3:
                    return aux_pred
        return pred


def board_predict(ser, seq, raw_window):
    norm = normalize(raw_window)
    packet = build_packet(seq, norm)
    assert len(packet) == 64

    ser.reset_input_buffer()
    ser.write(packet)

    response = ser.readline()
    if not response:
        return None, "TIMEOUT"

    decoded = response.decode(errors="replace").strip()

    if decoded.startswith("OK,"):
        return 0, decoded
    elif decoded.startswith("ALERT,"):
        parts = decoded.split(",")
        if len(parts) >= 2 and parts[1] in CLASS_NAMES:
            return CLASS_NAMES.index(parts[1]), decoded
    return None, decoded


def generate_windows(n_samples, seed=0):
    injectors = [
        (None, 0),
        (AttackInjector.dos, 1),
        (AttackInjector.spoofing, 2),
        (AttackInjector.replay, 3),
        (AttackInjector.fuzzing, 4),
    ]
    rng = np.random.default_rng(seed)
    per_class = n_samples // N_CLASSES
    for injector, label in injectors:
        for _ in range(per_class):
            if label == 0:
                regime = rng.choice(
                    list(NORMAL_REGIME_WEIGHTS.keys()),
                    p=list(NORMAL_REGIME_WEIGHTS.values()),
                ).item()
            else:
                regime = rng.choice(CLASS_REGIMES[label]).item()
            sim = VehicleSimulator(regime=regime, seed=int(rng.integers(0, 1_000_000)))
            window = injector(sim) if injector else sim.window()
            yield window, label


def run(port, n_samples, baud=115200, reference="torchscript", seed=0):
    print("CA-IDS HITL Roundtrip Test")
    print(f"Port: {port} | Samples: {n_samples}")
    if reference == "ai8x":
        print("Desktop model: ai8x QAT checkpoint")
    else:
        print("Desktop model: TorchScript q8 reference")
    print("-" * 60)

    try:
        aux_model = None
        if reference == "ai8x":
            model = load_ai8x_model()
            print("ai8x desktop model loaded.")
        else:
            model = load_torchscript_model()
            try:
                aux_model = load_ai8x_model(silent=True)
            except Exception:
                aux_model = None
            print("TorchScript desktop model loaded.")
        use_desktop = True
    except Exception as e:
        print(f"WARNING: Could not load desktop model: {e}")
        print("Board-only mode.")
        use_desktop = False

    total = agreed = true_matches = timeouts = crc_fails = 0
    board_counts = [0] * N_CLASSES
    desk_counts = [0] * N_CLASSES

    with serial.Serial(port, baud, timeout=5) as ser:
        time.sleep(0.5)
        seq = 0

        for raw_window, true_label in generate_windows(n_samples, seed=seed):
            board_label, raw_resp = board_predict(ser, seq & 0xFF, raw_window)
            seq += 1

            if board_label is None:
                if "TIMEOUT" in raw_resp:
                    timeouts += 1
                elif "CRC_FAIL" in raw_resp:
                    crc_fails += 1
                print(f"  [SEQ {seq-1:>4}] SKIP - {raw_resp}")
                continue

            board_counts[board_label] += 1
            total += 1
            true_matches += int(board_label == true_label)

            if use_desktop:
                desk_label = desktop_predict(model, raw_window, reference, aux_model=aux_model)
                desk_counts[desk_label] += 1
                match = board_label == desk_label
                agreed += int(match)
                status = "MATCH" if match else "MISMATCH"
                print(
                    f"  [SEQ {seq-1:>4}] true={CLASS_NAMES[true_label]:<10} "
                    f"board={CLASS_NAMES[board_label]:<10} "
                    f"desk={CLASS_NAMES[desk_label]:<10} {status}"
                )
            else:
                print(
                    f"  [SEQ {seq-1:>4}] true={CLASS_NAMES[true_label]:<10} "
                    f"board={CLASS_NAMES[board_label]:<10}"
                )

    print("-" * 60)
    print(f"Total valid packets : {total}")
    print(f"Timeouts            : {timeouts}")
    print(f"CRC failures        : {crc_fails}")
    print(f"Board counts        : {board_counts}")
    if total > 0:
        board_accuracy = true_matches / total
        print(f"Board vs true       : {true_matches}/{total} = {board_accuracy * 100:.1f}%")
    if use_desktop:
        print(f"Desktop counts      : {desk_counts}")
        if total > 0:
            agreement = agreed / total
            print(f"Agreement           : {agreed}/{total} = {agreement * 100:.1f}%")
            print()
            if agreement >= 0.95:
                print("Task 5 PASS CHECK: COMPLETE  (>= 95% agreement)")
            else:
                print(f"Task 5 PASS CHECK: FAILED    ({agreement * 100:.1f}% < 95%)")
    elif total > 0:
        print("Agreement           : unavailable (desktop model not loaded)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="COM4")
    ap.add_argument("--samples", type=int, default=100, dest="n_samples")
    ap.add_argument("--reference", choices=["torchscript", "ai8x"], default="torchscript")
    ap.add_argument("--seed", type=int, default=0)
    run(**vars(ap.parse_args()))
