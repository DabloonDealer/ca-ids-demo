import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(__file__).resolve().parent / ".matplotlib"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score, roc_auc_score
from torch.utils.data import DataLoader

from dataset import CANDataset
from shared.feature_contract import CLASS_NAMES

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "caids_q8.pth"
DEFAULT_PLOT_PATH = BASE_DIR / "confusion_matrix.png"

def evaluate(model_path: str = str(DEFAULT_MODEL_PATH)) -> None:
    Path(os.environ["MPLCONFIGDIR"]).mkdir(parents=True, exist_ok=True)
    test_ds = CANDataset(n_samples=2000, seed=123)
    test_dl = DataLoader(test_ds, batch_size=64, shuffle=False)

    quantized = torch.jit.load(model_path, map_location="cpu")
    quantized.eval()

    all_preds, all_labels, all_probs = [], [], []
    with torch.no_grad():
        for features, labels in test_dl:
            logits = quantized(features)
            probs = torch.softmax(logits, dim=1)
            preds = logits.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())

    all_preds = np.asarray(all_preds)
    all_labels = np.asarray(all_labels)
    all_probs = np.asarray(all_probs)

    print("\n=== Classification Report ===")
    print(classification_report(all_labels, all_preds, target_names=CLASS_NAMES, zero_division=0))

    macro_f1 = f1_score(all_labels, all_preds, average="macro")
    roc_auc = roc_auc_score(all_labels, all_probs, multi_class="ovr")
    accuracy = (all_preds == all_labels).mean()

    print(f"Overall Accuracy : {accuracy:.4f}")
    print(f"Macro F1 Score   : {macro_f1:.4f}")
    print(f"ROC-AUC (OvR)    : {roc_auc:.4f}")

    cm = confusion_matrix(all_labels, all_preds)
    normal_recall = cm[0, 0] / max(cm[0].sum(), 1)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", xticklabels=CLASS_NAMES, yticklabels=CLASS_NAMES, cmap="Blues")
    plt.title("Confusion Matrix After Targeted Normal/DoS Fix", pad=18)
    plt.suptitle(f"Normal recall: {normal_recall:.2%} | Macro F1: {macro_f1:.4f}", y=0.98, fontsize=10)
    plt.ylabel("True")
    plt.xlabel("Predicted")
    plt.tight_layout()
    plt.savefig(DEFAULT_PLOT_PATH, dpi=150)
    print(f"\nSaved: {DEFAULT_PLOT_PATH}")

    size_kb = os.path.getsize(model_path) / 1024
    print(f"\nModel file size  : {size_kb:.1f} KB  (Target: <400 KB)")
    if size_kb < 400:
        print("Fits within MAX78000 weight memory budget.")
    else:
        print("Exceeds budget - reduce filters in model.py.")


if __name__ == "__main__":
    evaluate()
