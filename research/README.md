# Research Reference List

Index and content summaries of primary-source research files backing Swift's
ML/NLP decisions in `context/model-research.md` (architecture decisions stay
in `context/architecture.md` — the two files are kept separate; each links to
the other and to the relevant paper here rather than duplicating content).
Add new PDFs to this folder as they're sourced, and add a row + summary here
— this is meant to grow as the project's research addon expands, not stay
fixed at two papers.

## Quick index

| File | Citation | Used in |
| --- | --- | --- |
| `NLP.pdf` | de Silva, N. *Survey on Publicly Available Sinhala NLP Tools and Research.* arXiv:1906.02358, living survey, rev. Jan 2026 (v5.7.1). | `model-research.md` throughout (§3.1–3.34, see its Key Sources list) |
| `SINHALA – ENGLISH LANGUAGE DETECTION IN CODE-MIXED DATA.pdf` | Smith, J. R. I. (2020). *Sinhala-English Language Detection in Code-Mixed Data.* MSc dissertation, Dept. of Computer Science & Engineering, University of Moratuwa. Supervisor: Dr. Uthyasanker Thayasivam. | `model-research.md` → **Language ID — Finalized Plan**, Si-En pair model |
| `Adapter_Based_Fine-Tuning_of_Pre-Trained_Multiling.pdf` | Rathnayake, H., Sumanapala, J., Rukshani, R., Ranathunga, S. (2022). *Adapter Based Fine-Tuning of Pre-Trained Multilingual Language Models for Code-Mixed and Code-Switched Text Classification.* Research Square preprint, DOI 10.21203/rs.3.rs-1564359/v2. University of Moratuwa. | `model-research.md` → **Finalized Decision** (Sentiment/Priority LoRA-expert architecture), direct empirical precedent |
| `Bank Customer Complaint Classification Using Machine Learning and Deep Learning Models.pdf` | Arya, S. (2026). *Bank Customer Complaint Classification Using Machine Learning and Deep Learning Models.* IJRTI, Vol. 11, Issue 2. | `model-research.md` → Dataset Strategy (category classification, class-balancing method, data-scale calibration) |
| `prioritybased.pdf` | Deshmukh, K. V., Shiravale, S. S. *Priority Based Sentiment Analysis for Quick Response to Citizen Complaints.* IEEE conference paper (Marathwada Mitra Mandal's College of Engineering, Pune). | `model-research.md` → Priority derivation rules (starvation-prevention addition) |

Full content summaries below — read these instead of re-opening the PDFs for anything covered here.

---

## `NLP.pdf` — Survey on Publicly Available Sinhala NLP Tools and Research

de Silva, N. (2026 living rev., v5.7.1, arXiv:1906.02358). 61 pages; pages 34–61 are the reference list (581 numbered sources) — the actual survey content is pages 1–33.

**What it is:** a comprehensive literature survey of *every* publicly documented Sinhala NLP tool/dataset/paper the author could find, organized by NLP layer (phonological → morphological → lexical → syntactic → semantic → discourse → pragmatic, per Liddy's framework) plus cross-cutting sections (OCR, translation, sign language, etc). Not original research — it's a map of the field, with a running thesis: **Sinhala NLP is fragmented and chronically under-published**. Only 11.43% of Sinhala NLP papers release their dataset, 9.71% release code, 5.71% release tools (Ranathunga & de Silva's figures, cited in the survey) — meaning most "existing work" the survey lists is a paper only, not a usable artifact. Treat every citation below as "a paper exists" not "a checkpoint/dataset is downloadable" until verified.

**Section-by-section content** (§ numbers match the survey and match citations elsewhere in `model-research.md`):

- **§2 Properties of Sinhala** — Indo-Aryan (not Dravidian; Tamil is Dravidian and NOT in the same language-tree branch, despite sharing Sri Lanka and some loanwords) — this is the linguistic basis for the whole Cross-Lingual Interference Research section in `model-research.md`. Sinhala is diglossic (written ≠ spoken register), SOV word order (relaxable in speech), head-final, highly inflected (9 grammatical cases), abugida script (own Brahmi-derived script, distinct Unicode block from Tamil).
- **§3.1 Corpora** — SinMin, OSCAR, CulturaX, MADLAD-400, sin-cc-15M, Glot500 (7.29M Sinhala sentences), Dakshina (200k native + 20k romanized Singlish). Very few Sinhala-Tamil parallel corpora exist and most claimed ones weren't actually public at time of writing.
- **§3.2 Data sets** — task-specific labelled sets: POS, NER (multiNER — Si/En/Ta), sentiment (ACTSEA — 318k tweets w/ emotion labels, GeeSanBhava — valence-arousal model, SOLD/SemiSOLD — offensive language), hate speech, fake news, XTREME-UP, FLORES (Si-En translation benchmark), Aya dataset/collection.
- **§3.3 Dictionaries** — English-Sinhala dictionaries mostly locked behind copyright; Wickramasinghe & De Silva's 1.37M-pair dictionary is the largest open one.
- **§3.4–3.7 WordNets / Morphology / POS / Parsers** — Sinhala WordNet efforts stalled/incomplete; several rule-based and ML morphological analyzers (best BiGRU accuracy 87.96%); a handful of POS taggers and a couple of CFG-based parsers, none handling the full grammar.
- **§3.8 NER** — hardest for Sinhala than English because Sinhala has **no capitalization cue**. Three main systems (Dahanayaka & Weerasinghe → Senevirathne et al. → Manamini et al.'s "Ananya") each add features (context words, gazetteers, clue words, frequency); only tag person/location/organization types. **Directly relevant** to Swift's OCR-evidence/entity-extraction work (pulling account numbers, amounts, reference numbers from bank slips).
- **§3.9–3.10 Semantic similarity / Text classification** — TF-IDF baselines through SinBERT/XLM-R adapter fine-tuning; Dhananjaya et al.'s BERTify-Sinhala paper is the main comparative study of pretrained LMs for Sinhala classification.
- **§3.11 Sentiment** — MLP → lexicon-based → LSTM → RNN/BiLSTM → XLM-R/SinBERT progression. **XLM-R-large and SinBERT report the best results** in multiple studies (Bandaranayake & Usoof; Mohamed et al.) — the source for `model-research.md`'s sentiment model-candidate table.
- **§3.12 Hate speech** — treated interchangeably with "offensive"/"inappropriate" speech in the Sinhala literature (no clean task separation); SOLD is the standard benchmark dataset; XLM-R-base and TwHIN-BERT-base report the best SOLD results.
- **§3.15 Summarization** — XL-Sum, M3LS, M2DS datasets; mT5 best ROUGE; BART/DistilBART used specifically on **romanized Sinhala WhatsApp chats** — a direct precedent for handling romanized banking-ticket text.
- **§3.17 Phonological tools (TTS/ASR)** — extensive but fragmented list of Sinhala TTS (Coqui/MaryTTS adaptations, VITS, VAENAR-TTS) and ASR (CMUSphinx, DeepSpeech, Wav2Vec2-BERT) efforts; almost none are publicly released end-to-end.
- **§3.18 OCR** — Tesseract is the de facto default (with fine-tuning); `SinOCR`/`SinFUND` are the main labelled datasets; accuracy improved from 53% → 86% with tuning in one study.
- **§3.19.3 Singlish transliteration** — Dakshina, IndoNLP-2025 BERT reverse-transliterator, Swa-Bhasha 2.0 are the three live options; the ZWJ (U+200D) Unicode rendering bug is a recurring gotcha across multiple of these tools — worth checking for if Swift ever integrates one.
- **§3.26 Sinhala-English code-mixing** — **this is the section the Smith & Thayasivam thesis (below) sits in.** Also covers Kugathasan & Sumathipala's Sinhala Code-Mixed NMT work and Shakir & Deuber's (paywalled) South-Asian code-mixing corpus.
- **§3.28 Embeddings, LLMs** — LaBSE/BGE-M3/multilingual-e5 for embeddings; **Aya-101 is genuinely trilingual (Si+Ta), Apache-2.0** — the strongest open generation-model choice; **Gemini was excluded from a Sinhala LLM study for "poor or non-existent support for Sinhala"** — the direct source of the Gemini caveat already in `model-research.md`; GPT-4o scores highest of tested LLMs on Sinhala Q&A benchmarks but still lowest of all its languages on the same benchmarks.
- **§3.30 Tokenizing** — Sinhala has **8.83–12.86 subword tokens per word** vs ~1 for English (Petrov et al.) — directly explains Swift's latency/cost-per-ticket asymmetry between languages; CANINE (byte-level) is the best-scoring tokenizer at ~1.0; SinLLaMA ships its own Sinhala-aware tokenizer.
- **§3.34 Language Identification (LID)** — GlotScript (>80% Sinhala), Burchell et al.'s open-LID model, NLLB LID, GLOT500/Textcat (99%+ on native-script only — **all of these are native-script only; none solve the romanized/code-mixed case**, which is exactly why the Smith & Thayasivam thesis below is the one that matters for Swift).
- **§5 Conclusion** — restates the fragmentation thesis: many isolated implementations, very little reuse/citation across Sri Lankan research groups, code/data disappearing after publication. Practical implication for Swift: budget time to *reach out to the original authors* for anything we want to reuse (per `model-research.md`'s own note on the UoM projects), don't assume a cited GitHub link still resolves.

---

## `SINHALA – ENGLISH LANGUAGE DETECTION IN CODE-MIXED DATA.pdf` — Smith & Thayasivam (2020)

Smith, J. R. I. *Sinhala-English Language Detection in Code-Mixed Data.* MSc thesis, University of Moratuwa, April 2020. Supervisor: Dr. Uthyasanker Thayasivam. 68 pages. Published as two papers: Smith & Thayasivam, *Sinhala-English Code-Mixed Data Analysis: A Review on Data Collection Process*, ICTer 2019; and *Language Detection in Sinhala-English Code-mixed Data*, IALP 2019 (Shanghai).

**Why it matters to Swift:** this is the primary source for the Si-En half of Swift's Language ID pipeline (`model-research.md` → Language ID Finalized Plan). At the time it was written it was **the first ML-based language-ID attempt on Sinhala-English code-mixed data written in Latin script** — exactly Swift's Singlish problem.

**Problem framing:** Sri Lankans write Sinhala in Latin characters (Singlish) mixed with English words in the same sentence on social media ("Api yaluwo kattiya film eken balanna yanna inne"). Unlike Unicode Sinhala (trivially detected by codepoint range), Latin-script code-mixed text is ambiguous at the word level — a token can look like an English word and be a phonetic Sinhala word (or vice versa), so the language of a token often depends on its **neighboring tokens**, not just the token itself.

**Data collection & annotation (Ch. 3.1):**
- Source: public Facebook posts/comments/chats via the Facebook API. 7,500 sentences → 40,915 tokens after manual cleaning.
- **Two-level annotation**, both done by 3 CS/SE undergrad native Sinhala speakers (fluent in English), via Google Sheets, rotated/shuffled batches per annotator to prevent collusion, each sentence annotated independently by all 3:
  - **Level 1 (sentence-level):** label each sentence English / Singlish / Sinhala-Unicode / Code-mixed / Unknown. Final label required *total agreement* across all 3 annotators (7,080 of 7,500 sentences achieved this; 420 discarded). **Result: Singlish 4,691 (62.5%), Code-mixed 1,900 (25.3%), English 476 (6.3%), Unknown 13.** Cohen's Kappa = 0.888 overall (0.807–0.936 per batch) — strong agreement.
  - **Level 2 (token-level, only on the 1,900 code-mixed sentences):** each of 11,795 tokens labelled Sinhala / English / Name / Unknown, **considering surrounding tokens** (their worked example: "me ahanna" — "me" looks English but is actually Sinhala "listen," disambiguated only by the following word). Majority vote (no total-agreement requirement, since discarding a mismatched token would break sentence meaning). **Result: Sinhala 8,568 (72.6%), English 2,824 (23.9%), Name 350, Unknown 53.** Name+Unknown merged to Unknown for the modeling stage → a clean 3-class token problem.
  - Annotators were told to ignore spelling errors/short forms (e.g. "tnx"→"thanks") and label by most-probable intended word.
  - Ambiguous-word examples worth remembering: "sinhala" (the language name itself, labelled Sinhala), "royal" (labelled Name — refers to Royal College, not the English word), "shape" (context-dependent: English "shape" vs. Sinhala "nevertheless"), "oke"/"maxaa" (Sinhala discourse particles that look English).

**Modeling — two separate stages, not two options for one task:**
1. **Sentence classification** (English/Singlish/Code-mixed/Unknown, 4-class, on the Level-1 dataset): tested 10 models (Naive Bayes baseline, Logistic Regression, SVM, Random Forest, XGBoost, plus 6 neural architectures — Deep NN, CNN, Shallow NN, GRU, Recurrent CNN, LSTM, Bidirectional RNN) × 6 feature sets (BOG, word-level TF-IDF, char-n-gram TF-IDF, n-gram TF-IDF, pretrained Word2Vec, locally-trained Word2Vec). **Winner: XGBoost + character n-gram features, 92.1% accuracy** — beat every neural model. Notably, **none of the neural models beat the Naive-Bayes baseline**; Deep NN scored as low as 50% (random guess) on some feature sets — the author attributes this squarely to insufficient training data (only ~7,500 sentences) for deep learning to work, not a flaw in the architectures themselves.
2. **Token-level sequence tagging** (Sinhala/English/Unknown, 3-class, on the Level-2 dataset, 1,900 sentences / 11,795 tokens): tested CRF, SVM, K-nearest-neighbor, LSTM, with features = character n-grams + label of left/right neighboring token + capitalization + is-digit flag. **Winner: CRF — precision 0.95, recall 0.94, F1 0.94 overall** (per-class F1: Sinhala 0.94, English 0.97, Unknown 0.92), beating SVM/LSTM/KNN by a wide margin on every metric. CRF correctly handled tricky tokens like "10k" and "4i". LSTM underperformed here too, again attributed to limited data (only 1,900 training sentences).

**Author's own stated limitations (Ch. 4.2 / conclusion) — important for Swift not to repeat:**
- The corpus is small — deep learning approaches (Deep NN, CNN, RNN variants) consistently failed to beat classical ML **because of data volume**, not model choice. The author explicitly recommends a corpus ~4x larger to properly support neural approaches.
- Single platform only (Facebook) — code-mixing patterns may differ across Twitter/YouTube/WhatsApp (Swift cares about this: banking tickets arrive via web/Telegram/WhatsApp, not Facebook).
- fastText was not tested as a feature (only Word2Vec) — flagged as a gap by the author themself.
- Stacked/hybrid architectures (CRF-LSTM, CNN-LSTM) were not tried — future work.

**Direct implication for Swift's dataset plan:** the Finalized Dataset Preparation Plan's LID corpus (see `model-research.md`) must clear this thesis's ~1,900-sentence code-mixed ceiling before trying anything beyond CRF/XGBoost on hand-built features — this is exactly the regime this thesis validated, and exactly where its own neural experiments broke down.

---

## `Adapter_Based_Fine-Tuning_of_Pre-Trained_Multiling.pdf` — Rathnayake, Sumanapala, Rukshani & Ranathunga (2022)

*Adapter Based Fine-Tuning of Pre-Trained Multilingual Language Models for Code-Mixed and Code-Switched Text Classification.* Research Square preprint, May 2022, University of Moratuwa. 27 pages + supplementary. Code, dataset, and trained models are public: `github.com/HimashiRathnayake/CMCS-Text-Classification`.

**Why it matters to Swift — this is the single strongest direct precedent in the library.** It is literally Sinhala-English code-mixed **sentiment classification** (plus hate speech, humor, language ID, aspect extraction) fine-tuned on **XLM-R with adapters**, from a University of Moratuwa group (Ranathunga co-authors several other works already cited in `NLP.pdf` and `model-research.md`) — i.e., near-identical to one of Swift's two production models, done by adjacent authors.

**Dataset preparation (Ch. 4.3) — directly reusable pattern:**
- Started from a **465,314-comment raw social-media corpus** (from prior work, Chathuranga & Ranathunga 2021) → randomly sampled 15,000 → manually filtered out Tamil-mixed comments (only ~0.02% of the sample, so negligible loss) → dropped noisy rows (one-character comments, pure-integer comments) → **10,000 comments** randomly selected for annotation.
- **Anonymization before public release**: phone numbers via data-swapping, personal/company names via pseudonymization — a concrete template for Swift's own PII-handling requirement on any customer-ticket data release.
- **Annotation**: 4 annotators, task-specific tag schemes (sentiment: positive/negative/neutral/**conflict** — a 4th class for mixed-polarity sentences, worth considering for Swift's own sentiment scheme; hate speech: hate-inducing/abusive/not-offensive; humor: binary; **language ID tagged at word level** with a richer 7-tag scheme — Sinhala / English / Sin-Eng / Eng-Sin / Mixed / NameEntity / Symbol — more granular than Smith & Thayasivam's 3-class scheme; aspect: multi-label, telecom-domain, adaptable to banking categories).
- **Inter-annotator agreement measured properly**: Fleiss' Kappa for single-label tasks (Humor 0.71, Hate Speech 0.75, Sentiment 0.79, Language ID 0.93 — all "substantial" or better), Krippendorff's alpha for the multi-label aspect task (0.64).
- **Code-Mixing Index (CMI)** computed to quantify mixing level objectively (Das & Gambäck's formula, given in their Appendix A): this dataset scored 11.59 (CMI-All) / 23.77 (CMI-CS), comparable to or higher than Spanish-English, Hindi-English, and Modern-Standard-Arabic-Egyptian corpora in the same benchmark — i.e., a legitimately heavily-code-mixed corpus, not a token gesture.
- **Class imbalance**: tried Random Oversampling (ROS) and SMOTE; **only ROS helped**, and even then inconsistently (improved hate speech for every model, but humor only for LSTM/Capsule Network) — SMOTE did not help at all. This is now the *second* paper in this library to find synthetic oversampling (SMOTE) underperforms plain oversampling for code-mixed/low-resource text (see the Bank Complaint paper below, which used plain oversampling successfully) — treat SMOTE as unproven for Swift's own class-imbalance handling.
- Validated the same techniques on two other **public** CMCS datasets (Kannada-English sentiment/hate speech, Hindi-English humor/language-ID) to check generalization — not just single-dataset overfitting.

**Models fine-tuned — three genuinely novel adapter techniques, benchmarked against baselines:**
- Baselines: LSTM, BiLSTM, 2-layer BiLSTM (word-level LID), Capsule Network (Senevirathne et al. 2020's best-performing Sinhala sentiment architecture) — all on fastText 300-dim embeddings.
- **Basic (vanilla) fine-tuning of XLM-R** — a full-parameter fine-tune, no adapters — already strong: Sentiment F1 54, Humor F1 79, Hate F1 73, Language ID F1 97 (macro-averaged).
- **Technique 1 — stacking language adapters + a task adapter**, tried both *sequentially* (one language adapter on top of another) and *in parallel* (Rückle et al.'s composition). Parallel stacking beat sequential in most experiments. Best combination for Sinhala-English: stacking **En + Si + Si-En** language adapters (pretrained English adapter reused from AdapterHub; Sinhala and Sinhala-English adapters trained fresh, since AdapterHub had none for them) under a task adapter.
- **Technique 2 — continuous fine-tuning across specialized PLMs**: train a task adapter on a language-1-specialized PLM (e.g. SinBERT), continue training the *same* adapter on a language-2-specialized PLM (e.g. English BERT), then continue again on the multilingual PMLM (XLM-R). Best order found for Sinhala-English: **BERT → SinBERT → XLM-R**.
- **Technique 3 — training adapters *without* freezing the backbone PMLM** (i.e., adapter parameters *and* the original XLM-R parameters both update, following Friedman et al. 2021's early-stopping-on-validation trick to avoid overfitting the now-unfrozen backbone). **This technique gave the best results across all four classification tasks, on all three language-pair datasets** — the strongest single finding in the paper.
- Houlsby vs. Pfeiffer adapter architectures: no significant difference (confirms Pfeiffer et al. 2020b) — they used Pfeiffer for all further experiments.

**Results and the calibration this sets for Swift:**
- On **sentiment specifically**, macro-F1 barely moved across methods — vanilla XLM-R fine-tuning (54), task-adapter-only (54), sequential stacking (53), parallel stacking (55), continuous fine-tuning (55), unfrozen-backbone adapters (54) — a **1-2 point band**, not a meaningful accuracy gap. The bigger wins from adapter techniques showed up on **hate speech** (73 → 74–80) and **humor** (79 → 71–80, mixed) instead.
- **Practical implication for Swift's Finalized Decision (per-language LoRA experts):** don't expect the LoRA-expert architecture to noticeably beat a well-tuned single multilingual model on **sentiment accuracy** for Sinhala-English specifically — the paper's own results say that gap is small to nonexistent at this data scale. The reason to keep the per-language-expert design is still valid (deployment/interference/scaling reasons per the Cross-Lingual Interference Research section), but frame it that way in the evaluation report — as an architecture choice for robustness/maintainability, not a guaranteed accuracy uplift, so the bake-off doesn't get reported as a failure if the numbers land close together.
- **Actionable technique to adopt:** benchmark "adapters with the backbone unfrozen" (Technique 3) against a standard frozen-backbone LoRA/QLoRA setup for Swift's per-language experts — this paper's best result came specifically from *not* freezing the backbone, which cuts against the usual LoRA assumption that freezing is what makes it parameter-efficient and safe from catastrophic forgetting. Worth testing both, not assuming frozen-backbone LoRA is automatically better just because it's more standard.
- The paper also found XLM-R's cross-lingual signal on CMCS data to be strong for Sinhala **despite** Sinhala being underrepresented in XLM-R's pretraining corpus — a small positive data point against the interference-research pessimism, worth citing alongside it rather than instead of it.
- **Correction after inspecting the actual released file (verified, not inferred from the paper text):** the public sentence-level CSV columns are `Unnamed: 0` (index), `Sentence`, `Hate_speech`, `Sentiment`, `Humor`, then **7 one-hot aspect columns** — `Billing or price`, `Customer service`, `Data`, `Network`, `Package`, `Service or product`, `None`. Two things this changes from what the paper text alone suggested:
  - **The aspect columns are telecom-domain** (this corpus's source comments were telecom customer feedback, not banking) — they do **not** map onto Swift's 7 banking categories and must not be used as category-classification ground truth. Where there's surface overlap (e.g. "Billing or price" ~ rates/fees), it would be a forced, lossy relabel, not a real category signal — skip it; keep BANKING77/CFPB/synthetic as the only category-label sources per the Dataset Strategy above.
  - **This sentence-level file has no word-level Language ID column at all**, despite the paper describing LID as tagged separately at word level (Table 8's 7-tag scheme). That annotation, if released, must live in a different file/format in the repo (word-level tagging doesn't fit a one-row-per-sentence CSV). **Verify a separate LID-tagged file actually exists in `github.com/HimashiRathnayake/CMCS-Text-Classification` before relying on this dataset to close the Si-En LID corpus gap** — don't assume it ships just because the paper describes annotating it.
  - **What's still genuinely reusable**: the raw `Sentence` column (real, naturally-occurring Sinhala-English CMCS text, not synthetic) plus the `Sentiment` labels (Positive/Negative/Neutral/Conflict) — useful as **general-domain Si-En sentiment/robustness data** (e.g. code-switch augmentation source material, or a bake-off comparison point for CMCS-handling ability), but it is not banking-domain ground truth and must stay on the auxiliary-resource side of the corpus-separation rule in the Finalized Dataset Preparation Plan, same as Dakshina/DravidianCodeMix/SOLD.

---

## `Bank Customer Complaint Classification Using Machine Learning and Deep Learning Models.pdf` — Arya (2026)

IJRTI, Vol. 11 Issue 2, Feb 2026. 7 pages. Single-author, real-world Kaggle dataset (162,421 records — this is a repackaging of the CFPB Consumer Complaint Database, the same source `model-research.md`'s Dataset Strategy already names for Swift's category-gap-filling).

**Dataset preparation — directly applicable template for Swift's category classifier:**
- 162,421 raw records (index, product, narrative) → dropped index column → deduplicated (37,742 duplicates removed → 124,676 unique) → dropped 3 rows with missing narrative → text cleaning (lowercase, strip URLs/punctuation/digits/whitespace, stopword removal, lemmatization).
- **Class balancing: plain random oversampling** of every category up to the size of the largest class (56,303) → a balanced 281,515-row set across 5 product categories (credit_card, retail_banking, credit_reporting, mortgages_and_loans, debt_collection). This is the **third** data point in this library favoring simple oversampling over synthetic techniques (SMOTE wasn't tried here, but the plain-oversample approach clearly worked at this scale, and the Adapter paper above found SMOTE specifically unhelpful) — reinforces "duplicate-to-balance" as Swift's default, not something fancier.
- TF-IDF (10,000 max features) for classical ML; separate train/test vectorization to avoid leakage; tokenize+pad for the LSTM; 80/20 stratified split.

**Models fine-tuned — a clean classical-ML-vs-DL bake-off, structurally identical to what `model-research.md`'s Evaluation Plan already calls for:**
- Logistic Regression: **87.27% accuracy** (best of the classical models)
- Multinomial Naive Bayes: 83.05%
- Decision Tree: 74.45%
- Random Forest: 69.85% (notably *worse* than a single Decision Tree here — the author attributes this to tree ensembles struggling with high-dimensional sparse TF-IDF vectors)
- **LSTM** (Embedding 128-dim → LSTM 64 units → Dense 10 ReLU → Dense 5 softmax, 10 epochs): **96.61% validation accuracy**, validation loss 0.1755, stable convergence, no overfitting — a decisive win over every classical model.
- No transformer (BERT/XLM-R) was tried — explicitly listed as future work by the author.

**The data-scale calibration this sets, read against the Smith & Thayasivam thesis above:** here, with **281,515 balanced rows**, a plain LSTM decisively beats classical ML (96.6% vs. 87.3%). In the Smith & Thayasivam thesis, with only **~1,900–7,500 rows**, every neural model *failed* to beat classical ML/CRF, some as badly as random-guess accuracy. Taken together, these two papers bracket a **crossover point somewhere between low thousands and hundreds of thousands of rows** where neural approaches start reliably winning over classical ones for text classification. Swift's own banking77_trilingual target (1,500–3,000 source examples, ×5 language/script variants) sits firmly in the "classical/CRF might still win" regime per this bracket — another reason `model-research.md`'s bake-off (never assume the transformer wins without checking) is the right call, and another argument for the category-gap-filling (CFPB + synthetic) work to prioritize *volume*, not just category coverage, if the goal is for XLM-R fine-tuning to reliably beat the TF-IDF baseline.

**Future work the author flags** (sentiment integration for complaint prioritization, topic modeling, BERT/RoBERTa, multi-label classification, explainable AI) — reads as an unprompted external validation that Swift's own planned pipeline (transformer classification + sentiment-driven priority + explainability via confidence scores) is the right next step past where this paper stopped.

---

## `prioritybased.pdf` — Deshmukh & Shiravale, *Priority Based Sentiment Analysis for Quick Response to Citizen Complaints*

IEEE conference paper, Marathwada Mitra Mandal's College of Engineering, Pune, India. 5 pages. **Evidentially thin** — no dataset was actually collected or released (the "dataset" section shows 3 hand-written example Q&A pairs, not real data), no model was trained or benchmarked by the authors themselves (Table 1 is a literature-review comparison of *other* researchers' sentiment techniques, not this paper's own results), and no accuracy/F1 numbers are reported for their own SVM-based sentiment classifier. Treat this as a design-pattern source, not an empirical one — it is a proposal for a Pune Municipal Corporation citizen-complaint system, not a completed, evaluated study.

**What is genuinely useful — the priority-derivation rule set (Section IV.B):** priority is computed from sentiment intensity (%, from an SVM sentiment score) with three explicit tie-breaking cases:
1. **Case 1**: between two pending requests, the one with higher negative-sentiment intensity gets priority.
2. **Case 2**: if intensities are equal, first-submitted gets priority (FIFO tiebreak).
3. **Case 3** — **the one Swift doesn't currently have**: a **starvation-prevention rule** — a threshold wait-time is defined, and once a low-intensity (low-priority) request has been waiting past that threshold, it gets bumped up in priority regardless of its original sentiment-derived score, so it doesn't sit ignored indefinitely just because it was never angry/urgent-sounding.

**Direct implication for Swift:** `model-research.md`'s existing priority logic (category + sentiment → priority, "Fraud & Security always pinned to Urgent") is a snapshot rule evaluated once at ticket creation — it has no equivalent of Case 3. Recommend adding a time-based priority escalation to Swift's rule-derived priority baseline (and to the live escalation queue behavior in `architecture.md`'s `pipeline/route.py`): a ticket whose priority was derived as Low/Medium and which has sat open past a configurable threshold gets bumped up a tier, independent of its original category/sentiment score. Cheap to implement, and it's the one idea from this paper not already covered elsewhere in the research library.

---

## Gaps — candidates to source next

These are currently cited in `model-research.md` only as external links (web search, not a local PDF). Pull them in here when doing the next research pass so the bibliography is self-contained:

- **Ta-En equivalent of the Smith & Thayasivam thesis** — a Tamil-English word-level code-mixed LID paper/thesis with the same rigor (DravidianCodeMix-adjacent work). Needed to properly ground the second production LID model the way the Sinhala one now is. Still the single biggest gap: three of the four papers now on file are Sinhala-centric (or English-only), none cover Tamil-English code-mixing directly.
- **Conneau et al., XLM-R** (`arXiv:1911.02116`) — the "curse of multilinguality" primary source, currently only cited via a secondary overview.
- **Role of Language Relatedness in Multilingual Fine-tuning of LMs** (`arXiv:2109.10534`) — Indo-Aryan case study behind the Sinhala-vs-Tamil transfer asymmetry claim.
- **IndicMMLU-Pro** (`arXiv:2501.15747`) — source of the quantified Dravidian-vs-Indo-Aryan "family gap" figure (up to 13.2pp).
- **Script Sensitivity: Benchmarking LMs on Unicode, Romanized and Mixed-Script Sinhala** (`arXiv:2601.14958`) — source of the ~300x Unicode-vs-Romanized degradation figure.
- **DravidianCodeMix** dataset paper (`doi:10.1007/s10579-022-09583-7`) — referenced for Tamil-English code-mix data/features but not yet on file.

## Conventions

- Keep the original filename as downloaded (even if long/awkward) so it stays traceable back to its source — don't rename to a short slug.
- When a paper grounds a specific decision in `model-research.md` or `architecture.md`, cite it there by filename (e.g. `research/NLP.pdf`) as well as adding/updating its entry here — this file is the bibliography (full content summary lives here); the inline citation elsewhere is just a pointer back to this file, never a duplicate of the summary.
- `model-research.md` and `architecture.md` stay separate files (research/model rationale vs. system design) — they cross-reference each other by section name rather than merging.
- If a gap above gets filled, move its bullet into the Quick Index table (and add a full summary section) and delete it from Gaps.
