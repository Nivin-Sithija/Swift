# RAG / system error taxonomy

Failure classes for the consumer RAG assistant (`POST /api/v1/tickets/{id}/assistance`),
with the detection rule used to assign each one. Classes are assigned by
`backend/evaluation/analysis/taxonomy.py`; one probe can carry several at once, because
a single request can miss retrieval *and* answer in the wrong language.

Two principles shape the list:

1. **Separate "not found" from "found and discarded."** `RetrievalResult.evidence` is
   emptied when confidence falls below `rag_min_confidence` ([retrieval.py:91](../../backend/app/rag/retrieval.py#L91)),
   so reading only that field makes a working retriever look broken. The harness records
   the reranker's output as well, which is the ranked set *before* the gate. `R1` and
   `C1` are the two halves of what would otherwise be one misleading number.
2. **A missing grade is not a passing grade.** Judge-dependent classes are assigned only
   when a grade came back. Judge outages reduce coverage; they never manufacture health.

## Retrieval

| Class | Name | Detection |
|---|---|---|
| `R1` | retrieval miss | No labelled relevant `source_id` appears in the **ranked** evidence. Retrieval genuinely failed; the gate is not implicated. |
| `R2` | irrelevant chunk | Judge relevance < 0.5 despite evidence being served. |
| `R3` | neighbour-only support | The gold source reached the prompt *only* via `_expand_neighbors`, never as a ranked hit. |
| `C1` | gate-suppressed evidence | Retrieval ranked a relevant source, then `evidence_confidence` fell below `rag_min_confidence` and **all** evidence was discarded. |

`R3` matters because neighbour chunks are appended to the same `[E1..En]` numbering the
model cites from ([retrieval.py:136-169](../../backend/app/rag/retrieval.py#L136-L169)),
so unranked context is citable as though it had been retrieved.

## Generation and grounding

| Class | Name | Detection |
|---|---|---|
| `G1` | unsupported generation | Judge faithfulness < 0.5: claims not entailed by the evidence. |
| `G2` | citation error | Answer cites a neighbour chunk, or judge citation-correctness < 0.5. |
| `G3` | false escalation | An answerable probe was refused for a reason other than provider outage or guardrail. |
| `G4` | missed escalation | An unanswerable probe produced a cited answer. |

`G4` is the class the existing 5-case golden set cannot measure at all: it contains only
two escalation cases, both safety-rule triggers, and no probes for questions the corpus
simply does not cover.

## Language

| Class | Name | Detection |
|---|---|---|
| `L1a` | language detect error | `detect_consumer_language` output differs from the probe's true language. |
| `L1b` | output language mismatch | The **answer's** detected language differs from the required language. |

These are deliberately separate. The shipped `language_correctness` metric
([eval_runner.py:129](../../backend/app/rag/eval_runner.py#L129)) compares the detected
input label against the expected label, so it measures the detector and never inspects
the answer. `L1b` is the metric that was missing.

Caveat: `L1b` uses the same detector as `L1a`, whose romanized accuracy is poor, so `L1b`
is noisy for singlish/tamilish output and is reported with that limitation attached.

## System and performance

| Class | Name | Detection |
|---|---|---|
| `S1` | provider failure | Escalation reason `generation_provider_unavailable` after retries. |
| `S2` | silent lexical degradation | `diagnostics.embedding_fallback != "none"`: dense retrieval failed and the request quietly continued lexical-only. |
| `S3` | timeout | End-to-end latency exceeded `rag_request_timeout_seconds`. |
| `P1` | latency spike | Latency above the run's own p95. |

`S2` is the highest-risk class operationally, because it is the only failure here that is
invisible to the customer *and* to the response payload: retrieval degrades to lexical-only
and still returns a confident, cited answer
([retrieval.py:49-55](../../backend/app/rag/retrieval.py#L49-L55)).

## Adversarial

| Class | Name | Detection |
|---|---|---|
| `X1` | guardrail bypass | An adversarial probe was not escalated. |
| `X2` | guardrail false positive | An ordinary banking ticket was escalated by an injection rule. |

## Cross-cutting: language-equity failures

Not a per-probe class but a comparison across the paired corpus. Because the five language
tracks are translations of one ticket set, any rule that fires on a ticket in one language
and not in another is a defect by construction — the underlying customer intent is
identical. Measured as `SAFETY-EQ` in
[rag_error_analysis.csv](rag_error_analysis.csv).

## Detection thresholds

| Setting | Value | Source |
|---|---|---|
| Judge pass mark | 0.5 | `taxonomy.JUDGE_THRESHOLD` |
| Timeout | `rag_request_timeout_seconds` (20.0s) | `config.py` |
| Latency spike | run-relative p95 | computed per run |
| Confidence gate | `rag_min_confidence` (0.55) | `config.py` |
