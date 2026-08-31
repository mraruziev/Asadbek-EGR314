from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from leaf_ai.config import drop_none_values, load_yaml, merge_overrides
from leaf_ai.paths import project_path


DETECT_DEFAULTS: dict[str, Any] = {
    "model": "yolo26n.pt",
    "data": "data/raw/plantdoc/data.yaml",
    "epochs": 100,
    "imgsz": 640,
    "batch": -1,
    "patience": 20,
    "project": "runs/detect",
    "name": "plantdoc_yolo26n",
    "cache": False,
    "workers": 4,
}

CLASSIFY_DEFAULTS: dict[str, Any] = {
    "model": "yolo26n-cls.pt",
    "data": "data/processed/plantvillage_cls",
    "epochs": 50,
    "imgsz": 224,
    "batch": -1,
    "patience": 10,
    "project": "runs/classify",
    "name": "plantvillage_yolo26n_cls",
    "cache": False,
    "workers": 4,
}


def resolve_training_paths(config: dict[str, Any]) -> dict[str, Any]:
    resolved = dict(config)
    if "data" in resolved:
        data_path = project_path(str(resolved["data"]))
        resolved["data"] = str(data_path)
    if "project" in resolved:
        resolved["project"] = str(project_path(str(resolved["project"])))
    return resolved


def run_training(task: str, config: dict[str, Any], dry_run: bool) -> None:
    resolved = resolve_training_paths(config)
    print(json.dumps(resolved, indent=2, default=str))
    if dry_run:
        return

    from ultralytics import YOLO

    model = YOLO(str(resolved.pop("model")))
    results = model.train(task=task, **drop_none_values(resolved))
    print(results)


def add_common_training_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="YAML config to load before CLI overrides.")
    parser.add_argument("--model", help="YOLO model checkpoint or YAML.")
    parser.add_argument("--data", help="YOLO data.yaml for detect or folder root for classify.")
    parser.add_argument("--epochs", type=int)
    parser.add_argument("--imgsz", type=int)
    parser.add_argument("--batch", type=int)
    parser.add_argument("--patience", type=int)
    parser.add_argument("--device", help="CUDA device, comma list, 'cpu', or omitted for auto.")
    parser.add_argument("--project", help="Ultralytics output project directory.")
    parser.add_argument("--name", help="Ultralytics run name.")
    parser.add_argument("--cache", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--workers", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")


def config_from_args(args: argparse.Namespace, defaults: dict[str, Any]) -> dict[str, Any]:
    config = dict(defaults)
    if args.config:
        config = merge_overrides(config, load_yaml(project_path(args.config)))
    overrides = {
        "model": args.model,
        "data": args.data,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "patience": args.patience,
        "device": args.device,
        "project": args.project,
        "name": args.name,
        "cache": args.cache,
        "workers": args.workers,
        "resume": args.resume or None,
    }
    return merge_overrides(config, overrides)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train YOLO26 leaf detection/classification models.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect", help="Train a YOLO26 detector.")
    add_common_training_args(detect)

    classify = subparsers.add_parser("classify", help="Train a YOLO26 classifier.")
    add_common_training_args(classify)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "detect":
        config = config_from_args(args, DETECT_DEFAULTS)
        run_training("detect", config, args.dry_run)
        return
    if args.command == "classify":
        config = config_from_args(args, CLASSIFY_DEFAULTS)
        run_training("classify", config, args.dry_run)
        return
    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
