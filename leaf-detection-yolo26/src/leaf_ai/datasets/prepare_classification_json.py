from __future__ import annotations

import argparse
import csv
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from tqdm import tqdm

from leaf_ai.datasets.common import clear_directory, link_or_copy_file, safe_class_name
from leaf_ai.paths import PROCESSED_DATA_ROOT, project_path


def load_class_map(path: Path | None) -> dict[str, str]:
    if not path:
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {str(key): safe_class_name(str(value)) for key, value in data.items()}
    if isinstance(data, list):
        return {str(index): safe_class_name(str(value)) for index, value in enumerate(data)}
    raise ValueError("Class map must be a JSON object or list")


def load_records(path: Path, image_field: str, class_field: str) -> list[dict[str, str]]:
    if path.suffix.lower() == ".json":
        payload: Any = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("annotations") or payload.get("data") or payload.get("items")
        if not isinstance(payload, list):
            raise ValueError("JSON annotations must be a list or contain annotations/data/items list")
        return [
            {"image": str(item[image_field]), "class": str(item[class_field])}
            for item in payload
        ]

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            {"image": row[image_field], "class": row[class_field]}
            for row in reader
        ]


def split_records(records: list[dict[str, str]], val_ratio: float, test_ratio: float, seed: int) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for record in records:
        grouped[record["class"]].append(record)

    splits = {"train": [], "val": [], "test": []}
    rng = random.Random(seed)
    for class_records in grouped.values():
        rng.shuffle(class_records)
        total = len(class_records)
        test_count = int(round(total * test_ratio))
        val_count = int(round(total * val_ratio))
        train_count = total - val_count - test_count
        splits["train"].extend(class_records[:train_count])
        splits["val"].extend(class_records[train_count : train_count + val_count])
        splits["test"].extend(class_records[train_count + val_count :])
    return splits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare classification folders from JSON/CSV annotations.")
    parser.add_argument("--images", required=True, help="Directory containing source images.")
    parser.add_argument("--annotations", required=True, help="JSON or CSV labels.")
    parser.add_argument("--out", default=str(PROCESSED_DATA_ROOT / "json_cls"))
    parser.add_argument("--image-field", default="image_id")
    parser.add_argument("--class-field", default="disease_class")
    parser.add_argument("--class-map", help="Optional JSON class-id to class-name map.")
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--link-mode", choices=["hardlink", "symlink", "copy"], default="hardlink")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    images_dir = project_path(args.images)
    annotations_path = project_path(args.annotations)
    output_dir = project_path(args.out)
    class_map = load_class_map(project_path(args.class_map) if args.class_map else None)

    if args.overwrite:
        clear_directory(output_dir)
    else:
        output_dir.mkdir(parents=True, exist_ok=True)

    records = load_records(annotations_path, args.image_field, args.class_field)
    splits = split_records(records, args.val, args.test, args.seed)
    manifest = {"source_images": str(images_dir), "annotations": str(annotations_path), "splits": {}, "classes": {}}
    class_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})

    for split, split_records_list in splits.items():
        manifest["splits"][split] = len(split_records_list)
        for record in tqdm(split_records_list, desc=split):
            class_name = class_map.get(record["class"], f"class_{safe_class_name(record['class'])}")
            image_path = images_dir / record["image"]
            if not image_path.exists():
                image_path = next(images_dir.rglob(record["image"]), None)
            if image_path is None or not image_path.exists():
                raise FileNotFoundError(f"Image not found: {record['image']}")
            destination = output_dir / split / class_name / image_path.name
            link_or_copy_file(image_path, destination, args.link_mode)
            class_counts[class_name][split] += 1

    manifest["classes"] = dict(sorted(class_counts.items()))
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
