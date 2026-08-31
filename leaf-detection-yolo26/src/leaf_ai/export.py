from __future__ import annotations

import argparse
import json

from leaf_ai.paths import project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a trained YOLO26 model.")
    parser.add_argument("--model", required=True, help="Path to best.pt or another YOLO checkpoint.")
    parser.add_argument("--format", default="onnx", help="onnx, engine, openvino, torchscript, tflite, etc.")
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", help="CUDA device, 'cpu', or omitted for auto.")
    parser.add_argument("--half", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--int8", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--dynamic", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_args = {
        "format": args.format,
        "imgsz": args.imgsz,
        "device": args.device,
        "half": args.half,
        "int8": args.int8,
        "dynamic": args.dynamic,
    }
    export_args = {key: value for key, value in export_args.items() if value is not None}
    model_path = project_path(args.model)
    print(json.dumps({"model": str(model_path), **export_args}, indent=2))
    if args.dry_run:
        return

    from ultralytics import YOLO

    model = YOLO(str(model_path))
    output = model.export(**export_args)
    print(output)


if __name__ == "__main__":
    main()
