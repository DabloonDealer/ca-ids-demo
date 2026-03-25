import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, f1_score


def val_report(labels, preds, class_names, epoch):
    f1 = f1_score(labels, preds, average="macro", zero_division=0)
    cm = confusion_matrix(labels, preds)
    print(f"\n[Epoch {epoch}] Macro F1: {f1:.4f}")
    print(classification_report(labels, preds, target_names=class_names, zero_division=0))
    print(cm)
    # Collapse detector: warn if any predicted column dominates
    col_sums = cm.sum(axis=0)
    total = cm.sum()
    for i, s in enumerate(col_sums):
        if s > 0.6 * total:
            print(f"WARNING: Class {class_names[i]} dominates predictions ({s}/{total}). Possible collapse.")
    return f1

