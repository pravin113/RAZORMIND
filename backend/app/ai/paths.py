from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_DIR / "models"
DOCS_DIR = PROJECT_DIR / "docs"


def ensure_project_dirs() -> None:
    for path in (RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, DOCS_DIR):
        path.mkdir(parents=True, exist_ok=True)
