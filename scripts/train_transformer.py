"""
scripts/train_transformer.py

Fine-tunes FacebookAI/xlm-roberta-base on the 77-class BANKING77 dataset across
the 5 language tracks (english, sinhala, singlish, tamil, tamilish) or individual languages.

Supports:
  - --smoke-test mode for rapid 10-step verification without GPU OOM or long CPU runtimes.
  - Full reproducible training with dynamic padding (max_length=128) and model saving.
  - Test set untouched during model selection; evaluated overall and per-language after training.
"""
import argparse
import json
import os
import sys
import time
import torch
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)
from datasets import Dataset

RANDOM_STATE = 42
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]


def load_and_prepare_dataset(language_arg: str, val_size: float = 0.1):
    """
    Loads train and test CSVs across target languages and creates:
      - train split (90% stratified by default)
      - validation split (10% stratified by default)
      - test split (100% untouched official test set)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    datasets_dir = os.path.join(base_dir, "datasets")

    if language_arg.lower() == "all":
        target_langs = LANGUAGES
    else:
        target_langs = [l.strip().lower() for l in language_arg.split(",") if l.strip()]
    train_rows, test_rows = [], []

    for lang in target_langs:
        train_path = os.path.join(datasets_dir, lang, "train_labeled.csv")
        test_path = os.path.join(datasets_dir, lang, "test_labeled.csv")

        if not os.path.exists(train_path) or not os.path.exists(test_path):
            raise FileNotFoundError(f"Missing train or test CSV for language: {lang}")

        tr_df = pd.read_csv(train_path)
        te_df = pd.read_csv(test_path)

        for _, r in tr_df.iterrows():
            train_rows.append({
                "source_id": r.get("id", ""),
                "text": str(r["text"]).strip(),
                "category": r.get("category", r.get("label", "")),
                "language": lang,
                "split": "train"
            })
        for _, r in te_df.iterrows():
            test_rows.append({
                "source_id": r.get("id", ""),
                "text": str(r["text"]).strip(),
                "category": r.get("category", r.get("label", "")),
                "language": lang,
                "split": "test"
            })

    full_train_df = pd.DataFrame(train_rows)
    test_df = pd.DataFrame(test_rows)

    # Grouped stratified split by source_id so all language tracks for a given ID stay in either train or val
    unique_ids_df = full_train_df[["source_id", "category"]].drop_duplicates(subset=["source_id"])
    train_ids, val_ids = train_test_split(
        unique_ids_df["source_id"],
        test_size=val_size,
        random_state=RANDOM_STATE,
        stratify=unique_ids_df["category"]
    )
    train_df = full_train_df[full_train_df["source_id"].isin(train_ids)].reset_index(drop=True)
    val_df = full_train_df[full_train_df["source_id"].isin(val_ids)].reset_index(drop=True)

    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


def compute_metrics(eval_prediction):
    logits, labels = eval_prediction
    predictions = np.argmax(logits, axis=-1)

    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        labels, predictions, average="macro", zero_division=0
    )
    _, _, weighted_f1, _ = precision_recall_fscore_support(
        labels, predictions, average="weighted", zero_division=0
    )

    return {
        "accuracy": accuracy_score(labels, predictions),
        "macro_precision": macro_precision,
        "macro_recall": macro_recall,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
    }


def save_environment_info(output_dir: str, sys_args: list):
    env_file = os.path.join(output_dir, "environment.txt")
    cmd_file = os.path.join(output_dir, "run_command.txt")
    
    with open(cmd_file, "w", encoding="utf-8") as f:
        f.write(" ".join(sys_args) + "\n")
        
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(f"Python Version: {sys.version}\n")
        f.write(f"PyTorch Version: {torch.__version__}\n")
        f.write(f"CUDA Available: {torch.cuda.is_available()}\n")
        if torch.cuda.is_available():
            f.write(f"CUDA Device Name: {torch.cuda.get_device_name(0)}\n")
        else:
            f.write("Device: CPU\n")


def main():
    parser = argparse.ArgumentParser(description="Fine-tune XLM-RoBERTa on BANKING77 Multilingual Intent Classifier")
    parser.add_argument("--config", default=None, help="Path to JSON experiment config file (e.g. configs/xlm_roberta_all_01.json)")
    parser.add_argument("--model-name", default="FacebookAI/xlm-roberta-base", help="Pretrained model identifier")
    parser.add_argument("--language", default="all", help="Language track (all, english, sinhala, singlish, tamil, tamilish)")
    parser.add_argument("--max-length", type=int, default=128, help="Max tokenization sequence length")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    parser.add_argument("--train-batch-size", type=int, default=16, help="Per-device train batch size")
    parser.add_argument("--eval-batch-size", type=int, default=32, help="Per-device eval batch size")
    parser.add_argument("--gradient-accumulation-steps", type=int, default=2, help="Gradient accumulation steps")
    parser.add_argument("--lr-scheduler-type", default="linear", help="Learning rate scheduler type (linear, cosine)")
    parser.add_argument("--warmup-ratio", type=float, default=0.1, help="Warmup ratio for scheduler")
    parser.add_argument("--label-smoothing-factor", type=float, default=0.0, help="Label smoothing factor (e.g. 0.05)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output-dir", default="outputs/xlmr_all_01", help="Output directory for checkpoints and reports")
    parser.add_argument("--smoke-test", action="store_true", help="Run a rapid 10-step smoke test for verification")
    args = parser.parse_args()

    # If --config is passed, load parameters from JSON config file
    if args.config and os.path.exists(args.config):
        print(f"=== Loading Experiment Configuration from {args.config} ===")
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        args.model_name = cfg.get("model_name", args.model_name)
        args.max_length = cfg.get("max_length", args.max_length)
        args.epochs = cfg.get("epochs", args.epochs)
        args.learning_rate = cfg.get("learning_rate", args.learning_rate)
        args.train_batch_size = cfg.get("per_device_train_batch_size", args.train_batch_size)
        args.eval_batch_size = cfg.get("per_device_eval_batch_size", args.eval_batch_size)
        args.gradient_accumulation_steps = cfg.get("gradient_accumulation_steps", args.gradient_accumulation_steps)
        args.lr_scheduler_type = cfg.get("lr_scheduler_type", args.lr_scheduler_type)
        args.warmup_ratio = cfg.get("warmup_ratio", args.warmup_ratio)
        args.label_smoothing_factor = cfg.get("label_smoothing_factor", args.label_smoothing_factor)
        args.seed = cfg.get("seed", args.seed)

    # If smoke test, override output_dir if default
    if args.smoke_test and args.output_dir == "outputs/xlmr_all_01":
        args.output_dir = "outputs/xlmr_smoke_test"

    os.makedirs(args.output_dir, exist_ok=True)
    save_environment_info(args.output_dir, sys.argv)

    print(f"=== Starting XLM-RoBERTa Training Pipeline (Language: {args.language}) ===")
    print(f"Model: {args.model_name} | Max Length: {args.max_length} | Smoke Test: {args.smoke_test}")
    print(f"CUDA Available: {torch.cuda.is_available()}")

    # 1. Load Data
    train_df, val_df, test_df = load_and_prepare_dataset(args.language)
    print(f"Dataset Split Counts -> Train: {len(train_df)}, Val: {len(val_df)}, Test: {len(test_df)}")

    # 2. Build 77-class Label Mapping (Alphabetically Sorted)
    labels = sorted(train_df["category"].unique())
    assert len(labels) == 77, f"Expected 77 unique categories, found {len(labels)}"

    label2id = {label: idx for idx, label in enumerate(labels)}
    id2label = {idx: label for label, idx in label2id.items()}

    # Verify mapping covers val and test
    assert set(val_df["category"]) <= set(label2id)
    assert set(test_df["category"]) <= set(label2id)

    with open(os.path.join(args.output_dir, "label_mapping.json"), "w", encoding="utf-8") as f:
        json.dump({"label2id": label2id, "id2label": id2label}, f, indent=2)
    print(f"Saved 77-class label mapping to {os.path.join(args.output_dir, 'label_mapping.json')}")

    # 3. Configure Tokenizer and Dynamic Padding
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize_function(examples):
        return tokenizer(
            examples["text"],
            truncation=True,
            max_length=args.max_length,
            padding=False,
        )

    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # Convert DataFrames to Hugging Face Datasets
    train_ds = Dataset.from_pandas(train_df)
    val_ds = Dataset.from_pandas(val_df)
    test_ds = Dataset.from_pandas(test_df)

    # Map string labels to integer IDs
    train_ds = train_ds.map(lambda x: {"label": label2id[x["category"]]})
    val_ds = val_ds.map(lambda x: {"label": label2id[x["category"]]})
    test_ds = test_ds.map(lambda x: {"label": label2id[x["category"]]})

    # Tokenize datasets
    tokenized_train = train_ds.map(tokenize_function, batched=True, remove_columns=["source_id", "text", "category", "language", "split"])
    tokenized_val = val_ds.map(tokenize_function, batched=True, remove_columns=["source_id", "text", "category", "language", "split"])
    tokenized_test = test_ds.map(tokenize_function, batched=True, remove_columns=["source_id", "text", "category", "language", "split"])

    # 4. Load Sequence Classification Model
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=77,
        label2id=label2id,
        id2label=id2label,
    )

    # 5. Configure TrainingArguments
    if args.smoke_test:
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            max_steps=10,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=16,
            eval_strategy="steps",
            eval_steps=5,
            save_strategy="steps",
            save_steps=5,
            logging_steps=2,
            learning_rate=args.learning_rate,
            fp16=torch.cuda.is_available(),
            seed=args.seed,
            report_to="none",
        )
    else:
        training_args = TrainingArguments(
            output_dir=args.output_dir,
            learning_rate=args.learning_rate,
            num_train_epochs=args.epochs,
            per_device_train_batch_size=args.train_batch_size,
            per_device_eval_batch_size=args.eval_batch_size,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            weight_decay=0.01,
            warmup_ratio=args.warmup_ratio,
            lr_scheduler_type=args.lr_scheduler_type,
            label_smoothing_factor=args.label_smoothing_factor,
            max_grad_norm=1.0,
            eval_strategy="epoch",
            save_strategy="epoch",
            logging_strategy="steps",
            logging_steps=50,
            load_best_model_at_end=True,
            metric_for_best_model="macro_f1",
            greater_is_better=True,
            save_total_limit=2,
            fp16=torch.cuda.is_available(),
            seed=args.seed,
            data_seed=args.seed,
            report_to="none",
        )

    # 6. Create Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_val,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    # 7. Launch Training
    print("=== Launching Trainer.train() ===")
    start_time = time.time()
    train_result = trainer.train()
    training_time_s = time.time() - start_time
    print(f"Training completed in {training_time_s:.2f} seconds.")

    # Save model, tokenizer, and state
    best_model_dir = os.path.join(args.output_dir, "best_model")
    trainer.save_model(best_model_dir)
    tokenizer.save_pretrained(best_model_dir)
    trainer.save_state()

    # Save training metrics
    with open(os.path.join(args.output_dir, "train_metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"training_time_seconds": training_time_s, "metrics": train_result.metrics}, f, indent=2)

    # 8. Evaluate on Untouched Official Test Set
    print("=== Running Final Evaluation on Untouched Test Set ===")
    test_output = trainer.predict(tokenized_test)
    test_metrics = test_output.metrics
    print(f"Overall Test Macro F1: {test_metrics.get('test_macro_f1', 0.0):.4f}")
    print(f"Overall Test Accuracy: {test_metrics.get('test_accuracy', 0.0):.4f}")

    with open(os.path.join(args.output_dir, "test_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(test_metrics, f, indent=2)

    # 9. Detailed Predictions & Per-Language Breakdown
    test_preds_ids = np.argmax(test_output.predictions, axis=-1)
    test_pred_labels = [id2label[i] for i in test_preds_ids]

    test_df["predicted_category"] = test_pred_labels
    test_df["correct"] = test_df["category"] == test_df["predicted_category"]
    test_df.to_csv(os.path.join(args.output_dir, "test_predictions.csv"), index=False, encoding="utf-8")

    # Classification report and confusion matrix
    cls_report = classification_report(test_df["category"], test_pred_labels, output_dict=True, zero_division=0)
    pd.DataFrame(cls_report).transpose().to_csv(os.path.join(args.output_dir, "classification_report.csv"), encoding="utf-8")

    cm = confusion_matrix(test_df["category"], test_pred_labels, labels=labels)
    pd.DataFrame(cm, index=labels, columns=labels).to_csv(os.path.join(args.output_dir, "confusion_matrix.csv"), encoding="utf-8")

    # Evaluate separately by language track
    lang_results = []
    for lang_name, group in test_df.groupby("language"):
        y_true = group["category"]
        y_pred = group["predicted_category"]
        acc = accuracy_score(y_true, y_pred)
        _, _, m_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
        _, _, w_f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
        lang_results.append({
            "language": lang_name,
            "test_samples": len(group),
            "accuracy": round(acc, 4),
            "macro_f1": round(m_f1, 4),
            "weighted_f1": round(w_f1, 4)
        })

    # Add overall row
    lang_results.append({
        "language": "all",
        "test_samples": len(test_df),
        "accuracy": round(test_metrics.get("test_accuracy", 0.0), 4),
        "macro_f1": round(test_metrics.get("test_macro_f1", 0.0), 4),
        "weighted_f1": round(test_metrics.get("test_weighted_f1", 0.0), 4)
    })

    lang_df = pd.DataFrame(lang_results)
    lang_df.to_csv(os.path.join(args.output_dir, "test_metrics_by_language.csv"), index=False, encoding="utf-8")

    print("\n=== Test Set Metrics by Language Track ===")
    print(lang_df.to_string(index=False))
    print(f"\nAll reproducible outputs saved to: {args.output_dir}")



if __name__ == "__main__":
    main()
