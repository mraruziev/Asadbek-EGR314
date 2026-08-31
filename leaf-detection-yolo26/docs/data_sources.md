# Data Sources

## PlantDoc

- URL: https://public.roboflow.com/object-detection/plantdoc/
- Task fit: primary object-detection dataset.
- Size noted by Roboflow: 2,569 images, 8,851 labels, 30 classes, 13 plant species.
- License noted by Roboflow: CC BY 4.0.
- Action: export in YOLOv8/YOLO format to `data/raw/plantdoc`.

## PlantVillage

- URL: https://www.kaggle.com/datasets/emmarex/plantdisease?select=PlantVillage
- Task fit: disease classification, not native detection.
- Action: download with Kaggle CLI to `data/raw/plantvillage`, then prepare to `data/processed/plantvillage_cls`.
- Risk: dataset mirrors can carry different licenses. Confirm Kaggle data card terms before release or commercial use.

## Chinese Dataset Candidate

- Primary candidate: AI Challenger 2018 Agricultural Disease dataset.
- Reference: https://spj.science.org/doi/10.34133/plantphenomics.0208
- Reported shape in literature: large-scale Chinese agricultural disease image dataset with image-level classes.
- Task fit: classification branch unless bounding boxes are included in the received package.
- Action: request authorized access using `docs/chinese_dataset_request.md`.

## Public YOLO-Format Chinese Fallback

- Candidate: https://huggingface.co/datasets/GYD-418/yolo_bingchonghai
- Task fit: YOLO detection format, but provenance needs review before training production models.
- Action: use only after license/provenance review.
