#!/usr/bin/env python3
"""
Train & Evaluate Classical ML Baselines (TF-IDF Word + Character n-grams)
for Trilingual Banking Support Ticket Triage across 77 BANKING77 Categories.

Supports:
  - Logistic Regression (solver='saga', L2 regularization)
  - Linear SVM (LinearSVC, maximum-margin linear classification)

Supports both:
  - Monolingual/monoscript runs (--language english, sinhala, singlish, tamil, tamilish)
  - Combined multilingual runs (--language all)

Usage:
  python scripts/train_baseline.py --language tamilish --model linear_svm --output-dir models
"""
import argparse
import json
import os
import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

RANDOM_STATE = 42
LANGUAGES = ["english", "sinhala", "singlish", "tamil", "tamilish"]


def load_dataset(args) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load train and test splits from configurable CSV or from repository dataset directories."""
    if args.input and os.path.exists(args.input):
        print(f"Loading unified dataset from: {args.input}")
        df = pd.read_csv(args.input)
        required_cols = {args.text_column, args.label_column, args.language_column, args.split_column}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns in CSV: {sorted(missing)}")
        
        if args.language.lower() != "all":
            df = df[df[args.language_column].str.lower() == args.language.lower()]
            
        train_df = df[df[args.split_column].str.lower() == "train"].copy()
        test_df = df[df[args.split_column].str.lower() == "test"].copy()
        train_df = train_df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
        return train_df, test_df
    else:
        # Load directly from existing multi-folder structure
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        datasets_dir = os.path.join(base_dir, "datasets")
        
        target_langs = LANGUAGES if args.language.lower() == "all" else [args.language.lower()]
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
                    "id": r["id"],
                    "text": str(r["text"]).strip(),
                    "label": r.get("category", r.get("label", "")),
                    "language": lang,
                    "split": "train"
                })
            for _, r in te_df.iterrows():
                test_rows.append({
                    "id": r["id"],
                    "text": str(r["text"]).strip(),
                    "label": r.get("category", r.get("label", "")),
                    "language": lang,
                    "split": "test"
                })
                
        train_df = pd.DataFrame(train_rows)
        test_df = pd.DataFrame(test_rows)
        train_df = train_df.sample(frac=1.0, random_state=RANDOM_STATE).reset_index(drop=True)
        print(f"Loaded {len(train_df)} train rows and {len(test_df)} test rows across {len(target_langs)} language(s).")
        return train_df, test_df


def build_pipeline(model_type: str, C_param: float = 1.0) -> Pipeline:
    """Build sklearn FeatureUnion (Word TF-IDF + Char TF-IDF) + Linear Classifier pipeline."""
    features = FeatureUnion([
        (
            "word_tfidf",
            TfidfVectorizer(
                analyzer="word",
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.98,
                sublinear_tf=True,
                max_features=25_000,
            ),
        ),
        (
            "char_tfidf",
            TfidfVectorizer(
                analyzer="char_wb",
                ngram_range=(3, 5),
                min_df=2,
                sublinear_tf=True,
                max_features=50_000,
            ),
        ),
    ])

    if model_type == "logistic_regression":
        classifier = LogisticRegression(
            C=C_param,
            max_iter=500,
            class_weight="balanced",
            solver="lbfgs",
            random_state=RANDOM_STATE,
        )
    elif model_type == "linear_svm":
        classifier = LinearSVC(
            C=C_param,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            dual=True,
            max_iter=2000,
        )
    else:
        raise ValueError(f"Unsupported model_type: {model_type}. Choose 'logistic_regression' or 'linear_svm'.")

    return Pipeline([
        ("features", features),
        ("classifier", classifier),
    ])


def evaluate_pipeline(pipeline: Pipeline, test_df: pd.DataFrame, label_col: str, text_col: str) -> dict:
    """Evaluate pipeline on test dataset and return dictionary of metrics."""
    y_true = test_df[label_col].values
    y_pred = pipeline.predict(test_df[text_col].values)
    
    acc = accuracy_score(y_true, y_pred)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    weighted_f1 = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    
    # Class-wise report
    report_dict = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    report_str = classification_report(y_true, y_pred, digits=4, zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    
    return {
        "accuracy": acc,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "report_dict": report_dict,
        "report_str": report_str,
        "confusion_matrix": cm.tolist(),
        "n_test_samples": len(y_true),
        "n_classes": len(np.unique(y_true)),
    }


def main():
    parser = argparse.ArgumentParser(description="Train and evaluate TF-IDF classical ML baseline.")
    parser.add_argument("--input", type=str, default=None, help="Optional path to unified CSV dataset.")
    parser.add_argument("--text-column", type=str, default="text", help="Text column name.")
    parser.add_argument("--label-column", type=str, default="label", help="Label/category column name.")
    parser.add_argument("--language-column", type=str, default="language", help="Language column name.")
    parser.add_argument("--split-column", type=str, default="split", help="Split column name (train/test).")
    parser.add_argument("--language", type=str, default="english", help="Target language (english, sinhala, singlish, tamil, tamilish, or all).")
    parser.add_argument("--model", type=str, default="logistic_regression", choices=["logistic_regression", "linear_svm"], help="Model type.")
    parser.add_argument("--C", type=float, default=1.0, help="Regularization parameter C.")
    parser.add_argument("--output-dir", type=str, default="models", help="Directory to save trained models and metrics.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    
    train_df, test_df = load_dataset(args)
    
    print(f"\nBuilding TF-IDF Word+Char pipeline for [{args.model}] (C={args.C})...")
    pipeline = build_pipeline(args.model, args.C)
    
    print(f"Training on {len(train_df)} rows for language=[{args.language}]...")
    pipeline.fit(train_df[args.text_column].values, train_df[args.label_column].values)
    
    print(f"Evaluating on {len(test_df)} test rows...")
    metrics = evaluate_pipeline(pipeline, test_df, args.label_col if hasattr(args, 'label_col') else args.label_column, args.text_column)
    
    print("\n" + "="*80)
    print(f"EVALUATION RESULTS — Language: [{args.language}] | Model: [{args.model}]")
    print("="*80)
    print(f"  Accuracy:    {metrics['accuracy']*100:.2f}%")
    print(f"  Macro F1:    {metrics['macro_f1']*100:.2f}%")
    print(f"  Weighted F1: {metrics['weighted_f1']*100:.2f}%")
    print("="*80)
    
    # Save model artifact
    model_filename = f"tfidf_{args.model}_{args.language}.joblib"
    model_path = os.path.join(args.output_dir, model_filename)
    joblib.dump(pipeline, model_path)
    print(f"\nSaved trained pipeline to: {model_path}")
    
    # Save detailed metrics JSON
    metrics_path = os.path.join("reports", f"baseline_metrics_{args.model}_{args.language}.json")
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "language": args.language,
            "model": args.model,
            "C": args.C,
            "accuracy": metrics["accuracy"],
            "macro_f1": metrics["macro_f1"],
            "weighted_f1": metrics["weighted_f1"],
            "n_test_samples": metrics["n_test_samples"],
            "n_classes": metrics["n_classes"],
        }, f, indent=2)
    print(f"Saved evaluation JSON to: {metrics_path}")


if __name__ == "__main__":
    main()
