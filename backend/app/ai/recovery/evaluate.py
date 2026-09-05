from __future__ import annotations

import numpy as np
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score


def evaluate_recovery(y_true, probabilities, amounts, threshold: float = 0.5) -> dict:
    y_pred = (np.asarray(probabilities) >= threshold).astype(int)
    expected_value = np.asarray(amounts) * np.asarray(probabilities)
    return {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, probabilities)) if len(set(y_true)) > 1 else 0.0,
        "pr_auc": float(average_precision_score(y_true, probabilities)) if len(set(y_true)) > 1 else 0.0,
        "mean_expected_recovered_value": float(expected_value.mean()),
        "total_expected_recovered_value": float(expected_value.sum()),
    }

