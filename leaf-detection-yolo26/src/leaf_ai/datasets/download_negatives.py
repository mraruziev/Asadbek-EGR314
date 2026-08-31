"""Add a `Not_a_leaf` class to the classification dataset.

PlantVillage is a closed set: every image is a leaf, so a model trained on it alone has
no way to answer "that is not a leaf". Pointed at a face it must still pick one of the 38
classes, and softmax makes that guess look confident. Training on real negatives gives the
model an explicit escape hatch.

Negatives come from COCO val2017 (public, no account): people, rooms, furniture, food,
street scenes -- the kind of thing a webcam actually sees when no leaf is in front of it.

Images that are mostly foliage are skipped by default, so we do not teach the model that
green plant matter belongs in the reject class.
"""

from __future__ import annotations

import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

from leaf_ai.paths import project_path

COCO_VAL_URL = "http://images.cocodataset.org/zips/val2017.zip"
CLASS_NAME = "Not_a_leaf"


def download(url: str, destination: Path) -> Path:
    if destination.exists():
        print(f"Reusing cached download: {destination}")
        return destination

    destination.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} (about 800 MB)...")
    temporary = destination.with_suffix(destination.suffix + ".part")

    def report(block_count: int, block_size: int, total_size: int) -> None:
        if total_size > 0 and block_count % 500 == 0:
            done = min(block_count * block_size, total_size)
            print(f"  {done / 1e6:.0f} / {total_size / 1e6:.0f} MB", flush=True)

    urllib.request.urlretrieve(url, temporary, reporthook=report)
    temporary.rename(destination)
    return destination


def run(args: argparse.Namespace) -> None:
    import cv2

    from leaf_ai.realtime import vegetation_fraction

    dataset_root = project_path(args.dataset)
    if not (dataset_root / "train").is_dir():
        raise SystemExit(f"Expected a YOLO classification folder at {dataset_root}. Run leaf-download-plantvillage-hf first.")

    archive = download(args.url, project_path(args.cache))

    extract_root = project_path(args.cache).parent / "coco_val2017"
    if not extract_root.exists():
        print(f"Extracting to {extract_root}...")
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extractall(extract_root)

    sources = sorted(extract_root.rglob("*.jpg"))
    if not sources:
        raise SystemExit(f"No images found under {extract_root}")
    print(f"{len(sources)} candidate negatives found")

    train_dir = dataset_root / "train" / CLASS_NAME
    val_dir = dataset_root / "val" / CLASS_NAME
    for directory in (train_dir, val_dir):
        if directory.exists() and args.overwrite:
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)

    wanted_train, wanted_val = args.train_count, args.val_count
    kept_train = kept_val = skipped_green = 0

    for source in sources:
        if kept_train >= wanted_train and kept_val >= wanted_val:
            break
        image = cv2.imread(str(source))
        if image is None:
            continue
        if args.max_vegetation < 1.0 and vegetation_fraction(image) > args.max_vegetation:
            skipped_green += 1
            continue
        if kept_train < wanted_train:
            target = train_dir / f"{kept_train:06d}.jpg"
            kept_train += 1
        else:
            target = val_dir / f"{kept_val:06d}.jpg"
            kept_val += 1
        shutil.copyfile(source, target)

    print(f"Wrote {kept_train} train and {kept_val} val negatives as class '{CLASS_NAME}'")
    print(f"Skipped {skipped_green} mostly-foliage images so the reject class stays non-plant")
    print(f"Retrain with: leaf-train classify --data {args.dataset} --epochs 8 --batch 64 --device mps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Add a Not_a_leaf background class from COCO images.")
    parser.add_argument("--dataset", default="data/processed/plantvillage_cls", help="Classification folder to extend.")
    parser.add_argument("--url", default=COCO_VAL_URL)
    parser.add_argument("--cache", default="data/raw/coco_val2017.zip")
    parser.add_argument("--train-count", type=int, default=2500)
    parser.add_argument("--val-count", type=int, default=600)
    parser.add_argument(
        "--max-vegetation",
        type=float,
        default=0.35,
        help="Skip candidate negatives greener than this so foliage is not labelled as background.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
