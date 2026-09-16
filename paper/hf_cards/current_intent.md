---
language:
- en
- si
- ta
pipeline_tag: text-classification
tags:
- banking
- intent-classification
- labse
- multilingual
- code-mixed
---

# Swift-Support LaBSE Intent Classifier (v1.0)

This is a fine-tuned **Language-Agnostic BERT Sentence Embedding (LaBSE)** model designed for trilingual intent classification in the banking and financial support domain. It was developed as part of the **Swift** Support Ticket Classification project.

## Model Details
* **Base Architecture:** `sentence-transformers/LaBSE` (501k Vocabulary)
* **Task:** Text Classification (Intent Recognition)
* **Number of Classes:** 77 (Derived from the BANKING77 taxonomy)
* **Supported Languages:** English, Sinhala, Tamil, Singlish (Code-mixed), and Tanglish (Code-mixed).

## Evaluation & Benchmark Results
During the architectural ablation phase, this model was strictly evaluated on a held-out test set against classical ML algorithms, Indic Specialists (MuRIL & IndicBERT), and XLM-RoBERTa.

The metric used is **Macro-F1** across all 77 intent classes.

| Language Track | Best Classical ML | MuRIL | IndicBERT | XLM-RoBERTa | **LaBSE (This Model)** |
|---|---:|---:|---:|---:|---:|
| **English** | 90.98% | — | — | 93.88% | **94.13%** |
| **Sinhala** | 83.08% | — | — | 92.42% | **92.95%** |
| **Singlish** (Romanized) | 86.49% | — | — | 90.03% | **90.65%** |
| **Tamil** | 86.35% | 66.01% | 89.81% | 91.74% | **93.27%** |
| **Tanglish** (Romanized) | 61.05% | 57.62% | 61.25% | **72.04%** | 70.57% | 
| **ALL (Pooled)** | 83.18% | 62.10% | 76.24% | 88.29% | **88.54%** | 

**Key Findings:**
1. **LaBSE is the Intent Champion:** Achieving **88.54% Macro-F1** on the pooled track, it outperformed the classical baseline by +5.36pp.
2. **Specialists failed on Code-Mixed Data:** Indic specialists like MuRIL and IndicBERT failed outright on the pooled and code-mixed tracks because their smaller vocabularies couldn't handle heavy romanization or English slang, proving that massive multilingual coverage (LaBSE's 501k vocab) is required for real-world South Asian support tickets.

## How to use in Python

You can easily use this model via the `transformers` pipeline:

```python
from transformers import pipeline

classifier = pipeline("text-classification", model="Swift-Support/labse-intent-1.0")

result = classifier("I lost my credit card yesterday, please help me cancel it")
print(result)
# Output: [{'label': 'Card payment declined', 'score': 0.98}]
