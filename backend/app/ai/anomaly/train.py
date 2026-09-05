from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.pipeline import Pipeline

from app.ai.features import ANOMALY_FEATURES, build_preprocessor
from app.ai.model_io import save_metadata, save_model_bundle
from app.ai.paths import DOCS_DIR, PROCESSED_DATA_DIR, ensure_project_dirs


def train_anomaly_detector(dataset_path=None) -> dict:
    ensure_project_dirs()
    data = pd.read_csv(dataset_path or PROCESSED_DATA_DIR / "transactions.csv")
    contamination = max(0.01, min(0.08, float(data["is_fraud"].mean() * 1.5)))
    pipeline = Pipeline(
        [
            ("preprocessor", build_preprocessor(ANOMALY_FEATURES, scale_numeric=True)),
            ("model", IsolationForest(n_estimators=160, contamination=contamination, random_state=42, n_jobs=2)),
        ]
    )
    pipeline.fit(data[ANOMALY_FEATURES])
    raw_scores = -pipeline.decision_function(data[ANOMALY_FEATURES])
    threshold = float(pd.Series(raw_scores).quantile(1 - contamination))
    flags = (raw_scores >= threshold).astype(int)
    version = datetime.now(timezone.utc).strftime("anomaly-%Y%m%d%H%M%S")
    metadata = {
        "version": version,
        "record_count": int(len(data)),
        "contamination": contamination,
        "score_threshold": threshold,
        "flag_rate": float(flags.mean()),
        "fraud_rate_among_flagged": float(data.loc[flags == 1, "is_fraud"].mean()) if flags.sum() else 0.0,
        "note": "Isolation Forest detects unusual behavior independently from fraud classification.",
    }
    save_model_bundle("anomaly_model.joblib", {"model": pipeline, "features": ANOMALY_FEATURES, "version": version, "threshold": threshold})
    save_metadata("anomaly_metadata.json", metadata)
    (DOCS_DIR / "anomaly_evaluation.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    print(json.dumps(train_anomaly_detector(), indent=2))

