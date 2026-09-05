from __future__ import annotations

import json

from app.ai.anomaly.train import train_anomaly_detector
from app.ai.dataset import generate_and_save
from app.ai.fraud.train import train_fraud_models
from app.ai.paths import DOCS_DIR, ensure_project_dirs
from app.ai.recovery.train import train_recovery_models


def write_report(dataset: dict, fraud: dict, anomaly: dict, recovery: dict) -> None:
    ensure_project_dirs()
    best = fraud["selected_model"]
    best_metrics = fraud["test_metrics"][best]
    recovery_best = recovery["selected_model"]
    recovery_metrics = recovery["test_metrics"][recovery_best]
    lines = [
        "# RazorMind AI ML Evaluation",
        "",
        "## Dataset",
        f"- Records: {dataset['record_count']}",
        f"- Fraud percentage: {dataset['fraud_rate'] * 100:.2f}%",
        f"- Payment failure percentage: {dataset['payment_failure_rate'] * 100:.2f}%",
        f"- Recovery rate on failed payments: {dataset['recovery_rate_on_failures'] * 100:.2f}%",
        "",
        "The dataset is synthetic and generated from merchant, customer, transaction, behavioral, payment failure, and recovery variables. Suspicious signals increase fraud likelihood, but no feature directly reveals `is_fraud`.",
        "",
        "## Feature Description",
        "Features include transaction amount, payment method, timing, customer history, merchant averages, amount deviation, failed attempts, device/IP/country changes, velocity, previous chargebacks/fraud events, checkout duration, retries, subscription status, payment failure context, and recovery history.",
        "",
        "## Methodology",
        "Fraud and recovery models use stratified train/validation/test splits of 70%/15%/15%. Model selection is made on validation data, then reported on held-out test data. Imbalance is handled through model class weighting rather than naive oversampling.",
        "",
        "## Fraud Model Comparison",
    ]
    for name, metrics in fraud["test_metrics"].items():
        lines.extend(
            [
                f"### {name}",
                f"- Precision: {metrics['precision']:.4f}",
                f"- Recall: {metrics['recall']:.4f}",
                f"- F1: {metrics['f1']:.4f}",
                f"- ROC-AUC: {metrics['roc_auc']:.4f}",
                f"- PR-AUC: {metrics['pr_auc']:.4f}",
                f"- False-positive rate: {metrics['false_positive_rate']:.4f}",
                f"- False-negative rate: {metrics['false_negative_rate']:.4f}",
                f"- False-positive cost: {metrics['false_positive_cost']:.2f}",
                f"- False-negative cost: {metrics['false_negative_cost']:.2f}",
            ]
        )
    lines.extend(
        [
            "",
            f"Best fraud model: `{best}` selected by validation total business cost and PR-AUC tie-break.",
            f"Best model held-out total cost: {best_metrics['total_cost']:.2f}",
            "",
            "## Ensemble Comparison",
            f"- Ensemble PR-AUC: {fraud['ensemble_metrics']['pr_auc']:.4f}",
            f"- Ensemble F1: {fraud['ensemble_metrics']['f1']:.4f}",
            f"- Ensemble total cost: {fraud['ensemble_metrics']['total_cost']:.2f}",
            f"- Ensemble improved total cost: {fraud['ensemble_improved_total_cost']}",
            "",
            "## Anomaly Detection",
            "Isolation Forest is used to identify unusual transaction behavior independently from supervised fraud classification.",
            f"- Contamination: {anomaly['contamination']:.4f}",
            f"- Flag rate: {anomaly['flag_rate']:.4f}",
            f"- Fraud rate among flagged transactions: {anomaly['fraud_rate_among_flagged']:.4f}",
            "",
            "## Recovery Model Results",
            f"Best recovery model: `{recovery_best}`.",
            f"- Precision: {recovery_metrics['precision']:.4f}",
            f"- Recall: {recovery_metrics['recall']:.4f}",
            f"- F1: {recovery_metrics['f1']:.4f}",
            f"- ROC-AUC: {recovery_metrics['roc_auc']:.4f}",
            f"- PR-AUC: {recovery_metrics['pr_auc']:.4f}",
            f"- Mean expected recovered value: {recovery_metrics['mean_expected_recovered_value']:.2f}",
            f"- Total expected recovered value: {recovery_metrics['total_expected_recovered_value']:.2f}",
            "",
            "## Limitations",
            "These results are measured on synthetic data, not production Razorpay data. The models demonstrate pipeline behavior and should be recalibrated with real merchant data before any production decisioning.",
            "",
            "## Synthetic-Data Disclaimer",
            "No real customer, merchant, Razorpay, or Supabase data was used.",
        ]
    )
    (DOCS_DIR / "ml_evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> dict:
    dataset = generate_and_save()
    fraud = train_fraud_models()
    anomaly = train_anomaly_detector()
    recovery = train_recovery_models()
    write_report(dataset, fraud, anomaly, recovery)
    return {"dataset": dataset, "fraud": fraud, "anomaly": anomaly, "recovery": recovery}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))

