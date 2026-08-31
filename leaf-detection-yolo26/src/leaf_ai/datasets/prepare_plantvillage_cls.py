from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

from leaf_ai.datasets.common import IMAGE_EXTENSIONS, clear_directory, iter_images, link_or_copy_file, safe_class_name
from leaf_ai.paths import PROCESSED_DATA_ROOT, RAW_DATA_ROOT, project_path


def discover_class_dirs(source: Path) -> list[Path]:
    candidates = []
    for path in source.rglob("*"):
        if path.is_dir() and any(child.suffix.lower() in IMAGE_EXTENSIONS for child in path.iterdir() if child.is_file()):
            candidates.append(path)
    return sorted(candidates)


def split_items(items: list[Path], val_ratio: float, test_ratio: float, seed: int) -> dict[str, list[Path]]:
    if val_ratio < 0 or test_ratio < 0 or val_ratio + test_ratio >= 1:
        raise ValueError("val_ratio and test_ratio must be non-negative and sum to less than 1")

    shuffled = list(items)
    random.Random(seed).shuffle(shuffled)
    total = len(shuffled)
    test_count = int(round(total * test_ratio))
    val_count = int(round(total * val_ratio))
    train_count = total - val_count - test_count
    return {
        "train": shuffled[:train_count],
        "val": shuffled[train_count : train_count + val_count],
        "test": shuffled[train_count + val_count :],
    }


def prepare_dataset(
    source: Path,
    output: Path,
    val_ratio: float,
    test_ratio: float,
    seed: int,
    link_mode: str,
    overwrite: bool,
) -> dict[str, object]:
    if overwrite:
        clear_directory(output)
    else:
        output.mkdir(parents=True, exist_ok=True)

    class_dirs = discover_class_dirs(source)
    if not class_dirs:
        raise SystemExit(f"No class folders with images found under {source}")

    manifest: dict[str, object] = {
        "source": str(source),
        "output": str(output),
        "splits": {"train": 0, "val": 0, "test": 0},
        "classes": {},
    }
    class_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"train": 0, "val": 0, "test": 0})

    for class_dir in class_dirs:
        class_name = safe_class_name(class_dir.name)
        images = sorted(iter_images(class_dir))
        split_map = split_items(images, val_ratio, test_ratio, seed)
        for split, split_images in split_map.items():
            for image_path in tqdm(split_images, desc=f"{split}/{class_name}", leave=False):
                destination = output / split / class_name / image_path.name
                link_or_copy_file(image_path, destination, link_mode)
                class_counts[class_name][split] += 1
                manifest["splits"][split] += 1

    manifest["classes"] = dict(sorted(class_counts.items()))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare PlantVillage for YOLO classification training.")
    parser.add_argument("--source", default=str(RAW_DATA_ROOT / "plantvillage"))
    parser.add_argument("--out", default=str(PROCESSED_DATA_ROOT / "plantvillage_cls"))
    parser.add_argument("--val", type=float, default=0.15)
    parser.add_argument("--test", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--link-mode", choices=["hardlink", "symlink", "copy"], default="hardlink")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = prepare_dataset(
        source=project_path(args.source),
        output=project_path(args.out),
        val_ratio=args.val,
        test_ratio=args.test,
        seed=args.seed,
        link_mode=args.link_mode,
        overwrite=args.overwrite,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
