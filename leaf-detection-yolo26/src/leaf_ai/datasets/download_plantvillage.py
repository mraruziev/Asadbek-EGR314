from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv

from leaf_ai.paths import RAW_DATA_ROOT, project_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download PlantVillage from Kaggle.")
    parser.add_argument("--dataset", default=os.getenv("KAGGLE_DATASET", "emmarex/plantdisease"))
    parser.add_argument("--out", default=str(RAW_DATA_ROOT / "plantvillage"))
    parser.add_argument("--keep-zip", action="store_true", help="Keep Kaggle zip after extraction.")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    args = parse_args()
    output_dir = project_path(args.out)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        args.dataset,
        "-p",
        str(output_dir),
        "--unzip",
    ]
    subprocess.run(command, check=True)

    if not args.keep_zip:
        for zip_path in output_dir.glob("*.zip"):
            zip_path.unlink()

    print(f"PlantVillage ready at: {output_dir}")


if __name__ == "__main__":
    main()
