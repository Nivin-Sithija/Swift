# v8 relabel + SLM multi-task results

Everything below is measured after the v8 sentiment relabel (711/13,077 labels changed per
language: 557 train + 154 test) and the joint multi-task Gemma-3-1B experiments that answer
`RESULTS.md` open item #8 ("joint multi-task fine-tuning, and LoRA adapters over a shared base,
both untested"). Split sha `e7b5934392cd` throughout except where marked. One table, test set
only, all three tasks, all five architectures. Every cell is fit on train+dev and scored on test
exactly once, per this project's own rule — nothing here was re-touched after being recorded.

| Task (test, frozen split) | Metric | Classical | LaBSE (full FT) | Gemma-3-1B (single adapter/task) | Gemma-3-1B joint — 3 heads, 1 adapter | Gemma-3-1B joint — 1 head, 1 adapter, prefixed |
|---|---|---:|---:|---:|---:|---:|
| Intent (77-way) | macro-F1 | **0.8307** | 0.8854¹ | 0.8586 | 0.8616 | 0.8673 |
| Sentiment (binary) | negative-F1 | **0.6663** | **0.7138** | **0.7126** | 0.7042 | 0.7048 |
| Priority (3-way) | macro-F1 | 0.8722 | 0.8900 | 0.8898 | 0.8895 | 0.8904 |

¹ LaBSE intent is a teammate's number on the **official BANKING77 split** (`train_transformer.py`,
pooled ALL-track row), not the frozen swiftbench split `e7b5934392cd` every other cell in this table
uses — not directly comparable to the rest of the Intent row. A frozen-split LaBSE intent test was
deliberately not (re-)run to avoid duplicating that result.

Priority's three SLM cells, sentiment's two joint-multi-task cells, and the entire Intent row except
LaBSE are first-time numbers on this split — only dev (or nothing at all) existed for any of them
before this table.

## What changed under v8

Sentiment is the only task v8 touched. Every sentiment number above is a fresh measurement, not
carried over — classical test negative-F1 alone moved **0.4572 → 0.6663** (+0.209), and for the
first time on this project, test now scores *above* dev for the sentiment classical champion.
LaBSE and Gemma both cleared 0.71 on test, comfortably past the old best (LaBSE, v6-pilot labels,
0.5664). Confirms the standing finding that relabeling beats remodeling by a wide margin.

## The joint multi-task question (open item #8)

First test-set measurements ever for this question. Both joint variants **beat single-task on
intent** (3-heads +0.0030, shared-head +0.0087), are a wash on priority (±0.0006–0.0009), and give
up a little on sentiment (-0.0084, -0.0078) — the smallest gap of the three tasks and much smaller
than the same comparison read on dev (-0.024 for shared-head there). One shared Gemma-3-1B backbone
serving all three tasks costs at most ~0.008 headline points on any task, and on intent it's free
money: sharing the backbone regularizes rather than dilutes.

The shared-head variant's off-task prediction rate stays effectively 0% on test too (0.0000–0.0001
across all three tasks): a plain text prefix reliably steers a single shared classification head
into the right task's region of the 82-way union space, with no masking help at inference. Between
the two joint shapes, shared-head is the better one here — it wins or ties 3-heads on all three
tasks despite being the more literal "one model, one head" reading that the embedding-head
literature (`SLM_RESEARCH.md` §1) predicted would be the *weaker* prior.
