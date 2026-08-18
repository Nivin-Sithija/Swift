import json
import joblib
import pandas as pd
import torch
from pathlib import Path
from sklearn.metrics import f1_score
from transformers import pipeline
from symspellpy import SymSpell, Verbosity

def main():
    root_dir = Path(__file__).parent.resolve()
    ml_dir = root_dir.parent
    synthetic_dataset_dir = ml_dir.parent / "synthetic_ticket_dataset"
    
    ocr_results_path = root_dir / "results" / "ocr_tesseract_optimized_metrics.csv"
    labels_json_path = synthetic_dataset_dir / "labels.json"
    model_path = ml_dir / "models" / "encoders" / "intent_labse" / "best_model"
    svm_model_path = ml_dir / "models" / "tfidf_linear_svm_all.joblib"
    
    if not ocr_results_path.exists():
        print(f"Error: OCR results not found at {ocr_results_path}")
        return
        
    if not labels_json_path.exists():
        print(f"Error: Labels JSON not found at {labels_json_path}")
        return
        
    if not model_path.exists():
        print(f"Error: Intent model not found at {model_path}")
        return
        
    # Load mapping of image_path -> true intent (category)
    print("Loading true intent labels...")
    with open(labels_json_path, "r", encoding="utf-8") as f:
        labels = json.load(f)
        
    # Create mapping dictionary
    intent_mapping = {item["image_path"]: item["category"] for item in labels}
    
    # Load OCR predictions
    print(f"Loading OCR predictions from {ocr_results_path}...")
    df = pd.read_csv(ocr_results_path)
    
    # Handle image_path prefixes (metadata might have 'screenshots/...' but labels might have just 'screenshots/...')
    # They should both be 'screenshots/synthetic_bank_XXXX.png'
    # Wait, the augmented images in metadata.csv have '_blur.png', etc.
    # The labels.json only has the CLEAN image path (e.g. 'screenshots/synthetic_bank_0001.png')!
    # So we need to map based on the 'id' field instead!
    
    id_to_intent = {}
    for item in labels:
        base_name = Path(item["image_path"]).stem
        img_id = base_name.split("_")[-1] # '0001'
        id_to_intent[img_id] = item["category"]
        # Convert to int just in case
        id_to_intent[int(img_id)] = item["category"]
        
    df["true_intent"] = df["id"].map(lambda x: id_to_intent.get(x) or id_to_intent.get(int(x)))
    
    unmapped = df["true_intent"].isna().sum()
    if unmapped > 0:
        print(f"Warning: {unmapped} rows could not be mapped to a true intent.")
        df = df.dropna(subset=["true_intent"])
        
    # Load model
    print(f"Loading intent classifier from {model_path}...")
    device = 0 if torch.cuda.is_available() else -1
    classifier = pipeline(
        "text-classification",
        model=str(model_path),
        tokenizer=str(model_path),
        device=device,
        max_length=128,
        truncation=True,
        batch_size=32
    )
    
    print("\nRunning Intent Predictions...")
    # Predict on Ground Truth text
    print("- Predicting on Clean Ground Truth Text...")
    gt_texts = df["ground_truth"].fillna("").astype(str).tolist()
    gt_preds = classifier(gt_texts)
    df["gt_intent_pred"] = [p["label"] for p in gt_preds]
    
    # Predict on OCR text
    print("- Predicting on OCR Predicted Text (LaBSE)...")
    ocr_texts = df["predicted_text"].fillna("").astype(str).tolist()
    ocr_preds = classifier(ocr_texts)
    df["ocr_intent_pred"] = [p["label"] for p in ocr_preds]
    
    # Load and Predict with TF-IDF SVM Baseline
    print(f"Loading SVM intent classifier from {svm_model_path}...")
    svm_pipeline = joblib.load(svm_model_path)
    print("- Predicting on Clean Ground Truth Text (SVM)...")
    df["svm_gt_intent_pred"] = svm_pipeline.predict(df["ground_truth"].fillna("").astype(str))
    print("- Predicting on OCR Predicted Text (SVM)...")
    df["svm_ocr_intent_pred"] = svm_pipeline.predict(df["predicted_text"].fillna("").astype(str))
    
    # Initialize and run Spelling Correction
    print("- Running Spelling Correction on OCR Text...")
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
    dict_path = root_dir / "results" / "custom_symspell_dict.txt"
    sym_spell.load_dictionary(str(dict_path), term_index=0, count_index=1, encoding="utf-8")
    
    def correct_text(text):
        if not isinstance(text, str) or not text.strip(): return ""
        words = text.split()
        corrected = []
        for w in words:
            suggs = sym_spell.lookup(w, Verbosity.CLOSEST, max_edit_distance=2, include_unknown=True)
            corrected.append(suggs[0].term if suggs else w)
        return " ".join(corrected)
        
    df["corrected_ocr_text"] = df["predicted_text"].apply(correct_text)
    
    print("- Predicting on Corrected OCR Text...")
    corrected_texts = df["corrected_ocr_text"].tolist()
    corrected_preds = classifier(corrected_texts)
    df["corrected_intent_pred"] = [p["label"] for p in corrected_preds]
    
    print("\n" + "="*105)
    print("END-TO-END IMPACT ANALYSIS (OCR ABLATION)")
    print("="*105)
    print(f"{'Condition':<15} | {'LaBSE Raw OCR':<20} | {'LaBSE+SpellCheck':<20} | {'SVM Raw OCR':<20}")
    print("-" * 105)
    
    report_lines = [
        "# End-to-End OCR Impact on Intent Classification\n",
        "This report isolates the downstream impact of OCR Character Error Rate (CER).",
        "Since the synthetic dataset uses 15 simplified categories while the classifier outputs 77 BANKING77 intents,",
        "we use the classifier's prediction on the **clean ground truth text** as the target baseline.",
        "The F1 score below represents how well the classifier agrees with its own optimal prediction when forced to read noisy OCR text.\n",
        "| Condition | LaBSE Raw OCR vs Clean | LaBSE+SpellCheck vs Clean | SVM Raw OCR vs Clean |",
        "|---|---|---|---|"
    ]
    
    for condition in df["condition"].unique():
        cond_df = df[df["condition"] == condition]
        y_true = cond_df["gt_intent_pred"]
        svm_y_true = cond_df["svm_gt_intent_pred"]
        
        ocr_f1 = f1_score(y_true, cond_df["ocr_intent_pred"], average='macro', zero_division=0) * 100
        corr_f1 = f1_score(y_true, cond_df["corrected_intent_pred"], average='macro', zero_division=0) * 100
        svm_f1 = f1_score(svm_y_true, cond_df["svm_ocr_intent_pred"], average='macro', zero_division=0) * 100
        
        print(f"{condition:<15} | {ocr_f1:>19.2f}% | {corr_f1:>19.2f}% | {svm_f1:>19.2f}%")
        report_lines.append(f"| `{condition}` | {ocr_f1:.2f}% | {corr_f1:.2f}% | **{svm_f1:.2f}%** |")
        
    # Overall
    overall_ocr_f1 = f1_score(df["gt_intent_pred"], df["ocr_intent_pred"], average='macro', zero_division=0) * 100
    overall_corr_f1 = f1_score(df["gt_intent_pred"], df["corrected_intent_pred"], average='macro', zero_division=0) * 100
    overall_svm_f1 = f1_score(df["svm_gt_intent_pred"], df["svm_ocr_intent_pred"], average='macro', zero_division=0) * 100
    print("-" * 105)
    print(f"{'OVERALL':<15} | {overall_ocr_f1:>19.2f}% | {overall_corr_f1:>19.2f}% | {overall_svm_f1:>19.2f}%")
    report_lines.append(f"| **OVERALL** | {overall_ocr_f1:.2f}% | {overall_corr_f1:.2f}% | **{overall_svm_f1:.2f}%** |")
    
    report_path = ml_dir / "reports" / "temp_end_to_end_results.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")
        
    print(f"\nSaved temporary report to {report_path}")

if __name__ == "__main__":
    main()
