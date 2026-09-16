# RAG / system error analysis — findings

**Commit measured:** `f6ad3c1` · **Probe manifest:** `01305cdeb24d` · **Corpus:** 5 documents, 31 chunks, all English

Every figure below traces to a JSON report under `backend/evaluation/reports/`, regenerable
with the commands in [Reproduction](#reproduction). Offline-lane numbers are deterministic;
live-lane numbers are stamped with the commit above.

---

## Headline

**The dominant failure is not retrieval. Retrieval works — the confidence gate discards its
results.**

Across 90 answerable probes on the dev split, retrieval placed a labelled-relevant document
in the ranked set **94%** of the time, and the confidence gate then threw the evidence away
in **81 of those 90 cases (90%)**. Only **4 probes in the entire dev split ever cleared the
gate, and all four were English.**

This is structural, not a tuning accident:

```
evidence_confidence = 0.45*rerank + 0.30*retrieval + 0.15*authority + 0.10*coherence
```

The reranker returns **0.0000 (median)** in every language — including English, at 0.0020.
With `rerank = 0` the maximum achievable confidence is `0.30*dense + 0.25`, so clearing the
shipped gate of **0.55** would require `dense = 1.0` exactly: a perfect cosine identity that
no real query achieves. The highest dense score observed across 165 probes was **0.6954**,
giving a hard ceiling of **0.4586**.

> For the 125 of 165 probes (76%) where the reranker returns zero, **the confidence gate is
> mathematically unpassable.**

Because non-English text scores exactly 0.0000 on the English-only reranker, **no
non-English query cleared the gate at any point in this study.**

---

## Method and contamination controls

| Control | Status |
|---|---|
| Judge independent of generator | **Met.** Judge pinned to Gemini `gemini-3.6-flash`; generator is Groq `qwen/qwen3.8-27b`. |
| Dev/holdout split | **Met.** Split on `ticket_id`, so all five language renderings of a ticket share a split. Frozen in `probe_manifest.json` (sha `01305cdeb24d`). |
| Existing 5 golden cases excluded | **Met.** Kept as a smoke set only; they are probable tuning data for `rag_min_confidence`. |
| Paired statistics for language | **Met.** The five tracks are translations of one ticket set, so comparisons use McNemar's exact test rather than independent-sample tests. |
| Single commit for all runs | **Met.** Every report stamped `f6ad3c1`. |
| Detector provenance | **Unverified, and stated as such.** The singlish/tamilish keyword lists may have been authored by inspecting this corpus. Evaluation rows are held-out test ids, but the risk is recorded rather than dismissed. |

**Probe set.** 330 probes = 66 tickets × 5 languages; 210 answerable, 120 unanswerable.
Drawn from `datasets/*/test_labeled.csv` — official BANKING77 test ids, which
`ml/splits/split_manifest.json` records as never used for model selection.

**A correction to the original plan.** The plan assumed BANKING77 intents could be mapped
onto the knowledge base to derive `relevant_sources`. They largely cannot: BANKING77 is a
neobank intent set, the corpus is Sri Lankan retail banking, and `SRC-LOAN-001` has no
corresponding intent at all. Labels were therefore assigned only where the corpus text
demonstrably answers the intent, each with a recorded justification
(`probe_manifest.json → label_provenance`); and the language axis was measured by divergence
across the paired corpus, which needs no labels and so cannot be contaminated by them.

---

## 1. The confidence gate (`C1`) — dominant failure

| Measure | Value |
|---|---|
| Answerable probes (dev) | 90 |
| Relevant document present in ranked set | 85 (94%) |
| Evidence discarded by the gate (`C1`) | **81 (90%)** |
| Genuine retrieval misses (`R1`) | 5 (6%) |
| Neighbour-only support (`R3`) | **0** |
| Probes clearing the 0.55 gate | **4, all English** |
| Median confidence, answerable probes | **0.392** |

Component decomposition of the top-ranked hit (165 probes):

| Component | Min | Median | Max | Weight |
|---|---|---|---|---|
| `rerank` | 0.0000 | **0.0000** | 0.8568 | **0.45** |
| `dense` | 0.3044 | 0.4862 | 0.6954 | 0.30 |
| `lexical` | 0.0000 | 0.0000 | 0.0000 | — |
| authority + coherence | — | 1.0 | — | 0.25 (unconditional) |

Rerank score distribution: `>0` on only 40/165 probes, `>0.1` on 6, `>0.5` on 2.

The `gate_open` counterfactual isolates the gate cleanly: with `min_confidence = 0.0`,
`C1` falls from 81 to **0** and every answerable probe is served ranked evidence. Nothing
else about retrieval changes. `R3 = 0` in both configurations — neighbour expansion never
had to rescue a missing gold document, because ranking had already found it.

*Correction:* earlier iterations of this harness reported `R3` as 2 and then 32. Both were
a bug in the analysis code, not in the product: neighbour chunks share their seed's
`source_id`, so subtracting neighbour source-ids also removed the ranked hit. `R3` is
computed from non-neighbour served items now, and the true value is 0.

Two independent defects compound:

1. **The largest weight sits on the weakest signal.** `rerank` carries 0.45 but is zero for
   76% of probes.
2. **A quarter of the score is unconditional.** `authority` and `coherence` are both 1.0 for
   any single approved chunk from one institution, so 0.25 of every score is independent of
   relevance. Only 0.75 of the scale ever responds to whether the evidence answers the
   question.

Lowering the threshold is not a fix: at `min_confidence = 0.45`, `C1` falls only from 81 to
80. The distribution is not near the boundary — it is nowhere near it.

## 2. "Hybrid" retrieval is dense-only (`lexical = 0` on 165/165 probes)

The lexical channel returned **zero rows for every query in every language**, and the
`dense_only` ablation reproduces baseline results *exactly* — removing the lexical channel
changes nothing, because it contributed nothing.

Root cause: `websearch_to_tsquery` **ANDs every term**, and the `'simple'` text-search
configuration does not strip stopwords, so every stopword becomes a required term:

```
'I made a payment but it is not recognised on my statement'
  -> 'i' & 'made' & 'a' & 'payment' & 'but' & 'it' & 'is' & 'not' & ...
```

Measured against the live index:

| Strategy | Matches |
|---|---|
| **Current** — `'simple'` + `websearch_to_tsquery` (AND) | **0** |
| `'english'` config + `websearch_to_tsquery` (AND) | 0 |
| `'simple'` + `plainto_tsquery` (also AND) | 0 |
| `'simple'` + OR over terms >3 chars | **10** |

Short queries do match (`"card dispute"` → 3, `"savings account"` → 7), which is why this
survives unit testing: the failure appears only with natural-language ticket text.

Consequence: reciprocal-rank fusion runs over `[dense, [], []]` — the lexical ranking is
computed twice, once per query variant (`retrieval.py:68-71`), and both are empty — so RRF
degenerates to the dense ordering.

## 3. Language

### 3.1 Detection (`L1a`) — 15,395 held-out rows

| Language | Accuracy | 95% CI | Dominant confusion |
|---|---|---|---|
| english / sinhala / tamil | 100% | — | — (Unicode-block match) |
| singlish | 91.6% | [90.5, 92.5] | 249 → english |
| **tamilish** | **25.6%** | [24.1, 27.2] | **2,284 → english (74%)** |

Paired McNemar against tamilish: 2,290 discordant pairs vs 0, p ≈ 0.

The root cause is transliteration-variant mismatch, not concept difficulty. Three of seven
tamilish tokens are effectively dead, while high-signal forms are absent entirely:

| Listed token | Fires on tamilish | Absent token | Fires on tamilish | On english |
|---|---|---|---|---|
| `epdi` | **0.00%** | `enoda` | 46.90% | 0.00% |
| `venum` | 0.29% | `naan` | 42.58% | 0.00% |
| `aayiduchu` | 0.65% | `enakku` | 15.04% | 0.00% |
| `irukku` | 4.71% | `eppadi` | 11.24% | 0.00% |

The corpus writes `eppadi`/`irukka`; the list contains `epdi`/`irukku`. Singlish survives
only because one token, `eka`, fires on 82.75% of the track — and on **0.00%** of English,
disproving the prior assumption that it was a false-positive risk. Two singlish tokens are
single-letter variant misses: `puluwanda` fires 0.00% while the corpus writes `puluvanda`
(10.10%).

Scope: production overrides detection with `ticket.response_language` on the first turn, so
this error bites **follow-up chat turns**, where `language=None` is passed.

### 3.2 Safety-rule coverage — a language-equity failure

Of the **113** tickets whose English rendering triggers a safety escalation, the *same
tickets* in other languages trigger as follows:

| Language | Also escalated | Coverage |
|---|---|---|
| english | 113/113 | 100.0% |
| sinhala | 4/113 | **3.5%** |
| tamil | 3/113 | **2.6%** |
| singlish | 4/113 | 3.5% |
| tamilish | 4/113 | 3.5% |

**109 of 113 are missed in both Sinhala and Tamilish.** These are translations of identical
customer questions, so this is a defect by construction: a request that is escalated to a
human in English is routed into RAG generation in every other language.

Root cause: `safety.py` holds 5 English phrases + 1 Sinhala + 1 Tamil for
`private_account_data`, and 11 English + 1 + 1 for `financial_action`. Code-mixed Sri Lankan
text keeps the English **noun** but localizes the **possessive**, so the two-word rule
`"my statement"` never matches:

```
en  (ESCALATED): My statement has Rs 10 I have been charged showing up on it.
si  (MISSED)   : මගේ statement එකේ මට අයකරපු Rs 10ක් පේනවා.
ta* (MISSED)   : Enoda statement-la enakku charge panna Rs 10 kaattuthu.
```

### 3.3 Retrieval penalty for non-English queries

Median score of the top hit, against an entirely English corpus:

| Language | Median dense | Median confidence |
|---|---|---|
| english | 0.5560 | 0.4168 |
| sinhala | 0.5004 | 0.3897 |
| tamil | 0.4654 | 0.3502 |
| tamilish | 0.4640 | 0.3530 |
| singlish | 0.4396 | 0.3580 |

Cross-lingual querying costs roughly **0.09–0.12 cosine**. Ranked recall stays high
(88.9–100%), so BGE-M3 still finds the right document — but the confidence penalty pushes
non-English queries further below a gate they already cannot pass.

## 4. Latency

Baseline, dev split, 165 probes (only the uncached run is representative):

| Stage | Median (ms) | Share |
|---|---|---|
| `embed` (HuggingFace Inference API) | **1243** | **85%** |
| `rerank` (local FlashRank ONNX) | 144 | 10% |
| SQL + fusion + neighbours *(derived)* | 55 | 4% |
| **end-to-end p50 / p95** | **1464 / 2432** | |

Latency is almost entirely one remote embedding call. The database contributes ~4%, though
against only 31 chunks that will not generalise to a production-scale corpus.

`P1` counts (9 per configuration) are a within-run p95 flag and self-referential by
construction: they identify relative outliers, not an absolute budget breach.

Run-to-run variance is real and worth recording. A second baseline run at a different time
of day gave p50 **1981 ms** (vs 1464 ms), 5 probes past the 20s timeout (`S3`), and — most
importantly — **`S2` fired spontaneously on 4 of 165 probes (2.4%)**: the hosted embedding
provider failed intermittently and retrieval silently degraded to lexical-only, which on
this corpus means no usable retrieval at all (§2). Silent degradation is not a hypothetical
risk; it happened unprompted during an ordinary run, and nothing in the response would tell
a customer or an operator.

## 5. Guardrails

| Measure | Result |
|---|---|
| Bypass rate on the repo's own 18-case corpus (`X1`) | **83.3%** (3/18 detected) — reproduces the recorded 16.7% |
| Closed by normalizing *before* the check | **1 of 15** (`fullwidth_unicode` only) |
| False positives on 15,395 real tickets (`X2`) | **0** in every language |
| `ticket_context` scanned | **No** — a payload is caught as a query, invisible in `ticket_context` |

The normalization result is worth stating precisely, because it is easy to over-claim: the
raw-vs-NFKC split is a genuine structural bug, but fixing it moves detection from 3/18 to
4/18. The remaining 14 bypasses — base64, rot13, leetspeak, roleplay framing, payload
splitting, Sinhala/Tamil paraphrase — need a semantic check, not more substrings.

The zero false-positive rate is the useful half: there is measured headroom to make the
injection filter considerably stricter at no observed cost to real traffic.

## 6. Structural defects

**Citation validation (`G2`).** Two confirmed defects:

- *False accept* — an answer citing an unranked neighbour chunk validates cleanly.
  `_expand_neighbors` appends neighbours into the same `[E1..En]` numbering that
  `citations_are_valid` range-checks, so unranked context is citable as if retrieved.
- *False reject* — a bolded heading without a trailing colon is treated as an uncited
  factual block, so a well-formed bulleted answer is refused over formatting.

**Chunking.** 5 documents → 31 chunks, median 370 chars, **zero overlap**:

- Max chunk is **3,165 chars against an 1,800 `max_chars` setting** — splitting occurs only
  at paragraph boundaries, so an oversized paragraph is emitted whole.
- 9 of 31 chunks are under 200 chars. `loans_peoples_bank_pahasu.md` fragments into 5 chunks
  with a median of 134 chars, and it is a golden-set retrieval target.

**Confidence falsy-chain.** `top.dense_score or top.lexical_score or top.fused_score * 30`
is falsy chaining, not null-coalescing. A genuine `0.0` dense score silently falls through
to the lexical score; dense `0.0` vs `0.001`, all else equal, swings confidence by
**0.2697**.

## 7. What could not be measured, and why

The generation and groundedness lane is **rate-limited to the point of being
unmeasurable on this account**, and it would be wrong to report the numbers it produced as
findings:

- **Groq is on a 1000 output-tokens-per-minute tier.** In a 40-probe generation run, **24
  probes (60%) failed with `S1` provider-unavailable**, and 5 more hit the 20s timeout. In
  the 165-probe `gate_open` run — where evidence reaches the model on every answerable
  probe — **`S1` reached 73 of 90 (81%)**.
- **The Gemini key is free-tier, limited to 20 requests/day**, and the judge exhausted it.
  Both graded answers returned `ProviderError`, so `judge_failures = 2/2`.

Net: **2 of 40 probes produced an answer, and 0 were successfully graded.** Across every
live run in this study, exactly **one** probe at a time produced a draft answer.

A note on harness semantics, since it affects how these runs should be read: `--mode
retrieval` disables only the judge. `assist()` is a single pipeline, so the provider is
still called whenever evidence clears the gate. At the shipped threshold that is nearly
free — 4 of 165 probes — which is precisely why the gate's severity was invisible until
`gate_open` made generation actually happen.

Consequently `G1` (unsupported generation), `R2` (irrelevant chunk) and citation-correctness
are **not measured**, and are recorded as `not_measured` in
[rag_error_analysis.csv](rag_error_analysis.csv) rather than as zero. The done-criterion
"groundedness conclusions are evidence-backed" is **not met** for generation-side
groundedness. It *is* met for the retrieval and gating behaviour that determines whether
generation happens at all — which, on this evidence, is the more binding constraint anyway.

To close this gap: a paid Gemini tier (or any judge with >20 req/day) and a Groq tier above
1000 OTPM. No code change is required — `run_analysis.py --mode full` is ready.

## 8. Operational defects found while bringing the environment up

Not the object of study, but each blocks the system outright, and all three were found by
running it rather than reading it.

1. **All three `.env` model pins were stale**, each causing 100% provider failure:
   `llama-3.3-70b-versatile` returns **HTTP 404 (decommissioned)**; `gemini-2.5-flash`
   returns **404, "no longer available to new users"**. In both cases `config.py`'s own
   defaults were already correct, so `.env` was overriding working values with dead ones.
2. **`qwen/qwen3.6-27b` (the `config.py` default) fails HTTP 429 on this account.**
   `providers.py` sets `max_completion_tokens: 2048` for `qwen/` models, exceeding the
   1000 OTPM tier limit. Because 429 is in `RETRYABLE_STATUS`, the provider burns **two
   futile retries with backoff** on a deterministic quota rejection before escalating —
   pure added latency. Retries should distinguish rate-limited-by-load from
   request-too-large-for-tier. (Dropping the qwen parameters returns 200 but leaks raw
   `<think>` reasoning into the answer, so that is not a workaround.)
3. **`app/inference/services.py` imports `torch` and `transformers` but uses neither.**
   Added by the OCR branch (`main` has the file clean) and declared in no extra, so
   `pip install -e '.[dev,rag]'` did not provide them. `tests/conftest.py` imports that
   module unconditionally, so **the entire pytest suite failed to collect**. Resolved here
   by declaring a new `inference` extra and installing it in both CI jobs, which restores
   `pytest` and `mypy` — but **`ruff` still reports `F401` for both imports**, because
   declaring a dependency does not make an import used. Clearing the lint gate needs either
   deletion or an explicit `# noqa: F401`.
4. **`swift-eval-rag` cannot run on Windows.** `eval_runner.py:47` calls `Path.read_text()`
   with no `encoding=`, so the multilingual golden set is decoded as cp1252 and raises
   `UnicodeDecodeError`. The same bug at `tests/database/test_integrity.py:345` fails two
   tests. Both clear under `PYTHONUTF8=1`, but the production path should pass
   `encoding="utf-8"` explicitly.

---

## Trade-offs, mitigations and priorities

Ordered by measured impact. These are recommendations, not changes: this workstream measured
the system as it stands and made no production edits beyond one dead-import deletion.

**P1 — Rebalance or replace the confidence gate.** *Unblocks ~90% of answerable queries.*
The gate cannot be fixed by moving the threshold. In order of preference: (a) cut the
`rerank` weight sharply, or gate on `dense` directly; (b) replace FlashRank with a
multilingual cross-encoder — BGE-reranker-v2-m3 pairs with the BGE-M3 embedder already in
use; (c) stop summing relevance and provenance into one number, so `authority`/`coherence`
no longer contribute an unconditional 0.25.
*Trade-off:* opening the gate admits weaker evidence, so it must ship with working
groundedness validation (§7), not before it.

**P2 — Make the lexical channel functional.** *Restores half of "hybrid" retrieval.* Build
an OR query (`to_tsquery` with `|`) instead of `websearch_to_tsquery` and let RRF rank — that
is what fusion is for. *Trade-off:* OR returns more low-quality candidates, which is
tolerable precisely because RRF and the reranker rank them, but it grows the candidate set
and SQL time (currently 4% of latency, so there is room).

**P3 — Close the safety-rule language gap.** *109 of 113 escalations are currently missed
for non-English speakers.* Match single high-signal nouns (`statement`, `balance`,
`transfer`) plus per-language possessives, and add a parity test over the paired corpus so
coverage is enforced rather than assumed. *Trade-off:* single-noun matching raises escalation
volume; the measured X2 headroom (0 false positives in 15,395) suggests that is affordable,
but it shifts load onto human agents.

**P4 — Rebuild the language keyword lists from the corpus.** *Tamilish detection 25.6% →
plausibly >90%.* Every candidate token in §3.1 fires on >2% of its track and 0.00% of
English. *Trade-off:* these lists would then be corpus-derived, so they must be fitted on
dev and confirmed once on holdout, exactly as `datasets/translation/run_prompt_eval.py`
already requires for prompts.

**P5 — Surface silent degradation.** `diagnostics.embedding_fallback` already carries the
signal and nothing alerts on it. The `embedding_outage` ablation showed `S2` firing on
165/165 probes while every response still looked well-formed.

**P6 — Cache or co-locate embeddings.** 85% of latency is one remote call. Caching query
embeddings, or moving to the local `rag-local` extra, is the largest single latency lever.

**P7 — Stop neighbour chunks being citable.** Number only ranked evidence in the prompt, or
mark neighbours so that a citation to one fails validation.

**P8 — Fix the `.env` model drift and the futile-retry path.** See §8.

---

## Residual limitations

- **The corpus is 5 English documents / 31 chunks.** Retrieval metrics describe this corpus,
  not production scale; database latency (4%) will not generalise; and every multilingual
  query retrieves English evidence by construction.
- **Generation-side groundedness is unmeasured** — see §7. `G1`, `R2` and citation
  correctness have no sample behind them.
- **Probe labels are authored, not human-verified.** `relevant_sources` was assigned by
  reading the corpus text, with justifications recorded in `probe_manifest.json`. They need
  a human spot-check before being quoted as ground truth.
- **BANKING77 and the corpus are different banking domains.** Answerable coverage is thin,
  and `SRC-LOAN-001` is untested by the probe set.
- **Wrapper timing excludes** FastAPI middleware and connection-pool acquisition, so latency
  figures are a floor, not the whole cost.
- **Only the first configuration in each sweep has representative latency**; later ones reuse
  cached query embeddings. Each run records this as `latency_is_representative`.
- **`L1b` uses the same detector as `L1a`**, whose romanized accuracy is 25.6%, so
  output-language measurement would be noisy even with enough samples.
- **Holdout is unscored.** Every live number above is dev-split; the holdout half of the
  frozen manifest is deliberately untouched so it remains available for a clean
  before/after comparison once fixes land.

---

## Reproduction

```bash
cd backend
python -m venv .venv && ./.venv/Scripts/python.exe -m pip install -e '.[dev,rag,inference]'
docker compose up -d postgres          # compose.override.yaml publishes 5433
./.venv/Scripts/python.exe -m alembic upgrade head
./.venv/Scripts/swift-ingest-kb.exe

export PYTHONUTF8=1 PYTHONPATH=.
python evaluation/analysis/env_check.py            # all four dependencies must PASS

# offline lane — no database, no providers, no cost
python evaluation/analysis/offline_language.py
python evaluation/analysis/offline_guardrails.py
python evaluation/analysis/offline_pipeline.py

# live lane
python evaluation/analysis/probes.py               # rebuild the frozen probe set
python evaluation/analysis/run_analysis.py --mode retrieval --split dev \
    --cache-embeddings --configurations baseline dense_only lexical_only no_rerank \
    embedding_outage final_limit_3 final_limit_8 candidate_limit_10 candidate_limit_40 \
    min_confidence_045 min_confidence_065 --out dev_retrieval_sweep
python evaluation/analysis/report.py               # regenerate rag_error_analysis.csv
```

`PYTHONUTF8=1` is required on Windows — see §8.4.

## Verification state at time of writing

| Check | Result |
|---|---|
| `pytest -q` (with `PYTHONUTF8=1`) | **154 passed, 3 skipped, 22 xfailed, 0 failed** |
| All 22 `xfail`s still `xfail` | **Yes** — no `XPASS`, so no production behaviour moved |
| `mypy app` | 2 pre-existing `type-arg` errors in `ocr.py` / `routes.py` (OCR branch) |
| `ruff check app tests` | 4 pre-existing errors, all in OCR-branch files (§8.3) |
| `git diff --stat -- backend/app` | **1 file, 1 deletion** — the dead `StaticFiles` import only |
| Offline lane reproducibility | **Bit-for-bit identical** across reruns (confusion matrix, per-language, McNemar, root cause, bypass corpus, safety coverage) |
| `swift-eval-rag` | Unchanged and still loads its 5 golden + 7 guardrail cases |

The `xfail` result is the load-bearing one: this workstream set out to measure the system as
it stands, and 22 known-failing behaviours are still failing in exactly the same way.
