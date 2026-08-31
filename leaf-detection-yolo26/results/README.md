# Training results

Metrics and curves from the runs in this repo, copied out of `runs/`
(which is gitignored — it holds 85 MB of checkpoints and per-epoch images).

Each folder has:

- `args.yaml` — the exact hyperparameters the run used
- `results.csv` — per-epoch loss and accuracy
- `results.png` — the training curves
- `confusion_matrix_normalized.png` — per-class performance (classification runs)

| Run | Task |
|-----|------|
| `plantvillage_yolo26n_cls_39` | YOLO26-n classification, 39 PlantVillage classes |
| `plantvillage_plantwild_cls` | classification on PlantVillage + PlantWild merged |
| `plantvillage_yolo26n_cls` | first classification baseline |
| `plantdoc_yolo26n` | YOLO26-n detection on PlantDoc |

Delete this folder if you'd rather keep the repo source-only.
