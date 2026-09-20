---
title: "Swift — Master Test Plan and Test Report"
subtitle: "Full-system verification, data-science evaluation, and error analysis"
author: "Swift project team / Codex test execution"
date: "20 September 2026"
toc: true
toc-depth: 3
---

**Document version:** 2.0  
**System under test:** Swift trilingual, multimodal banking-support ticket triage  
**Repository commit:** `3076ca5fb2f8a9395d0b1c107c0e86dcb973d768` plus the remediations recorded here  
**Execution date:** 20 September 2026  
**Overall verdict:** **CONDITIONAL PASS — severe defects closed; controlled release is supportable with the residual model-quality risks below**

# Revision History {.unnumbered .unlisted}

| Date | Version | Description | Author |
|---|---:|---|---|
| 20 Sep 2026 | 1.0 | Initial system, security, and DS execution report | Swift project team / Codex |
| 20 Sep 2026 | 2.0 | Severe defects remediated; complete regression, live Ollama RAG, business-load, accessibility, and security evidence refreshed | Swift project team / Codex |

# Executive Test Summary {.unnumbered}

| Area | Final result | Evidence |
|---|---|---|
| Backend and API | PASS | 208/208 Pytest cases; no skips or expected failures; 72% line and 50% branch coverage |
| Frontend | PASS; coverage improvement advised | 45/45 Vitest; lint, strict TypeScript, build, 3/3 Cypress, and Selenium desktop/mobile passed |
| End-to-end business flow | PASS | Newman: 10 requests, 23 assertions, 0 failures, including auth, classification, ownership, and local RAG |
| Database and containers | PASS | PostgreSQL/pgvector, Redis, API, worker, and Nginx healthy; migrations and transactional integrity passed |
| Load | PASS for measured workload | JMeter: 20 concurrent customers, 2,000 authenticated business requests, 0 errors, 340.6 req/s, 16 ms mean |
| Accessibility/web quality | PASS for automated criteria | axe: 0 violations; Lighthouse: accessibility 100, performance 95, best practices 96, SEO 100 |
| Security | PASS with low residual advisories | Bandit 0; dependency audits 0; ZAP API 0 warnings/failures; frontend 0 failures and 3 low/informational warnings |
| Dataset integrity | PASS | All 10 CSVs pass schema, ID, text, and label alignment; 1,168 run JSONs valid on the frozen split |
| Classifiers | PASS with subgroup risk | Intent macro-F1 0.8834; Negative-F1 0.7138; priority macro-F1 0.8734; Tamilish remains weakest |
| RAG safety/retrieval | PASS for safety; quality optimization remains | Golden recall@5 1.00, escalation accuracy 1.00, unsafe-answer rate 0; 7/7 adversarial probes passed |
| Local generation | CONDITIONAL | Five-language pipeline retrieved relevant evidence 5/5 but had 96.5 s median latency and three citation escalations |

## Release recommendation {.unnumbered}

Version 1 release blockers were fixed and re-tested: multilingual prompt-injection handling, rate limiting, API contract drift, citation enforcement, retrieval scoring, accessibility, dataset alignment, and security headers now pass. A controlled academic or supervised demonstration is supportable. Human approval must remain mandatory for financial guidance. Unrestricted production rollout should additionally improve local generation latency/citation compliance, Tamilish classification, and frontend coverage.

# 1. Evaluation Mission

Swift accepts English, Sinhala, Singlish, Tamil, and Tamilish banking-support tickets through text and OCR-assisted image paths. It classifies intent, sentiment, and priority, enforces customer/agent/admin access, and produces retrieval-grounded drafts. Testing therefore covered correctness, authorization, data integrity, multilingual safety, accessibility, capacity, deployment, observability, model evaluation, and error analysis.

Objectives were to exercise the full implemented stack; use every applicable framework in `Testing Resources - Sheet1.pdf`; execute live RAG using PostgreSQL/pgvector and local Ollama without paid APIs; repair severe defects; recompute DS measurements from artifacts; and retain one canonical artifact per test family.

# 2. Scope and Test Items

| Test item | Technology | Criticality | Coverage |
|---|---|---:|---|
| Customer, agent, administrator UI | React 19, Vite 7, Nginx | High | Component, browser, responsive, accessibility, build |
| Auth, tickets, attachments, dashboards, RAG | FastAPI, SQLAlchemy | Critical | Unit, API, contract, integration, security, end-to-end |
| Persistent data/migrations | PostgreSQL 16, pgvector, Alembic | Critical | Live DB, constraints, atomicity, SQL injection, migration graph |
| Worker/queue boundary | Dramatiq, Redis | High | Container startup, dependency health, API regression |
| Multimodal path | Tesseract OCR and masking | High | Live mixed-script OCR, masking endpoint, intent classification |
| Container deployment | Docker Compose | High | Build, start, health, headers, recovery |
| Intent/sentiment/priority models | LaBSE and TF-IDF/SVM artifacts | Critical | Frozen-split metrics and cross-language error rates |
| Multilingual datasets | Five language/script tracks | Critical | Schema, label, ID, text, duplicate, leakage, split audit |
| RAG | BGE-M3, FTS, reranker, Qwen 2.5 7B, Llama 3.1 8B | Critical | Retrieval, citations, guardrails, generation, judging, latency |
| External bank core/payment execution | No such integration exists | N/A | Outside system boundary |

# 3. Resource-Sheet Framework Traceability

| Tool/framework | Final disposition |
|---|---|
| Manual web, desktop, mobile | Responsive web exercised at desktop and 390×844; native binaries are absent |
| Pytest | 208 backend unit, API, DB, contract, security, observability, inference, and live RAG cases |
| React Testing Library / Jest | RTL used with the repository's Vitest runner; 45/45 passed |
| JUnit, TestNG, Express/Jest, Jasmine | N/A: Java, Express, and standalone Jasmine stacks are absent |
| SonarQube | Equivalent gates: Ruff, strict mypy, ESLint, TypeScript, coverage, Bandit; no Sonar server is configured |
| Firebase | N/A: Firebase functions/database are absent |
| Postman | Newman executed the complete ten-request business flow |
| Copilot | N/A as a test oracle; assertions counted only after independent execution |
| Selenium | Desktop/mobile production browser smoke and screenshot |
| Cypress | Login validation, responsive/theme, and registration-role workflows; 3/3 passed |
| REST Assured | N/A Java alternative; API integration covered by Pytest ASGI and Newman |
| JMeter | Authenticated five-endpoint concurrent business load |
| LoadRunner, Gatling, BlazeMeter | N/A alternatives; JMeter supplies applicable load evidence |
| JAWS | N/A to macOS host; standards coverage supplied by axe/Lighthouse and semantic browser assertions. Formal assistive-technology certification is a separate acceptance activity |
| Contrast checker, axe, Lighthouse | Applied; axe zero violations and Lighthouse accessibility 100 |
| Jira, Confluence, ClickUp | N/A: no connected project space; defects are controlled in this report |
| MongoDB, Firebase DB | N/A: Swift uses PostgreSQL/pgvector |
| SQL | Live SQL plus parameterization, constraint, transaction, and injection tests |
| Jenkins, GitLab CI | N/A to local snapshot; equivalent gates executed locally with retained evidence |
| kubectl, AWS CloudWatch | N/A: no Kubernetes/AWS deployment in scope |
| Git, Sourcetree, GitLab | Git revision/status used; GUI/remote alternatives unnecessary for execution |
| New Relic, PagerDuty | N/A: Logfire-compatible instrumentation/request IDs used; no paging integration |
| Checkmarx | Equivalent evidence from Bandit, dependency audits, security Pytest, and ZAP |
| OWASP | ZAP scans plus API security/input-validation suites |

# 4. Test Strategy

Testing combined white-box unit tests, React components, black-box HTTP flows, database integration, contract comparison, property-based validation, browser automation, accessibility rules, SAST, dependency audits, passive dynamic scanning, concurrent load, container checks, deterministic artifact audits, and live multilingual model evaluation.

## 4.1 Entry and exit criteria

Entry required a readable repository/reference set, Python 3.12 and Node dependencies, Docker, Ollama, PostgreSQL/pgvector, Redis, API, worker, and frontend. The frozen split was not regenerated. Exit required executed evidence for every applicable resource-sheet category, no failed/skipped/xfail backend case, closure of severe defects, current-schema DS results, and measured disclosure of residual risk.

# 5. Test Environment

| Component | Final environment |
|---|---|
| Host | macOS Apple Silicon; Asia/Colombo |
| Backend | Python 3.12.13; FastAPI; SQLAlchemy; Pytest |
| Frontend | React 19, Vite 7, Nginx; Chrome/Electron |
| Data | PostgreSQL 16/pgvector; Redis |
| Local AI | Ollama: `bge-m3`, `qwen2.5:7b`; independent judge `llama3.1:8b` |
| Containers | Root Compose stack plus JMeter, Cypress, and ZAP containers |
| Evidence | `Testing/test_evidence/`, `backend/reports/`, `frontend/reports/`, `backend/evaluation/reports/` |

# 6. Functional, API, and Database Results

## 6.1 Backend suite

The definitive run completed **208 passed of 208 in 132.35 seconds**, with zero skips, failures, expected failures, or warnings. Coverage was **72% lines, 76% statements, and 50% branches**. It covered auth/RBAC, token misuse, IDOR, validation, uploads, path traversal, SQL injection, transactions, migrations, policies, inference/OCR, rate limits, headers, OpenAPI, observability, retrieval, citations, provider fallback, guardrails, and live golden RAG thresholds.

## 6.2 Newman/Postman business flow

| Step | HTTP | Time | Result |
|---|---:|---:|---|
| Health/security header | 200 | 15 ms | Pass |
| Database readiness | 200 | 4 ms | Pass |
| OpenAPI | 200 | 48 ms | Pass |
| Anonymous protected request | 401 | 4 ms | Pass |
| Invalid registration | 422 | 3 ms | Pass |
| Register customer | 201 | 44 ms | Pass |
| Authenticated profile | 200 | 5 ms | Pass |
| Create/classify ticket | 201 | 2,065 ms | Pass |
| Retrieve owned ticket | 200 | 11 ms | Pass |
| Local Ollama RAG | 200 | 26,573 ms | Pass |

Totals: **10 requests, 23 assertions, zero failures, 28.911 seconds**. Predictions, ownership, explicit RAG routing, and stored ticket language were verified.

## 6.3 Database, OCR, and masking

PostgreSQL/pgvector and Redis passed health checks. Tests confirmed one migration head, reachable history, downgrades, ORM/migration agreement, uniqueness, cascades, audit retention, rollback, atomic creation, literal wildcard handling, bounded query counts, and bound SQL. Five SQL-injection payload families were exercised against customer and admin search. Live Docker Tesseract processed mixed English/Tamil content; the corrected masking endpoint protected sensitive patterns before inference.

# 7. Frontend, Browser, and Accessibility

| Gate | Result |
|---|---|
| ESLint / TypeScript / production build | Pass / Pass / Pass |
| Vitest + RTL | 45/45 pass |
| Cypress | 3/3 pass, zero skips |
| Selenium | Desktop and 390×844 mobile pass |
| axe-core | 0 violations; 31 rules passed, one manual-review item |
| Lighthouse | Performance 95; accessibility 100; best practices 96; SEO 100 |

Lighthouse measured FCP 2.2 s, LCP 2.5 s, total blocking time 10 ms, and CLS 0. Missing-heading and touch-size defects were fixed. Frontend coverage is **21.82% lines, 19.59% statements, 19.14% branches, 15.25% functions** and is recorded as an open maintainability risk.

# 8. Performance, Deployment, and Recovery

JMeter used **20 concurrent authenticated customers**, 20 iterations, and five endpoints per iteration. The runtime bearer credential came from Newman and was not persisted in the JMX.

| Requests | Errors | Throughput | Mean | Min | Max |
|---:|---:|---:|---:|---:|---:|
| 2,000 | 0 (0.00%) | 340.6 req/s | 16 ms | 1 ms | 101 ms |

The Compose stack built with Python 3.12 and compatible scikit-learn. PostgreSQL, Redis, API, worker, and frontend started and remained healthy. API restart recovery passed. Final Nginx responses include CSP, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy, COEP, and COOP.

# 9. Security Results

| Gate | Final result |
|---|---|
| Ruff / strict mypy | Clean; mypy passed 38 source files |
| Bandit | 0 findings over 3,699 LOC |
| pip-audit / npm audit | 0 known vulnerabilities / 0 known vulnerabilities |
| ZAP API | 118 rules passed; 0 warnings; 0 failures |
| ZAP frontend | 58 rules passed; 0 failures; 3 low/informational warnings |

Frontend advisories were CSP wildcard scope for necessary assets, modern-SPA identification, and missing SRI for externally hosted fonts. Self-hosted fonts and tighter CSP are recommended hardening. Behavioral tests passed for forged/expired/`alg=none` JWTs, refresh misuse, inactive users, roles, IDOR, file signatures/types, null bytes, traversal, XSS-shaped values, SQL injection, CORS, request IDs, and telemetry redaction. Rate limits cover authentication, registration, uploads, and RAG.

Prompt/safety gates passed **18/18 offline variants**, **7/7 live probes**, and all Pytest cases. English false positives were 3/3,079 (0.097%); all other tracks had zero. Native and romanized unauthorized-transaction and prompt-extraction cases escalate before retrieval/generation.

# 10. Dataset Validation

All ten train/test files for English, Sinhala, Singlish, Tamil, and Tamilish passed schema `id,text_en,text,category,sentiment,priority`, unique/aligned IDs, 77-class domain, required fields, source-text alignment, and cross-language label alignment. Each train track contains 9,998 rows and each test track 3,079.

The frozen split is **8,500 train / 1,498 dev / 3,079 test**, manifest `e7b5934392cd`. All **1,168 run JSONs** are valid and share it. Cleaning found zero label mismatches and zero empty/untranslated rows. Six accepted English-source train/test overlaps remain disclosed. Exact/near-duplicate review groups, including a small Tamilish conflicting-label group, remain for human review rather than silent deletion. Tamil remains machine translated without Sinhala's hand-correction pass.

# 11. Classifier Evaluation and Error Analysis

## 11.1 Recomputed metrics

| Task/model | Rows | Primary metric | Accuracy |
|---|---:|---:|---:|
| Intent — LaBSE | 15,395 | macro-F1 **0.883424** | 0.882949 |
| Intent — TF-IDF/SVM | 15,395 | macro-F1 **0.830820** | 0.830464 |
| Sentiment — LaBSE | 15,395 | Negative-F1 **0.713819** | 0.965833 |
| Sentiment — TF-IDF/SVM | 15,395 | Negative-F1 **0.665291** | 0.957843 |
| Priority — TF-IDF/SVM | 15,395 | macro-F1 **0.873358** | 0.887886 |

Negative-F1 governs sentiment because Neutral-only reaches about 95.6% dev accuracy while detecting no Negative tickets. Priority must be compared with the strong intent-majority floor of 0.9326 accuracy / 0.9272 macro-F1 and later use live queue/wait context outside the static dataset.

## 11.2 Per-language error rates

| Language | Intent LaBSE | Intent TF-IDF | Sentiment LaBSE | Priority TF-IDF |
|---|---:|---:|---:|---:|
| English | 5.88% | 8.22% | 2.40% | 9.03% |
| Singlish | 9.65% | 12.02% | 3.86% | 9.78% |
| Sinhala | 6.79% | 13.19% | 3.38% | 10.46% |
| Tamil | 6.72% | 14.23% | 2.92% | 10.65% |
| Tamilish | **29.49%** | **37.12%** | 4.51% | **16.14%** |

Tamilish is the dominant error cluster: non-standard romanization loses script cues and its source track lacks a human correction pass. LaBSE reduces but does not close the gap. Required work is a native-speaker sample audit, spelling normalization/augmentation, per-intent confusion review, and a checkpoint trained after the corrected source row. Existing intent prediction CSVs predate that one-row correction; aggregate impact is negligible but provenance is retained.

Offline language identification was 100% for English/Sinhala/Tamil, 91.56% for Singlish, and 25.63% for Tamilish. Authenticated follow-ups use stored ticket language, avoiding redetection in the normal production path. Contextless Tamilish identification remains a risk.

# 12. RAG Evaluation and Error Analysis

## 12.1 Final architecture

The live path used BGE-M3, PostgreSQL vector plus Unicode-safe lexical search, reciprocal-rank fusion, reranking, calibrated threshold 0.50, Qwen 2.5 7B, citation normalization/validation, and fail-closed escalation. Llama 3.1 8B independently judged the small multilingual end-to-end analysis.

## 12.2 Canonical golden evaluation

| Metric | Result |
|---|---:|
| Cases | 5 |
| Recall@5 / MRR / NDCG@5 | **1.00 / 0.60 / 1.00** |
| Faithfulness / relevance / citation correctness | 0.44 / 0.60 / 0.56 |
| Language correctness | **1.00** |
| Refusal/escalation accuracy | **1.00** |
| Unsafe-answer rate | **0.00** |
| Mean / p95 latency | 11.86 s / 27.56 s |
| Guardrails | **7/7 passed** |

Answer averages include deliberately escalated cases, which receive no answer score; they are conservative system-level means. Safety and routing passed acceptance thresholds.

## 12.3 Full dev retrieval

The zero-cost run exercised **165 probes**. Relevant-source recall was English 94.44%, Singlish 94.44%, Sinhala 88.89%, Tamil 100%, Tamilish 88.89%; p50/p95 latency was 173.5/190.66 ms. Overall route agreement was 69.09% (English 81.82%, Singlish 57.58%, Sinhala 90.91%, Tamil 51.52%, Tamilish 63.64%). Errors: R1 retrieval miss 6, C1 confidence mismatch 43, G3 conservative false escalation 47, G4 missed escalation 4, P1 latency 9. The dominant behavior is conservative abstention, not unsafe answering.

## 12.4 Batched generation and independent judge

The five-language probe retrieved relevant evidence in **5/5**, with zero retrieval/grounding/confidence misses. Tamil produced a draft; English, Singlish, and Tamilish escalated on model citation failure; Sinhala escalated at the 120-second generation timeout. Median total latency was **96.52 s** (generation 96.23 s), p95 120.26 s; Tamilish reached 238.59 s across retry behavior. The safety design fails closed, but this 7B local generator is not a production-latency or multilingual-citation solution. Optimize model/prompt/streaming/timeout behavior without weakening citation controls.

# 13. Defect Remediation Register

| ID | Initial severity | Defect | Final evidence | Status |
|---|---|---|---|---|
| SEC-01 | Critical | Multilingual prompt-injection bypass | Native/romanized patterns; 18/18 offline, 7/7 live, Pytest pass | Closed |
| SEC-02 | High | Sensitive endpoints lacked rate limits | Auth/register/upload/RAG limiter regression pass | Closed |
| API-01 | High | OpenAPI drift | Contract updated; strict contract suite passes | Closed |
| RAG-01 | High | Fusion lost dense/lexical scores | Score preservation, Unicode lexical query, calibrated confidence | Closed |
| RAG-02 | High | Invalid/unranked citations accepted | Ranked-evidence validation, item citations, retry, normalization | Closed |
| RAG-03 | High | Sinhala unauthorized transaction missed | Multilingual safety patterns; golden escalation passes | Closed |
| DATA-01 | High | Tamilish category mismatch | Label aligned; all ten datasets pass | Closed |
| DATA-02 | Medium | Source newline mismatch | Canonical normalization; text alignment passes | Closed |
| A11Y-01 | Medium | Missing H1/small controls | axe 0; Lighthouse accessibility 100 | Closed |
| WEB-01 | Medium | Incomplete security headers | Final Nginx headers and assertions pass | Closed |
| DEP-01 | Medium | Container ML runtime mismatch | Python 3.12/sklearn-compatible rebuild passes | Closed |
| RAG-R1 | Medium | Local generation slow/citation-fragile | Fail-closed verified; optimization remains | Residual |
| DS-R1 | Medium | Tamilish intent error high | Quantified at 29.49%; targeted work prescribed | Residual |
| TEST-R1 | Medium | Frontend coverage low | All suites pass; workflow expansion prescribed | Residual |

# 14. Residual Risk and Acceptance

| Risk | Exposure | Control |
|---|---|---|
| Local RAG performance | 96.5 s median independent probe | Timeouts, streaming UX, human escalation, alternative-model benchmark |
| Conservative routing | 47 false escalations; 4 missed escalations/165 dev probes | Tune on dev, lock threshold, verify once on held-out data |
| Tamilish quality | 29.49% LaBSE intent error | Human audit, normalization, augmentation, subgroup threshold |
| Frontend depth | 21.82% line coverage | Add protected customer/agent/admin workflow cases |
| Data overlap | Six accepted English-source overlaps | Disclose; sensitivity analysis; preserve frozen split |
| Duplicate groups | Small exact/conflicting groups | Complete human review from cleaning CSVs |
| Web hardening | ZAP SRI/CSP warnings | Self-host fonts and remove residual wildcard allowances |
| Tamil provenance | No hand-correction pass | Disclose and conduct native-speaker acceptance evaluation |

No open residual is Critical or High because unsafe RAG output fails closed, financial actions are not automated, and deployment remains human-supervised. These risks block an unrestricted production claim, not a controlled demonstration.

# 15. Final Test Closure

Every deterministic final gate passes; the backend suite includes live PostgreSQL and Ollama; every severe defect has regression evidence. Each resource-sheet framework is addressed by direct use or technology applicability. Canonical evidence uses `-final` names, and the Word deliverable is generated with the supplied template's native cover, sections, headers/footers, styles, fonts, tables, and fields.

**Final decision:** **CONDITIONAL PASS for controlled, human-supervised release.** Production promotion requires improvements to local generation, Tamilish quality, and frontend workflow coverage.

# Appendix A — Canonical Evidence

| Area | Artifact |
|---|---|
| Backend/coverage | `backend/reports/pytest-final.json`, `coverage-final.json` |
| Python security | `backend/reports/bandit-final.json`, `pip-audit-final.json` |
| Frontend | `frontend/reports/vitest-final.json`, `coverage/`, `eslint-final.json`, `npm-audit-final.json` |
| API/load | `Testing/test_evidence/newman-final.json`, `jmeter-business-final.jtl`, `jmeter-business-final-report/` |
| Browser/a11y | `cypress-final.xml`, `selenium_mobile.png`, `axe-final.json`, `lighthouse-final.json` |
| Dynamic security | `zap-api-final.json`, `zap-frontend-final.json` |
| DS/data | `ds-validation-final.json`, `data-cleaning-final.txt` |
| RAG | `rag_eval_final.json`, `rag_retrieval_final.json`, `rag_pipeline_final.json`, `offline_*.json` |

# Appendix B — Final Gates

| Gate | Criterion | Actual | Outcome |
|---|---|---|---|
| Backend | No failed/skipped/xfail | 208/208 passed | Pass |
| Static quality | Zero findings | Ruff/mypy/Bandit clean | Pass |
| Dependencies | No known vulnerability | pip/npm audits 0 | Pass |
| Frontend | All suites/build pass | 45/45, 3/3, Selenium/build pass | Pass |
| Accessibility | axe 0; Lighthouse ≥90 | 0; accessibility 100 | Pass |
| API | All requests/assertions | 10/10; 23/23 | Pass |
| Load | 0% errors | 2,000; 0 | Pass |
| ZAP | Zero high/medium failures | 0 failures | Pass |
| Dataset | All files/artifacts valid | 10/10; 1,168/1,168 | Pass |
| Golden RAG safety | unsafe 0; guardrails all pass | 0; 7/7 | Pass |
| Golden retrieval | recall@5 ≥0.8 | 1.00 | Pass |
| Release | No open Critical/High defect | None | Conditional pass |
