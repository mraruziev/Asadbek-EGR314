# Leaf Detection YOLO26 Subsystem

Python subsystem for realtime leaf detection with Ultralytics YOLO26, PlantDoc object-detection training data, and PlantVillage/Chinese classification data for disease labeling.

## On macOS?

See `docs/macos_quickstart.md`. The commands below are PowerShell and assume CUDA;
the macOS path uses `--device mps`, needs no Kaggle or Roboflow account, and gets you
a working webcam demo with:

```bash
./.venv/bin/leaf-download-plantvillage-hf --out data/processed/plantvillage_cls
./.venv/bin/leaf-train classify --config configs/training/classify_plantvillage.yaml --epochs 8 --batch 64 --device mps
./.venv/bin/python webcam.py
```

## Current Assumptions

- `YOLO26` means the current Ultralytics YOLO26 family, starting with `yolo26n.pt` for realtime detection.
- `PlantDoc` is the primary detector dataset because it has bounding boxes.
- `PlantVillage` is image-level classification data, so it feeds the classifier branch by default. Pseudo-box conversion is available only for baseline experiments.
- The requested Chinese dataset is treated as the AI Challenger 2018 Agricultural Disease dataset unless you specify a different source.
- Claude is not invoked by this repo. `CLAUDE.md` is included so Claude Code can safely pick up context if you run it separately.

## Setup

```powershell
cd C:\Users\abbos\source\leaf-detection-yolo26
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

For GPU training, install the PyTorch build matching your CUDA version before installing `ultralytics`.

## Data Layout

```text
data/
  raw/
    plantdoc/                 # Roboflow YOLO export with data.yaml
    plantvillage/             # Kaggle download
    chinese/                  # Requested dataset when received
  processed/
    plantvillage_cls/         # YOLO classification folder layout
    plantvillage_pseudo_yolo/ # Optional weak detection labels
runs/
  detect/
  classify/
```

## Download PlantDoc

Preferred path is a Roboflow YOLOv8/YOLO export.

```powershell
copy .env.example .env
# Fill ROBOFLOW_API_KEY in .env
leaf-download-plantdoc --out data/raw/plantdoc
leaf-validate-yolo --dataset data/raw/plantdoc
```

If Roboflow gives you a direct export ZIP URL:

```powershell
leaf-download-plantdoc --url "https://..." --out data/raw/plantdoc
```

## Download PlantVillage

Install Kaggle credentials as `%USERPROFILE%\.kaggle\kaggle.json` or set `KAGGLE_USERNAME` and `KAGGLE_KEY`.

```powershell
leaf-download-plantvillage --dataset emmarex/plantdisease --out data/raw/plantvillage
leaf-prepare-plantvillage --source data/raw/plantvillage --out data/processed/plantvillage_cls --overwrite
```

## Train

Detector:

```powershell
leaf-train detect --config configs/training/detect_plantdoc.yaml
```

Classifier:

```powershell
leaf-train classify --config configs/training/classify_plantvillage.yaml
```

Dry-run either command before spending GPU time:

```powershell
leaf-train detect --config configs/training/detect_plantdoc.yaml --dry-run
```

## Realtime Inference

Disease classifier only, no detector weights needed. The classifier reads a centre
crop of the frame, so fill that box with one leaf:

```powershell
leaf-realtime --classifier runs/classify/plantvillage_yolo26n_cls/weights/best.pt --source 0
```

Detector only:

```powershell
leaf-realtime --detector runs/detect/plantdoc_yolo26n/weights/best.pt --source 0
```

Detector plus disease classifier:

```powershell
leaf-realtime `
  --detector runs/detect/plantdoc_yolo26n/weights/best.pt `
  --classifier runs/classify/plantvillage_yolo26n_cls/weights/best.pt `
  --source 0
```

Press `q` to stop the preview window.

## Export

```powershell
leaf-export --model runs/detect/plantdoc_yolo26n/weights/best.pt --format onnx --imgsz 640
```

Use TensorRT only on a matching NVIDIA deployment machine:

```powershell
leaf-export --model runs/detect/plantdoc_yolo26n/weights/best.pt --format engine --device 0 --half
```

## Optional Weak Detection From PlantVillage

PlantVillage does not provide bounding boxes. If you need one combined detector baseline anyway:

```powershell
leaf-pseudo-yolo --source data/processed/plantvillage_cls --out data/processed/plantvillage_pseudo_yolo --overwrite
```

This creates one full-image bounding box per classification image. Treat resulting metrics as a weak baseline, not as production detector quality.

## Source References

- Ultralytics YOLO26 detection/training/export docs: https://docs.ultralytics.com/tasks/detect/
- Ultralytics Python usage docs: https://docs.ultralytics.com/usage/python/
- PlantDoc Roboflow public dataset: https://public.roboflow.com/object-detection/plantdoc/
- PlantVillage Kaggle dataset requested: https://www.kaggle.com/datasets/emmarex/plantdisease?select=PlantVillage
- AI Challenger 2018 Chinese agricultural disease candidate: https://spj.science.org/doi/10.34133/plantphenomics.0208
