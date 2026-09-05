# Intent Accuracy by Router and OCR Engine

Accuracy against the **true** category from `labels.json`, not self-agreement. A prediction
counts as correct when it falls in the set of BANKING77 intents that mean the same thing as
the synthetic category (the `ACCEPTABLE` map in `ml/OCR/measure_intent_accuracy.py`).

Scored on 1868 of 2000 rows. The 132 rows labelled ['OTP not received'] are excluded: no BANKING77 intent expresses that meaning, so no
router can be right on them.

`ground_truth` is the ceiling: perfect OCR. The two engine columns show what each OCR
engine costs against that ceiling.

### SVM router

| Condition | ground_truth | tesseract | google_vision |
|---|---|---|---|
| `clean` | 78.16% | 73.66% | 78.16% |
| `blur` | 78.16% | 86.94% | 78.16% |
| `rotation` | 78.16% | 77.30% | 77.94% |
| `low-resolution` | 78.16% | 71.09% | 78.80% |
| **OVERALL** | 78.16% | 77.25% | 78.27% |

### LaBSE router

| Condition | ground_truth | tesseract | google_vision |
|---|---|---|---|
| `clean` | 79.23% | 78.16% | 77.94% |
| `blur` | 79.23% | 84.80% | 78.16% |
| `rotation` | 79.23% | 73.02% | 79.01% |
| `low-resolution` | 79.23% | 71.09% | 76.66% |
| **OVERALL** | 79.23% | 76.77% | 77.94% |

### Per-category accuracy (SVM, all conditions pooled)

| Category | ground_truth | tesseract | google_vision | n |
|---|---|---|---|---|
| Account blocked | 97.0% | 75.8% | 97.0% | 132 |
| Balance not updated | 100.0% | 93.9% | 99.2% | 132 |
| Beneficiary not added | 100.0% | 100.0% | 100.0% | 132 |
| Card payment declined | 100.0% | 97.8% | 100.0% | 136 |
| Card stolen | 100.0% | 99.2% | 100.0% | 132 |
| Cash not received | 0.0% | 22.7% | 3.0% | 132 |
| Cash withdrawal charged incorrectly | 100.0% | 98.5% | 99.2% | 132 |
| Cash withdrawal failure | 0.0% | 1.5% | 0.0% | 136 |
| Duplicate transaction | 100.0% | 99.2% | 100.0% | 132 |
| Refund pending | 48.5% | 62.1% | 48.5% | 132 |
| Transfer failed | 100.0% | 99.3% | 100.0% | 136 |
| Transfer pending | 100.0% | 91.2% | 100.0% | 136 |
| Unauthorized transaction | 100.0% | 79.5% | 100.0% | 132 |
| Wrong exchange rate | 50.0% | 61.8% | 50.0% | 136 |
