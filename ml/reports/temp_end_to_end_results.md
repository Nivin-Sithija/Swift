# End-to-End OCR Impact on Intent Classification

This report isolates the downstream impact of OCR Character Error Rate (CER).
Since the synthetic dataset uses 15 simplified categories while the classifier outputs 77 BANKING77 intents,
we use the classifier's prediction on the **clean ground truth text** as the target baseline.
The F1 score below represents how well the classifier agrees with its own optimal prediction when forced to read noisy OCR text.

| Condition | LaBSE Raw OCR vs Clean | LaBSE+SpellCheck vs Clean | SVM Raw OCR vs Clean |
|---|---|---|---|
| `clean` | 49.70% | 31.17% | **94.15%** |
| `blur` | 39.56% | 30.74% | **45.32%** |
| `rotation` | 48.29% | 26.58% | **69.30%** |
| `low-resolution` | 30.05% | 25.47% | **30.36%** |
| **OVERALL** | 34.18% | 23.42% | **35.37%** |
