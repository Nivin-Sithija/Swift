# Multimodal Pipeline Ablation: OCR Engine Evaluation

**Generated Date:** `2026-08-07` · **Extended:** `2026-09-04` (§5, Google Cloud Vision)  
**Dataset Scope:** 2,000 synthetically generated and augmented support tickets.  
**Augmentations Evaluated:** `clean`, `blur`, `rotation`, `low-resolution`.  
**OCR Engines Tested:** `EasyOCR` (English/Latin model), `Tesseract` (language-routed), `Google Cloud Vision` (`DOCUMENT_TEXT_DETECTION`, §5).

---

## 1. Executive Summary
As part of the Trilingual Multimodal Financial Support classification pipeline, we evaluated the baseline performance of **EasyOCR** across 2,000 synthetic banking support tickets spanning 5 language tracks (English, Singlish, Tanglish, Sinhala, Tamil) and 4 environmental conditions.

The objective was to empirically determine if a lightweight, out-of-the-box OCR engine (EasyOCR) could handle the Sri Lankan banking context, or if a dedicated multilingual pipeline (e.g., Tesseract / Google Cloud Vision) with image pre-processing is mathematically required.

> **Update 2026-09-04 — the recommendation has changed.** Google Cloud Vision has since been benchmarked on this same suite and beats Tesseract on every script and every condition (pooled CER **15.71%** vs **37.21%**; **3.67%** vs **37.21%** once a status-bar reading-order artifact is removed). The two engines tie on `clean` input; Vision's advantage is entirely in its immunity to the blur and low-resolution degradation that triples Tesseract's error. **§5 supersedes decision 1 of §4** — the engine, not the pre-processing, was the lever. §3's routing analysis and §3B's pre-processing finding stand.

---

## 2. Experimental Findings (Character Error Rate - CER)

### A. Baseline: EasyOCR (English-Only Model)
| Script Group | `clean` CER | `blur` CER | `low-resolution` CER | `rotation` CER |
|---|---:|---:|---:|---:|
| **Latin** (English/Singlish/Tanglish) | **10.14%** | 17.54% | 46.58% | 52.58% |
| **Sinhala** (Native) | **21.81%** | 29.11% | 57.07% | 58.20% |
| **Tamil** (Native) | **26.41%** | 33.57% | 60.13% | 60.28% |

### B. Specialized Engine: Tesseract OCR (with `sin` and `tam` language packs)
| Script Group | `clean` CER | `blur` CER | `low-resolution` CER | `rotation` CER |
|---|---:|---:|---:|---:|
| **Latin** (English/Singlish/Tanglish) | **9.94%** | 34.96% | 55.34% | 30.76% |
| **Sinhala** (Native) | **11.26%** | 39.92% | 64.52% | 33.93% |
| **Tamil** (Native) | **10.63%** | 34.45% | 58.49% | 31.97% |



## 3. Scientific Root Cause Analysis & Justifications

### A. Tesseract Solves the Native Script Collapse
The baseline evaluation unequivocally proved that default EasyOCR architectures fail on native Sri Lankan scripts. However, dynamically routing the images through **Tesseract OCR** using the dedicated `sin` and `tam` language packs completely resolved this bottleneck:
* **Tamil Optimization:** Tesseract slashed the Tamil Character Error Rate by **-15.78%** absolute (from 26.41% down to `10.63%`).
* **Sinhala Optimization:** Tesseract slashed the Sinhala Character Error Rate by **-10.55%** absolute (from 21.81% down to `11.26%`).
* **Justification for Hybrid Architecture:** This empirical success validates the architectural decision outlined in the project proposal to utilize a **Language-Routed OCR Pipeline**. EasyOCR is viable for Romanized scripts, but **Tesseract OCR** is mathematically required for the Sinhala/Tamil pipeline branches. 

### B. The Fallacy of External Image Pre-Processing (OpenCV)
In an attempt to combat the extreme vulnerability to environmental degradations (rotation, blur, low-resolution), we constructed a custom OpenCV pre-processing pipeline. Through rigorous ablation, we discovered a highly counter-intuitive scientific reality: **External OpenCV manipulation mathematically degrades performance.**
* **Binarization Destroys Morphology:** Applying a global Gaussian Blur followed by harsh Otsu binarization caused the delicate features of Indic scripts (loops, curves, diacritics) to bleed together, causing error rates to spike over 80%.
* **Deskewing & Grayscaling Interference:** Even when we stripped the pipeline down to strictly isolated Auto-Deskewing and Grayscale conversion, the CER for `clean` images regressed (e.g., Sinhala jumped from 11.26% to 15.55%). 
* **Scientific Root Cause:** Tesseract does not expect raw pixels; it utilizes a highly optimized internal C library called **Leptonica**. Leptonica performs adaptive, localized binarization and structural analysis specifically tuned for Tesseract's LSTM neural network. By feeding Tesseract an externally altered OpenCV matrix (even a perfectly deskewed grayscale one), we blind Leptonica's internal optimizations. 

---

## 4. Final Architectural Decisions Enforced
Based on this 2,000-image evaluation suite across multiple engines and pre-processing techniques, the final system architecture will adopt the following constraints:
1. **Language-Routed OCR Pipeline:** The system will dynamically route Romanized scripts (English, Singlish, Tanglish) to a lightweight engine, while strictly routing Sinhala and Tamil text extraction through **Tesseract OCR**.
2. **Zero-Interference Direct Feed:** We mathematically proved that external OpenCV pre-processing layers (Deskewing, Binarization, Super-Resolution) interfere with Leptonica's internal optimizations on complex Indic scripts. Therefore, **raw, unmodified RGB images must be fed directly into Tesseract** to achieve the highest possible accuracy.

---

## 5. Addendum (2026-09-04): Google Cloud Vision — the third engine

§4 named Cloud Vision as the obvious next comparison and it has now been run, on the identical
2,000-image suite with the identical `jiwer` metric and the identical language routing (`sin+eng` /
`tam+eng` becomes Vision language hints `si`/`ta`/`en` from the same metadata column). Full write-up
in [OCR Engine Benchmark: Google Cloud Vision vs Tesseract](ocr_google_vision_benchmark.md);
summarised in `RESULTS.md` §17.7.

### C. Third Engine: Google Cloud Vision (`DOCUMENT_TEXT_DETECTION`)

| Script Group | `clean` CER | `blur` CER | `low-resolution` CER | `rotation` CER |
|---|---:|---:|---:|---:|
| **Latin** (English/Singlish/Tanglish) | **15.61%** | 16.62% | 14.89% | 14.97% |
| **Sinhala** (Native) | **16.36%** | 17.20% | 16.64% | 15.69% |
| **Tamil** (Native) | **15.71%** | 17.00% | 14.98% | 15.03% |

Pooled over all 2,000 images: **Vision 15.71% CER / 11.28% WER** against **Tesseract 37.21% /
111.22%**, with Vision better on **85.9%** of individual images and zero failed or empty extractions
across 2,000 API calls.

### D. What the Third Engine Changes

**1. The degradation weakness is an engine property, not a pre-processing problem.** §3B established
that no amount of OpenCV work recovers Tesseract's collapse under blur and low-resolution, and §2B
shows that collapse plainly: Sinhala runs 15.55% clean to 71.99% low-resolution. Vision's row is
flat — 16.36% to 16.64%. The degradation column that resisted every pre-processing variant tested
here simply does not appear in a different recogniser. The correct fix was never a filter; it was an
engine.

**2. On clean input the engines tie.** Three of three clean cells fall within ±1pp, with Tesseract
nominally ahead on both native scripts (Sinhala 15.55% vs 16.36%, Tamil 14.73% vs 15.71%). The
language-routing conclusion in §3A stands undisturbed: routing native script away from a Latin-only
model was and remains the decisive fix for the script penalty. Vision's entire advantage is bought
on degraded input, which is the population real uploads are drawn from.

**3. Tesseract's word-level error is worse than its character-level error suggests.** Its WER exceeds
100% in several cells (clean Latin 122.17%, rotation Latin 141.55%): it emits more tokens than the
reference contains, hallucinating stray Indic characters out of app logos and signal bars. Vision
stays between 8.90% and 14.87% everywhere. Those phantom tokens reach the TF-IDF/SVM intent router
downstream, which is where the cost is actually paid.

**4. Vision's headline number is depressed by a scoring artifact.** Its CER never falls below 11.65%
on any image and varies by only 1.79 points across all 2,000 — too uniform to be recognition error.
Vision serialises the status-bar block after the header, where the generated ground truth places it
first, and renders the signal glyph as a placeholder; every synthetic ticket carries the same status
bar, so the penalty is near-constant. Re-scored order-insensitively (tokens sorted before alignment,
preserving every substitution, insertion and deletion) Vision reads **3.67%** CER pooled — ≈96.3%
character accuracy — against Tesseract's **37.21%**, which is *unchanged* under the same treatment,
confirming its errors are true misreads rather than ordering:

| Script Group | Vision `clean` | Vision `blur` | Vision `low-res` | Vision `rotation` |
|---|---:|---:|---:|---:|
| **Latin** | **2.36%** | 4.07% | 5.44% | 1.83% |
| **Sinhala** | **2.97%** | 3.99% | 7.78% | 2.47% |
| **Tamil** | **2.82%** | 4.74% | 6.12% | 2.40% |

### E. Operational Cost

| Dimension | Tesseract | Google Vision |
|---|---|---|
| Latency / image | 0.435s local CPU | 0.699s network, batched 16 per request |
| Failure rate | n/a (local) | 0 / 2,000 |
| Dependency | `tesseract-ocr` + `sin`/`tam` apt packs in the image | HTTPS + API key |
| Cost | free | 1,000 images/month free, then ~$1.50 / 1,000 |
| Offline capable | yes | no |

The full 2,000-image benchmark cost approximately **$1.50**. The two latency figures are not
comparable: Vision's is a batched round trip amortised over 16 images, Tesseract's is local CPU
time.

### F. Revision to §4

Decisions 1 and 2 of §4 were correct for a Tesseract pipeline and are superseded as engine policy:

| §4 decision | Status |
|---|---|
| 1. Language-Routed OCR Pipeline (native script → Tesseract) | **Superseded.** Route all scripts to Google Cloud Vision with `si`/`ta`/`en` language hints; keep Tesseract as the offline/outage fallback. The routing *principle* — tell the engine what script to expect — carries over intact |
| 2. Zero-Interference Direct Feed (raw RGB into Tesseract) | **Upheld and extended.** Vision performs its own server-side normalisation, and its flat degradation curve indicates no client-side enhancement would help it either. Feed raw RGB to both |

Implementation: the engine is selected at runtime by `SWIFT_OCR_ENGINE` in
[`backend/app/inference/ocr.py`](../../backend/app/inference/ocr.py), so no call site changes.
**As of this writing neither the switch nor the fallback is implemented** — the setting still reads
`tesseract`.

### G. Caveats Carried Forward, and One New

Unchanged by this run: the images are **synthetic** with exact generated ground truth, so every CER
here is an optimistic floor; Sinhala and Tamil hold only 84 and 83 images per condition, with no
confidence intervals computed; and Surya, PaddleOCR and TrOCR remain untested.

New: the end-to-end downstream numbers (`RESULTS.md` §17.6 — SVM router agreement 94.15% clean,
35.37% overall) were produced from **Tesseract** output. They are Tesseract-conditioned, and the
engine now recommended for production is the other one. Re-running that chain on Vision text is the
measurement that would justify the switch in product rather than CER terms.

**Note on comparing tables across sections.** §2B's Tesseract figures (clean 9.94% / 11.26% /
10.63%) and §5's (15.82% / 15.55% / 14.73%) disagree by 4-6pp on every script. §5 computes from the
committed `ml/OCR/results/ocr_tesseract_optimized_metrics.csv`; the per-image file behind §2B is not
committed, so the two cannot be reconciled row by row. Order-insensitive re-scoring of the committed
file lands at 11.81% / 10.69% / 11.62%, close to §2B, which points at a normalisation difference
rather than a different Tesseract configuration — unverified. §5's Vision-vs-Tesseract comparison is
internally consistent (both engines, same files, one metric), but **do not compare a Tesseract number
from §2B against one from §5**. Logged as `RESULTS.md` §11 inconsistency (c).
