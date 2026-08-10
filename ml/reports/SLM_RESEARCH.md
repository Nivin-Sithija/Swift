# SLMs for Swift classification — literature review & experiment plan

Desk research, August 2026. Written after `ENCODER_FINDINGS.md` settled the encoder question
(**champion = multilingually fine-tuned LaBSE**) and asks the next one: *does a small decoder
language model (0.3–4B) beat it on intent / sentiment / priority, and if so which one?*

Nothing here is measured on Swift data. Every number below is someone else's; the "what to run"
section at the end is the part that produces our own.

---

## 0. Where we're starting from

| task | classes | current champion | test score | label ceiling |
|---|---|---|---|---|
| intent | 77 | **classical only** (tfidf-svm) | *not yet run on test* — dev 0.87–0.90 macro-F1 per language | not measured |
| sentiment | 3 | LaBSE (471M encoder) | 0.566 Negative-F1 | 0.577 [0.40, 0.73] |
| priority | 3 | LaBSE | 0.890 macro-F1 | 0.772 |

Two facts constrain everything that follows:

1. **Priority is already ~0.12 above its label ceiling.** The model has learned the v5 labelling
   rule better than the rule agrees with humans. There is no headroom for a bigger model to win —
   any gain is fitting the rule harder, not classifying better. *Do not spend GPU hours here.*
2. **Sentiment sits inside its ceiling's CI.** `sentiment-priority-test-results` already concluded
   relabelling (v6 → 0.6875 vs v5 0.4615 on holdout) beats re-modelling. An SLM contests a metric
   whose ground truth we've measured as unreliable.

That leaves **intent** — 77 classes, no encoder run, no ceiling measured, and the one task where
the literature says decoders actually have an edge. This is the real target.

---

## 1. Does a fine-tuned SLM beat a fine-tuned encoder at classification?

**Short answer: not reliably, and not by enough to matter at our sizes.** Four independent 2024–26
results, none of which we ran:

| source | finding |
|---|---|
| [Cost-Aware Model Selection (arXiv:2602.06370)](https://arxiv.org/html/2602.06370v1) | Fine-tuned BERT/RoBERTa/DistilBERT match or beat GPT-4o / Claude Sonnet 4.5 prompting on 4 classification benchmarks at **1–2 orders of magnitude lower cost** (p50 latency 98–206ms vs 326–1435ms; $5–33 vs $192–2702 per 1M requests). Conclusion: for a fixed label space, the fine-tuned encoder is the default right tool. *(English-only, prompting not fine-tuning — so it bounds the prompted-LLM option, not the fine-tuned-SLM one.)* |
| [Are We Really Making Much Progress? (arXiv:2204.03954v6)](https://arxiv.org/html/2204.03954v6) | Best text classifiers remain BERT/RoBERTa/DeBERTa. In-context learning with LLMs does not generally beat fine-tuned encoders. |
| [Advancing Single/Multi-task Classification (arXiv:2412.08587)](https://arxiv.org/abs/2412.08587) | *Fully* fine-tuned decoders **do** beat RoBERTa-large — but the win comes from Llama3-**70B**-scale parameters, not from being a decoder. Irrelevant at 1–4B. |
| [Fine-Tuning Causal LLMs for Classification (arXiv:2512.12677)](https://arxiv.org/html/2512.12677) | ~20 causal LLMs, 270M–20B. Best embedding-head result **Llama-3.2-3B, LoRA r=8 → F1 0.86** vs **BERT baseline 0.854**. Statistically indistinguishable (p=0.24 / p=0.51). Prompted frontier models (Claude best, 0.823) *lost* to supervised fine-tuning. |

The last row is the one to internalise: a 3B decoder with LoRA, on a single 24GB GPU, ties a
110M-parameter BERT. That is the realistic prior for what an SLM buys us over LaBSE.

**The one methodological finding worth adopting regardless** — same paper: of the two ways to
fine-tune a causal LLM for classification,

- **Approach 1, embedding head** — classification head on the final-token embedding, base frozen,
  LoRA adapters trainable: F1 0.86 with **12.2M** trainable params.
- **Approach 2, instruction tuning** — reformulate as prompt→label generation: F1 0.85, and needs
  **≥100M** trainable params to get there.

Same accuracy, 8× the trainable parameters, plus label-parsing brittleness at inference. **If we
test an SLM, use the classification head, not instruction tuning.** Their own recommendation is
embedding-head adaptation as "a practical default under single-GPU constraints" — and then
distilling into ModernBERT-base for serving, retaining ≥97% of teacher F1 at BERT throughput.

---

## 2. How small can you go? Where the size/quality knee sits

[How Small Can You Go? LoRA Fine-Tuning 270M–8B (arXiv:2606.08051)](https://arxiv.org/html/2606.08051)
— 24 model variants, Gemma 3 (270M/1B/4B), Qwen 3.5 (0.8B/2B/4B), Aya-3.35B, Llama-3.1-8B, on
noisy-string entity extraction from bank transactions. Closest published setup to ours in domain,
though English-only and extraction not classification.

| model | F1 |
|---|---|
| Llama 3.1-8B (r=8) | 96.75 |
| Qwen 3.5 4B | 96.60 |
| Gemma 3 4B | 96.24 |
| **Qwen 3.5 0.8B** | **94.75** |
| Gemma 3 1B | 93.93 |
| Gemma 3 270M | 87.35 |

- **The knee is 1B.** Gemma 3 gains **+6.58 F1** from 270M→1B but only **+2.31** from 1B→4B.
  270M is below the cliff — rules out Gemma-3-270M as a serious candidate.
- **Qwen 3.5 0.8B is the efficiency outlier**, matching models 2.5–4× larger; attributed to its
  hybrid Mamba-attention design.
- **LoRA rank barely matters**: r=8 lands within 0.20 F1 of the r=32 production baseline. Cheap
  adapters are fine.
- Their config, worth copying as a starting point: **LoRA r=8, α=16, lr 1e-4, cosine, 6 epochs**.
  Note this is **5× the LR we used** in the failed LoRA experiment (§4 of `ENCODER_FINDINGS.md`,
  lr 2e-5, lost by 0.2–0.3) — that result was a hyperparameter artifact, exactly as flagged there.

---

## 3. The part that actually decides this: Sinhala, Tamil, and romanized text

Everything above is English. Our problem is not.

### 3.1 Scale does not predict Sinhala competence

[Script Sensitivity (arXiv:2601.14958)](https://arxiv.org/html/2601.14958), already in `research/` —
24 decoder-only LLMs, **350M–14B**, perplexity on Unicode / Romanized / mixed-script Sinhala:

- **Correlation between model scale and Sinhala script-handling: ρ ≈ 0.08, not significant.**
  Pythia-410M frequently beats 8–14B models.
- Unicode→Romanized median perplexity ratio **312×** (up to 770×). Root cause traced to
  **tokenizer fragmentation**, not unfamiliarity.
- Unicode skill predicts mixed-script skill (ρ=0.957) but *not* pure-romanized skill (ρ=0.519).

This is the single most important paper for this decision, and it says: **do not pick an SLM by
size or by leaderboard rank. Pick it by tokenizer, and verify on our own text.**

### 3.2 Claimed language support ≠ measured competence

- Gemma 3 (270M/1B/4B/12B/27B) advertises **140+ languages**; Qwen 3.5 Small (0.8B/2B/4B/9B,
  released 2026-03-01) advertises **200+ languages and dialects**, Qwen 3.6 claims explicitly
  balanced training on under-represented languages *including Sinhala and Tamil*.
- But on [SinhalaMMLU (arXiv:2509.03162)](https://arxiv.org/abs/2509.03162), the *best* models are
  Claude 3.5 Sonnet at 67% and GPT-4o at 62% — and perplexity across architectures confirms all
  models find Sinhala substantially harder than high-resource languages. Small open models are not
  in the running on knowledge tasks.
- Classification is a much easier ask than SinhalaMMLU, so this isn't disqualifying — but it means
  **treat every "supports Sinhala" claim as a hypothesis to measure**, per `research/README.md`'s
  standing rule about Sinhala NLP claims.

### 3.3 Tokenizer fertility: the pre-filter we can run for free

Our own `encoder_tokenizer_fertility.csv` already shows how much this varies and how badly it can
go wrong (mBERT: **61.3% UNK on Sinhala**; mmBERT: fertility **3.67** on Sinhala, 3.72 on Tamil;
LaBSE best everywhere at 1.36–2.19). Published fertility signals for the SLM candidates:

- **Gemma 3** — ~2.275 mean fertility across Indic languages; reported as the most efficient
  tokenizer for morphologically complex scripts in several comparisons (262k Gemini vocab).
- **Qwen3** — reported as the *least* efficient tokenizer across languages in head-to-head
  comparisons (6.6 vs Gemma's 3.7 mean tokens on one 12-word probe); English-centric BPE families
  (Llama-3, Qwen2.5) hit **10–11 tokens/word** on Telugu.
- **Llama-3** — the tokenizer SinLlama had to *extend with Sinhala vocabulary* before continual
  pretraining would work. Expect poor Sinhala fertility out of the box.

**None of these sources report Sinhala or Tamil specifically.** We have the probe already written
and it runs on CPU in minutes. Measure before spending a single GPU hour.

### 3.4 The Sinhala-specific decoder: SinLlama

[SinLlama (arXiv:2508.09115)](https://arxiv.org/abs/2508.09115), `polyglots/SinLlama_v01` — Llama-3-8B
+ merged Sinhala tokens + continual pretraining on 10.7M Sinhala sentences. Sentiment F1:

| | F1 |
|---|---|
| SinLlama, un-fine-tuned | 22.7 |
| Llama-3-8B instruct, fine-tuned | 68.8 |
| **SinLlama, fine-tuned** | **72.5** |

The 3.2× jump from fine-tuning is the reusable lesson — *un-tuned decoder use is the weak end of
every comparison in our library*. But as a Swift candidate it fails on three counts: **8B** (QLoRA
only on a T4, ~3× the cost of a 2B run), **native-script Sinhala only** (no Tamil, no romanized —
half our tracks), and **no XLM-R/LaBSE baseline reported**, so we can't even tell whether 72.5 beats
an encoder on its own data.

---

## 4. Hardware reality: Kaggle T4

`ml/kaggle/runner.py` pins `NvidiaTeslaT4` — Turing, so **fp16 only (no bf16), no flash-attn-2**,
16GB per GPU, ~30 GPU-h/week per account.

- 4-bit NF4 + LoRA is the only way decoders ≥2B fit comfortably. The causal-LLM paper ran 8B models
  this way on a 24GB L4; we have less.
- **fp16 is the friction point**: bf16 is what everyone's QLoRA recipe assumes. On T4 we need
  fp16 compute dtype with loss scaling, and fp16 LoRA is known to be less stable than bf16.
  Budget a run or two for NaN-chasing.
- Rough throughput estimate (**estimate, not measured**): a 1–2B 4-bit model at seq ~160 should
  land in the low tens of rows/s, so one 3-epoch pass over 42.5k train rows is ~2–4 h. A 4B is
  ~3× that — 6–9 h, a fifth of the weekly budget for a single arm. **Measure on 1k rows before
  committing a full run.**

---

## 4b. MEASURED: tokenizer fertility on Swift's own text

Step 0 of §6, run 2026-08-07 — `ml/scripts/probe_slm_tokenizers.py`, output
`ml/reports/slm_tokenizer_fertility.csv`. 2,000-row stratified sample per language from the frozen
split `e7b5934392cd`, same fertility definition as `07_encoder_bakeoff.ipynb` §1. **This is the
first measured evidence in this document; everything above it is other people's numbers.**

Fertility (subword tokens per whitespace word — lower is better):

| model | english | singlish | **sinhala** | **tamil** | tamilish | vocab |
|---|---|---|---|---|---|---|
| **labse** (incumbent) | 1.184 | 1.617 | **1.374** | **1.858** | 1.999 | 501k |
| **gemma-3-1b / -270m** | 1.181 | 1.862 | **2.239** | **2.195** | 2.205 | 262k |
| qwen3-0.6b / 1.7b / emb-0.6b | 1.158 | 2.022 | 5.969 | 9.225 | 2.345 | 152k |
| llama-3.2-1b | 1.155 | 2.005 | 7.394 | 11.460 | 2.335 | 128k |
| sinllama | 1.155 | 2.005 | **1.279** | 11.460 | 2.335 | 133k |

**Gemma 3 is the only SLM that survives.** At 1.63× LaBSE on Sinhala and 1.18× on Tamil it is in
the same league as the encoders we already trained — for calibration, **mmBERT sits at 3.67 on
Sinhala (2.67× LaBSE) and still came second on both tasks**, so ~2.2 is comfortably workable. Both
Gemma sizes share one tokenizer, so the 270M and 1B rows are identical by construction.

**The Qwen and Llama families are disqualified.** 6–11 tokens per Sinhala/Tamil word is the
fragmentation regime the Script Sensitivity paper traced the 312× perplexity gap to. Note this
kills the cheapest tier-A candidate, `Qwen3-Embedding-0.6B` — its MTEB-multilingual ranking is
real, and irrelevant here, because the leaderboard does not contain Sinhala or Tamil. Buying a
4–5× longer sequence for every non-Latin ticket also means 4–5× the attention cost, so it loses on
latency as well as on quality.

**SinLlama's vocabulary extension genuinely worked** — 1.279 on Sinhala, *better than LaBSE*, the
only checkpoint here to beat it on any language. And Tamil at 11.46 is untouched Llama-3, exactly
as expected. It is a Sinhala-cell specialist and nothing else, and at 8B it is not worth a T4
session while priority sits above its label ceiling and sentiment's ceiling is unreliable.

**Two null results worth recording**, both checks added because this project has been burned before:

- **Character preservation is 1.0 for every candidate** on every language, combining marks
  (`Mn`/`Mc`) included. The `token_pattern` defect that silently discarded 40.1% of Sinhala and
  69.3% of Tamil characters was an sklearn problem; no HF tokenizer here repeats it.
- **ZWJ (U+200D) survives the round trip everywhere.** `ට්‍රැක්` comes back intact from all eight.
  The `research/README.md` §3.19.3 gotcha is real for transliteration tools, not for these
  tokenizers.

Gated-repo note: `google/*` and `meta-llama/*` need a licence click that a Kaggle kernel cannot
perform. The `unsloth/` mirrors carry identical vocabularies (262,145 / 128,256) and weights, so
the registry uses those.

---

## 5. Model shortlist

Ordered by expected value per GPU hour, not by leaderboard rank.

Revised after §4b. The fertility gate did most of the work: **the shortlist is one family.**

| verdict | model | why |
|---|---|---|
| **RUN** | `unsloth/gemma-3-1b-pt` + classification head + LoRA | The only SLM to clear the fertility gate (Sinhala 1.63× LaBSE, Tamil 1.18×). Sits exactly on the 1B knee from arXiv:2606.08051. |
| **RUN** | `unsloth/gemma-3-270m` | Same tokenizer, ¼ the cost. Included specifically to test the published "below the knee" claim (−6.6 F1 at 270M) on *our* data — if 270M holds up, it changes the serving story entirely. |
| **DROPPED** | Qwen3-Embedding-0.6B, Qwen3-0.6B/1.7B | 4.3× LaBSE on Sinhala, 5.0× on Tamil. The cheap tier-A candidate died here; MTEB-multilingual rank does not survive contact with languages the leaderboard omits. |
| **DROPPED** | Llama-3.2-1B | 5.4× / 6.2×. Worst of the roster, exactly as SinLlama's need to extend this vocabulary predicted. |
| **DEFERRED** | `polyglots/SinLlama_v01` | Sinhala fertility 1.279 beats LaBSE — the vocabulary extension works. But Tamil 11.46, and 8B on a T4 is QLoRA-only. Revisit only if a Sinhala-cell ceiling becomes the question. |
| **NOT TESTED** | Qwen 3.5 2B | Same tokenizer family as the Qwen3 models measured above; no reason to expect it clears the gate. Measure the tokenizer before considering it. |

Explicitly **not** on the list, with reasons already measured or published:

- **Instruction/generative fine-tuning for labels** — 8× trainable params for the same F1
  (arXiv:2512.12677), plus output-parsing failure modes.
- **Zero-shot / prompted SLMs** — the weak end of every comparison in `research/`, and
  SinLlama un-tuned scores 22.7 F1.
- **Per-language SLMs** — we already measured that per-language specialization doesn't beat
  multilingual LaBSE (`ENCODER_FINDINGS.md` §2), and romanized tracks *lose* from it.

---

## 6. What to actually run

Sequenced so each step can kill the next one. Same frozen split `e7b5934392cd`, same headline
metrics (sentiment = Negative-F1, priority = macro-F1, intent = macro-F1), same protocol: refit
train+dev, score test **once**, **rank on the CI, not the point estimate**.

**Step 0 — tokenizer fertility probe. ✅ DONE, see §4b.** Cut the shortlist from six models to one
family for zero GPU hours. The 1.5× gate written here originally was too strict on its own
evidence — mmBERT ran at 2.67× LaBSE and still placed second on both tasks — so Gemma 3 (1.63×)
passes on the corrected reading, and the Qwen/Llama families (4.3–6.2×) fail under either.

**Step 1 — throughput + fp16-stability smoke (GPU, ~15 min).**
`runner.py run --models gemma-3-1b,gemma-3-270m --task intent --lora --lr 1e-4 --batch-size 16
--smoke`. Confirms Turing fp16 doesn't NaN with a half-precision backbone under fp32 adapters, and
returns a real rows/s to replace the estimate in §4 before anything long is queued.

Three integration details this surfaced, all silent-failure class:

- Gemma 3's checkpoints are stored **bfloat16**, and transformers honours the stored dtype. The T4
  has no bf16 at all, so the dtype is pinned explicitly in `train_encoder.ENCODERS` handling —
  fp16 on CUDA, fp32 elsewhere.
- Decoder sequence classification pools the **last non-pad token**, so `config.pad_token_id` must
  be set or every short row in a batch is classified from a padding embedding. No error, plausible
  metrics — the same shape as the Indic tokenizer defect.
- The classification head is `score` on causal backbones, `classifier` on the encoders. Passing the
  wrong name to `modules_to_save` leaves the head frozen at its random init.

A fourth, pre-existing: intent's 77-class label space was derived *after* subsampling, so any smoke
run raised `KeyError` on the first intent absent from the sample. Fixed — the label space is now
fixed from the full training frame.

**Step 2 — one task, one arm: intent.**
Intent is the target because it's the only task with headroom (priority is above its ceiling,
sentiment's ceiling is unreliable) and because fine-grained many-class problems are where the
literature's decoder gains actually appear. Run the surviving candidates on `task=intent`, pooled
multilingual, LoRA **r=8, α=16, lr 1e-4, cosine, 3–6 epochs**. Compare against a LaBSE intent run
(which we owe ourselves anyway — intent has no encoder result at all) and the classical dev
baselines.

**Step 3 — decide.**
Ship an SLM only if it clears the LaBSE **CI upper bound** on intent. If it merely ties — which the
literature says is the most likely outcome — the answer is *no SLM*: LaBSE is 471M, already trained,
already integrated, and serves at a fraction of the cost.

**Not in scope:** anything on priority (no headroom above the label ceiling), and any
romanized-specific SLM conclusion (Singlish is rule-generated and Tamilish machine-translated —
`ENCODER_FINDINGS.md` §3's standing caveat applies unchanged; still blocked on human-typed
romanized tickets).

---

## Sources

- [Cost-Aware Model Selection for Text Classification (arXiv:2602.06370)](https://arxiv.org/html/2602.06370v1)
- [Fine-Tuning Causal LLMs for Text Classification: Embedding-Based vs. Instruction-Based (arXiv:2512.12677)](https://arxiv.org/abs/2512.12677)
- [How Small Can You Go? LoRA Fine-Tuning 270M–8B Models (arXiv:2606.08051)](https://arxiv.org/html/2606.08051)
- [Are We Really Making Much Progress in Text Classification? (arXiv:2204.03954)](https://arxiv.org/html/2204.03954v6)
- [Advancing Single and Multi-task Text Classification through LLM Fine-tuning (arXiv:2412.08587)](https://arxiv.org/abs/2412.08587)
- [Script Sensitivity: Unicode, Romanized and Mixed-Script Sinhala (arXiv:2601.14958)](https://arxiv.org/html/2601.14958) — also `research/`
- [SinLlama — A Large Language Model for Sinhala (arXiv:2508.09115)](https://arxiv.org/abs/2508.09115) — also `research/`
- [SinhalaMMLU (arXiv:2509.03162)](https://arxiv.org/abs/2509.03162)
- [BERTifying Sinhala (arXiv:2208.07864)](https://arxiv.org/pdf/2208.07864)
- [Qwen3 Embedding (arXiv:2506.05176)](https://arxiv.org/pdf/2506.05176) / [Qwen3-Embedding-0.6B](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B)
- [Qwen 3.5 Small series release (0.8B–9B, 2026-03-01)](https://www.marktechpost.com/2026/03/02/alibaba-just-released-qwen-3-5-small-models-a-family-of-0-8b-to-9b-parameters-built-for-on-device-applications/)
- [Tokenization is Killing our Multilingual LLM Dream](https://huggingface.co/blog/omarkamali/tokenization) — Gemma-vs-Qwen fertility comparison
- [LoResLM 2026 proceedings](https://aclanthology.org/volumes/2026.loreslm-1/)
