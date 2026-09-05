from __future__ import annotations

import json
from pathlib import Path

from app.ai.features import load_artifact, save_artifact
from app.ai.paths import MODELS_DIR, ensure_project_dirs


def artifact_path(name: str) -> Path:
    ensure_project_dirs()
    return MODELS_DIR / name


def save_model_bundle(name: str, bundle: dict) -> Path:
    path = artifact_path(name)
    save_artifact(bundle, path)
    return path


def load_model_bundle(name: str) -> dict:
    return load_artifact(artifact_path(name))


def save_metadata(name: str, metadata: dict) -> Path:
    path = artifact_path(name)
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return path


def load_metadata(name: str) -> dict:
    path = artifact_path(name)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))

