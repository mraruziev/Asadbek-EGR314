"""Analyse still photos instead of a live camera.

Upload a photo, get a diagnosis, a confidence score, and what to do about it. This is the
same model the webcam preview uses, but a photo can be framed properly, which usually
beats holding a leaf in front of a laptop.

    leaf-analyze photo.jpg
    leaf-analyze photos/ --out reports/ --json report.json

When a detector checkpoint exists the image is searched for leaves first and each one is
diagnosed separately, so a cluttered field photo works. Without a detector the whole image
is classified as one leaf.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from leaf_ai.advice import DISCLAIMER, advice_for
from leaf_ai.paths import project_path
from leaf_ai.realtime import describe, is_healthy, is_reject, vegetation_fraction

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
URGENCY_MARK = {"urgent": "!!", "routine": "->", "none": "ok"}


def gather_images(inputs: list[str]) -> list[Path]:
    found: list[Path] = []
    for raw in inputs:
        path = Path(raw).expanduser()
        if path.is_dir():
            found.extend(sorted(p for p in path.rglob("*") if p.suffix.lower() in IMAGE_SUFFIXES))
        elif path.suffix.lower() in IMAGE_SUFFIXES:
            found.append(path)
        else:
            print(f"Skipping {path}: not an image")
    return found


def classify(model, image, imgsz: int, device: str | None, topk: int) -> list[tuple[str, float]]:
    result = model.predict(image, imgsz=imgsz, device=device, verbose=False)[0]
    if result.probs is None:
        return []
    indices = result.probs.top5[:topk]
    confidences = result.probs.top5conf.tolist()[:topk]
    return [(result.names[int(i)], float(c)) for i, c in zip(indices, confidences)]


def analyse_image(path: Path, classifier, detector, args) -> dict:
    import cv2

    image = cv2.imread(str(path))
    if image is None:
        return {"image": str(path), "error": "could not be read"}

    regions: list[dict] = []

    if detector is not None:
        result = detector.predict(image, imgsz=args.imgsz, conf=args.conf, device=args.device, verbose=False)[0]
        boxes = result.boxes if result.boxes is not None else []
        for box in boxes:
            left, top, right, bottom = (int(v) for v in box.xyxy[0].tolist())
            crop = image[max(top, 0) : bottom, max(left, 0) : right]
            if crop.size == 0:
                continue
            predictions = classify(classifier, crop, args.cls_imgsz, args.device, args.topk)
            if predictions:
                regions.append(
                    {
                        "box": [left, top, right, bottom],
                        "detector_label": result.names[int(box.cls[0])],
                        "detector_confidence": float(box.conf[0]),
                        "predictions": predictions,
                    }
                )

    if not regions:
        # No detector, or it found nothing: treat the whole photo as one leaf.
        predictions = classify(classifier, image, args.cls_imgsz, args.device, args.topk)
        if predictions:
            height, width = image.shape[:2]
            regions.append({"box": [0, 0, width, height], "predictions": predictions, "whole_image": True})

    for region in regions:
        label, score = region["predictions"][0]
        guidance = advice_for(label)
        region["diagnosis"] = describe(label)
        region["raw_label"] = label
        region["confidence"] = score
        region["healthy"] = is_healthy(label)
        region["is_leaf"] = not is_reject(label)
        region["cause"] = guidance.cause
        region["urgency"] = guidance.urgency
        region["actions"] = list(guidance.actions)

    return {
        "image": str(path),
        "vegetation": round(vegetation_fraction(image), 3),
        "regions": regions,
    }


def annotate(path: Path, report: dict, out_dir: Path) -> Path | None:
    import cv2

    image = cv2.imread(str(path))
    if image is None:
        return None
    for region in report.get("regions", []):
        left, top, right, bottom = region["box"]
        if region.get("whole_image"):
            continue
        colour = (0, 255, 0) if region["healthy"] else (0, 0, 255)
        if not region["is_leaf"]:
            colour = (140, 140, 140)
        cv2.rectangle(image, (left, top), (right, bottom), colour, 2)
        text = f"{region['diagnosis']} {region['confidence']:.0%}"
        cv2.putText(image, text, (left + 3, max(top - 6, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2, cv2.LINE_AA)

    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"{path.stem}_diagnosed{path.suffix}"
    cv2.imwrite(str(target), image)
    return target


def print_report(report: dict) -> None:
    print("\n" + "=" * 72)
    print(Path(report["image"]).name)
    if "error" in report:
        print(f"  {report['error']}")
        return

    regions = report.get("regions", [])
    if not regions:
        print("  Nothing to diagnose.")
        return

    for index, region in enumerate(regions, start=1):
        header = "Whole image" if region.get("whole_image") else f"Leaf {index} at {region['box']}"
        mark = URGENCY_MARK.get(region["urgency"], "->")
        print(f"\n  [{mark}] {header}")
        print(f"       Diagnosis  : {region['diagnosis']}")
        print(f"       Confidence : {region['confidence']:.1%}")
        others = [f"{describe(l)} {s:.1%}" for l, s in region["predictions"][1:] if s >= 0.01]
        if others:
            print(f"       Also        : {', '.join(others)}")
        print(f"       Cause      : {region['cause']}")
        for action in region["actions"]:
            print(f"        - {action}")


def run(args: argparse.Namespace) -> None:
    from ultralytics import YOLO

    images = gather_images(args.images)
    if not images:
        raise SystemExit("No images found.")

    classifier = YOLO(str(project_path(args.classifier)))
    detector = YOLO(str(project_path(args.detector))) if args.detector else None
    print(f"Classifier: {args.classifier} ({len(classifier.names)} classes)")
    print(f"Detector  : {args.detector or 'none (whole-image mode)'}")
    print(f"Analysing {len(images)} image(s)")

    reports = []
    for path in images:
        report = analyse_image(path, classifier, detector, args)
        if args.out:
            saved = annotate(path, report, project_path(args.out))
            if saved:
                report["annotated"] = str(saved)
        reports.append(report)
        print_report(report)
        if report.get("annotated"):
            print(f"\n       Annotated  : {report['annotated']}")

    urgent = sum(1 for r in reports for region in r.get("regions", []) if region.get("urgency") == "urgent")
    diseased = sum(
        1 for r in reports for region in r.get("regions", []) if region.get("is_leaf") and not region.get("healthy")
    )
    print("\n" + "=" * 72)
    print(f"{len(reports)} image(s): {diseased} diseased finding(s), {urgent} needing urgent action")
    print(DISCLAIMER)

    if args.json:
        target = project_path(args.json)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(reports, indent=2), encoding="utf-8")
        print(f"JSON written to {target}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose plant disease from uploaded photos.")
    parser.add_argument("images", nargs="+", help="Image files or directories.")
    parser.add_argument("--classifier", help="Classification checkpoint. Defaults to the newest finished run.")
    parser.add_argument("--detector", help="Optional detection checkpoint for locating leaves.")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--cls-imgsz", type=int, default=224)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--topk", type=int, default=4)
    parser.add_argument("--device", help="'mps', a CUDA index, 'cpu', or omitted for auto.")
    parser.add_argument("--out", help="Directory for annotated copies.")
    parser.add_argument("--json", help="Write the full report as JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.classifier or not args.device:
        import sys

        sys.path.insert(0, str(project_path(".")))
        from webcam import default_device, newest_weights

        args.classifier = args.classifier or str(newest_weights("classify"))
        args.device = args.device or default_device()
        if args.detector is None:
            detector = newest_weights("detect", optional=True)
            args.detector = str(detector) if detector else None
    run(args)


if __name__ == "__main__":
    main()
