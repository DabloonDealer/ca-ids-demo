import sys

import torch

sys.path.insert(0, r"C:\Users\Amiltha M\IDS_Hardware")

from shared.feature_contract import CLASS_NAMES, normalize, to_int8
from training.simulator import AttackInjector, VehicleSimulator


def load_model(path):
    model = torch.jit.load(path, map_location="cpu")
    model.eval()
    return model


model = load_model(r"C:\Users\Amiltha M\IDS_Hardware\training\caids_q8.pth")

injectors = [
    (None, "Normal"),
    (AttackInjector.dos, "DoS"),
    (AttackInjector.spoofing, "Spoofing"),
    (AttackInjector.replay, "Replay"),
    (AttackInjector.fuzzing, "Fuzzing"),
]

print("Desktop model predictions on 20 samples per class:")
print(f"{'True':<12} {'Correct'}")
print("-" * 30)
for injector, true_name in injectors:
    correct = 0
    for i in range(20):
        sim = VehicleSimulator("cruise", seed=42 + i)
        raw = injector(sim) if injector else sim.window()
        norm = normalize(raw)
        tensor = torch.tensor(norm).unsqueeze(0)
        with torch.no_grad():
            pred = model(tensor).argmax(1).item()
        if CLASS_NAMES[pred] == true_name:
            correct += 1
    print(f"{true_name:<12} {correct}/20 correct")

print("\nSpoofing int8 payload sent to board:")
sim = VehicleSimulator("cruise", seed=42)
raw = AttackInjector.spoofing(sim)
norm = normalize(raw)
payload = to_int8(norm).flatten(order="C")
print(payload)
print("Shape:", payload.shape)
