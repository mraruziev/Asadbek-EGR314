"""Download PlantVillage from the Hugging Face Hub into a YOLO classification layout.

This is the credential-free alternative to `leaf-download-plantvillage`, which needs a
Kaggle account. The Hub copy is public, so no API key is required.

Output layout (what `yolo classify` expects):

    <out>/train/<Class_Name>/000123.jpg
    <out>/val/<Class_Name>/000456.jpg
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from leaf_ai.paths import project_path

DEFAULT_REPO = "GVJahnavi/PlantVillage_dataset"


def _label_names(repo_id: str) -> list[str]:
    """Read class names out of the dataset card's feature metadata."""
    from huggingface_hub import HfApi

    info = HfApi().dataset_info(repo_id)
    card = info.cardData or {}
    for entry in card.get("dataset_info", []) if isinstance(card.get("dataset_info"), list) else [card.get("dataset_info")]:
        if not entry:
            continue
        for feature in entry.get("features", []):
            if feature.get("name") in {"label", "labels"}:
                dtype = feature.get("dtype")
                holder = dtype if isinstance(dtype, dict) else feature
                names = (holder.get("class_label") or {}).get("names")
                if isinstance(names, dict):
                    return [names[key] for key in sorted(names, key=int)]
                if isinstance(names, list):
                    return list(names)
    raise SystemExit(f"Could not read class names from {repo_id}. Pass --labels-json instead.")


def _safe_dir_name(label: str) -> str:
    cleaned = label.replace(",", "").replace("(", "").replace(")", "")
    for bad in " /\\":
        cleaned = cleaned.replace(bad, "_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def _write_split(parquet_paths: list[Path], split_dir: Path, names: list[str], limit_per_class: int | None) -> int:
    import pyarrow.parquet as pq

    written = 0
    per_class: dict[int, int] = {}
    for parquet_path in parquet_paths:
        parquet_file = pq.ParquetFile(parquet_path)
        for batch in parquet_file.iter_batches(batch_size=256, columns=["image", "label"]):
            images = batch.column("image").to_pylist()
            labels = batch.column("label").to_pylist()
            for image, label in zip(images, labels):
                if image is None or label is None:
                    continue
                count = per_class.get(label, 0)
                if limit_per_class is not None and count >= limit_per_class:
                    continue
                payload = image.get("bytes") if isinstance(image, dict) else image
                if not payload:
                    continue
                class_dir = split_dir / _safe_dir_name(names[label])
                class_dir.mkdir(parents=True, exist_ok=True)
                (class_dir / f"{count:06d}.jpg").write_bytes(payload)
                per_class[label] = count + 1
                written += 1
    return written


def run(args: argparse.Namespace) -> None:
    from huggingface_hub import snapshot_download

    out_dir = project_path(args.out)
    if out_dir.exists():
        if not args.overwrite:
            raise SystemExit(f"{out_dir} already exists. Pass --overwrite to rebuild it.")
        shutil.rmtree(out_dir)

    names = json.loads(Path(args.labels_json).read_text()) if args.labels_json else _label_names(args.repo)
    print(f"{len(names)} classes from {args.repo}")

    print("Downloading parquet shards (about 850 MB on first run, cached afterwards)...")
    local_repo = Path(
        snapshot_download(repo_id=args.repo, repo_type="dataset", allow_patterns=["data/*.parquet"])
    )

    shards = sorted(local_repo.glob("data/*.parquet"))
    train_shards = [p for p in shards if "train" in p.name]
    val_shards = [p for p in shards if "train" not in p.name]
    if not val_shards:  # dataset ships a single split; hold out the last shard
        val_shards = train_shards[-1:]
        train_shards = train_shards[:-1]

    print(f"Extracting {len(train_shards)} train shard(s) and {len(val_shards)} val shard(s) to {out_dir}")
    n_train = _write_split(train_shards, out_dir / "train", names, args.limit_per_class)
    n_val = _write_split(val_shards, out_dir / "val", names, args.limit_per_class)
    print(f"Wrote {n_train} train images and {n_val} val images to {out_dir}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download PlantVillage from Hugging Face into a YOLO classification folder.")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Hugging Face dataset repo id.")
    parser.add_argument("--out", default="data/processed/plantvillage_cls")
    parser.add_argument("--labels-json", help="Optional JSON file with an ordered list of class names.")
    parser.add_argument("--limit-per-class", type=int, help="Cap images per class for a quick smoke-test build.")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
