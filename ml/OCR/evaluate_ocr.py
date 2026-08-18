import os
import time
import warnings
import pandas as pd
import easyocr
import jiwer
from pathlib import Path

# Suppress PyTorch DataLoader 'pin_memory' warnings on CPU
warnings.filterwarnings("ignore", category=UserWarning)

def main():
    root_dir = Path(__file__).parent.resolve()
    metadata_path = root_dir / "metadata.csv"
    results_path = root_dir / "results" / "ocr_raw_metrics.csv"
    
    if not metadata_path.exists():
        print("metadata.csv not found!")
        return
        
    df = pd.read_csv(metadata_path)
    df = df.head(200) # ONLY evaluate 200 for speed
    print(f"Loaded {len(df)} records from metadata.csv.")
    
    # Initialize EasyOCR reader for English (EasyOCR's Tamil model is throwing a size mismatch bug, and Sinhala is unsupported)
    import torch
    use_gpu = torch.cuda.is_available()
    print(f"Initializing EasyOCR (GPU Enabled: {use_gpu})...")
    reader = easyocr.Reader(['en'], gpu=use_gpu)
    
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
            
        start_time = time.time()
        try:
            # detail=0 returns just the text, join with space
            extracted = reader.readtext(orig_img_path, detail=0)
            pred_text = " ".join(extracted).strip()
        except Exception as e:
            print(f"Error processing {img_path_rel}: {e}")
            pred_text = ""
            
        latency = time.time() - start_time
        
        # Calculate metrics
        try:
            # lowercasing and basic strip for fair comparison
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
        
        if (idx + 1) % 10 == 0:
            print(f"Processed {idx+1}/{len(df)} images...")
            
    res_df = pd.DataFrame(results)
    (root_dir / "results").mkdir(exist_ok=True)
    res_df.to_csv(results_path, index=False)
    print(f"Saved {len(results)} evaluated records to {results_path}")

if __name__ == "__main__":
    main()
