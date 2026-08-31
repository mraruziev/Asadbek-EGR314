# Claude Working Notes

This project is a YOLO26 leaf detection and plant disease classification subsystem.

## Constraints

- Do not commit `data/`, `runs/`, `models/`, `exports/`, or downloaded datasets.
- Prefer `yolo26n.pt` for realtime detector work unless accuracy requires moving to `yolo26s.pt`.
- Use PlantDoc for true object detection because it has bounding boxes.
- Use PlantVillage and Chinese image-label datasets for classification unless verified bounding boxes are available.
- Do not silently train on pseudo boxes as if they are ground truth.
- Keep the PowerShell commands in README.md working; macOS equivalents live in docs/macos_quickstart.md.
- On Apple Silicon use `--device mps` and an explicit `--batch`; Ultralytics AutoBatch (`batch: -1`) is CUDA-only.

## Main Commands

```powershell
leaf-download-plantdoc --out data/raw/plantdoc
leaf-download-plantvillage --dataset emmarex/plantdisease --out data/raw/plantvillage
leaf-prepare-plantvillage --source data/raw/plantvillage --out data/processed/plantvillage_cls --overwrite
leaf-train detect --config configs/training/detect_plantdoc.yaml
leaf-train classify --config configs/training/classify_plantvillage.yaml
leaf-download-plantvillage-hf --out data/processed/plantvillage_cls   # no Kaggle account needed
leaf-download-plantdoc-hf --overwrite                                 # no Roboflow key needed
leaf-analyze photo.jpg                                                # diagnose an uploaded photo
leaf-realtime --classifier runs/classify/plantvillage_yolo26n_cls/weights/best.pt --source 0
leaf-realtime --detector runs/detect/plantdoc_yolo26n/weights/best.pt --source 0
```

## Review Priorities

- Validate dataset layout before training.
- Keep train/inference scripts configurable from CLI.
- Prefer small, testable utility functions over notebook-only workflows.
- Surface licensing and dataset provenance concerns before model release.

## Realtime Modes

`leaf-realtime` takes `--detector`, `--classifier`, or both.

- classifier only: classifies a centre crop of each frame. This is the path that needs no
  Roboflow key, and it assumes one leaf fills the crop box.
- detector only: draws leaf boxes.
- both: detects leaves, then classifies each crop.

`webcam.py` is the zero-argument wrapper: it picks the newest weights under `runs/`,
selects mps/cuda/cpu automatically, and opens the preview.

## Advice

`src/leaf_ai/advice.py` maps every class to cause, urgency and actions. Keep one entry per
class the classifier can emit -- `tests/test_advice.py` fails when a trained class has no
guidance. Mark a disease `urgent` only when a slow response actually loses the crop.
