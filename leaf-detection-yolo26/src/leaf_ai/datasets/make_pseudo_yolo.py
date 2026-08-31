from __future__ import annotations

import argparse
import json
from pathlib import Path

from tqdm import tqdm

from leaf_ai.datasets.common import clear_directory, iter_images, link_or_copy_file
from leaf_ai.paths import PROCESSED_DATA_ROOT, project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a YOLO classification folder dataset into weak YOLO detection labels. "
            "Each image receives one centered full-image box. Use for baseline experiments only."
        )
    )
    parser.add_argument("--source", default=str(PROCESSED_DATA_ROOT / "plantvillage_cls"))
    parser.add_argument("--out", default=str(PROCESSED_DATA_ROOT / "plantvillage_pseudo_yolo"))
    parser.add_argument("--link-mode", choices=["hardlink", "symlink", "copy"], default="hardlink")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = project_path(args.source)
    output = project_path(args.out)
    if args.overwrite:
        clear_directory(output)
    else:
        output.mkdir(parents=True, exist_ok=True)

    split_dirs = [split for split in ("train", "val", "test") if (source / split).exists()]
    class_names = sorted({class_dir.name for split in split_dirs for class_dir in (source / split).iterdir() if class_dir.is_dir()})
    class_ids = {name: index for index, name in enumerate(class_names)}
    counts = {split: 0 for split in split_dirs}

    for split in split_dirs:
        for class_dir in sorted((source / split).iterdir()):
            if not class_dir.is_dir():
                continue
            class_id = class_ids[class_dir.name]
            for image_path in tqdm(list(iter_images(class_dir)), desc=f"{split}/{class_dir.name}", leave=False):
                relative_stem = Path(class_dir.name) / image_path.stem
                image_destination = output / "images" / split / class_dir.name / image_path.name
                label_destination = output / "labels" / split / f"{relative_stem}.txt"
                link_or_copy_file(image_path, image_destination, args.link_mode)
                label_destination.parent.mkdir(parents=True, exist_ok=True)
                label_destination.write_text(f"{class_id} 0.5 0.5 1.0 1.0\n", encoding="utf-8")
                counts[split] += 1

    yaml_lines = [
        f"path: {output.as_posix()}",
        "train: images/train",
        "val: images/val",
        "test: images/test" if "test" in split_dirs else "",
        "names:",
    ]
    yaml_lines.extend(f"  {index}: {name}" for name, index in class_ids.items())
    (output / "data.yaml").write_text("\n".join(line for line in yaml_lines if line) + "\n", encoding="utf-8")

    manifest = {"source": str(source), "output": str(output), "classes": class_names, "splits": counts}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    print("Warning: pseudo boxes are weak labels. Prefer true bounding boxes for detector training.")


if __name__ == "__main__":
    main()
