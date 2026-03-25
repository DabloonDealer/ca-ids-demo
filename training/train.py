import argparse
import copy
import random
import sys
from pathlib import Path

import numpy as np
import torch
import torch.ao.quantization as tq
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader, random_split

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.feature_contract import CLASS_NAMES
from training.dataset import CANDataset
from training.model import get_qat_ready_model
from training.training_utils import val_report

DEFAULT_OUTPUT = Path(__file__).resolve().parent / "caids_q8.pth"


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def apply_if_supported(model: nn.Module, method_name: str) -> None:
    for module in model.modules():
        method = getattr(module, method_name, None)
        if callable(method):
            method()


def evaluate_accuracy(model: nn.Module, dataloader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for features, labels in dataloader:
            features = features.to(device)
            labels = labels.to(device)
            predictions = model(features).argmax(dim=1)
            correct += (predictions == labels).sum().item()
            total += labels.size(0)
    model.train()
    return correct / max(total, 1)


def train(
    epochs: int = 20,
    batch_size: int = 64,
    lr: float = 8e-4,
    n_samples: int = 12000,
    seed: int = 42,
    output: str = str(DEFAULT_OUTPUT),
) -> Path:
    set_seed(seed)
    device = torch.device("cpu")

    dataset = CANDataset(n_samples=n_samples, seed=seed)
    val_size = max(len(dataset) // 5, 1)
    train_size = len(dataset) - val_size
    train_ds, val_ds = random_split(
        dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(seed),
    )

    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    model = get_qat_ready_model(device=device)
    class_counts = np.bincount(np.array(train_ds.dataset.y)[train_ds.indices], minlength=len(CLASS_NAMES))
    weights = 1.0 / class_counts.astype(np.float32)
    # Mildly upweight the hardest classes to reduce residual drift of Normal into DoS/Replay.
    weights[0] *= 1.35
    weights[3] *= 1.15
    weights = weights / weights.sum() * len(weights)
    criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=5, min_lr=1e-5
    )

    best_state = None
    best_val_acc = 0.0
    best_macro_f1 = 0.0

    for epoch in range(1, epochs + 1):
        running_loss = 0.0
        for features, labels in train_dl:
            features = features.to(device)
            labels = labels.to(device)

            optimizer.zero_grad(set_to_none=True)
            logits = model(features)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * labels.size(0)

        train_loss = running_loss / max(train_size, 1)
        model.eval()
        all_preds = []
        all_labels = []
        with torch.no_grad():
            for features, labels in val_dl:
                features = features.to(device)
                labels = labels.to(device)
                preds = model(features).argmax(dim=1)
                all_preds.append(preds.cpu())
                all_labels.append(labels.cpu())
        model.train()
        all_preds = torch.cat(all_preds)
        all_labels = torch.cat(all_labels)
        val_acc = (all_preds == all_labels).float().mean().item()
        val_macro_f1 = f1_score(all_labels.numpy(), all_preds.numpy(), average="macro", zero_division=0)

        print(f"Epoch {epoch:02d}/{epochs} - loss: {train_loss:.4f} - val_acc: {val_acc:.4f}")

        if epoch % 5 == 0:
            macro_f1 = val_report(all_labels.numpy(), all_preds.numpy(), CLASS_NAMES, epoch)
            scheduler.step(macro_f1)

        if val_macro_f1 >= best_macro_f1:
            best_macro_f1 = val_macro_f1
            best_val_acc = val_acc
            best_state = copy.deepcopy(model.state_dict())

        if epoch >= 3:
            model.apply(tq.disable_observer)
        if epoch >= max(epochs - 2, 1):
            apply_if_supported(model, "freeze_bn_stats")

    if best_state is None:
        raise RuntimeError("Training finished without capturing a model checkpoint.")

    model.load_state_dict(best_state)
    model.cpu().eval()
    quantized = tq.convert(copy.deepcopy(model), inplace=False)

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scripted = torch.jit.script(quantized)
    torch.jit.save(scripted, output_path)
    print(f"Saved quantized model to {output_path.resolve()}")
    print(f"Best validation accuracy: {best_val_acc:.4f}")
    print(f"Best validation macro F1: {best_macro_f1:.4f}")
    print(f"Model size: {output_path.stat().st_size / 1024:.1f} KB")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the CAN IDS CNN with quantization-aware training.")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=8e-4)
    parser.add_argument("--n-samples", type=int, default=12000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train(
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        n_samples=args.n_samples,
        seed=args.seed,
        output=args.output,
    )
