import os
import pandas as pd
from pathlib import Path
import sys

def main():
    root_dir = Path(__file__).parent.resolve()
    
    # Default to EasyOCR if no arg is provided, else use the provided arg
    filename = sys.argv[1] if len(sys.argv) > 1 else "ocr_raw_metrics.csv"
    results_path = root_dir / "results" / filename
    
    if not results_path.exists():
        print(f"{filename} not found. Please run evaluate_ocr.py first.")
        return
        
    df = pd.read_csv(results_path)
    print(f"Loaded {len(df)} records for analysis.")
    
    # We want to group by primary_language, scripts, condition
    # Calculate mean CER, WER, Latency
    
    summary = df.groupby(["primary_language", "scripts", "condition"]).agg(
        avg_cer=("cer", "mean"),
        avg_wer=("wer", "mean"),
        avg_latency=("latency", "mean"),
        count=("id", "count")
    ).reset_index()
    
    # Also create a high-level summary grouped just by script and condition
    summary_script = df.groupby(["scripts", "condition"]).agg(
        avg_cer=("cer", "mean"),
        avg_wer=("wer", "mean"),
        avg_latency=("latency", "mean")
    ).reset_index()
    
    print("\n=== Detailed Summary by Language, Script, and Condition ===")
    print(summary.to_string(index=False, float_format="%.4f"))
    
    print("\n=== High-Level Summary by Script and Condition ===")
    print(summary_script.to_string(index=False, float_format="%.4f"))
    
    # Determine fallback recommendations
    print("\n=== Fallback Analysis ===")
    for script in df["scripts"].unique():
        script_df = df[(df["scripts"] == script) & (df["condition"] == "clean")]
        if not script_df.empty:
            clean_cer = script_df["cer"].mean()
            if clean_cer > 0.2:
                print(f"[Warning] High CER ({clean_cer:.4f}) for CLEAN {script} images. Fallback highly recommended (e.g., Tesseract or Cloud Vision).")
            else:
                print(f"[OK] EasyOCR performs adequately on CLEAN {script} images (CER: {clean_cer:.4f}).")
                
        for cond in ["blur", "rotation", "low-resolution"]:
            cond_df = df[(df["scripts"] == script) & (df["condition"] == cond)]
            if not cond_df.empty:
                cond_cer = cond_df["cer"].mean()
                if cond_cer > 0.3:
                    print(f"  -> High degradation on {cond} for {script}. Fallback/Enhancement required.")

if __name__ == "__main__":
    main()
