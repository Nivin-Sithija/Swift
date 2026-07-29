# Baseline & Transformer Experiment Matrix — Trilingual Banking Support Classifier

This document defines the **11-run pruned experiment matrix**, evaluation methodology, and model promotion/fallback criteria for the Swift banking-ticket triage classifier bake-off across five language/script representations (`english`, `sinhala`, `singlish`, `tamil`, `tamilish`).

---

## 1. Pruned 11-Run Experiment Matrix

To avoid combinatorial explosion while rigorously testing whether fine-tuned transformers beat classical ML baselines across low-resource native and romanized scripts (~10,000 rows per language), the experiment matrix is pruned to **11 canonical runs**:

| Run ID | Model Family | Architecture | Training Script / Language(s) | Eval Test Sets | Primary Objective |
|---|---|---|---|---|---|
| **EX-01** | Classical Baseline | TF-IDF (char + word n-grams) + Logistic Regression | `english` (10k rows) | `en` | Establish English classical baseline. |
| **EX-02** | Classical Baseline | TF-IDF + Logistic Regression | `sinhala` (10k rows) | `si` | Establish native Sinhala baseline. |
| **EX-03** | Classical Baseline | TF-IDF + Logistic Regression | `singlish` (10k rows) | `si-Latn` | Measure classical resilience to romanized Sinhala spelling variation. |
| **EX-04** | Classical Baseline | TF-IDF + Logistic Regression | `tamil` (10k rows) | `ta` | Establish native Tamil baseline. |
| **EX-05** | Classical Baseline | TF-IDF + Logistic Regression | `tamilish` (10k rows) | `ta-Latn` | Measure classical resilience to Tanglish code-mixing. |
| **EX-06** | Transformer (Primary) | `xlm-roberta-base` + LoRA (`r=16`) | `english` (10k rows) | `en` | Establish English neural ceiling (target ≥ 88.4% Acc). |
| **EX-07** | Transformer (Primary) | `xlm-roberta-base` + LoRA (`r=16`) | `sinhala` (10k rows) | `si` | Evaluate native Sinhala subword tokenization & classification. |
| **EX-08** | Transformer (Primary) | `xlm-roberta-base` + LoRA (`r=16`) | `singlish` (10k rows) | `si-Latn`, `si` | Evaluate Singlish subword fertility & cross-script transfer. |
| **EX-09** | Transformer (Primary) | `xlm-roberta-base` + LoRA (`r=16`) | `tamil` (10k rows) | `ta` | Evaluate native Tamil subword tokenization & classification. |
| **EX-10** | Transformer (Primary) | `xlm-roberta-base` + LoRA (`r=16`) | `tamilish` (10k rows) | `ta-Latn`, `ta` | Evaluate Tanglish code-mixed banking classification. |
| **EX-11** | Transformer (Joint) | `xlm-roberta-base` + LoRA (`r=16`) | **All 5 splits combined** (~50k rows) | `en`, `si`, `si-Latn`, `ta`, `ta-Latn` | Test whether joint multi-script training outperforms single-language fine-tuning via cross-lingual transfer. |

---

## 2. Standard Training & Evaluation Protocol

### Classical Baseline Hyperparameters (`EX-01` to `EX-05`)
- **Vectorizer**: TfidfVectorizer with word n-grams `(1, 3)` and char n-grams `(2, 5)`, `max_features=25000`, `sublinear_tf=True`.
- **Classifier**: `LogisticRegression(C=1.0, max_iter=1000, class_weight='balanced')`.
- **Why**: Protects against neural over-claiming in the ~10k row regime (*Smith & Thayasivam, 2020*).

### Transformer LoRA Hyperparameters (`EX-06` to `EX-11`)
- **Backbone**: `xlm-roberta-base` (270M parameters).
- **LoRA Configuration**:
  - Rank `r = 16`, Alpha `32`, Dropout `0.1`.
  - Target Modules: `["query", "value", "key", "output.dense"]`.
- **Optimization**: AdamW (`lr = 3e-4` for LoRA weights), Batch Size `32`, Epochs `5` with linear warmup (10% steps) and early stopping (patience = 2).
- **Class Balancing**: Plain random oversampling for rare categories (`count < 20`) per *Arya (2026)*.

### Primary Evaluation Metrics
1. **Category 77-Way Macro F1 & Overall Accuracy** (Primary quality metric).
2. **Sentiment Binary F1** (`Neutral` vs. `Negative`).
3. **Priority 3-Way Macro F1** (`Low`, `Medium`, `High`).
4. **ONNX FP16 CPU Runtime Latency** (ms/sample; hard SLO budget `< 100ms`).

---

## 3. Primary & Fallback Selection Criteria

```
                        [ Run EX-06 to EX-11: XLM-R + LoRA ]
                                         │
                    Does XLM-R beat TF-IDF Baseline by ≥ +3.0% F1
                    AND meet CPU Latency SLO < 100ms?
                                         │
                           ┌─────────────┴─────────────┐
                         YES                           NO
                           │                           │
                           ▼                           ▼
                [ PROMOTE XLM-RoBERTa ]      [ TRIGGER FALLBACK ]
                Primary production engine    Is the issue low native F1
                for all 5 script tracks.     OR high CPU latency?
                                                       │
                                        ┌──────────────┴──────────────┐
                                   Low Native F1                High Latency (>100ms)
                                        │                             │
                                        ▼                             ▼
                            [ FALLBACK: IndicBERTv2 ]        [ FALLBACK: mBERT ]
                            Switch native si/ta tracks       Deploy 178M mBERT
                            to IndicBERTv2 backbone.         for edge/CPU serving.
```

### 1. Promotion Criteria for Primary Transformer (`xlm-roberta-base`)
- **Accuracy Gate**: Must exceed the classical TF-IDF + Logistic Regression baseline by at least **+3.0% Macro F1** across `si-Latn`, `ta`, and `ta-Latn`.
- **Latency Gate**: ONNX FP16 runtime latency on standard CPU must remain **< 50ms per inference** (leaving 50ms for language ID and database routing in the `< 100ms` SLO budget).
- **Joint Synergy**: If `EX-11` (Joint 50k model) matches or exceeds monolingual models (`EX-06` to `EX-10`) within `0.5% F1`, **EX-11 is promoted** as the single unified production classifier.

### 2. Trigger Conditions for Fallback Models (`IndicBERTv2` / `mBERT`)
- **Trigger IndicBERTv2**: If XLM-R underperforms TF-IDF on native script Tamil (`ta`) or Sinhala (`si`) due to subword under-segmentation, trigger **IndicBERTv2 (`ai4bharat/IndicBERTv2-MLM-only`)** for native-script tracks.
- **Trigger mBERT**: If edge CPU deployment constraints restrict model memory below 200M parameters, trigger **mBERT (`bert-base-multilingual-cased`, 178M params)** as the lightweight fallback.
