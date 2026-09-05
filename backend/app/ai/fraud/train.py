from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from app.ai.features import FRAUD_FEATURES, build_preprocessor
from app.ai.fraud.ensemble import average_probabilities
from app.ai.fraud.evaluate import evaluate_classifier
from app.ai.model_io import save_metadata, save_model_bundle
from app.ai.paths import DOCS_DIR, PROCESSED_DATA_DIR, ensure_project_dirs


def _model_candidates(scale_pos_weight: float) -> dict:
    return {
        "xgboost": XGBClassifier(
            n_estimators=120,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            n_jobs=2,
        ),
        "lightgbm": LGBMClassifier(
            n_estimators=160,
            learning_rate=0.06,
            num_leaves=31,
            class_weight="balanced",
            random_state=42,
            n_jobs=2,
            verbosity=-1,
        ),
        "catboost": CatBoostClassifier(
            iterations=140,
            depth=5,
            learning_rate=0.08,
            loss_function="Logloss",
            auto_class_weights="Balanced",
            random_seed=42,
            verbose=False,
            allow_writing_files=False,
        ),
    }


def train_fraud_models(
    dataset_path=None,
    false_positive_cost: float = 50.0,
    false_negative_cost: float = 500.0,
) -> dict:
    ensure_project_dirs()
    path = dataset_path or PROCESSED_DATA_DIR / "transactions.csv"
    data = pd.read_csv(path)
    x = data[FRAUD_FEATURES]
    y = data["is_fraud"]
    x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.3, stratify=y, random_state=42)
    x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))

    trained = {}
    validation = {}
    test_metrics = {}

    for name, model in _model_candidates(scale_pos_weight).items():
        pipeline = Pipeline([("preprocessor", build_preprocessor(FRAUD_FEATURES)), ("model", model)])
        pipeline.fit(x_train, y_train)
        val_prob = pipeline.predict_proba(x_val)[:, 1]
        validation[name] = evaluate_classifier(y_val, val_prob, false_positive_cost=false_positive_cost, false_negative_cost=false_negative_cost)
        test_prob = pipeline.predict_proba(x_test)[:, 1]
        test_metrics[name] = evaluate_classifier(y_test, test_prob, false_positive_cost=false_positive_cost, false_negative_cost=false_negative_cost)
        trained[name] = pipeline

    best_name = min(validation, key=lambda item: (validation[item]["total_cost"], -validation[item]["pr_auc"]))
    ensemble_prob = average_probabilities([trained[name].predict_proba(x_test)[:, 1] for name in trained])
    ensemble_metrics = evaluate_classifier(
        y_test,
        ensemble_prob,
        false_positive_cost=false_positive_cost,
        false_negative_cost=false_negative_cost,
    )

    version = datetime.now(timezone.utc).strftime("fraud-%Y%m%d%H%M%S")
    selected_bundle = {"model": trained[best_name], "features": FRAUD_FEATURES, "version": version, "model_name": best_name}
    save_model_bundle("fraud_model.joblib", selected_bundle)
    metadata = {
        "version": version,
        "selected_model": best_name,
        "record_count": int(len(data)),
        "fraud_rate": float(y.mean()),
        "false_positive_cost_assumption": false_positive_cost,
        "false_negative_cost_assumption": false_negative_cost,
        "validation_metrics": validation,
        "test_metrics": test_metrics,
        "ensemble_metrics": ensemble_metrics,
        "ensemble_improved_total_cost": bool(ensemble_metrics["total_cost"] < test_metrics[best_name]["total_cost"]),
    }
    save_metadata("fraud_metadata.json", metadata)
    (DOCS_DIR / "fraud_evaluation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(train_fraud_models(), indent=2))

