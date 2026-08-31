# Chinese Dataset Request

## Target

Primary target: AI Challenger 2018 Agricultural Disease / Plant Disease Recognition dataset.

If you meant a different Chinese dataset, replace the dataset name and recipient before sending.

## Email Template

Subject: Request for authorized access to AI Challenger 2018 Agricultural Disease dataset

Hello,

I am requesting access to the AI Challenger 2018 Agricultural Disease / Plant Disease Recognition dataset for a computer vision project focused on realtime plant leaf disease detection and classification.

Project summary:

- Model family: Ultralytics YOLO26
- Initial object-detection dataset: PlantDoc
- Additional classification dataset: PlantVillage
- Intended use: research/prototyping first, with any production or commercial use subject to dataset license approval

Could you please confirm:

1. Whether the dataset is still available for download or access request.
2. The current license and allowed usage terms.
3. Whether annotations are image-level labels only or include bounding boxes.
4. Required citation or attribution text.
5. Any redistribution restrictions for trained model weights.

If approved, please share the current access process or download instructions.

Thank you,

[Your name]

## After Access Is Granted

If the dataset has image-level labels:

```powershell
leaf-prepare-json-cls `
  --images data/raw/chinese/images `
  --annotations data/raw/chinese/AgriculturalDisease_train_annotations.json `
  --out data/processed/chinese_cls `
  --image-field image_id `
  --class-field disease_class `
  --overwrite
```

If the dataset has YOLO detection labels:

```powershell
leaf-validate-yolo --dataset data/raw/chinese
leaf-train detect --data data/raw/chinese/data.yaml --name chinese_yolo26n
```
