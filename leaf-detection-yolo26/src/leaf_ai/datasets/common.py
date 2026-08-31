from __future__ import annotations

import os
import re
import shutil
from collections.abc import Iterable
from pathlib import Path


IMAGE_EXTENSIONS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def iter_images(root: str | Path) -> Iterable[Path]:
    root_path = Path(root)
    for path in root_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            yield path


def safe_class_name(raw_name: str) -> str:
    name = raw_name.strip().replace("___", "_").replace("__", "_")
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("._-")
    return name or "unknown"


def link_or_copy_file(source: Path, destination: Path, mode: str = "hardlink") -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        return

    if mode == "copy":
        shutil.copy2(source, destination)
        return

    if mode == "symlink":
        try:
            destination.symlink_to(source)
            return
        except OSError:
            shutil.copy2(source, destination)
            return

    if mode == "hardlink":
        try:
            os.link(source, destination)
            return
        except OSError:
            shutil.copy2(source, destination)
            return

    raise ValueError(f"Unsupported link mode: {mode}")


def clear_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
