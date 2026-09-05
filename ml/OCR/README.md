# Multimodal Support Ticket OCR Pipeline

This module contains the optical character recognition (OCR) pipeline for extracting text from Sri Lankan banking support tickets (English, Sinhala, Tamil, Singlish, and Tanglish). 

Based on rigorous ablation studies, this pipeline utilizes **Tesseract OCR** (bypassing EasyOCR and external OpenCV pre-processing) to maximize text extraction accuracy on complex native Indic scripts.

**Update (2026-09-04):** a head-to-head benchmark against **Google Cloud Vision** on the same 2,000-image suite found Vision better on every script and every condition (overall CER **15.71%** vs. **37.21%**; **3.67%** vs. **37.21%** once a status-bar reading-order artifact is neutralised), and effectively immune to the blur and low-resolution degradation that triples Tesseract's error rate. See the [Google Cloud Vision Benchmark](../reports/ocr_google_vision_benchmark.md). Vision is recommended as the primary engine with Tesseract retained as an offline fallback; the runtime switch is `SWIFT_OCR_ENGINE` in `backend/.env`.

## Prerequisites (Local)
Ensure you have the required python packages installed:
```bash
pip install pandas pillow jiwer pytesseract
```

## 1. Generating the Dataset (Required)
**Note:** The augmented dataset images and zip files are deliberately excluded from version control (`.gitignore`) to save space. You **must** generate them locally before running the Kaggle evaluation.

We test the OCR engine on 2,000 synthetic images that are artificially degraded (`clean`, `blur`, `rotation`, and `low-resolution`) to simulate real-world WhatsApp uploads.

Run the preparation script to generate these images:
```bash
python prepare_ocr_dataset.py
```
This script will read `labels.json`, apply the OpenCV augmentations, save the degraded images into a local `screenshots/augmented/` directory, and generate a master `metadata.csv` file.

## 2. Packaging for Kaggle
Because you cannot push the thousands of generated images to GitHub, you need to zip them up to upload to Kaggle.

**Important for Windows Users:** Standard Windows zip tools bake `\` (backslashes) into the zip paths, which breaks when extracted on Kaggle's Linux servers. 

Use this cross-platform python one-liner in your terminal to safely zip the generated dataset into `kaggle_tesseract_dataset.zip`:

```bash
python -c "import zipfile, os; z=zipfile.ZipFile('kaggle_tesseract_dataset.zip','w',zipfile.ZIP_DEFLATED); z.write('metadata.csv'); z.write('evaluate_tesseract.py'); z.write('analyze_ocr_results.py'); [z.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f), '.').replace('\\\\','/')) for r,d,fs in os.walk('screenshots') for f in fs]; z.close()"
```

## 3. Running on Kaggle (GPU/CPU)
Upload the generated `kaggle_tesseract_dataset.zip` to a new Kaggle Notebook.

In a Kaggle cell, run the following steps to extract the dataset, install the required Ubuntu language packages, and run the evaluation:

```python
import os, zipfile
import shutil

# 1. Extract the dataset cleanly into the Kaggle working directory
for root, dirs, files in os.walk('/kaggle/input'):
    for file in files:
        if file.endswith('.zip'):
            zip_path = os.path.join(root, file)
            print(f"Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('/kaggle/working')
            print("Extracted successfully!")
            break

# 2. Install Tesseract engine and Sri Lankan language packs
!apt-get update -qq
!apt-get install -y -qq tesseract-ocr tesseract-ocr-sin tesseract-ocr-tam

# 3. Install Python dependencies
!pip install -q pytesseract jiwer pandas pillow

# 4. Run the OCR Evaluation Script
!python evaluate_tesseract.py

# 5. Generate the Final Accuracy Metrics
!python analyze_ocr_results.py
```

## 4. Benchmarking Google Cloud Vision
`evaluate_google_vision.py` scores Cloud Vision on the identical dataset with the identical
`jiwer` metrics and output schema as `evaluate_tesseract.py`, so the two result files are directly
comparable. It batches 16 images per `images:annotate` call and routes language hints
(`si`/`ta`/`en`) from the same metadata columns Tesseract's `sin+eng`/`tam+eng` routing uses.

Set `SWIFT_GOOGLE_VISION_API_KEY` in `backend/.env` (or the environment) first. Cloud Vision bills
per image, so start with the stratified pilot, which stays inside the 1,000/month free tier:

```bash
python evaluate_google_vision.py --sample 950     # free-tier pilot, stratified by condition x language
python evaluate_google_vision.py --resume         # complete the remaining images (~$1.50 per 1,000)
```

Useful flags: `--limit N` (first N rows instead of a stratified sample), `--out FILE`,
`--batch-size` (max 16), `--concurrency` (default 4), `--resume` (skip images already scored in
`--out`, so an interrupted run never pays twice).

`compare_ocr_engines.py` puts any two result files side by side, joined on `image_path` — note that
`id` repeats once per degradation condition and is **not** a valid join key:

```bash
python compare_ocr_engines.py                     # tesseract_optimized vs. google_vision by default
python compare_ocr_engines.py ocr_tesseract_optimized_metrics.csv ocr_vision_950.csv
```

It reports overall CER/WER/latency, per-condition, per-script and per-language deltas, the
per-image win rate, and the ten worst regressions. Only images present in both files are compared,
so a sampled run can be checked against the full baseline.

## 5. Measuring what the OCR engine costs the intent router
CER is a proxy. These two scripts measure the thing the pipeline actually claims: that an image
ticket routes the same as a typed one. Both run offline against the committed result CSVs -- no API
calls, no cost. Results are written to `ml/reports/`.

```bash
python measure_end_to_end_ocr.py              # self-agreement, SVM only (the production path)
python measure_end_to_end_ocr.py --labse      # adds the LaBSE arm (slow on CPU, ~4 min)
python measure_intent_accuracy.py [--labse]   # accuracy against the true label
```

`measure_end_to_end_ocr.py` scores **self-agreement** -- the target is each router's own prediction
on the clean ground-truth text, because the synthetic set carries 15 categories while the routers
emit 77 BANKING77 intents. It reproduces the Tesseract figures in `RESULTS.md` §17.6 exactly and
adds the Google Vision column.

`measure_intent_accuracy.py` scores **accuracy against the true category** from `labels.json`,
bridging the 15 categories to BANKING77 through the hand-built `ACCEPTABLE` map at the top of the
file. A prediction counts as correct if it lands anywhere in the category's acceptable set. Editing
that map changes the numbers, so every run prints the per-category table alongside the headline.
The 132 `OTP not received` rows are excluded: no BANKING77 intent expresses that meaning.

Headline (`RESULTS.md` §17.8): on the SVM path, Vision text reproduces the typed-text routing
decision on **99.50%** of images against Tesseract's 81.70%, and scores **78.27%** true accuracy
against a **78.16%** perfect-text ceiling. OCR is no longer the constraint; the 15-to-77 taxonomy
mismatch is.

## Scientific Note on Pre-processing
As documented in the [OCR Multimodal Ablation Report](../reports/ocr_multimodal_ablation_report.md), this pipeline specifically avoids using OpenCV for Image Binarization, Deskewing, or Super-resolution. External pixel manipulation mathematically degrades Tesseract's internal Leptonica engine when analyzing the morphological complexities of Sinhala and Tamil scripts. Raw, un-altered RGB images must be passed directly into Tesseract for maximum accuracy.
