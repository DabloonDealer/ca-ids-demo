import sys
from pathlib import Path

import argparse

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from bridge.pipeline import FeaturePipeline
from shared.feature_contract import CLASS_NAMES
from training.simulator import VehicleSimulator


def run(model: str, samples: int) -> None:
    quantized = torch.jit.load(model, map_location="cpu")
    quantized.eval()

    pipeline = FeaturePipeline()
    simulator = VehicleSimulator("cruise", seed=123)
    correct = 0

    print(f"Running {samples} loopback inferences...")
    seen = 0
    for i in range(samples + 10):
        pipeline.push(simulator.step())
        if not pipeline.ready():
            continue
        if seen >= samples:
            break
        tensor = pipeline.get_tensor()
        with torch.no_grad():
            pred = int(quantized(tensor).argmax(1).item())
        correct += int(pred == 0)
        print(f"  [{seen:>4}] pred={CLASS_NAMES[pred]}")
        seen += 1

    accuracy = correct / samples
    print(f"Normal-traffic accuracy: {accuracy:.3f}  (expect > 0.85)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="training/caids_q8.pth")
    parser.add_argument("--samples", type=int, default=200)
    run(**vars(parser.parse_args()))
