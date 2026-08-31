from __future__ import annotations

import argparse
import time
from collections import deque
from pathlib import Path

from leaf_ai.paths import project_path


def parse_source(raw_source: str) -> int | str:
    return int(raw_source) if raw_source.isdigit() else raw_source


# The 14 crop species PlantVillage covers, longest prefix first so "Corn_maize" wins over
# a bare "Corn". Categories are culinary, which is what a user reading the overlay expects:
# tomato, pepper and squash are botanically fruits but nobody shops for them that way.
_SPECIES: tuple[tuple[str, str, str], ...] = (
    # PlantVillage (14 crops)
    ("Cherry_including_sour", "Cherry", "fruit"),
    ("Corn_maize", "Corn (maize)", "grain"),
    ("Pepper_bell", "Bell pepper", "vegetable"),
    ("Blueberry", "Blueberry", "fruit"),
    ("Raspberry", "Raspberry", "fruit"),
    ("Strawberry", "Strawberry", "fruit"),
    ("Soybean", "Soybean", "legume"),
    ("Potato", "Potato", "vegetable"),
    ("Squash", "Squash", "vegetable"),
    ("Tomato", "Tomato", "vegetable"),
    ("Orange", "Orange", "fruit"),
    ("Apple", "Apple", "fruit"),
    ("Grape", "Grape", "fruit"),
    ("Peach", "Peach", "fruit"),
    # PlantWild adds these in-the-wild crops
    ("Bell_pepper", "Bell pepper", "vegetable"),
    ("Grapevine", "Grape", "fruit"),
    ("Cauliflower", "Cauliflower", "vegetable"),
    ("Broccoli", "Broccoli", "vegetable"),
    ("Cucumber", "Cucumber", "vegetable"),
    ("Eggplant", "Eggplant", "vegetable"),
    ("Zucchini", "Zucchini", "vegetable"),
    ("Cabbage", "Cabbage", "vegetable"),
    ("Lettuce", "Lettuce", "vegetable"),
    ("Tobacco", "Tobacco", "crop"),
    ("Banana", "Banana", "fruit"),
    ("Carrot", "Carrot", "vegetable"),
    ("Celery", "Celery", "vegetable"),
    ("Citrus", "Citrus", "fruit"),
    ("Coffee", "Coffee", "crop"),
    ("Garlic", "Garlic", "vegetable"),
    ("Ginger", "Ginger", "root"),
    ("Basil", "Basil", "herb"),
    ("Wheat", "Wheat", "grain"),
    ("Maple", "Maple", "tree"),
    ("Rice", "Rice", "grain"),
    ("Bean", "Bean", "legume"),
    ("Plum", "Plum", "fruit"),
)

# Longest prefix first, so "Corn_maize" wins over "Corn" and "Bell_pepper" over "Bean".
SPECIES: tuple[tuple[str, str, str], ...] = tuple(
    sorted(_SPECIES, key=lambda entry: len(entry[0]), reverse=True)
)

REJECT_CLASS = "Not_a_leaf"


def split_label(raw_label: str) -> tuple[str, str, str]:
    """Split a class name into (species, kind, disease).

    Handles both the upstream PlantVillage form (`Tomato___Late_blight`) and the flattened
    form this repo's downloader writes (`Tomato_Late_blight`). Returns an empty species
    when the label is the reject class or an unknown name.
    """
    normalised = raw_label.replace("___", "_").replace("__", "_")
    if normalised == REJECT_CLASS:
        return "", "", ""
    for prefix, display_name, kind in SPECIES:
        if normalised == prefix or normalised.startswith(prefix + "_"):
            remainder = normalised[len(prefix) :].strip("_")
            disease = "" if remainder.lower() == "healthy" else remainder.replace("_", " ")
            return display_name, kind, disease
    return normalised.replace("_", " "), "", ""


def describe(raw_label: str) -> str:
    """Overlay text for one prediction."""
    if raw_label.replace("___", "_").replace("__", "_") == REJECT_CLASS:
        return "not a leaf"
    species, kind, disease = split_label(raw_label)
    if not species:
        return raw_label.replace("_", " ")
    if disease:
        return f"{species}: {disease}"
    return f"Healthy {species} - {kind}" if kind else f"Healthy {species}"


def pretty_label(raw_label: str) -> str:
    """Turn 'Tomato___Late_blight' into 'Tomato - Late blight'."""
    plant, _, disease = raw_label.partition("___")
    if not disease:
        plant, _, disease = raw_label.partition("__")
    if not disease:
        return raw_label.replace("_", " ").strip()
    return f"{plant.replace('_', ' ').strip()} - {disease.replace('_', ' ').strip()}"


def is_healthy(raw_label: str) -> bool:
    if raw_label.replace("___", "_").replace("__", "_") == REJECT_CLASS:
        return False
    return raw_label.lower().endswith("healthy")


def is_reject(raw_label: str) -> bool:
    return raw_label.replace("___", "_").replace("__", "_") == REJECT_CLASS


def draw_text_box(frame, text: str, left: int, top: int, color=(255, 255, 255), scale: float = 0.5) -> None:
    import cv2

    font = cv2.FONT_HERSHEY_SIMPLEX
    thickness = 1 if scale < 0.8 else 2
    (width, height), baseline = cv2.getTextSize(text, font, scale, thickness)
    y = max(top - height - baseline - 6, 0)
    cv2.rectangle(frame, (left, y), (left + width + 6, y + height + baseline + 6), (0, 0, 0), -1)
    cv2.putText(frame, text, (left + 3, y + height + 3), font, scale, color, thickness, cv2.LINE_AA)


def format_score(score: float) -> str:
    """Percentages that do not lie. A 0.4% runner-up is not '0%', it is negligible."""
    if score >= 0.005:
        return f"{score:.0%}"
    return "<1%"


def draw_bar(frame, x: int, y: int, width: int, height: int, fraction: float, colour) -> None:
    """A small filled confidence bar. Easier to read at a glance than a percentage."""
    import cv2

    cv2.rectangle(frame, (x, y), (x + width, y + height), (60, 60, 60), -1)
    filled = int(width * min(max(fraction, 0.0), 1.0))
    if filled > 0:
        cv2.rectangle(frame, (x, y), (x + filled, y + height), colour, -1)


def draw_ranking(frame, predictions, left: int, top: int, colour) -> None:
    """Top-k ranking with confidence bars, drawn as a block starting at (left, top)."""
    import cv2

    font = cv2.FONT_HERSHEY_SIMPLEX
    line_height = 20
    bar_width = 90
    rows = [(describe(label), score) for label, score in predictions]
    if not rows:
        return
    text_width = max(cv2.getTextSize(text, font, 0.45, 1)[0][0] for text, _ in rows)
    block_width = bar_width + 12 + text_width + 52
    block_height = line_height * len(rows) + 8

    overlay = frame.copy()
    cv2.rectangle(overlay, (left, top), (left + block_width, top + block_height), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    for index, (text, score) in enumerate(rows):
        y = top + 6 + index * line_height
        row_colour = colour if index == 0 else (170, 170, 170)
        draw_bar(frame, left + 6, y + 4, bar_width, 9, score, row_colour)
        cv2.putText(frame, f"{score:5.1%}", (left + bar_width + 12, y + 13), font, 0.45, row_colour, 1, cv2.LINE_AA)
        cv2.putText(frame, text, (left + bar_width + 60, y + 13), font, 0.45, row_colour, 1, cv2.LINE_AA)


def draw_info_panel(frame, lines: list[str], left: int = 8, spacing: int = 22) -> None:
    """Draw lines bottom-left, stacked upward so they always fit inside the frame."""
    if not lines:
        return
    bottom_y = frame.shape[0] - 6
    first_y = bottom_y - (len(lines) - 1) * spacing
    for index, line in enumerate(lines):
        draw_text_box(frame, line, left, first_y + index * spacing, (180, 180, 180))


def center_square(frame, fraction: float = 0.8):
    """Return the centre crop the classifier looks at, plus its box in frame coords."""
    height, width = frame.shape[:2]
    side = int(min(height, width) * fraction)
    left = (width - side) // 2
    top = (height - side) // 2
    return frame[top : top + side, left : left + side], (left, top, left + side, top + side)


def vegetation_fraction(crop) -> float:
    """Fraction of pixels that look like plant matter, via the excess-green index.

    ExG = 2G - R - B on channel-normalised pixels. Foliage has more green than red or
    blue and scores positive; skin, wood, walls and most indoor clutter have more red
    than green and score negative. This is what stops the classifier from confidently
    calling a human face a peach leaf: the model itself cannot abstain, so we decide
    whether it is worth asking.
    """
    import numpy as np

    if crop is None or crop.size == 0:
        return 0.0
    pixels = crop.astype(np.float32)
    blue, green, red = pixels[:, :, 0], pixels[:, :, 1], pixels[:, :, 2]
    total = red + green + blue + 1e-6
    excess_green = (2.0 * green - red - blue) / total
    return float((excess_green > 0.05).mean())


def identify_object(identifier, crop, imgsz: int, device: str | None) -> tuple[str, float] | None:
    """Name whatever non-plant thing is in the crop, using a general COCO detector.

    "not a leaf" alone is a dead end for the user -- it does not say whether the model saw
    a face, a phone, or nothing at all. This runs only on rejected frames, so it costs
    nothing in the normal path.
    """
    if identifier is None or crop is None or crop.size == 0:
        return None
    result = identifier.predict(crop, imgsz=imgsz, device=device, verbose=False)[0]
    if result.boxes is None or len(result.boxes) == 0:
        return None
    best = max(result.boxes, key=lambda box: float(box.conf[0]))
    return result.names[int(best.cls[0])], float(best.conf[0])


def classify_crop(classifier, crop, cls_imgsz: int, device: str | None, topk: int = 1):
    """Return a list of (raw_label, confidence) ordered best first."""
    if crop is None or crop.size == 0:
        return []
    result = classifier.predict(crop, imgsz=cls_imgsz, device=device, verbose=False)[0]
    if result.probs is None:
        return []
    indices = result.probs.top5[:topk]
    confidences = result.probs.top5conf.tolist()[:topk]
    return [(result.names[int(i)], float(c)) for i, c in zip(indices, confidences)]


def open_writer(path: Path | None, fps: float, width: int, height: int):
    if path is None:
        return None

    import cv2

    path.parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(str(path), fourcc, fps or 30.0, (width, height))


def run(args: argparse.Namespace) -> None:
    import cv2
    from ultralytics import YOLO

    if not args.detector and not args.classifier:
        raise SystemExit("Pass --classifier (disease labels), --detector (leaf boxes), or both.")

    detector = YOLO(str(project_path(args.detector))) if args.detector else None
    classifier = YOLO(str(project_path(args.classifier))) if args.classifier else None
    identifier = YOLO(args.identifier) if args.identify else None
    if identifier:
        print(f"Identifier: {args.identifier} (names non-leaf objects)")
    if detector:
        print(f"Detector: {args.detector}")
    if classifier:
        print(f"Classifier: {args.classifier} ({len(classifier.names)} classes)")

    capture = cv2.VideoCapture(parse_source(args.source))
    if not capture.isOpened():
        raise SystemExit(
            f"Could not open video source: {args.source}\n"
            "On macOS this usually means camera access is denied. Grant it in\n"
            "System Settings > Privacy & Security > Camera for the app running this script."
        )

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1280
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 720
    fps = float(capture.get(cv2.CAP_PROP_FPS)) or 30.0
    writer = open_writer(project_path(args.save) if args.save else None, fps, width, height)

    frame_count = 0
    last_time = time.perf_counter()
    rolling_fps = 0.0
    history: deque[tuple[str, float]] = deque(maxlen=max(args.smooth, 1))
    crop_fraction = args.crop_fraction
    gate_enabled = args.min_leaf > 0
    honour_reject = not args.ignore_reject
    show_help = True

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if args.flip:
                frame = cv2.flip(frame, 1)

            if detector:
                result = detector.predict(
                    frame,
                    imgsz=args.imgsz,
                    conf=args.conf,
                    iou=args.iou,
                    device=args.device,
                    verbose=False,
                )[0]
                annotated = result.plot()

                if classifier and result.boxes is not None:
                    for box in result.boxes:
                        left, top, right, bottom = [int(value) for value in box.xyxy[0].tolist()]
                        crop = frame[max(top, 0) : max(bottom, 0), max(left, 0) : max(right, 0)]
                        predictions = classify_crop(crop=crop, classifier=classifier, cls_imgsz=args.cls_imgsz, device=args.device)
                        if predictions:
                            label, score = predictions[0]
                            colour = (0, 255, 0) if is_healthy(label) else (0, 0, 255)
                            draw_text_box(annotated, f"{describe(label)} {score:.2f}", left, top, colour)
            else:
                # Classifier-only: read the centre of the frame. Fill it with one leaf.
                annotated = frame.copy()
                crop, (left, top, right, bottom) = center_square(frame, crop_fraction)

                greenness = vegetation_fraction(crop)
                gate_open = (not gate_enabled) or greenness >= args.min_leaf
                # Ask for top-5 so a usable plant guess survives even when the reject class
                # takes almost all the probability mass.
                predictions = (
                    classify_crop(classifier, crop, args.cls_imgsz, args.device, topk=max(args.topk, 5))
                    if gate_open
                    else []
                )
                if not honour_reject:
                    predictions = [pair for pair in predictions if not is_reject(pair[0])]

                best_label, best_score, note = "", 0.0, ""
                if predictions:
                    history.append(predictions[0])
                    votes: dict[str, float] = {}
                    for label, score in history:
                        votes[label] = votes.get(label, 0.0) + score
                    best_label = max(votes, key=votes.get)
                    best_score = votes[best_label] / len(history)
                    runner_up = predictions[1][1] if len(predictions) > 1 else 0.0
                    if args.min_margin > 0 and predictions[0][1] - runner_up < args.min_margin:
                        note = "close call"
                else:
                    history.clear()

                # Headline: plant name and disease, or what the thing actually is.
                if best_label and is_reject(best_label):
                    named = identify_object(identifier, crop, args.imgsz, args.device)
                    if named:
                        headline = f"not a leaf - {named[0]}  {named[1]:.0%}"
                    else:
                        headline = f"not a leaf  {best_score:.0%}"
                    colour = (140, 140, 140)
                elif best_label:
                    colour = (0, 255, 0) if is_healthy(best_label) else (0, 0, 255)
                    headline = f"{describe(best_label)}  {best_score:.0%}"
                    if best_score < args.conf:
                        headline = f"unsure: {headline}"
                        colour = (200, 200, 200)
                    elif note:
                        headline = f"{headline}  ({note})"
                else:
                    named = identify_object(identifier, crop, args.imgsz, args.device) if not gate_open else None
                    if named:
                        headline = f"no leaf in view - {named[0]}  {named[1]:.0%}"
                    else:
                        headline = f"no leaf in view  (veg {greenness:.2f} < {args.min_leaf:.2f})"
                    colour = (140, 140, 140)

                cv2.rectangle(annotated, (left, top), (right, bottom), colour, 2)
                draw_text_box(annotated, headline, left, top - 4, colour, scale=0.9)

                # Runner-up guesses, always listed so a wrong top answer is still readable.
                plant_guesses = [pair for pair in predictions if not is_reject(pair[0])]
                if best_label and not is_reject(best_label):
                    plant_guesses = plant_guesses[1:]
                others = [pair for pair in plant_guesses[: args.topk] if pair[1] >= args.min_alternative]
                if not others and plant_guesses:
                    # Reject took all the mass; still name the closest plant match.
                    others = plant_guesses[:1]
                panel = [
                    f"veg {greenness:.2f}   crop {crop_fraction:.0%}   "
                    f"gate {'on' if gate_enabled else 'OFF'}   "
                    f"reject {'on' if honour_reject else 'OFF'}   classes {len(classifier.names)}"
                ]
                if show_help:
                    panel.append("keys:  + -  crop    g  gate    r  reject class    h  hide    q  quit")
                if others:
                    panel.append("closest plant match:" if best_label and is_reject(best_label) else "also might be:")
                    panel.extend(f"  {describe(label)}  {format_score(score)}" for label, score in others)
                elif predictions:
                    panel.append("no other plausible match")
                draw_info_panel(annotated, panel)

            frame_count += 1
            now = time.perf_counter()
            elapsed = now - last_time
            if elapsed >= 0.5:
                rolling_fps = frame_count / elapsed
                frame_count = 0
                last_time = now
            draw_text_box(annotated, f"FPS {rolling_fps:.1f}  |  q to quit", 8, 28)

            if writer:
                writer.write(annotated)

            if args.view:
                cv2.imshow("leaf-ai-yolo26", annotated)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key in (ord("+"), ord("=")):
                    crop_fraction = min(crop_fraction + 0.05, 1.0)
                elif key in (ord("-"), ord("_")):
                    crop_fraction = max(crop_fraction - 0.05, 0.2)
                elif key == ord("g"):
                    gate_enabled = not gate_enabled
                elif key == ord("r"):
                    honour_reject = not honour_reject
                elif key == ord("h"):
                    show_help = not show_help
    finally:
        capture.release()
        if writer:
            writer.release()
        if args.view:
            cv2.destroyAllWindows()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Realtime YOLO26 leaf detection and plant disease classification.")
    parser.add_argument("--detector", help="Optional YOLO detection checkpoint for leaf bounding boxes.")
    parser.add_argument("--classifier", help="YOLO classification checkpoint for plant disease labels.")
    parser.add_argument("--source", default="0", help="Camera index, video path, RTSP URL, or stream URL.")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--cls-imgsz", type=int, default=224)
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--iou", type=float, default=0.5)
    parser.add_argument("--topk", type=int, default=4, help="Classifier-only mode: how many guesses to show.")
    parser.add_argument(
        "--min-alternative",
        type=float,
        default=0.01,
        help="Hide runner-up guesses below this probability. They are rounding noise, not alternatives.",
    )
    parser.add_argument("--smooth", type=int, default=5, help="Classifier-only mode: frames to average over.")
    parser.add_argument("--crop-fraction", type=float, default=0.8, help="Classifier-only mode: size of the centre crop.")
    parser.add_argument(
        "--min-leaf",
        type=float,
        default=0.05,
        help="Minimum fraction of plant-like pixels before the classifier is trusted. 0 disables the gate.",
    )
    parser.add_argument(
        "--min-margin",
        type=float,
        default=0.0,
        help="Flag the top guess as a close call when the runner-up is within this gap. 0 disables.",
    )
    parser.add_argument("--flip", action=argparse.BooleanOptionalAction, default=True, help="Mirror the webcam image.")
    parser.add_argument(
        "--identify",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Name non-leaf objects with a general COCO model instead of only saying 'not a leaf'.",
    )
    parser.add_argument("--identifier", default="yolo26n.pt", help="Model used to name non-leaf objects.")
    parser.add_argument(
        "--ignore-reject",
        action="store_true",
        help="Never report 'not a leaf' -- always show the best plant class. Toggle live with r.",
    )
    parser.add_argument("--device", help="'mps' on Apple Silicon, a CUDA index, 'cpu', or omitted for auto.")
    parser.add_argument("--save", help="Optional MP4 output path.")
    parser.add_argument("--view", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def main() -> None:
    run(parse_args())


if __name__ == "__main__":
    main()
