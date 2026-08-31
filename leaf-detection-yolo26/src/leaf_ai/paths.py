from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data"
RAW_DATA_ROOT = DATA_ROOT / "raw"
PROCESSED_DATA_ROOT = DATA_ROOT / "processed"
MODELS_ROOT = PROJECT_ROOT / "models"
EXPORTS_ROOT = PROJECT_ROOT / "exports"


def project_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return PROJECT_ROOT / candidate


def ensure_parent(path: str | Path) -> Path:
    target = project_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    return target
