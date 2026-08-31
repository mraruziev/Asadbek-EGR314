# macOS Quickstart (Apple Silicon)

The main `README.md` is written for Windows PowerShell. This is the macOS path, and it
skips the Roboflow and Kaggle accounts entirely.

## What runs today

Webcam plant disease classification: hold a leaf in the centre box and the model names
the plant and the disease. This uses the classifier branch only, so no detector weights
and no Roboflow key are needed.

## 1. Environment

```bash
cd ~/leaf-detection-yolo26
python3 -m venv .venv
./.venv/bin/pip install --upgrade pip
./.venv/bin/pip install -r requirements-macos.txt
./.venv/bin/pip install -e .
```

`requirements-macos.txt` drops `roboflow` and `kaggle` (neither is needed for the Hugging
Face data path) and adds `huggingface_hub` plus `pyarrow`.

## 2. Camera permission

macOS blocks camera access until you approve the app that launches Python. Without it you
get `OpenCV: not authorized to capture video`.

System Settings > Privacy & Security > Camera, then enable the app you run the script
from (Terminal, iTerm, VS Code, or Claude). Quit and reopen that app afterwards — the
permission only takes effect on a fresh launch.

## 3. Data

No Kaggle account required. PlantVillage comes from a public Hugging Face mirror:

```bash
./.venv/bin/leaf-download-plantvillage-hf --out data/processed/plantvillage_cls
```

That writes 43,503 training and 10,878 validation images across 38 classes
(about 900 MB) in the folder layout `yolo classify` expects.

## 4. Train the disease classifier

`batch: -1` (Ultralytics AutoBatch) is CUDA-only, so set a batch size explicitly and
point at the Apple GPU with `--device mps`:

```bash
./.venv/bin/leaf-train classify \
  --config configs/training/classify_plantvillage.yaml \
  --epochs 8 --batch 64 --device mps --workers 8
```

Weights land in `runs/classify/plantvillage_yolo26n_cls/weights/best.pt`.

## 5. Run the webcam

```bash
./.venv/bin/python webcam.py
```

`webcam.py` picks the newest checkpoint under `runs/`, selects `mps`, and opens the
preview. Press `q` to quit. For explicit control:

```bash
./.venv/bin/leaf-realtime \
  --classifier runs/classify/plantvillage_yolo26n_cls/weights/best.pt \
  --source 0 --device mps
```

Record the session instead of previewing it:

```bash
./.venv/bin/leaf-realtime --classifier runs/classify/plantvillage_yolo26n_cls/weights/best.pt \
  --source 0 --device mps --no-view --save runs/webcam.mp4
```

## Analysing uploaded photos

A photo can be framed properly, which beats holding a leaf in front of a laptop. Same
model, plus treatment guidance for every class:

```bash
./.venv/bin/leaf-analyze photo.jpg
./.venv/bin/leaf-analyze photos/ --out reports/ --json report.json
```

Output per finding: diagnosis, confidence, runner-up classes, the pathogen, and what to do
about it. Findings are marked `[!!]` when a slow response loses the crop -- late blight,
citrus greening, the whitefly-borne viruses -- and `[ok]` when nothing needs doing.

`--out` writes annotated copies with boxes drawn; `--json` writes the full structured
report for anything downstream. With a detector checkpoint present, each leaf in the photo
is found and diagnosed separately; without one the whole image is treated as a single leaf.

Treatment guidance lives in `src/leaf_ai/advice.py`. It is general agronomic practice --
approved products and notification rules vary by country, and citrus greening is
notifiable in many regions.

## Datasets

| Dataset | Rows | What it is | Used for |
|---|---|---|---|
| PlantVillage | 54,381 | detached leaves, plain background, studio light | classifier |
| COCO negatives | 3,100 | people, rooms, objects | the `Not_a_leaf` class |
| PlantDoc | 2,574 | field photos with bounding boxes | detector |
| PlantWild v2 | 18,542 | in-the-wild disease photos, 115 classes | classifier (in-the-wild) |

```bash
./.venv/bin/leaf-download-plantvillage-hf --out data/processed/plantvillage_cls
./.venv/bin/leaf-download-negatives --overwrite
./.venv/bin/leaf-download-plantdoc-hf --overwrite     # no Roboflow key needed
```

PlantDoc and PlantVillage are permissively licensed. **PlantWild v2 is CC-BY-NC-ND-4.0**:
non-commercial, no derivatives. Fine for personal and educational work, but a model
trained on it cannot be shipped commercially.

## Why it does not call your face a peach leaf

PlantVillage is a closed set. Every image in it is a leaf, so a model trained on it alone
cannot answer "that is not a leaf" -- softmax spreads 100% across the plant classes no
matter what the camera sees. Pointed at a person it will pick the nearest plant and look
confident doing it. Two independent guards handle this.

**1. Vegetation gate (heuristic, always on).** Before the classifier runs, the centre crop
is scored with an excess-green index, `2G - R - B` on channel-normalised pixels. Foliage
has more green than red; skin, wood and walls have more red than green. Measured scores:

| Input | Score | Result |
|---|---|---|
| Tomato late blight leaf | 0.34 | classified |
| Apple healthy leaf | 0.42 | classified |
| Citrus greening (brown/yellow leaf) | 0.56 | classified |
| Skin tone | 0.00 | rejected |
| Grey wall | 0.00 | rejected |
| Blue shirt | 0.00 | rejected |

Below `--min-leaf` (default 0.05) the overlay reads **no leaf in view** and no disease
label is drawn. Raise it to reject more aggressively, or pass `--min-leaf 0` to disable.

The live score is always drawn under the crop box as `veg 0.42`, so you can tune against
real numbers rather than guessing. Note it is a ratio, not a brightness measure -- a badly
underexposed leaf still scores around 0.8.

## Reading the overlay when nothing is identified

Three different things can suppress a diagnosis, and each says so explicitly:

| Overlay text | Meaning | What to change |
|---|---|---|
| `no leaf in view (veg 0.04 < 0.05)` | the heuristic gate rejected the crop | lower `--min-leaf`, or fill the box with the leaf |
| `model says: not a leaf (92%)` | the trained `Not_a_leaf` class fired | genuine reject, or the model is undertrained |
| `too close to call (margin 0.08)` | top two classes are near-tied | lower `--min-margin` to accept weaker calls |

If everything reads `model says: not a leaf`, check you are not running a half-trained
checkpoint. `webcam.py` prefers runs that completed every configured epoch and prints a
warning when it has to fall back to an in-progress one.

**2. `Not_a_leaf` class (trained).** The dataset carries a 39th class built from COCO
photos -- people, rooms, furniture, street scenes -- so the model has a real reject option
rather than relying on the heuristic alone:

```bash
./.venv/bin/leaf-download-negatives --overwrite
./.venv/bin/leaf-train classify --config configs/training/classify_plantvillage.yaml \
  --name plantvillage_yolo26n_cls_39 --epochs 8 --batch 64 --device mps
```

COCO images that are themselves mostly foliage are skipped (`--max-vegetation`, default
0.35) so the reject class never teaches the model that green plant matter is background.

**3. Margin check.** If the top two classes are within `--min-margin` (default 0.15) of
each other, the frame is reported as unsure rather than committed to a diagnosis.

## Accuracy caveat worth knowing

The classifier knows 14 crop species and nothing else: apple, blueberry, cherry, corn,
grape, orange, peach, bell pepper, potato, raspberry, soybean, squash, strawberry, tomato.
A houseplant, a fern or a tree leaf outside that list cannot be classified correctly -- the
right outcome there is `Not_a_leaf` or "no leaf in view", not a confident wrong answer.
Widening species coverage needs an additional dataset, not more PlantVillage.

### Distribution gap

PlantVillage images are single detached leaves on a plain background under even lighting.
A model trained only on it is accurate on that distribution and noticeably weaker on a
leaf still attached to a plant, on a cluttered background, or in uneven light. The
vegetation gate and the `Not_a_leaf` class stop it inventing a diagnosis for a non-leaf,
but they do not make it accurate on a hard leaf shot -- expect lower confidence there.

Two ways to improve real-world behaviour, in order of effort:

1. Fill the centre box with a single leaf against a plain background. This matches the
   training distribution and is the difference between a demo that works and one that
   does not.
2. Add the detector branch so leaves are located before classification. That needs
   PlantDoc, which is field-photo data with bounding boxes, and a Roboflow API key:
   `leaf-download-plantdoc --out data/raw/plantdoc` then
   `leaf-train detect --config configs/training/detect_plantdoc.yaml`. Once
   `runs/detect/*/weights/best.pt` exists, `webcam.py` picks it up automatically and
   switches to detect-then-classify.

## Differences from the PowerShell README

| README (Windows) | macOS |
|---|---|
| `.\.venv\Scripts\Activate.ps1` | `source .venv/bin/activate` |
| `--device 0` (CUDA) | `--device mps` |
| `batch: -1` AutoBatch | explicit `--batch 64` |
| Kaggle credentials for PlantVillage | `leaf-download-plantvillage-hf`, no account |
| TensorRT `--format engine` | not available; use `--format onnx` or `coreml` |
