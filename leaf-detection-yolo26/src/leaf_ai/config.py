from __future__ import annotations

from pathlib import Path
from typing import Any


def _parse_scalar(value: str) -> Any:
    normalized = value.strip()
    lowered = normalized.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return int(normalized)
    except ValueError:
        pass
    try:
        return float(normalized)
    except ValueError:
        return normalized.strip("'\"")


def _load_flat_yaml(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        if ":" not in line:
            raise ValueError(f"Unsupported YAML line {line_number} in {path}: {raw_line}")
        key, value = line.split(":", 1)
        data[key.strip()] = _parse_scalar(value)
    return data


def load_yaml(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    try:
        import yaml
    except ModuleNotFoundError:
        data = _load_flat_yaml(config_path)
    else:
        with config_path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a mapping: {config_path}")
    return data


def drop_none_values(config: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in config.items() if value is not None}


def merge_overrides(base: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged
