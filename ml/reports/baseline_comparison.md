# Classical ML Baseline Performance Report — Trilingual Banking Classifier

This report presents the empirical benchmark results for classical linear models (**Logistic Regression** and **Linear SVM**) trained on **TF-IDF Word + Character n-gram FeatureUnions** across all 77 fine-grained BANKING77 support-ticket intents.

## 1. Executive Baseline Comparison Table

| Model | Language / Track | Train Mode | Test Samples | Accuracy (%) | **Macro F1 (%)** | Weighted F1 (%) |
|---|---|---|---|---|---|---|
| **Logistic Regression** | `english` | Monolingual / Monoscript | 3079 | 90.61% | **90.62%** | 90.62% |
| **Logistic Regression** | `sinhala` | Monolingual / Monoscript | 3079 | 83.47% | **82.85%** | 82.85% |
| **Logistic Regression** | `singlish` | Monolingual / Monoscript | 3079 | 86.33% | **86.19%** | 86.19% |
| **Logistic Regression** | `tamil` | Monolingual / Monoscript | 3079 | 85.55% | **84.78%** | 84.78% |
| **Logistic Regression** | `tamilish` | Monolingual / Monoscript | 3079 | 60.8% | **59.3%** | 59.3% |
| **Logistic Regression** | `all` | Combined (All Scripts) | 15395 | 82.31% | **82.35%** | 82.35% |
| **Linear SVM** | `english` | Monolingual / Monoscript | 3079 | 90.94% | **90.95%** | 90.94% |
| **Linear SVM** | `sinhala` | Monolingual / Monoscript | 3079 | 83.66% | **82.81%** | 82.81% |
| **Linear SVM** | `singlish` | Monolingual / Monoscript | 3079 | 86.42% | **86.35%** | 86.35% |
| **Linear SVM** | `tamil` | Monolingual / Monoscript | 3079 | 86.81% | **86.31%** | 86.31% |
| **Linear SVM** | `tamilish` | Monolingual / Monoscript | 3079 | 62.23% | **61.0%** | 61.0% |
| **Linear SVM** | `all` | Combined (All Scripts) | 15395 | 83.23% | **83.26%** | 83.26% |

## 2. Key Findings & Classical Baseline Observations

### A. Monolingual vs. Code-Mixed Romanized Tracks
- **Character n-grams are critical**: Combining character n-grams `(3, 5)` with word n-grams `(1, 2)` allows both Logistic Regression and Linear SVM to capture subword prefixes and suffixes across Tanglish (`card-ai`, `account-la`) and Singlish (`card eka`, `login wenna`).
- **Linear SVM vs. Logistic Regression**: High-dimensional sparse TF-IDF features (`250,000` max features) benefit from maximum-margin separation, establishing a strong classical ceiling for fine-grained 77-way intent classification.

### B. Combined Multilingual Training (`--language all`)
- Training a single unified linear classifier across all five language representations (~50,000 train rows) demonstrates whether shared vocabulary and character n-grams can generalize across scripts without neural self-attention.
- These classical baseline numbers define the **+3.0% F1 promotion gate** required for candidate transformer models (`xlm-roberta-base`) in Phase 3.

## 3. Saved Model Bundles (`models/`)

All 12 trained pipelines (containing both fitted TF-IDF vectorizers and classifiers) are saved in `models/` as `.joblib` files, ready for raw-text inference:
```python
import joblib

# Example raw-text inference
pipeline = joblib.load('models/tfidf_linear_svm_tamilish.joblib')
predicted_category = pipeline.predict(['Enoda card innum vanthu serala'])[0]
```
