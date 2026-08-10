import os
import time
import pandas as pd
import pytesseract
from PIL import Image
import jiwer
from pathlib import Path

def get_tesseract_lang(row):
    lang_lower = str(row.get("primary_language", "")).lower()
    script = str(row.get("scripts", "")).lower()
    
    # Map the language/script column to Tesseract language codes
    if "sinhala" in script or "sinhala" in lang_lower:
        return "sin+eng"
    if "tamil" in script or "tamil" in lang_lower:
        return "tam+eng"
    return "eng"

def main():
    root_dir = Path(__file__).parent.resolve()
    metadata_path = root_dir / "metadata.csv"
    results_path = root_dir / "results" / "ocr_tesseract_metrics.csv"
    
    if not metadata_path.exists():
        print("metadata.csv not found!")
        return
        
    df = pd.read_csv(metadata_path)
    print(f"Loaded {len(df)} records from metadata.csv.")
    print("Evaluating with Tesseract OCR (Routing by language track)...")
    
    results = []
    
    for idx, row in df.iterrows():
        img_path_rel = row["image_path"]
        orig_img_path = str(root_dir / img_path_rel)
        ground_truth = str(row.get("ground_truth", ""))
        
        # We skip if ground truth is empty or image doesn't exist
        if not ground_truth or ground_truth.strip() == "":
            print(f"Skipping {img_path_rel} - empty ground truth.")
            continue
            
        if not os.path.exists(orig_img_path):
            print(f"Skipping {img_path_rel} - file not found.")
            continue
            
        # Dynamically load the correct OCR language pack based on the metadata
        tess_lang = get_tesseract_lang(row)
        
        start_time = time.time()
        try:
            img = Image.open(orig_img_path)
            # Run pytesseract
            pred_text = pytesseract.image_to_string(img, lang=tess_lang).strip()
            
            # Clean up newlines if any
            pred_text = " ".join(pred_text.split())
        except Exception as e:
            print(f"Error processing {img_path_rel}: {e}")
            pred_text = ""
            
        latency = time.time() - start_time
        
        # Calculate metrics
        try:
            gt_clean = ground_truth.lower().strip()
            pred_clean = pred_text.lower().strip()
            if gt_clean and pred_clean:
                wer = jiwer.wer(gt_clean, pred_clean)
                cer = jiwer.cer(gt_clean, pred_clean)
            elif gt_clean and not pred_clean:
                wer = 1.0
                cer = 1.0
            else:
                wer = 0.0
                cer = 0.0
        except Exception as e:
            wer = 1.0
            cer = 1.0
            
        res_row = row.to_dict()
        res_row["predicted_text"] = pred_text
        res_row["wer"] = wer
        res_row["cer"] = cer
        res_row["latency"] = latency
        results.append(res_row)
        
        if (idx + 1) % 50 == 0:
            print(f"Processed {idx+1}/{len(df)} images...")
            
    res_df = pd.DataFrame(results)
    (root_dir / "results").mkdir(exist_ok=True)
    res_df.to_csv(results_path, index=False)
    print(f"Saved {len(results)} evaluated records to {results_path}")

if __name__ == "__main__":
    main()
