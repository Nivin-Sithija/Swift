# Tanglish (Tamilish) Dataset Quality & Validation Summary

This document summarizes the dataset quality verification, style standardization, and code-mixing parity analysis for the Sri Lankan Tanglish support-ticket dataset (`datasets/tamilish/`).

## 1. Gold Benchmark Sample Validation (50 Rows)

A representative sample of 50 rows across 50 distinct banking categories (`datasets/tamilish/gold_benchmark_50.csv`) was evaluated against `TAMIL_STYLE.md` criteria:

- **Mean Naturalness Score (1–5)**: `4.70`
- **Median Naturalness Score**: `5.0`
- **Code-Mixing Appropriate**: `100.0%`
- **Transliteration Consistent**: `100.0%` (Aksharamukha `RomanColloquial` + Tanglish style rules)
- **Meaning Preserved**: `100.0%`

## 2. Code-Mixing Index (CMI) Parity Analysis

Using Das & Gambäck's (2014) formula (`CMI = 100 * (1 - max(w_i)/N)`), we evaluated code-mixing intensity across both train (`9,998 rows`) and test (`3,079 rows`) splits:

| Split | Row Count | Mean CMI | Min CMI | Max CMI | % CMI = 0 | % CMI 11–25 | % CMI > 25 |
|---|---|---|---|---|---|---|---|
| **Train** | 9998 | `19.3` | 0.0 | 50.0 | `16.6%` | `47.3%` | `28.6%` |
| **Test** | 3079 | `12.6` | 0.0 | 50.0 | `36.4%` | `39.2%` | `14.3%` |

### Comparison with Sinhala-English Benchmark Parity
The Tanglish dataset achieves structural parity with the Singlish (romanized Sinhala) dataset:
- **English Loanword Preservation**: Banking domain vocabulary (`card`, `account`, `transaction`, `app`, `fee`, `rate`, `status`) is consistently retained in Latin script without phonetic distortion.
- **Register Distribution**: Post-standardization, **82.8%** of train rows and **61.5%** of test rows reflect colloquial spoken syntax, reducing literary/formal outliers from `143` to `3` in train and `766` to `14` in test.

## 3. Style Standardization Impact (`fix_tamilish.py`)

| Metric | Before Standardization (Test) | After Standardization (Test) | Improvement |
|---|---|---|---|
| **FORMAL Rows** | 766 (24.9%) | **14 (0.5%)** | `-98.2%` |
| **COLLOQUIAL Rows** | 1,184 (38.5%) | **1,893 (61.5%)** | `+60.0%` |
| **Formal Pronouns (`enathu`, `ungaludaiya`)** | 1,053 (34.2%) | **0 (0.0%)** | `-100%` |
| **Tamil-Only Nouns (`attai`, `seyali`)** | 677 (22.0%) | **0 (0.0%)** | `-100%` |
| **Mean Code-Mixing Index (CMI)** | 8.9 | **12.6** | `+41.6%` |

## 4. Readiness for Transformer Experiments (Phase 3)

With formal register artifacts eliminated and banking loanword code-mixing standardized, both `train_labeled.csv` and `test_labeled.csv` are validated for the trilingual classifier bake-off against **XLM-RoBERTa**, **mBERT**, and **IndicBERT**.
