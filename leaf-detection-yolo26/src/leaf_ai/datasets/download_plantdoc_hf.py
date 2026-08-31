"""Download PlantDoc from the Hugging Face Hub into YOLO detection format.

This is the credential-free alternative to `leaf-download-plantdoc`, which needs a
Roboflow API key. The Hub copy carries the same bounding boxes.

PlantDoc matters because it is *field* photography: leaves on plants, cluttered
backgrounds, real lighting. A classifier trained only on PlantVillage rejects scenes like
that outright. With a detector the pipeline locates each leaf first and classifies the
crop, which is what makes a real-world photo work at all.

Output layout:

    <out>/images/train/000001.jpg
    <out>/labels/train/000001.txt      # class cx cy w h, all normalised
    <out>/data.yaml
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from leaf_ai.paths import project_path

DEFAULT_REPO = "agyaatcoder/PlantDoc"


def _shards(repo_id: str) -> tuple[list[Path], list[Path]]:
    from huggingface_hub import snapshot_download

    local_repo = Path(snapshot_download(repo_id=repo_id, repo_type="dataset", allow_patterns=["data/*.parquet"]))
    shards = sorted(local_repo.glob("data/*.parquet"))
    train = [p for p in shards if "train" in p.name]
    val = [p for p in shards if "train" not in p.name]
    return train, val or train[-1:]


def _collect_categories(paths: list[Path]) -> list[str]:
    import pyarrow.parquet as pq

    names: set[str] = set()
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(batch_size=256, columns=["objects"]):
            for objects in batch.column("objects").to_pylist():
                if objects:
                    names.update(objects.get("category") or [])
    return sorted(names)


def _write_split(paths: list[Path], out_root: Path, split: str, class_ids: dict[str, int]) -> tuple[int, int]:
    import pyarrow.parquet as pq

    image_dir = out_root / "images" / split
    label_dir = out_root / "labels" / split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)

    written = boxes_written = 0
    for path in paths:
        for batch in pq.ParquetFile(path).iter_batches(
            batch_size=128, columns=["image", "width", "height", "objects"]
        ):
            rows = zip(
                batch.column("image").to_pylist(),
                batch.column("width").to_pylist(),
                batch.column("height").to_pylist(),
                batch.column("objects").to_pylist(),
            )
            for image, width, height, objects in rows:
                payload = image.get("bytes") if isinstance(image, dict) else image
                if not payload or not width or not height or not objects:
                    continue

                lines = []
                for bbox, category in zip(objects.get("bbox") or [], objects.get("category") or []):
                    left, top, box_width, box_height = bbox
                    # COCO gives absolute xywh from the top-left; YOLO wants a normalised centre.
                    centre_x = (left + box_width / 2) / width
                    centre_y = (top + box_height / 2) / height
                    norm_w = box_width / width
                    norm_h = box_height / height
                    if not (0 < norm_w <= 1 and 0 < norm_h <= 1):
                        continue
                    centre_x = min(max(centre_x, 0.0), 1.0)
                    centre_y = min(max(centre_y, 0.0), 1.0)
                    lines.append(f"{class_ids[category]} {centre_x:.6f} {centre_y:.6f} {norm_w:.6f} {norm_h:.6f}")

                if not lines:
                    continue
                stem = f"{written:06d}"
                (image_dir / f"{stem}.jpg").write_bytes(payload)
                (label_dir / f"{stem}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
                written += 1
                boxes_written += len(lines)
    return written, boxes_written


def run(args: argparse.Namespace) -> None:
    out_root = project_path(args.out)
    if out_root.exists():
        if not args.overwrite:
            raise SystemExit(f"{out_root} already exists. Pass --overwrite to rebuild it.")
        shutil.rmtree(out_root)

    print(f"Fetching {args.repo} ...")
    train_shards, val_shards = _shards(args.repo)

    categories = _collect_categories(train_shards + val_shards)
    class_ids = {name: index for index, name in enumerate(categories)}
    print(f"{len(categories)} classes: {', '.join(categories[:6])}{' ...' if len(categories) > 6 else ''}")

    n_train, b_train = _write_split(train_shards, out_root, "train", class_ids)
    n_val, b_val = _write_split(val_shards, out_root, "val", class_ids)

    names_block = "\n".join(f"  {index}: {name}" for index, name in enumerate(categories))
    (out_root / "data.yaml").write_text(
        f"path: {out_root}\ntrain: images/train\nval: images/val\n\nnames:\n{names_block}\n",
        encoding="utf-8",
    )

    print(f"train: {n_train} images / {b_train} boxes")
    print(f"val:   {n_val} images / {b_val} boxes")
    print(f"Wrote {out_root / 'data.yaml'}")
    print(f"\nTrain with:\n  leaf-train detect --data {out_root / 'data.yaml'} --epochs 40 --batch 16 --device mps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download PlantDoc detection data from Hugging Face.")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--out", default="data/raw/plantdoc_hf")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
