from __future__ import annotations

import argparse
import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

from dotenv import load_dotenv

from leaf_ai.paths import RAW_DATA_ROOT, project_path


def _extract_zip(zip_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(output_dir)


def _download_url(url: str, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / "plantdoc_export.zip"
    urllib.request.urlretrieve(url, zip_path)
    _extract_zip(zip_path, output_dir)
    return output_dir


def _copy_zip(zip_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    local_zip = output_dir / zip_path.name
    if zip_path.resolve() != local_zip.resolve():
        shutil.copy2(zip_path, local_zip)
    _extract_zip(local_zip, output_dir)
    return output_dir


def _download_roboflow(args: argparse.Namespace, output_dir: Path) -> Path:
    from roboflow import Roboflow

    api_key = args.api_key or os.getenv("ROBOFLOW_API_KEY")
    if not api_key:
        raise SystemExit(
            "Missing Roboflow API key. Set ROBOFLOW_API_KEY or pass --api-key. "
            "If the public export gives you a direct zip URL, use --url instead."
        )

    workspace = args.workspace or os.getenv("ROBOFLOW_WORKSPACE", "plantdoc")
    project = args.project or os.getenv("ROBOFLOW_PROJECT", "plantdoc")
    version = int(args.version or os.getenv("ROBOFLOW_VERSION", "1"))
    export_format = args.format or os.getenv("ROBOFLOW_FORMAT", "yolov8")

    output_dir.mkdir(parents=True, exist_ok=True)
    rf = Roboflow(api_key=api_key)
    dataset = rf.workspace(workspace).project(project).version(version).download(
        export_format,
        location=str(output_dir),
    )
    return Path(dataset.location)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download or import PlantDoc from Roboflow.")
    parser.add_argument("--out", default=str(RAW_DATA_ROOT / "plantdoc"), help="Output directory.")
    parser.add_argument("--url", help="Direct Roboflow export zip URL.")
    parser.add_argument("--zip", dest="zip_path", help="Local Roboflow export zip.")
    parser.add_argument("--api-key", help="Roboflow API key.")
    parser.add_argument("--workspace", help="Roboflow workspace slug.")
    parser.add_argument("--project", help="Roboflow project slug.")
    parser.add_argument("--version", help="Roboflow dataset version.")
    parser.add_argument("--format", default=None, help="Roboflow export format, usually yolov8.")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    output_dir = project_path(args.out)

    if args.url:
        location = _download_url(args.url, output_dir)
    elif args.zip_path:
        location = _copy_zip(project_path(args.zip_path), output_dir)
    else:
        location = _download_roboflow(args, output_dir)

    print(f"PlantDoc ready at: {location}")
    data_yaml = location / "data.yaml"
    if data_yaml.exists():
        print(f"YOLO data config: {data_yaml}")
    else:
        print("No data.yaml found. Export PlantDoc in YOLOv8/YOLO format or validate the extracted layout.")


if __name__ == "__main__":
    main()
