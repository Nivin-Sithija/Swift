# Swift viva: rapid revision sheet

Use this before the viva. The [full guide](SWIFT_VIVA_QUESTIONS_AND_ANSWERS.md) has **505 questions and answers**, source references and worked examples. The [source map](SWIFT_SOURCE_MAP.md) indexes 302 first-party code/notebook files.

## Your opening answer

“Swift is a multilingual banking-support ticket triage prototype for English, Sinhala, Tamil and romanized messages. Customers submit text and optional image evidence. The system prepares intent, priority and sentiment predictions, allows staff corrections, and orders tickets using continuous urgency and waiting-time aging. A separate RAG flow retrieves approved policy sources for customer assistance. We evaluated classical and transformer models, but the project has no bank-core access and is not validated for production banking.”

## The three flows you must distinguish

1. **Text ticket:** form → FastAPI validation → store original → hosted LaBSE or named fallback → store predictions and template → staff review and response workflow.
2. **Image:** existing ticket → separate upload → validation → OCR → masked extraction → local SVM intent and rules → update unreviewed predictions.
3. **RAG:** owner-only request → ticket/current question → safety checks → approved/current hybrid retrieval → generation → citation checks → direct guidance or escalation result.

The RAG result is currently returned directly. It is not the same object or approval process as a stored ticket response.

## Twenty high-priority questions

### 1. What is the problem?
Support teams must understand mixed-language issues and screenshots, prioritize a backlog and respond consistently. Swift automates initial analysis while making evidence and human decisions visible.

### 2. What are the three prediction tasks?
Intent is the issue type; priority is handling urgency; sentiment is expressed tone. Seriousness and anger are different, so a calm fraud report can need careful review without being Negative.

### 3. Why five tracks if the project is trilingual?
English, Sinhala and Tamil are three languages. Singlish and Tamilish/Tanglish are romanized representations of Sinhala and Tamil.

### 4. What did you add to BANKING77?
Four non-English/romanized tracks, auxiliary sentiment and priority labels, a frozen grouped split, benchmarks, OCR experiments and application workflows. English text and 77-way intent labels came from the source corpus.

### 5. Why split by ID?
Five renderings share one underlying ticket. Independent row splitting would leak equivalent content across train and dev. The split manifest groups source tickets; exact repeated text across source splits needs a separate audit.

### 6. Why not accuracy for sentiment?
An always-Neutral model gets about 95.38% accuracy on current training labels but detects no Negative tickets. Negative-F1 measures the minority class that matters for the intended review use.

### 7. Why LaBSE?
Matched experiments support its multilingual intent performance. The runtime serves three separately trained LaBSE task models in one Space, not one jointly trained multitask model.

### 8. Why word plus character TF-IDF?
Words capture banking terms and short phrases. Character n-grams tolerate romanized spelling differences and suffixes. The combination is a strong, inexpensive baseline.

### 9. What was the Unicode bug?
The default sklearn word tokenizer dropped Indic combining marks. The harness replaces it with Indic-aware tokenization for native scripts and measures character preservation.

### 10. What if the hosted model fails?
After the submission budget, intent becomes unknown with confidence zero and an explicit timeout/unavailable version. Priority/sentiment rules provide fallbacks and manual review is flagged.

### 11. How does OCR fusion work?
Confident customer text wins at confidence >=0.60. Stronger OCR can replace weak text. Reviewed predictions stay unchanged; attachment rules can raise severity but not lower it.

### 12. Why calibrate SVM confidence?
SVM margins are not probabilities. A logistic function of the top margin and top-to-runner-up gap estimates prediction correctness. This scalar is not a full intent posterior.

### 13. What is dynamic urgency?
It combines priority expectation, Negative probability and intent risk, then increases with waiting time relative to a class-specific window. It ranks tickets more finely than a discrete priority label.

### 14. Why log-pool priority and intent?
Intent and priority are strongly related. The geometric combination of the direct priority head and intent-conditioned priority chain performed better on the paper's saved probability comparison. It is a measured choice, not an independence assumption.

### 15. What is RAG?
It retrieves approved policy evidence and supplies it to a generator with citation requirements. Sources can be updated independently of classifier weights. Valid citation formatting does not prove semantic faithfulness.

### 16. How do you protect accounts?
Password hashing, signed access tokens, rotating hashed refresh sessions, database-checked roles/activity and per-object ownership checks. UI route guards are navigation aids; backend checks determine permission.

### 17. Why PostgreSQL?
Structured ticket relationships need constraints and transactions; pgvector and full-text search also support the knowledge base. SQLite fixtures do not prove every PostgreSQL-specific feature works.

### 18. What is actually asynchronous?
HTTP/database operations yield while waiting and Tesseract is offloaded to a thread. Ticket analysis still runs inside the request; the Redis/Dramatiq actor is a placeholder.

### 19. What evidence do you have?
Saved classifier predictions, OCR benchmarks, queue simulation artifacts, historical test evidence and a fresh dataset/prediction audit. Each has its own split, label version, build and scope.

### 20. What are your main limitations?
Label-version mismatch, translation/romanization realism, incomplete production data protections, workflow/documentation differences and unmeasured concurrency on expensive paths.

## Numbers to know, with provenance

| Number | Meaning |
|---|---|
| 77 | Intent classes. |
| 2 | Learned sentiment classes: Neutral and Negative. |
| 3 | Learned priority classes: Low, Medium and High. |
| 4 | Application priority tiers: also Critical, from rules/staff. |
| 9,998 / 3,079 | Underlying official-source train/test tickets in the local corpus. |
| 65,385 | Total rows over five tracks; not independent tickets. |
| 8,500 / 1,498 / 3,079 | Frozen train/dev/test ticket counts. |
| e7b5934392cd | Frozen split identity; not a label-content hash. |
| 49,990 / 15,395 | Pooled train+dev/test row counts. |
| 462 / 101 | Current train/test Negative counts per track. |
| 0.883424 | Rechecked saved LaBSE intent macro-F1; matches current truth. |
| 0.713819 | Saved LaBSE sentiment Negative-F1 against archived truth. |
| 0.445906 | Same sentiment predictions against current CSV truth. |
| 770 rows / 154 IDs | Archived/current sentiment test-label differences. |
| 0.873358 | Rechecked saved TF-IDF/SVM priority macro-F1. |
| about 0.8900 | Separate saved LaBSE priority result, not the SVM score. |
| 0.60 | Hardcoded review floor and text-intent fusion floor. |
| 5 seconds | Outer hosted-inference budget for ticket submission. |
| 15 minutes / 7 days | Default access-token/refresh lifetimes. |
| 5 MiB / 10 MiB | Frontend image limit / backend default attachment limit. |
| 1,024 | Configured BGE-M3 vector dimensions. |
| 10 / 5 | Default RAG candidate/final seed limits. |
| 0.50 | Configured evidence threshold; heuristic relevance gate. |
| 365 days | Source review-age filter. |
| 500 / 2,000 | Synthetic base screenshots / augmented OCR images. |
| 1,868 | Scored downstream synthetic intent rows after unmatched OTP exclusion. |
| 0.0106 | Saved OCR SVM held-out calibration ECE. |
| 30 seconds | Local queue aging refresh interval, not full data polling. |

Source: [fresh audit](SOURCE_AUDIT.json), [configuration](../../backend/app/core/config.py), [OCR calibration](../../ml/models/tfidf_linear_svm_all.calibration.json), [results](../../ml/reports/RESULTS.md).

## Formulas to explain

**Classification**

Precision = TP/(TP+FP)

Recall = TP/(TP+FN)

F1 = 2TP/(2TP+FP+FN)

Macro-F1 = mean of class F1 scores.

**Priority combination**

chain[k] = sum_i P(intent=i)·P(priority=k | intent=i)

pooled[k] = normalize(sqrt((head[k]+1e-12)·(chain[k]+1e-12)))

**Urgency**

E[severity] = 0.5·P(Medium)+P(High)

S = max(0.01, 0.8·E[severity] + 0.1·P(Negative) + 0.1·intent_criticality)

U = S·(1+16·waiting_minutes/SLA_minutes)

Low=480, Medium=120, High/Critical=30 minutes. These are research assumptions.

Example: posterior=(.2,.3,.5), Negative=.4, criticality=.6 → E=.65 and S=.62. At 15 minutes with the High window: U=.62·9=5.58.

**RRF**

RRF(chunk) = sum_channels 1/(60+rank_in_channel).

**OCR**

CER or WER = (substitutions+deletions+insertions)/reference length.

## Twelve traps to avoid

1. **“Every answer needs human approval.”** Stored responses do; current RAG assistance returns directly.
2. **“Escalation notifies an agent.”** The RAG route result does not persist escalation or send a notification.
3. **“All model text is masked.”** OCR text is masked; initial text classification and RAG use original customer text.
4. **“All attachments are private.”** The protected download route coexists with an unprotected static storage mount.
5. **“The worker handles tickets.”** The actor is a placeholder; processing is inline.
6. **“Categories automatically route to queues.”** Initial creation uses General Support; the mapping is not applied.
7. **“Positive and Critical are learned classes.”** They are application compatibility/operational tiers, not these learned outputs.
8. **“Voice is implemented.”** No application ASR flow was found.
9. **“RAG reads image OCR directly.”** The current assistance request does not append OCR extraction.
10. **“The dataset is leakage-free.”** Grouping fixes translation leakage; historical exact source-text overlaps remain a separate concern.
11. **“Read-only p95 proves AI capacity.”** Expensive classification/OCR/RAG paths need their own concurrent measurements.
12. **“The current sentiment score is 0.7138.”** Qualify it as archived-label evaluation and disclose the current-label mismatch.

## Know these files without hesitation

- [routes.py](../../backend/app/api/v1/routes.py): ticket lifecycle and API authorization.
- [services.py](../../backend/app/inference/services.py): hosted models, fallback, calibration and fusion.
- [urgency.py](../../backend/app/domain/urgency.py): equations, modes, aging and tie breaks.
- [RAG service](../../backend/app/rag/service.py): routing, generation and validation.
- [retrieval.py](../../backend/app/rag/retrieval.py): hybrid search, RRF and evidence confidence.
- [security.py](../../backend/app/core/security.py): password hashes and tokens.
- [entities.py](../../backend/app/models/entities.py): persistent relationships.
- [splits.py](../../ml/swiftbench/splits.py): grouped train/dev membership.
- [models.py](../../ml/swiftbench/models.py): classical feature choices.
- [train_encoder.py](../../ml/swiftbench/train_encoder.py): fine-tuning defaults and epoch selection.
- [restTicketService.ts](../../frontend/src/services/restTicketService.ts): authentication refresh, API mapping and separate upload.
- [utils.ts](../../frontend/src/lib/utils.ts): filtering and dynamic local score updates.

## Demo readiness

Verify migrations, Space availability, SVM/calibration files, OCR packs/provider, knowledge ingestion and generation configuration. Use fictional examples. Demonstrate stored response approval separately from direct policy assistance. Be ready to show explicit fallback if a provider fails.

## A practical study sequence

**First session:** opening explanation, the three flows, dataset/split, task metrics and current results.

**Second session:** trace classify, fuse_intent, ticket_urgency and ConsumerRAGService.assist through their source files.

**Third session:** auth/database/frontend contracts, security gaps, historical test scope and a live demo.

**Final revision:** answer the twenty questions above aloud, calculate one urgency example, and practise acknowledging limitations precisely.

If you do not know a measurement: “We did not measure that scenario; this artifact establishes X, and I would test Y to answer your question.” If you did not build a feature: “It is proposed; the implemented code currently does X.”

