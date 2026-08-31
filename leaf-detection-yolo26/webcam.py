#!/usr/bin/env python3
"""Run plant disease detection on your webcam.

    python webcam.py

Holds no arguments by design: it picks the newest trained classifier under runs/,
turns on the Apple GPU when available, and opens the camera preview. Press q to quit.

For anything non-default use the full CLI instead:

    leaf-realtime --classifier runs/classify/<run>/weights/best.pt --source 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from leaf_ai.realtime import run  # noqa: E402


def is_finished(run_dir: Path) -> bool:
    """True when the run completed every epoch it was configured for.

    A run still in progress already has a best.pt on disk, and picking it silently gives
    you a half-trained model -- which looks like a bug in the app, not an unfinished job.
    """
    results = run_dir / "results.csv"
    args_file = run_dir / "args.yaml"
    if not results.exists() or not args_file.exists():
        return False
    planned = 0
    for line in args_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("epochs:"):
            planned = int(line.split(":", 1)[1].strip())
            break
    completed = max(len(results.read_text(encoding="utf-8").strip().splitlines()) - 1, 0)
    return planned > 0 and completed >= planned


def newest_weights(task_dir: str, optional: bool = False) -> Path | None:
    """Newest finished checkpoint for a task.

    `optional` is for the detector: an unfinished detector is worse than none at all,
    because its presence silently switches the app out of centre-crop mode and then finds
    nothing. The classifier is required, so there we fall back with a warning.
    """
    candidates = sorted(
        (PROJECT_ROOT / "runs" / task_dir).glob("*/weights/best.pt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    finished = [p for p in candidates if is_finished(p.parent.parent)]
    if finished:
        return finished[0]
    if optional:
        if candidates:
            print(f"Ignoring in-progress {candidates[0].parent.parent.name} under runs/{task_dir}/ until it finishes.")
        return None
    if candidates:
        print(
            f"Warning: no finished run under runs/{task_dir}/. "
            f"Using the in-progress {candidates[0].parent.parent.name}, which is not fully trained."
        )
    return candidates[0] if candidates else None


def default_device() -> str:
    try:
        import torch
    except ModuleNotFoundError:
        return "cpu"
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "0"
    return "cpu"


def main() -> None:
    parser = argparse.ArgumentParser(description="Webcam plant disease detection with sensible defaults.")
    parser.add_argument("--source", default="0", help="Camera index or video file.")
    parser.add_argument("--classifier", help="Override the auto-picked disease classifier.")
    parser.add_argument("--detector", help="Optional leaf detector checkpoint.")
    parser.add_argument("--save", help="Optional MP4 output path.")
    cli = parser.parse_args()

    classifier = cli.classifier or newest_weights("classify")
    if classifier is None:
        raise SystemExit(
            "No trained classifier found under runs/classify/.\n"
            "Train one first:\n"
            "  leaf-download-plantvillage-hf --out data/processed/plantvillage_cls\n"
            "  leaf-train classify --config configs/training/classify_plantvillage.yaml --batch 64 --device mps"
        )

    detector = cli.detector or newest_weights("detect", optional=True)

    args = argparse.Namespace(
        detector=str(detector) if detector else None,
        classifier=str(classifier),
        source=cli.source,
        imgsz=640,
        cls_imgsz=224,
        conf=0.25,
        iou=0.5,
        topk=4,
        min_alternative=0.01,
        smooth=5,
        crop_fraction=0.8,
        min_leaf=0.05,
        identify=True,
        identifier="yolo26n.pt",
        ignore_reject=False,
        min_margin=0.0,
        flip=True,
        device=default_device(),
        save=cli.save,
        view=True,
    )
    print(f"Device: {args.device}")
    run(args)


if __name__ == "__main__":
    main()
