# Multimodal Support Ticket OCR Pipeline

This module contains the optical character recognition (OCR) pipeline for extracting text from Sri Lankan banking support tickets (English, Sinhala, Tamil, Singlish, and Tanglish). 

Based on rigorous ablation studies, this pipeline utilizes **Tesseract OCR** (bypassing EasyOCR and external OpenCV pre-processing) to maximize text extraction accuracy on complex native Indic scripts.

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

## Scientific Note on Pre-processing
As documented in the [OCR Multimodal Ablation Report](../reports/ocr_multimodal_ablation_report.md), this pipeline specifically avoids using OpenCV for Image Binarization, Deskewing, or Super-resolution. External pixel manipulation mathematically degrades Tesseract's internal Leptonica engine when analyzing the morphological complexities of Sinhala and Tamil scripts. Raw, un-altered RGB images must be passed directly into Tesseract for maximum accuracy.
