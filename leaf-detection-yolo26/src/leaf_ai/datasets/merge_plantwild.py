"""Merge PlantWild (in-the-wild photos) into the PlantVillage classification folder.

PlantVillage is studio data: one detached leaf, plain background, even light. A classifier
trained on it alone rejects real field photographs outright. PlantWild is the same
diseases photographed in the field, so merging the two teaches the model that a leaf on a
plant, against clutter, is still a leaf.

Two joins happen here:

* 21 PlantWild classes are the same disease as an existing PlantVillage class. Their
  images go straight into that class, which is what fixes field photos for those diseases.
* The remaining classes are new crops and diseases and become new classes.

PlantWild contains no healthy categories, so merging it alone would teach the model that
any field photo is diseased. PlantDoc's plain "<crop> leaf" boxes are healthy leaves
photographed in the field, so those crops are added to the matching healthy classes.

PlantWild v2 is CC-BY-NC-ND-4.0: non-commercial, no derivatives.
"""

from __future__ import annotations

import argparse
import random
import zipfile
from pathlib import Path

from leaf_ai.paths import project_path

# PlantWild class -> existing PlantVillage class.
ALIASES: dict[str, str] = {
    "apple black rot": "Apple_Black_rot",
    "apple rust": "Apple_Cedar_apple_rust",
    "apple scab": "Apple_Apple_scab",
    "bell pepper bacterial spot": "Pepper_bell_Bacterial_spot",
    "cherry powdery mildew": "Cherry_including_sour_Powdery_mildew",
    "citrus greening disease": "Orange_Haunglongbing_Citrus_greening",
    "corn gray leaf spot": "Corn_maize_Cercospora_leaf_spot_Gray_leaf_spot",
    "corn northern leaf blight": "Corn_maize_Northern_Leaf_Blight",
    "corn rust": "Corn_maize_Common_rust",
    "grape black rot": "Grape_Black_rot",
    "potato early blight": "Potato_Early_blight",
    "potato late blight": "Potato_Late_blight",
    "squash powdery mildew": "Squash_Powdery_mildew",
    "strawberry leaf scorch": "Strawberry_Leaf_scorch",
    "tomato bacterial leaf spot": "Tomato_Bacterial_spot",
    "tomato early blight": "Tomato_Early_blight",
    "tomato late blight": "Tomato_Late_blight",
    "tomato leaf mold": "Tomato_Leaf_Mold",
    "tomato mosaic virus": "Tomato_Tomato_mosaic_virus",
    "tomato septoria leaf spot": "Tomato_Septoria_leaf_spot",
    "tomato yellow leaf curl virus": "Tomato_Tomato_Yellow_Leaf_Curl_Virus",
}

# PlantDoc "<crop> leaf" (healthy) -> PlantVillage healthy class.
HEALTHY_FROM_PLANTDOC: dict[str, str] = {
    "Apple leaf": "Apple_healthy",
    "Bell_pepper leaf": "Pepper_bell_healthy",
    "Blueberry leaf": "Blueberry_healthy",
    "Cherry leaf": "Cherry_including_sour_healthy",
    "Corn leaf": "Corn_maize_healthy",
    "Grape leaf": "Grape_healthy",
    "Peach leaf": "Peach_healthy",
    "Potato leaf": "Potato_healthy",
    "Raspberry leaf": "Raspberry_healthy",
    "Soyabean leaf": "Soybean_healthy",
    "Squash leaf": "Squash_healthy",
    "Strawberry leaf": "Strawberry_healthy",
    "Tomato leaf": "Tomato_healthy",
}


def normalise(plantwild_class: str) -> str:
    return "_".join(plantwild_class.split()).capitalize()


def merge_plantwild(archive: Path, dataset: Path, min_images: int, val_fraction: float, seed: int) -> dict:
    counts: dict[str, list[str]] = {}
    with zipfile.ZipFile(archive) as zf:
        for name in zf.namelist():
            if name.endswith("/") or name.count("/") < 2:
                continue
            counts.setdefault(name.split("/")[1], []).append(name)

        rng = random.Random(seed)
        stats = {"merged_into_existing": 0, "new_classes": 0, "images": 0, "skipped_small": 0}
        for plantwild_class, members in sorted(counts.items()):
            if len(members) < min_images:
                stats["skipped_small"] += 1
                continue

            target = ALIASES.get(plantwild_class)
            if target:
                stats["merged_into_existing"] += 1
            else:
                target = normalise(plantwild_class)
                stats["new_classes"] += 1

            members = sorted(members)
            rng.shuffle(members)
            split_at = max(int(len(members) * val_fraction), 1)
            for index, member in enumerate(members):
                split = "val" if index < split_at else "train"
                out_dir = dataset / split / target
                out_dir.mkdir(parents=True, exist_ok=True)
                (out_dir / f"pw_{Path(member).stem}.jpg").write_bytes(zf.read(member))
                stats["images"] += 1
    return stats


def merge_plantdoc_healthy(plantdoc_root: Path, dataset: Path, val_fraction: float, seed: int) -> dict:
    import cv2

    yaml_path = plantdoc_root / "data.yaml"
    if not yaml_path.exists():
        return {"images": 0, "note": "PlantDoc not built; run leaf-download-plantdoc-hf"}

    names: dict[int, str] = {}
    for line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and ": " in stripped:
            index, label = stripped.split(": ", 1)
            names[int(index)] = label.strip()

    rng = random.Random(seed)
    stats = {"images": 0}
    for split_dir in ("train", "val"):
        image_dir = plantdoc_root / "images" / split_dir
        label_dir = plantdoc_root / "labels" / split_dir
        if not image_dir.is_dir():
            continue
        for image_path in sorted(image_dir.glob("*.jpg")):
            label_path = label_dir / f"{image_path.stem}.txt"
            if not label_path.exists():
                continue
            image = cv2.imread(str(image_path))
            if image is None:
                continue
            height, width = image.shape[:2]
            for line_index, line in enumerate(label_path.read_text(encoding="utf-8").splitlines()):
                if not line.strip():
                    continue
                parts = line.split()
                target = HEALTHY_FROM_PLANTDOC.get(names.get(int(parts[0]), ""))
                if not target:
                    continue
                cx, cy, bw, bh = (float(v) for v in parts[1:5])
                left = max(int((cx - bw / 2) * width), 0)
                top = max(int((cy - bh / 2) * height), 0)
                right = min(int((cx + bw / 2) * width), width)
                bottom = min(int((cy + bh / 2) * height), height)
                crop = image[top:bottom, left:right]
                if crop.size == 0 or crop.shape[0] < 32 or crop.shape[1] < 32:
                    continue
                split = "val" if rng.random() < val_fraction else "train"
                out_dir = dataset / split / target
                out_dir.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(out_dir / f"pd_{split_dir}_{image_path.stem}_{line_index}.jpg"), crop)
                stats["images"] += 1
    return stats


def run(args: argparse.Namespace) -> None:
    dataset = project_path(args.dataset)
    if not (dataset / "train").is_dir():
        raise SystemExit(f"Expected a classification folder at {dataset}. Run leaf-download-plantvillage-hf first.")

    before = len([d for d in (dataset / "train").iterdir() if d.is_dir()])

    print("Merging PlantWild ...")
    pw = merge_plantwild(project_path(args.archive), dataset, args.min_images, args.val_fraction, args.seed)
    print(
        f"  {pw['images']} images: {pw['merged_into_existing']} classes merged into existing, "
        f"{pw['new_classes']} new classes, {pw['skipped_small']} skipped as too small"
    )

    if not args.no_plantdoc_healthy:
        print("Adding PlantDoc healthy-leaf crops ...")
        pd = merge_plantdoc_healthy(project_path(args.plantdoc), dataset, args.val_fraction, args.seed)
        print(f"  {pd['images']} in-the-wild healthy leaf crops{' -- ' + pd['note'] if pd.get('note') else ''}")

    after = len([d for d in (dataset / "train").iterdir() if d.is_dir()])
    total = sum(1 for _ in (dataset / "train").rglob("*.jpg"))
    print(f"\nClasses: {before} -> {after}")
    print(f"Train images now: {total}")
    print(f"\nRetrain with:\n  leaf-train classify --data {args.dataset} --epochs 8 --batch 64 --device mps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge PlantWild in-the-wild images into the classification dataset.")
    parser.add_argument("--dataset", default="data/processed/plantvillage_cls")
    parser.add_argument("--archive", default="data/raw/plantwild/plantwild_v2.zip")
    parser.add_argument("--plantdoc", default="data/raw/plantdoc_hf")
    parser.add_argument("--min-images", type=int, default=40, help="Skip PlantWild classes smaller than this.")
    parser.add_argument("--val-fraction", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--no-plantdoc-healthy", action="store_true", help="Skip the healthy in-the-wild crops.")
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
