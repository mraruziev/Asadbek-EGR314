from __future__ import annotations

import argparse
import json
from pathlib import Path

from leaf_ai.datasets.common import IMAGE_EXTENSIONS
from leaf_ai.paths import project_path


def relative_stem(root: Path, path: Path) -> str:
    return path.relative_to(root).with_suffix("").as_posix()


def image_map(images_root: Path) -> dict[str, Path]:
    return {
        relative_stem(images_root, path): path
        for path in images_root.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    }


def split_roots(dataset_root: Path, split: str) -> tuple[Path, Path] | None:
    yolo_root_images = dataset_root / "images" / split
    yolo_root_labels = dataset_root / "labels" / split
    if yolo_root_images.exists() or yolo_root_labels.exists():
        return yolo_root_images, yolo_root_labels

    roboflow_split = "valid" if split == "val" and (dataset_root / "valid").exists() else split
    roboflow_images = dataset_root / roboflow_split / "images"
    roboflow_labels = dataset_root / roboflow_split / "labels"
    if roboflow_images.exists() or roboflow_labels.exists():
        return roboflow_images, roboflow_labels

    return None


def validate_split(dataset_root: Path, split: str) -> dict[str, int]:
    roots = split_roots(dataset_root, split)
    if roots is None:
        return {
            "images": 0,
            "labels": 0,
            "missing_labels": 0,
            "orphan_labels": 0,
            "empty_labels": 0,
        }
    images_root, labels_root = roots
    images = image_map(images_root) if images_root.exists() else {}
    labels = {relative_stem(labels_root, path): path for path in labels_root.rglob("*.txt")} if labels_root.exists() else {}
    missing_labels = sorted(set(images) - set(labels))
    orphan_labels = sorted(set(labels) - set(images))
    empty_labels = [stem for stem, path in labels.items() if path.stat().st_size == 0]

    return {
        "images": len(images),
        "labels": len(labels),
        "missing_labels": len(missing_labels),
        "orphan_labels": len(orphan_labels),
        "empty_labels": len(empty_labels),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a YOLO detection dataset layout.")
    parser.add_argument("--dataset", required=True, help="Dataset root containing images/ and labels/.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_root = project_path(args.dataset)
    report = {
        "dataset": str(dataset_root),
        "data_yaml_exists": (dataset_root / "data.yaml").exists(),
        "splits": {},
    }
    for split in ("train", "val", "test"):
        if split_roots(dataset_root, split) is not None:
            report["splits"][split] = validate_split(dataset_root, split)

    if args.json:
        print(json.dumps(report, indent=2))
        return

    print(f"Dataset: {report['dataset']}")
    print(f"data.yaml: {'yes' if report['data_yaml_exists'] else 'no'}")
    for split, stats in report["splits"].items():
        print(
            f"{split}: images={stats['images']} labels={stats['labels']} "
            f"missing_labels={stats['missing_labels']} orphan_labels={stats['orphan_labels']} "
            f"empty_labels={stats['empty_labels']}"
        )


if __name__ == "__main__":
    main()
