from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from app.ai.features import RECOVERY_FEATURES, build_preprocessor
from app.ai.model_io import save_metadata, save_model_bundle
from app.ai.paths import DOCS_DIR, PROCESSED_DATA_DIR, ensure_project_dirs
from app.ai.recovery.evaluate import evaluate_recovery


def train_recovery_models(dataset_path=None) -> dict:
    ensure_project_dirs()
    data = pd.read_csv(dataset_path or PROCESSED_DATA_DIR / "transactions.csv")
    data = data[data["payment_failure"] == 1].copy()
    x = data[RECOVERY_FEATURES]
    y = data["recovered"]
    x_train, x_temp, y_train, y_temp = train_test_split(x, y, test_size=0.3, stratify=y, random_state=42)
    x_val, x_test, y_val, y_test = train_test_split(x_temp, y_temp, test_size=0.5, stratify=y_temp, random_state=42)

    models = {
        "lightgbm": LGBMClassifier(
            n_estimators=150,
            learning_rate=0.06,
            num_leaves=31,
            class_weight="balanced",
            random_state=42,
            n_jobs=2,
            verbosity=-1,
        ),
        "catboost": CatBoostClassifier(
            iterations=130,
            depth=5,
            learning_rate=0.08,
            loss_function="Logloss",
            auto_class_weights="Balanced",
            random_seed=42,
            verbose=False,
            allow_writing_files=False,
        ),
    }
    trained = {}
    validation = {}
    test_metrics = {}

    for name, model in models.items():
        pipeline = Pipeline([("preprocessor", build_preprocessor(RECOVERY_FEATURES)), ("model", model)])
        pipeline.fit(x_train, y_train)
        validation[name] = evaluate_recovery(y_val, pipeline.predict_proba(x_val)[:, 1], x_val["amount"])
        test_metrics[name] = evaluate_recovery(y_test, pipeline.predict_proba(x_test)[:, 1], x_test["amount"])
        trained[name] = pipeline

    best_name = max(validation, key=lambda item: (validation[item]["pr_auc"], validation[item]["f1"]))
    version = datetime.now(timezone.utc).strftime("recovery-%Y%m%d%H%M%S")
    save_model_bundle(
        "recovery_model.joblib",
        {"model": trained[best_name], "features": RECOVERY_FEATURES, "version": version, "model_name": best_name},
    )
    metadata = {
        "version": version,
        "selected_model": best_name,
        "record_count": int(len(data)),
        "recovery_rate_on_failures": float(y.mean()),
        "validation_metrics": validation,
        "test_metrics": test_metrics,
    }
    save_metadata("recovery_metadata.json", metadata)
    (DOCS_DIR / "recovery_evaluation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(train_recovery_models(), indent=2))

