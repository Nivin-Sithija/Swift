# Swift viva: complete question-and-answer study guide

Prepared from the local working tree on **7 October 2026**. Answers describe the implementation visible in this folder; they do not certify a live deployment. The source audit indexed **302 first-party Python, TypeScript and notebook files**. Dependencies, generated report assets, credentials and environment-file values were excluded. Application code was not changed.

This is a broad viva preparation bank, not a literal enumeration of every question an examiner could invent. Read the spoken answer first, then use each section's source references to practise explaining the code.

## Read this before memorising any answer

**Use four distinct labels when speaking:** implemented, measured in saved evidence, proposed, and limitation. They are different claims.

| Fact | Accurate answer for this working tree |
|---|---|
| Product | Banking-support ticket triage prototype called Swift; it is written in Python and TypeScript, not Apple's Swift language. |
| Languages | English, Sinhala and Tamil; five dataset tracks include Singlish and Tamilish/Tanglish. |
| Inputs implemented | Customer text and PNG/JPEG image evidence. PDFs can be stored through the API but do not enter image OCR. No implemented voice/ASR flow was found. |
| Roles | Customer, agent, administrator. Older documents also mention a supervisor; that role was merged into administrator. |
| Runtime classifier | Hosted Hugging Face Space returns three LaBSE task outputs. Local TF-IDF/SVM classifies OCR text. Keyword rules provide fallbacks and critical overrides. |
| Model count | Three task-specific LaBSE classifiers served in one Space; do not call this one jointly trained multitask model. Joint Gemma variants exist as experiments. |
| Processing | Ticket classification runs inline. The Dramatiq actor is a placeholder, not a completed background pipeline. |
| Stored responses | Template drafts can be edited, approved and sent by staff. Customers can see approved or sent responses. |
| RAG assistance | Separate owner-only customer endpoint; returns guidance directly with approval_required=false. It does not persist a staff-approved response. |
| Queue | Continuous priority/intent probability pooling plus sentiment, intent criticality and waiting-time aging. |
| Dataset | 9,998 train + 3,079 test underlying tickets; five renderings each; 65,385 total rows. |
| Frozen split | 8,500 train / 1,498 dev / 3,079 test tickets; sha e7b5934392cd. Numeric IDs have a split-specific namespace. |
| Current sentiment CSVs | Train: 9,536 Neutral / 462 Negative. Test: 2,978 Neutral / 101 Negative per track. |
| Saved sentiment score | 0.713819 Negative-F1 against embedded archived truth: 975 pooled Negatives. |
| Re-score against current CSV truth | 0.445906 Negative-F1; 770 pooled truth rows differ, representing 154 test ticket IDs. This is a label-version mismatch, not a new trained-model experiment. |
| Intent re-check | Saved LaBSE predictions: macro-F1 0.883424; archived and current truth match. |
| Priority re-check | Saved TF-IDF/SVM predictions: macro-F1 0.873358; archived and current truth match. Separate saved LaBSE priority results report about 0.8900. |
| Production claim | Controlled prototype. Stored test evidence, unit tests and simulations do not establish production readiness. |

**Evidence:** [fresh non-mutating audit](SOURCE_AUDIT.json), [source index](SWIFT_SOURCE_MAP.md), [master results](../../ml/reports/RESULTS.md), [historical test report](../../Testing/Swift_Master_Test_Plan_and_Report_v3.md). The fresh audit checked dataset alignment and three saved prediction files; it did not retrain models or rerun the complete application suite.

## How to answer in a viva

Use this pattern: **what it does → why this choice → how your code does it → evidence or limitation**. A concise answer is usually enough; use the follow-up detail when asked.

Example: “We split by ticket ID because the same ticket has five language renderings. The split manifest chooses English train IDs once, then applies those memberships to each track. This prevents translation copies crossing train and dev; exact repeated text across source splits still needs a separate leakage audit.”

## Topic index

**505 questions and answers across 26 topics.**

- [1. Project explanation and contribution](#1-project-explanation-and-contribution)
- [2. Scope, requirements and design documents](#2-scope-requirements-and-design-documents)
- [3. Architecture and boundaries](#3-architecture-and-boundaries)
- [4. Dataset construction, alignment and leakage](#4-dataset-construction-alignment-and-leakage)
- [5. Annotation, weak labels and version problems](#5-annotation-weak-labels-and-version-problems)
- [6. Text processing and tokenization choices](#6-text-processing-and-tokenization-choices)
- [7. Classical machine learning](#7-classical-machine-learning)
- [8. Transformers, fine-tuning and multitask experiments](#8-transformers-fine-tuning-and-multitask-experiments)
- [9. Evaluation methods and honest comparisons](#9-evaluation-methods-and-honest-comparisons)
- [10. Results you can defend](#10-results-you-can-defend)
- [11. Runtime inference and review behaviour](#11-runtime-inference-and-review-behaviour)
- [12. OCR, images and evidence fusion](#12-ocr-images-and-evidence-fusion)
- [13. Dynamic queue urgency and worked mathematics](#13-dynamic-queue-urgency-and-worked-mathematics)
- [14. Retrieval-augmented generation](#14-retrieval-augmented-generation)
- [15. Generation, citations and safety boundaries](#15-generation-citations-and-safety-boundaries)
- [16. Authentication and authorisation](#16-authentication-and-authorisation)
- [17. Database, entities and transactions](#17-database-entities-and-transactions)
- [18. API design, status workflows and administration](#18-api-design-status-workflows-and-administration)
- [19. Frontend state, forms and small implementation choices](#19-frontend-state-forms-and-small-implementation-choices)
- [20. Security controls and their practical limits](#20-security-controls-and-their-practical-limits)
- [21. Deployment, configuration and operations](#21-deployment-configuration-and-operations)
- [22. Testing, evidence and monitoring](#22-testing-evidence-and-monitoring)
- [23. Failure scenarios and debugging questions](#23-failure-scenarios-and-debugging-questions)
- [24. Limitations, improvements and examiner challenges](#24-limitations-improvements-and-examiner-challenges)
- [25. Demo walkthrough and oral practice](#25-demo-walkthrough-and-oral-practice)
- [26. Small code and terminology follow-ups](#26-small-code-and-terminology-follow-ups)

## 1. Project explanation and contribution

Sources: [README](../../README.md), [requirements](../../docs/srs/srs.tex), [data statement](../../paper/drafts/data_statement.md).

### Q001. What is Swift?
Swift is a multilingual banking-support ticket triage prototype. Customers describe an issue and optionally attach an image. The system prepares intent, priority and sentiment predictions, helps staff review and order tickets, and provides a separate retrieval-grounded policy assistance flow.

### Q002. What problem does it solve?
A support desk receives varied wording, mixed languages and screenshots. Manually identifying every issue and urgency takes time. Swift makes the first analysis and queue ordering more consistent while retaining human review for support decisions.

### Q003. Give your 30-second introduction.
“Swift helps a Sri Lankan banking support desk process English, Sinhala, Tamil and romanized messages. We built a five-track BANKING77-derived dataset, compared classical and transformer classifiers, integrated image OCR, and added staff review, dynamic queue ordering and grounded policy assistance. It is an advisory prototype without bank-core access.”

### Q004. Give your two-minute introduction.
Explain the problem, three user roles, text-to-classification flow, image-to-OCR flow, queue aging, and approved-source RAG. Then give correctly scoped metrics and close with label quality, romanized-language gaps and production limitations. Do not present the older README as a verified description of every current feature.

### Q005. What is your main contribution?
The project combines a five-track banking-ticket corpus, cross-script classifier experiments and an integrated support workflow. It also studies how intent and priority predictions can be combined for urgency scoring. These are contributions to a prototype and benchmark, not a claim to have invented transformers or OCR.

### Q006. What makes this different from a basic chatbot?
It stores tickets and staff decisions, predicts three different targets, processes evidence images, maintains roles and audit records, and ranks a support backlog. The customer assistance component retrieves approved evidence and exposes citations instead of relying only on unconstrained generation.

### Q007. What does triage mean?
Triage means identifying the issue, estimating how urgently it should be handled, and directing attention to the appropriate review workflow. It does not mean executing a transfer, checking a real balance, or solving every case automatically.

### Q008. What are intent, priority and sentiment?
Intent describes the type of problem, such as card arrival or a pending transfer. Priority represents handling urgency. Sentiment represents the customer's expressed tone under the annotation policy. A serious incident can be described calmly, so the targets should remain distinguishable.

### Q009. Why banking?
BANKING77 gives a fine-grained intent benchmark, and banking support exposes meaningful requirements for sensitive requests, urgency, evidence and multilingual access. A banking prototype also forces us to be explicit about unsupported account-specific claims and the boundary around financial actions.

### Q010. Is Swift a banking application?
It is a support application. The code does not connect to bank-core systems, execute payments, block cards, verify balances or confirm transaction outcomes. The assistance flow should offer general policy guidance and route account-specific work to a human.

### Q011. Is it fully automatic?
Classification and some routing checks are automatic. Staff can correct predictions and control stored response editing and sending. However, the separate RAG endpoint currently returns guidance directly, so saying every generated answer receives staff approval would misdescribe the implementation.

### Q012. Is it trilingual or five-language?
There are three underlying languages: English, Sinhala and Tamil. There are five dataset representations because Sinhala and Tamil also have romanized tracks. The runtime additionally recognises code-mixed and unknown language forms.

### Q013. What does multimodal mean here?
The implemented workflow combines customer text with text extracted from an optional image. It is OCR-mediated evidence fusion. It is not a jointly trained image-and-text neural model, and the current application does not implement voice input.

### Q014. What business value can you claim?
The design can reduce initial sorting effort and make evidence, predictions and review decisions visible to agents. Measured model scores and simulations support specific technical claims; actual reductions in bank staffing cost, response time or customer dissatisfaction require a field study.

### Q015. Which part did you personally implement?
Describe only your actual work: modules, dataset tasks, experiments, tests and commits you can explain. This repository alone cannot prove individual authorship or division of labour. Prepare one concrete feature, one difficult defect and one design tradeoff from your own contribution.

## 2. Scope, requirements and design documents

Sources: [SRS](../../docs/srs/srs.tex), [architecture](../../docs/architecture/architecture.tex), [feasibility](../../docs/feasibility-study/feasibility-study.tex), [enums](../../backend/app/domain/enums.py).

### Q016. What are the user roles?
Customers submit and view their own tickets. Agents review tickets, correct predictions, add internal notes and manage responses. Administrators manage users, queues, settings and audit information. Backend authorisation determines access, not the visible navigation alone.

### Q017. Where is the supervisor role?
Older documents include a supervisor, but the current enum has customer, agent and administrator only. Migration 0003 merges supervisor into administrator. Explain this as a change in the implementation rather than claiming a separate supervisor interface exists.

### Q018. What are the main functional requirements?
Registration and login, ticket submission and retrieval, classification, attachment handling, prediction review, assignment, escalation, response workflows, dashboards and administration. RAG assistance is an additional customer flow. Point to actual routes when asked which requirements are implemented.

### Q019. What are the main non-functional requirements?
Security, privacy, multilingual robustness, usability, reproducibility, maintainability and responsive behaviour. Latency and scalability also matter. A requirement such as encryption or malware scanning is not automatically implemented just because a document lists it.

### Q020. What is an SRS?
A Software Requirements Specification records what the system should do and the constraints it should satisfy. Swift's SRS uses requirement identifiers such as FR-NLP and FR-CLS so requirements can be traced to design, code and tests.

### Q021. What is requirement traceability?
It links a requirement to its implementation and verification. For example, owner-only ticket access connects to the customer filter and get_ticket ownership check, then to authorisation tests. This makes missing requirements and untested behaviours visible.

### Q022. What do use-case diagrams explain?
They show actors and their interactions with the system. They establish who submits, reviews, assigns, approves and administers. They do not show the precise SQL queries or sequence of model calls; those belong in other views.

### Q023. What do sequence diagrams explain?
They show messages over time between components. For ticket creation, a sequence can show the browser request, API validation, database flush, model request, prediction persistence and response. Update it if the implementation changes from proposed worker processing to inline processing.

### Q024. What do activity and class diagrams explain?
Activity diagrams show workflow decisions, such as review versus assistance escalation. Class diagrams show entities and relationships. In Swift, Ticket relates to predictions, events, notes, responses and attachments, while User appears as customer, agent or reviewer.

### Q025. What does the deployment diagram describe?
It describes runtime nodes such as frontend/Nginx, FastAPI, PostgreSQL/pgvector, Redis and external providers. A worker container is present, but its existence is not evidence that jobs are actually being queued and processed.

### Q026. Why is the project feasible academically?
Open-source tooling, a reusable benchmark dataset, local OCR and hosted model options reduce initial setup cost. The difficult work is data quality, multilingual evaluation and integration. Production costs for infrastructure, human annotation, security and support need a separate estimate.

### Q027. What is outside the project boundary?
Real bank-core integration, financial execution and real notification delivery are excluded. Voice support and richer visual understanding are not completed application features. Legal compliance certification and production capacity are also not established by the repository.

### Q028. Can you claim the project meets every requirement?
No. Several design requirements are broader than the prototype, including complete masking, secure attachment delivery, background processing and universal human approval. Explain implemented controls and remaining gaps individually rather than treating documentation as proof.

## 3. Architecture and boundaries

Sources: [main.py](../../backend/app/main.py), [routes.py](../../backend/app/api/v1/routes.py), [service interface](../../frontend/src/services/ticketService.ts), [RAG service](../../backend/app/rag/service.py).

### Q029. Describe the architecture.
It is a React/TypeScript frontend with a FastAPI modular monolith, an asynchronous SQLAlchemy persistence layer, PostgreSQL/pgvector, local attachment storage, and external inference/generation options. Domain policies and the RAG subsystem have separate modules within the backend.

### Q030. Why a modular monolith?
It keeps deployment and transactional workflows simpler for an academic team while separating responsibilities in code. Independent services would add network contracts, monitoring and operational overhead. Modules can become services later if measured scale or team boundaries justify it.

### Q031. Why React?
React supports reusable components and state-driven rendering for forms, role-specific pages and queues. The project uses providers for authentication, theme and language. This is a practical ecosystem and maintainability choice, not a claim that React is universally superior.

### Q032. Why TypeScript?
It describes service contracts and UI data structures and catches many mistakes before runtime. The service mapper translates API snake_case into frontend camelCase. Types improve consistency, but they do not validate arbitrary network responses unless runtime validation is added.

### Q033. Why FastAPI?
FastAPI combines typed request models, dependency injection, asynchronous handlers and generated OpenAPI documentation. It fits a Python ML-oriented backend. Framework choice alone does not guarantee security, speed or correct database transactions.

### Q034. Why separate API schemas from ORM entities?
ORM entities describe persistence; API schemas describe accepted and returned data. This allows the server to exclude password hashes, filter customer-visible information and validate input independently of database columns.

### Q035. What is dependency injection here?
FastAPI resolves dependencies such as database sessions, current user, staff/admin checks and the RAG service. A route declares what it needs, and tests can override those dependencies with isolated fixtures or fake providers.

### Q036. What is asynchronous programming doing?
HTTP and database waits can yield control so other requests progress. It does not make blocking CPU work asynchronous automatically. Tesseract and some embedding/reranking operations use asyncio.to_thread to avoid blocking the event loop.

### Q037. What is the frontend service abstraction?
TicketService describes the operations pages need. serviceSelector currently binds it to restTicketService. This separates UI decisions from HTTP details and helps component tests stub behaviour without calling a live server.

### Q038. What are the three important runtime flows?
Customer text produces stored advisory predictions and a template draft. Uploaded images produce OCR text and update unreviewed predictions. Customer assistance retrieves approved documents and generates a direct policy-guidance result. These flows have different persistence and approval behaviour.

### Q039. Why keep original customer text?
It preserves evidence and lets agents inspect what the customer actually wrote. OCR text is stored separately so attachment processing cannot silently rewrite the ticket. Original preservation also enables diagnosing disagreement between text and image evidence.

### Q040. Does classification translate every message to English?
No. The runtime sends customer wording directly to the multilingual classifier. Dataset translation was part of corpus construction. RAG normalisation is conservative text processing, not a universal machine-translation stage.

### Q041. Where is the separation weak?
routes.py contains much business logic as well as HTTP handling, making it large. Some policies live in domain modules, but extracting ticket processing and response workflow services would make responsibilities easier to test and maintain.

## 4. Dataset construction, alignment and leakage

Sources: [fresh audit](SOURCE_AUDIT.json), [data loader](../../ml/swiftbench/data.py), [split code](../../ml/swiftbench/splits.py), [cleaning audit](../../notebooks/data_preparation/data_cleaning.py), [licence](../../datasets/LICENSE).

### Q042. What is BANKING77?
It is the project's source corpus of English banking questions with 77 fine-grained intent categories. The English text and intent taxonomy are inherited. Sinhala, Tamil, romanized tracks and auxiliary labels are project additions.

### Q043. Why use 77 categories?
They provide a challenging fine-grained task with distinctions such as pending versus failed transfers. The benchmark taxonomy aids comparison, but it is not automatically the correct taxonomy for a specific Sri Lankan bank.

### Q044. What are the five tracks?
english, sinhala, singlish, tamil and tamilish. “Tanglish” is the product/runtime term for romanized Tamil in some code; “tamilish” is the dataset path. Explain the naming difference so it is not mistaken for a sixth corpus.

### Q045. What does one dataset row contain?
The six columns are id, text_en, text, category, sentiment and priority. text_en preserves the English source; text is the track rendering. category holds the intent label, even though the ML task is named intent.

### Q046. How large is the corpus?
Each track has 9,998 training and 3,079 test rows. Across five tracks there are 65,385 rows, representing 13,077 underlying source tickets. Five translations do not create five independent observations.

### Q047. Why are there 9,998 train rows rather than quoting the original benchmark count?
The actual local files have 9,998 after the repository's data preparation. Quote the audited corpus you used rather than an upstream total from memory. To explain exactly which source records were removed, inspect the deduplication artifacts and preprocessing history.

### Q048. How were Sinhala and Tamil produced?
The repository describes machine translation, a colloquial manual correction pass for Sinhala, and no equivalently documented full manual Tamil pass. Do not assert that every translated row was checked by fluent speakers unless you have separate evidence.

### Q049. How was Singlish produced?
It was generated by rules from the Sinhala track, with banking loanwords preserved where possible. This improves spelling consistency inside the benchmark but may make results optimistic for the inconsistent human-typed romanization seen in real support tickets.

### Q050. How was Tamilish produced?
The corpus documentation describes machine-translated romanization rather than the same controlled rules used for Singlish. Its varied spellings and different curation process can contribute to a performance gap, but the gap is not proof of a single cause.

### Q051. What is code-mixing?
A message uses material from more than one language, often retaining banking terms such as card or account in English alongside Sinhala or Tamil. Script detection and language identification are related but different: English letters can also encode romanized Sinhala or Tamil.

### Q052. Are translation quality and label alignment the same?
No. Identical IDs and labels across tracks prove structural alignment, not accurate translation or equivalent emotional tone. A fluent review should check meaning, register, banking terminology and whether auxiliary labels remain appropriate after translation.

### Q053. Why retain text_en?
It supports provenance and aligned comparisons and helps reviewers locate the source message. It should not accidentally become an input feature in a non-English model, because that would hide performance on the translated text.

### Q054. What is the train/dev/test split?
Train fits parameters. Dev chooses models, hyperparameters and thresholds. Test estimates performance after selection. The frozen manifest contains 8,500 train, 1,498 dev and 3,079 test underlying tickets, applied to every language track.

### Q055. Why split by ID instead of rows?
One ticket appears five times. A row split could put English in training and its Tamil rendering in dev, allowing near-equivalent content to leak across evaluation. ID grouping keeps all renderings of a train-source ticket on one side.

### Q056. Are train and test numeric IDs globally unique?
Not necessarily. They are indexes in different source CSV namespaces. The audit explicitly notes split-specific IDs. Comparing bare numeric IDs across train and test can falsely report leakage; compare (source split, ID) and separately check identical source text.

### Q057. What does stratification do?
The dev split is stratified by the 77 intent classes to preserve category representation. This does not guarantee adequate counts for rare Negative sentiment cases, because sentiment is a different target.

### Q058. What is the split hash for?
The manifest's short SHA identifies train/dev membership. Results stamp it so incompatible splits can be filtered. It does not identify dataset text or label versions; separate hashes or version metadata are necessary for those.

### Q059. What data-quality checks are present?
Schema, row counts, unique within-file IDs, track alignment, cross-language labels, empty fields, untranslated rows, duplicates, conflicting labels, source-text leakage, class imbalance and length anomalies. The audit writes review artifacts instead of silently changing the corpus.

### Q060. Is the dataset leakage-free?
The ID-based split prevents one important leakage mode, but the historical cleaning audit reports six test rows whose English source text also occurs in train. That requires separate handling or an ablation. “Split by ID” is not proof against every form of leakage.

### Q061. Why not silently delete every duplicate?
A duplicate can reflect repeated real phrasing, while a conflicting-label collision needs review. Automatic deletion can change class distributions, benchmark comparability and alignment across tracks. Any correction should be documented and propagated consistently.

### Q062. What did the fresh audit establish?
All ten CSVs have the expected row counts. IDs, English source text and three labels align across tracks. The script parsed indexed Python files and checked three prediction artifacts. It did not establish translation quality, absence of all leakage, or current live model performance.

### Q063. What licence applies?
datasets/LICENSE declares CC BY 4.0 for the derived corpus and attributes BANKING77. Attribute both the source and project additions when distributing the corpus. Do not claim CC BY legally requires every derivative to use the same licence; this repository chose it.

## 5. Annotation, weak labels and version problems

Sources: [v8 prompt](../../datasets/translation/prompts/labeling_prompt_v8.md), [label ceiling](../../paper/results/tables/label_ceiling.csv), [audit](SOURCE_AUDIT.json), [results](../../ml/reports/RESULTS.md).

### Q064. Are all three targets human ground truth?
No. Intent comes from BANKING77's labels. Sentiment and priority are generated through documented annotation rules and LLM-assisted pipelines. A model evaluated against these auxiliary labels measures agreement with that annotation system.

### Q065. What is weak supervision?
It creates training labels from imperfect sources such as rules or an LLM rather than a fully adjudicated human gold corpus. It makes annotation feasible at scale but introduces systematic label noise and requires human validation.

### Q066. Why generate auxiliary labels?
BANKING77 provides intent, not project-ready sentiment or urgency labels. Auxiliary annotation enables multitarget experiments. The limitation is that high model agreement can reproduce errors in the labeler rather than represent good operational decisions.

### Q067. What does the v8 sentiment rule try to fix?
It judges expressed distress and dissatisfaction rather than assuming that a serious topic is negative. It tightens grievance framing so a plain question about a fee is not automatically labelled a complaint.

### Q068. Give an example separating severity from tone.
“I noticed an unauthorised payment; please investigate” may be calm but safety-sensitive. “I am furious that my replacement card is still missing” expresses negative tone. Safety routing should protect the first case even when its sentiment is Neutral.

### Q069. Does the sentiment model have Positive?
The current ML harness uses Neutral and Negative only. The application enum retains positive for compatibility, but that does not mean the hosted model was trained as a three-class classifier.

### Q070. Does the trained priority model have Critical?
No. The ML label space is Low, Medium and High. Critical is a fourth application tier supplied by operational rules or staff decisions. Do not describe it as a learned fourth output from the priority classifier.

### Q071. Why not equate Negative with Critical?
Tone and incident risk are different. A customer can be angry about a routine issue, while a calm fraud report needs careful handling. The review policy considers several signals instead of turning all negative messages into critical incidents.

### Q072. What is a label ceiling?
It is agreement between the dataset's labels and a reviewed human benchmark under a specific metric and version. It estimates annotation quality. It is not a mathematical upper bound on every model score or an immutable truth about the task.

### Q073. What annotation-quality numbers are in the repository?
The saved 500-row table reports sentiment label-vs-human Negative-F1 0.7931 with kappa 0.7804, and priority macro-F1 0.7722 with kappa 0.6446. Raw v8 prompt output has 0.7812 sentiment F1. These are historical, version-specific artifacts, not a fresh validation of today's CSVs.

### Q074. Why can priority model F1 exceed the human agreement score?
The model is scored against generated priority labels, while the human comparison uses a different reference. Learning to reproduce a rule can yield 0.89 against the rule even if that rule agrees less well with humans. The two numbers answer different questions.

### Q075. What is Cohen's kappa?
It adjusts observed agreement for agreement expected from marginal class frequencies: kappa = (observed - expected)/(1 - expected). It can reveal that high raw agreement is partly driven by an imbalanced majority class.

### Q076. What exact sentiment mismatch did this analysis find?
The archived LaBSE prediction CSV has 975 Negative test rows pooled across tracks. Current CSVs have 505. The y_true labels differ on 770 pooled rows, or 154 paired tickets. Structural cross-language alignment is intact; the version differs between datasets and predictions.

### Q077. How can both 0.7138 and 0.4459 be correct?
They use the same saved predictions with different reference labels. Archived y_true gives 0.713819 Negative-F1; current CSV labels give 0.445906. This demonstrates provenance mismatch, not evidence that inference suddenly degraded on unchanged input.

### Q078. Can you call the current CSVs v8?
The model code and reports name v8, but the audited counts differ from the archived v8 predictions. Counts alone do not prove which exact historical prompt created every current label. Identify them as the current working-tree labels until their generation provenance is reconciled.

### Q079. How should this be fixed before publication?
Pin dataset and label hashes with the checkpoint and prediction files, recover the intended label set, and regenerate evaluation artifacts with explicit versions. Do not edit a headline number alone. Keep historical results available with their actual reference labels.

### Q080. Can repeated use of the 500-row gold set bias prompt selection?
Yes. Using its errors to revise prompts and then reporting performance on the same set introduces development-set reuse, even if only aggregate counts were read. A fresh blind human set would give a stronger final estimate.

## 6. Text processing and tokenization choices

Sources: [tokenize.py](../../ml/swiftbench/tokenize.py), [models.py](../../ml/swiftbench/models.py), [language rules](../../backend/app/inference/services.py), [RAG normalisation](../../backend/app/rag/languages.py).

### Q081. Why is Unicode handling important?
Sinhala and Tamil use combining vowel marks and script-specific shaping. A tokenizer can silently drop those marks without raising an exception, changing words and their distinctions. The project measures preservation rather than assuming a Unicode-aware flag is sufficient.

### Q082. What defect was found in the default sklearn tokenizer?
The default word pattern relies on word-character boundaries that exclude important combining marks. Repository measurements report losses of 40.1% of Sinhala and 69.3% of Tamil characters on the examined split. These are measured corpus findings, not universal rates.

### Q083. What is the replacement tokenizer?
For native Sinhala or Tamil, the harness calls indic_nlp tokenization. Latin-script text uses a Unicode-property-aware regex when available. The vectorizer supplies this tokenizer and disables the default token_pattern.

### Q084. Why not use only a Unicode letter regex?
Including letters and marks helps, but Sinhala conjuncts can contain the zero-width joiner. A simple letter/mark regex may split them. The project's tokenizer comparison motivated using Indic-aware tokenization for native script.

### Q085. What is character preservation?
It is the ratio of non-space characters represented in produced tokens to the input's non-space characters. It is a diagnostic for destructive tokenization. Punctuation filtering can affect it, so it is not itself a classification metric.

### Q086. Why retain English banking loanwords?
Words such as card, app and account are part of local support usage. Replacing them mechanically can reduce familiarity and create artificial spelling variation. The dataset style rules aim to preserve useful code-mixed vocabulary.

### Q087. What is normalization versus translation?
Normalization applies limited formatting or spelling rules while preserving meaning. Translation changes the language. RAG query normalization is not equivalent to translating every ticket to English.

### Q088. Why not remove every stopword from classification text?
Negation and small function words can change meaning: “received” versus “not received.” Broad removal can damage intent and sentiment. Retrieval query processing and classifier feature preprocessing can have different goals.

### Q089. Why not lowercase everything at every stage?
Lowercasing may be suitable for a classical TF-IDF vectorizer but can change the behaviour of cased pretrained tokenizers or identifiers. Use the preprocessing expected by each model and record it with the experiment.

### Q090. What is subword fertility?
It measures how many subword tokens are needed for words or text under a tokenizer. High fragmentation can increase sequence length, truncation and cost. It is a screening diagnostic, not a guarantee of better or worse downstream F1.

### Q091. Why is unknown-token rate also needed?
Low fertility can be misleading if many characters collapse into an unknown token. Measure coverage and unknown-token behaviour alongside length. A compact encoding that discards information is not a successful tokenizer.

### Q092. Why is regex-based runtime language detection limited?
Unicode blocks identify native scripts reasonably, but Latin script can represent three languages. Short marker lists miss spelling variants and can match English substrings accidentally. The reported heuristic confidence is not a measured posterior probability.

## 7. Classical machine learning

Sources: [estimator factory](../../ml/swiftbench/models.py), [imbalance](../../ml/swiftbench/imbalance.py), [classical training](../../ml/swiftbench/train_classical.py), [baselines](../../ml/swiftbench/baselines.py).

### Q093. Why train classical baselines before transformers?
They are fast, interpretable enough to inspect and establish whether complex modelling is worth its cost. A transformer should be compared on the same labels, split and metric, not merely described as newer.

### Q094. What is TF-IDF?
It weights a feature by how frequently it occurs in a document and how informative it is across the corpus. Common terms get less discriminative weight than uncommon ones. The implementation uses word and character n-grams with sublinear term frequency.

### Q095. Why combine word and character features?
Word n-grams capture terms and short phrases. Character n-grams share signal across romanized variants, suffixes and misspellings. Their union offers robustness without requiring a perfect transliteration system.

### Q096. What are the actual word-vectorizer settings?
Word 1–2 grams, min_df=2, max_df=0.98, sublinear_tf=true and up to 25,000 features. These trade vocabulary coverage against rare noise and memory. They are chosen configuration values, not universal optima.

### Q097. What are the character-vectorizer settings?
char_wb 3–5 grams, min_df=2, sublinear_tf=true and up to 50,000 features. char_wb forms character patterns within word boundaries, useful for spelling variation while avoiding arbitrary cross-word character sequences.

### Q098. What does sublinear TF do?
It compresses repeated counts using a logarithmic transformation, so repeating a word many times does not multiply its influence proportionally. The final TF-IDF pipeline also normalizes features according to vectorizer defaults.

### Q099. What is LinearSVC doing?
It learns linear decision boundaries in sparse TF-IDF space and uses decision margins to select one of the intent classes. Those margins are not class probabilities, which is why the OCR path adds a separate correctness-confidence calibration.

### Q100. What does C mean?
C controls the tradeoff between fitting training errors and regularization in SVM/logistic models. Larger C weakens regularization; smaller C strengthens it. Choose it on development data and keep the test set out of tuning.

### Q101. Why use logistic regression as another baseline?
It provides a different linear decision rule and can produce probabilities. Comparing it with SVM on the same feature union separates classifier choice from feature engineering.

### Q102. What other classical methods are included?
SGD, Complement Naive Bayes, Multinomial Naive Bayes, RidgeClassifier, cosine k-nearest neighbours and RandomForest. The extended roster is kept separate from the default roster so adding experiments does not silently redefine earlier sweeps.

### Q103. Why can ComplementNB be useful?
It is designed for imbalanced text and is quick to fit. It lacks the same class_weight parameter as some linear estimators, so the balancing arm must be interpreted carefully instead of assuming every model receives identical adjustments.

### Q104. Why is kNN a meaningful baseline?
It asks whether matching the most similar known ticket already performs well. Cosine distance suits sparse text vectors. It may have expensive inference and memory use as the training corpus grows.

### Q105. What imbalance strategies were tested?
None, balanced class weights and random oversampling. Class weights change error penalties; oversampling duplicates minority training rows. Oversampling occurs only after the split and never changes dev or test.

### Q106. Why not use SMOTE?
Interpolating sparse vectors between unrelated tickets does not produce a naturally written sentence. The project explicitly limits the comparison to three arms. This is a methodological choice, not proof SMOTE always fails in text tasks.

### Q107. Does oversampling create new linguistic information?
No. It changes exposure to existing examples. It can improve minority learning but increase training cost and overfitting. Translations and duplicated minority rows are still correlated with their underlying tickets.

### Q108. Why use a sklearn Pipeline?
It binds feature fitting and the classifier into one object, reducing training-serving mismatch. During proper evaluation, fit TF-IDF on train only; fitting vocabulary or IDF over test text leaks information even without test labels.

## 8. Transformers, fine-tuning and multitask experiments

Sources: [encoder training](../../ml/swiftbench/train_encoder.py), [joint training](../../ml/swiftbench/train_multitask.py), [probe](../../ml/swiftbench/probe.py), [Kaggle runner](../../ml/kaggle/runner.py).

### Q109. What is a transformer?
It builds context-dependent representations using attention. For classification, the model maps the token sequence to task logits and predicts a label. Pretraining supplies general representations; fine-tuning adapts them to banking tasks.

### Q110. What is attention in simple terms?
Attention lets the representation of a word depend on other words in the message. “Not” can influence the meaning of “received,” and words can be interpreted within the full ticket instead of as isolated counts.

### Q111. Why consider LaBSE?
Its multilingual representations are suitable candidates for semantically similar messages across scripts. The project's comparisons support its intent performance. Say “selected through experiments” rather than assuming every sentence-embedding model must be best for classification.

### Q112. Is LaBSE used as an embedding-only nearest-neighbour classifier?
Not in the hosted task configuration described here. The project fine-tunes sequence classification models from the LaBSE backbone. Frozen linear probes are separate experiments.

### Q113. What models are registered in the harness?
XLM-R, mmBERT, LaBSE, CANINE-C, SinBERT-large, SinhalaBERTo, TwHIN-BERT, MuRIL, IndicBERT and Gemma 3 variants. Their exact checkpoints and maximum lengths are defined centrally in train_encoder.py.

### Q114. Why compare multilingual and language-specific encoders?
A specialist might represent native text well, while a multilingual model may handle mixed scripts and shared banking terms better. Per-language results determine whether specialization helps. The choice must be measured under matched conditions.

### Q115. Does a larger model always win?
No. Pretraining coverage, tokenization, label quality, data volume, optimization and task fit matter. The Gemma experiments do not establish a general decoder advantage over LaBSE for these targets.

### Q116. What is full fine-tuning?
It updates pretrained model weights and the task head using labelled examples. It can adapt deeply but uses more memory and can overfit or forget general capabilities. The harness supports alternatives such as frozen probes and LoRA.

### Q117. What is a frozen linear probe?
It keeps the backbone fixed and trains a small classifier over extracted representations. It measures how useful the pretrained features already are and separates representation quality from gains produced by full fine-tuning.

### Q118. What are CLS and mean pooling?
CLS uses a designated sequence representation; mean pooling averages eligible token states. Attention masks must prevent padding from contributing. Their relative effectiveness depends on the backbone and task.

### Q119. How does decoder pooling differ?
A causal sequence classifier generally uses the last non-padding token rather than an encoder-style CLS token. The project explicitly sets padding configuration and includes pooling code robust to either padding side for joint Gemma models.

### Q120. What is LoRA?
Low-Rank Adaptation adds trainable low-rank updates to selected weight matrices while largely freezing the backbone. Conceptually W becomes W + scale·BA. This can reduce trainable parameters, but it does not eliminate backbone inference cost.

### Q121. What do LoRA rank and alpha mean?
Rank determines the size of the low-rank update. Alpha controls its scaling. This harness defaults to rank 8 and alpha 16 in the single-task entry point, but exact experimental configurations may override them.

### Q122. Why do target modules matter?
Q/V-only adapters and adapters over all attention plus MLP projections have different capacity and behaviour. Decoder and encoder module names also differ. The harness records lora_targets so materially different runs are not treated as identical.

### Q123. What are the two joint multitask Gemma designs?
One design shares a backbone and LoRA adapter with three task heads and joint losses. The other uses one 82-class head over 77 intent, two sentiment and three priority labels, with a task prefix; each ticket becomes three training examples.

### Q124. Is one hosted Space equivalent to one multitask model?
No. A Space can load and serve three separately fine-tuned models in one process. Joint multitask training requires shared learned parameters and a joint training objective. The repository's Gemma multitask experiments demonstrate that distinction.

### Q125. What are the typical training defaults?
The encoder function defaults to three epochs, batch size 32, learning rate 2e-5, warmup fraction 0.1 and seed 42. LaBSE defaults to max length 128. Quote the run record if an examiner asks for the exact configuration of a published result.

### Q126. Why choose maximum lengths per tokenizer?
Different tokenizers fragment the same text differently. The code uses measured high-percentile lengths and architecture-specific limits rather than one guessed universal length. CANINE's codepoint sequences need a larger length than subword models.

### Q127. What is padding versus truncation?
Padding equalizes batch lengths and should be masked out. Truncation discards content beyond the configured maximum and can remove useful issue details. Report its rate and choose limits using training/dev distributions.

### Q128. Why mixed precision?
It can reduce GPU memory and improve throughput. The harness uses FP16 on CUDA where suitable and handles Gemma's pretrained dtype carefully. It documents that Kaggle T4 GPUs do not provide the same BF16 capability as newer GPUs.

### Q129. What do warmup and gradient clipping accomplish?
Warmup avoids abrupt large updates early in fine-tuning. Gradient clipping limits unstable large gradients. Explain them as optimization safeguards and verify the exact implementation and values in the relevant training loop.

### Q130. Why a custom PyTorch loop?
The repository chooses a readable notebook-oriented loop and centralizes it so experiments share behaviour. This reduces copied-loop drift. It still requires careful handling of epoch selection, dtype, checkpoint saving and labels.

### Q131. How was test-set epoch selection addressed?
Older training code could pick the best epoch on eval_df even for test runs. The current path selects on dev by default and reports the final epoch for test. Historical unstamped records need per-run inspection; no claim that the old procedure was sound in general.

### Q132. Does random seed 42 guarantee identical results everywhere?
No. It helps reproducibility, but hardware kernels, library versions and nondeterministic GPU operations can change results. Record seeds and environments, and use multiple seeds when making close model comparisons.

## 9. Evaluation methods and honest comparisons

Sources: [metrics](../../ml/swiftbench/metrics.py), [result storage](../../ml/swiftbench/results.py), [significance](../../paper/experiments/significance.py), [results tables](../../paper/results/tables/main_pooled.md).

### Q133. What is accuracy?
Accuracy is the proportion of predictions equal to their reference labels. It is easy to understand but can hide failure on rare classes. In current train CSVs, always predicting Neutral already gets about 95.38% sentiment accuracy.

### Q134. What are precision and recall?
Precision asks how many predicted positives are actually positive. Recall asks how many actual positives were detected. For Negative sentiment, low precision creates unnecessary reviews; low recall misses upset customers.

### Q135. What is F1?
F1 is the harmonic mean of precision and recall: 2PR/(P+R), equivalently 2TP/(2TP+FP+FN). It balances the two and is zero if no relevant positives are detected. Specify the class or averaging method when quoting it.

### Q136. What is macro-F1?
It computes each class's F1 and averages them equally. This prevents common classes from dominating the summary. The harness uses macro-F1 for 77-way intent and three-class priority.

### Q137. What is weighted F1?
It weights class F1 values by reference support. It better reflects the overall class mix but can hide rare-class failure. It is recorded as a supporting metric rather than the primary sentiment metric.

### Q138. Why Negative-F1 for sentiment?
Most tickets are Neutral, while Negative is the class associated with review needs. A majority-only system can have high accuracy and zero Negative recall. Negative-F1 makes that failure explicit.

### Q139. What is a confusion matrix?
It counts reference versus predicted classes. It shows which intents are confused and whether High priority is being downgraded. The harness keeps fixed label orders for sentiment and priority so matrices remain interpretable across runs.

### Q140. What is a majority baseline?
It always predicts the most frequent training label. It provides a minimal sanity floor. It must be built from train frequencies rather than choosing the best constant after seeing the test distribution.

### Q141. What is an intent-chained priority baseline?
It predicts intent from text, then maps that predicted intent to the majority priority observed in training. It is servable and strong because intent and priority labels are statistically coupled.

### Q142. What is the gold-intent oracle?
It uses the true evaluation intent to look up priority. Real serving does not have that information, so it is an optimistic reference. Calling it an operational model would hide the intent classifier's errors.

### Q143. Why evaluate by language?
Pooled scores can conceal lower quality for one script or romanized variety. Per-track F1 and error rates show uneven service. Also report support and uncertainty so a small subgroup is not overinterpreted.

### Q144. Are the 15,395 test rows independent?
No. They are five renderings of 3,079 underlying tickets. A confidence interval that treats all rows as independent can be too narrow. Use ticket-level paired resampling to keep the five renderings together.

### Q145. What is bootstrap evaluation?
It repeatedly samples the evaluation units with replacement and recomputes a metric. The spread estimates sampling uncertainty. For this paired corpus, the resampling unit should be the underlying ticket rather than a language row.

### Q146. What is McNemar's test useful for?
It compares two classifiers on the same items using the cases where only one is correct. It addresses paired accuracy differences, not every property of macro-F1. Use it alongside appropriate bootstrap comparisons.

### Q147. What is the danger of many hyperparameter runs?
The best observed score among many trials may reflect noise. Select on dev, examine confidence intervals, and confirm a prespecified candidate on test. Do not interpret a tiny maximum-score difference as robust improvement.

### Q148. What must match for a fair comparison?
Dataset content, label version, split, evaluation population and metric must match. Training data quantity and selection procedure should be stated. The official-split workstream and frozen-split dev tables cannot be mixed without qualification.

### Q149. Why distinguish train from train+dev?
During selection, dev must remain held out. After a configuration is chosen, fitting on train+dev can use all 9,998 source training tickets before a final test evaluation. Scoring that checkpoint on dev would be scoring training data.

### Q150. What is log loss?
It penalizes the probability assigned to the true class using negative log probability. Confident wrong predictions are heavily penalized. It is useful for comparing posterior combinations used in continuous queue scores.

### Q151. What is ECE?
Expected Calibration Error groups predictions into confidence bins and measures mismatch between confidence and correctness frequency. It depends on the binning scheme and sample size. Low ECE does not alone establish useful ranking or good rare-class recall.

## 10. Results you can defend

Sources: [fresh audit](SOURCE_AUDIT.json), [master report](../../ml/reports/RESULTS.md), [model tables](../../paper/results/tables/main_pooled.md), [label quality](../../paper/results/tables/label_ceiling.csv).

### Q152. What intent result should I quote?
The fresh check reproduces LaBSE pooled intent macro-F1 0.883424 and accuracy 0.882949 from 15,395 saved predictions. Their intent reference labels match the current test CSVs. Say these are rechecked saved artifacts, not a new inference run.

### Q153. Why does the README say 88.54% instead?
That is an older official-split result with different provenance. The later report and audited prediction file give about 88.34% macro-F1. State the evaluation source and split; do not choose whichever number is larger.

### Q154. What sentiment result should I quote?
Quote “0.7138 Negative-F1 against the archived evaluation labels,” and immediately mention the current-label mismatch if discussing this working tree. The same predictions re-score at 0.4459 against current CSV labels, so an unqualified current-corpus claim is not defensible.

### Q155. What priority result should I quote?
The freshly rechecked TF-IDF/SVM artifact gives macro-F1 0.873358 and accuracy 0.887886. Separate LaBSE priority artifacts report about 0.8900. Name both the model and provenance; the TF-IDF score is not the hosted LaBSE priority score.

### Q156. Did the strongest intent model also decisively win every task?
No. The paper reports a clearer intent advantage, while several sentiment and priority systems have close scores and overlapping uncertainty. Slight headline differences are not sufficient to claim a general architectural victory.

### Q157. What is the weak subgroup?
Tamilish/Tanglish is a persistent risk in several models. The historical audit reports LaBSE intent error around 29.49% on that track. Some MuRIL comparisons show a different tradeoff, so avoid saying one model wins every language and every task.

### Q158. What is the biggest lesson about sentiment?
Annotation policy strongly changes both class balance and evaluation. Comparing v5 and v8 scores as if only model architecture changed is misleading. Improve and version label quality before interpreting modelling gains.

### Q159. Did Indic-specialist models universally lose?
No. Older pooled comparisons favoured multilingual models, but later frozen-split tables show more nuanced subgroup behaviour, including MuRIL's romanized performance. Quote the exact run rather than repeating a broad old README claim.

### Q160. Is reported batched milliseconds-per-sample serving latency?
No. Batched throughput omits queueing, network overhead, cold starts and per-request orchestration. End-to-end customer latency includes the Space request, database work and possibly OCR or generation.

### Q161. Can the human-label ceiling be compared directly with every F1?
Only with careful reference-label and population qualification. Model-vs-generated-label F1 and generated-label-vs-human F1 use different references. The current CSV version mismatch also means the historical ceiling cannot simply be declared today's ceiling.

### Q162. Why are saved predictions valuable?
They allow metrics, subgroup errors and paired tests to be recomputed without expensive model calls. They also expose label provenance problems. Preserve reference labels and model metadata; separately compare them to current dataset versions.

### Q163. What does an absent result mean?
It means no retained artifact exists for that exact configuration. It is not a score of zero and not evidence the model failed. Tables should distinguish missing evaluation from poor performance.

## 11. Runtime inference and review behaviour

Sources: [inference services](../../backend/app/inference/services.py), [ticket processing](../../backend/app/api/v1/routes.py), [review policy](../../backend/app/domain/policies.py), [Space tests](../../backend/tests/test_inference_space.py).

### Q164. Walk through ticket submission.
The API validates the customer role and payload, creates a Ticket, flushes it, runs classification inline, stores four predictions including language, creates a safe template draft, marks the ticket in_review, and commits. The frontend then uploads an optional attachment separately.

### Q165. What does the hosted Space return?
The Gradio prediction call returns intent, sentiment and priority Label outputs. The backend parses labels, confidences and, when complete, distributions. classify returns them internally in intent, priority, sentiment order, so tuple ordering matters.

### Q166. How is the Gradio call made?
The backend starts POST /gradio_api/call/predict with the message, receives an event_id, then GETs the corresponding event result. It reads data lines and parses the last result. Unexpected shapes or request failures lead to fallback handling.

### Q167. Why is there both a 60-second setting and a 5-second timeout?
The HTTP client setting allows a longer external request, but ticket submission wraps classification in a five-second wait_for budget. The outer budget prevents a cold Space from holding submission indefinitely. This does not limit every later OCR or RAG operation to five seconds.

### Q168. What happens when hosted inference is unavailable?
Intent becomes unknown with confidence zero and an explicit failure model_version. Priority and sentiment use development keyword rules. Low intent confidence triggers manual review. The backend does not pretend fallback output came from LaBSE.

### Q169. Why retain model_version?
It identifies whether output came from a trained model, rule fallback, timeout or OCR SVM. This is essential for auditability and interpretation of confidence. It should ultimately be tied to an immutable checkpoint revision.

### Q170. What can force Critical priority?
The keyword rule checks terms such as fraud, stolen and unauthorised. Because the trained head has only three classes, this rule can override the model's priority. Its English-heavy vocabulary is a limitation, not a complete multilingual fraud detector.

### Q171. When does manual review become required?
If any supplied confidence is below 0.60, priority is Critical, sentiment is Negative, or the category matches selected sensitive phrases. This is a conservative policy, but its literal sensitive-category substring checks do not reliably match every underscore-delimited intent.

### Q172. Does manual_review_required automatically set status escalated?
No. Initial processing sets status in_review even when the flag is true. The flag, priority tier, actual escalated ticket state and RAG human_escalation route are distinct concepts.

### Q173. Does the configured low_confidence_threshold control this policy?
The policy function currently uses a literal 0.60. A config field and an admin setting exist but are not read by that function. Do not demonstrate changing the admin value as if it changes runtime review behaviour.

### Q174. How is runtime language detected?
Unicode block counts identify native script and combinations with Latin. Short markers distinguish some Singlish and Tanglish from English. The result has a heuristic confidence of 0.90 or 0.30 for unknown, not a learned calibrated distribution.

### Q175. Why require complete probability vectors?
Queue pooling needs the full probability mass. The parser checks finite values in [0,1], sum near one and expected class count: 77 intent, three priority and two sentiment. Top-k outputs remain usable labels but are not fabricated into full posteriors.

### Q176. Why not normalize a top-five intent result?
It redistributes missing probability mass onto the five visible classes and creates false certainty. The Space's full-class output patch addresses the source problem. If outputs are incomplete, the urgency code uses an explicit fallback mode.

### Q177. Are all inference probabilities calibrated?
No. The queue uses complete raw model outputs. The OCR SVM has a separate correctness-confidence calibration. A high softmax number should not be described as a guaranteed probability of correctness for an individual ticket.

### Q178. Does predicted category automatically assign the configured queue?
Initial creation chooses General Support. The ORM has Category.default_queue_id, but process_ticket_record does not set category_id or route by that mapping. Automatic category-to-queue routing is a design extension, not a completed runtime feature.

### Q179. Why store processing jobs if work is inline?
The records document an analysis lifecycle and leave a boundary for future asynchronous processing. Here the job is created as running and then succeeded within the request. That does not establish a real external worker pipeline.

## 12. OCR, images and evidence fusion

Sources: [OCR runtime](../../backend/app/inference/ocr.py), [fusion](../../backend/app/inference/services.py), [attachment route](../../backend/app/api/v1/routes.py), [OCR benchmark](../../ml/reports/ocr_google_vision_benchmark.md), [intent benchmark](../../ml/reports/intent_accuracy_by_ocr_engine.md).

### Q180. What is OCR?
Optical Character Recognition extracts text from an image. Swift uses it for screenshots or other image evidence. OCR can misread text and UI graphics, so the extracted result is supplementary evidence rather than an authoritative bank record.

### Q181. Which OCR engines are implemented?
Tesseract and Google Cloud Vision are selectable through the OCR setting. Tesseract is the config default. The code does not automatically try the other engine after an OCR failure.

### Q182. What languages does Tesseract load at runtime?
The runtime uses eng+tam+sin together. Some experimental benchmarks route packs by metadata script. Explain that distinction rather than assuming benchmark routing and serving routing are identical.

### Q183. Why run Tesseract in a thread?
pytesseract and image loading are blocking. asyncio.to_thread keeps that work off the main event loop. It still consumes CPU/process resources, and the current path lacks a clear explicit Tesseract execution timeout.

### Q184. What does Google Vision do?
It sends a base64-encoded image to DOCUMENT_TEXT_DETECTION with English, Sinhala and Tamil hints. It can return page confidence. Network timeout and provider errors are wrapped as OcrError.

### Q185. Why keep Tesseract available?
It is local and useful when cloud credentials or connectivity are unavailable. It avoids a cloud OCR request. That practical fallback option exists, but automatic fallback orchestration is not implemented.

### Q186. What are CER and WER?
Character or Word Error Rate is (substitutions + deletions + insertions)/reference length. They measure transcription difference. WER can exceed 100% when inserted junk words outnumber reference words.

### Q187. What was the image evaluation dataset?
The OCR suite uses 500 fictional banking screenshots expanded into clean, blurred, rotated and low-resolution versions, for 2,000 images. Synthetic design aids reproducibility but does not represent the full variety of real photographs.

### Q188. Why is the fictional bank identity relevant?
The synthetic screenshots use Nova Mobile Banking and invented details rather than real customer accounts. This helps controlled testing. It does not prove uploaded real customer images contain no sensitive data.

### Q189. What did the later OCR comparison show?
The September artifact reports overall CER 15.71% for Vision versus 37.21% for Tesseract, with a reading-order-adjusted Vision figure around 3.67%. Distinguish raw and adjusted scoring; do not substitute the adjusted number into the raw table.

### Q190. Why not always preprocess with OpenCV?
The project's ablations found several preprocessing variants harmed Tesseract on its synthetic suite. Tesseract already performs internal preprocessing. That supports using raw RGB in this pipeline, not a universal claim that preprocessing can never help OCR.

### Q191. Is better CER guaranteed to improve intent?
No. Some recognition errors remove distracting UI text or leave the key issue words unchanged. The intent benchmark even shows a blurred Tesseract condition above clean ground-truth-text accuracy. That is a benchmark-specific interaction requiring error analysis.

### Q192. How good is downstream OCR intent classification?
The retained map-based synthetic benchmark scores 1,868 rows after excluding 132 OTP-not-received rows without a matching BANKING77 intent. Overall Tesseract-fed accuracy is 77.25% for SVM and 76.77% for LaBSE. This is not 77-class macro-F1 on the main ticket test set.

### Q193. What is the ground_truth column in that benchmark?
It feeds perfect intended screenshot text to the classifier. It measures classifier performance without OCR error. It is a reference point, not a strict upper bound: distorted text can occasionally make a fixed classifier predict more accurately.

### Q194. Why use local SVM for attachment text?
The benchmark supports competitive OCR-text intent accuracy, and local inference avoids another slow hosted transformer call. The user's text remains the primary model signal. The choice is specific to this evidence path.

### Q195. How is SVM confidence computed?
A logistic calibration estimates correctness from the top margin and the gap to the runner-up:
sigmoid(w_top·top + w_margin·(top-runner_up) + bias).
This gives a scalar correctness estimate, not a full 77-class posterior.

### Q196. What calibration evidence is saved?
The artifact records 7,695 fitting rows, 7,700 held-out rows, held-out accuracy 0.8245 and ECE 0.0106. Ticket IDs keep five renderings on the same half. Calibration uses a split of the official test corpus, so it needs separate provenance from final untouched-test evaluation.

### Q197. How are customer text and OCR intent fused?
If text confidence is at least 0.60, text wins. Below that floor, a stronger OCR result can replace it. If both labels agree, the label is retained and confidence takes the larger value; this is a heuristic, not a statistically derived combined posterior.

### Q198. Can an attachment lower priority or sentiment?
The attachment's keyword rules can raise severity relative to text results and do not lower it. Reviewed predictions are preserved. Existing manual-review flags are also never cleared merely because new attachment evidence looks reassuring.

### Q199. Where is OCR text stored?
Attachment.ocr_text stores the masked extraction. It is kept separate from Ticket.original_text. Earlier attachment texts are combined for reanalysis, allowing the original customer wording to remain intact.

### Q200. What happens if OCR fails?
The upload route catches OcrError and OSError and records an event, allowing storage to continue. Other failures, such as a missing SVM artifact or unexpected decode exception, may escape that narrow catch. Do not claim every analysis failure is safely absorbed.

### Q201. Are PDFs OCR'd?
The API accepts PDF storage, but only PNG and JPEG enter extract_text in the upload route. The frontend image uploader accepts only PNG/JPEG. PDF page rendering and OCR are not implemented in this flow.

## 13. Dynamic queue urgency and worked mathematics

Sources: [urgency code](../../backend/app/domain/urgency.py), [queue explanation](../../backend/QUEUE_ORDERING.md), [prior builder](../../backend/scripts/build_queue_priors.py), [paper combination](../../paper/ICATC_Paper/sections/05_combination.tex), [simulation artifacts](../../paper/results/tables/tus_queue_summary.csv).

### Q202. How is urgency different from the priority label?
Priority is a discrete label. Urgency is a continuous dispatch score that uses probability uncertainty, sentiment, intent risk and waiting time. Two High tickets can therefore have different scores, and an old Low ticket may overtake a fresh Medium ticket.

### Q203. What is the intent-conditioned priority chain?
For each priority class k:
chain[k] = sum_i P(intent=i)·P(priority=k | intent=i).
It marginalizes over all intents rather than using only the top intent. The conditional table is estimated from training-side labels.

### Q204. What is logarithmic pooling?
The code computes sqrt((head[k]+epsilon)·(chain[k]+epsilon)) and normalizes across Low, Medium and High. This equal-weight geometric combination favours classes supported by both estimates. It is a chosen dependent-expert combination, not proof of statistical independence.

### Q205. Why not simply average the two distributions?
The two signals overlap because intent strongly predicts the generated priority labels. The paper compares several combinations and reports better log loss for log pooling. A probability average is possible, but its measured behaviour differs.

### Q206. What dependence was measured?
The paper reports priority entropy 0.9333 nats and intent-priority mutual information 0.7178, about 76.9% of priority entropy. This is dependence in the annotated corpus, not a causal claim about real bank operations.

### Q207. What is the measured combination result?
The paper's saved comparison reports priority-head log loss 0.3697 versus log-pool 0.2683, and macro-F1 0.8901 versus 0.8983. This is about a 27.4% relative log-loss reduction. It does not directly measure waiting-time improvement in a live application.

### Q208. How is expected severity calculated?
Low has severity 0, Medium 0.5 and High 1. The expectation is 0.5·P(Medium)+P(High). It uses the full distribution rather than dropping uncertainty through an argmax.

### Q209. What is intrinsic severity?
The code uses S = max(0.01, 0.8·expected severity + 0.1·P(Negative) + 0.1·intent criticality). Priority contributes most, while sentiment and intent risk provide smaller adjustments.

### Q210. What is intent criticality?
It is the training-side empirical High fraction for the top effective intent. It is an annotation-derived risk prior. It is not measured fraud probability and is unrelated to Cohen's kappa despite using the symbol kappa in the paper.

### Q211. What is the complete urgency formula?
U = S·(1 + 16·waiting_minutes/SLA_minutes) for active tickets. Inactive tickets receive zero. The computation also returns components, mode and evaluation time so staff can inspect how the score was formed.

### Q212. What are the SLA values?
Low uses 480 minutes, Medium 120 and High/Critical 30. These are research response-window assumptions. Do not claim they are contractual SLAs from a bank or measured service commitments.

### Q213. Give a simple urgency example.
Suppose pooled priority is (Low=.2, Medium=.3, High=.5), Negative=.4 and criticality=.6. Expected severity=.65; S=.8·.65+.1·.4+.1·.6=.62. High is the argmax, so at 15 minutes U=.62·(1+16·15/30)=5.58.

### Q214. Give a log-pooling example.
If head=(.2,.3,.5) and chain=(.1,.3,.6), geometric values are approximately (.1414,.3000,.5477). Normalizing gives about (.1430,.3033,.5537). Expected severity becomes about .7054, before the other score components.

### Q215. Why have a minimum severity of 0.01?
Without it, S=0 would remain zero under multiplicative aging forever. The floor gives every active ticket some positive aging. It does not guarantee a finite maximum wait under arbitrary overload.

### Q216. Can an old Low ticket overtake a new Medium?
Yes. With S=.01 and a 480-minute window, 1,500 minutes of waiting produces U=.51. A fresh ticket with S=.5 has U=.5. This demonstrates aging, but the long example is not a promised acceptable waiting time.

### Q217. Is Critical permanently pinned at the top?
No. It gets High-style severity and a 30-minute window, but final dynamic scores still determine ordering. An aged ticket can outrank a fresh Critical ticket. A permanent emergency lane would be an additional policy.

### Q218. What happens after staff reviews priority?
The reviewed value is authoritative and bypasses model log pooling. Reviewed intent or sentiment become point-mass decisions for scoring. A point mass is an operational decision encoding, not certainty that the reviewer can never be wrong.

### Q219. What are the urgency modes?
log_pool uses complete priority and intent distributions. priority_head uses a complete priority head alone. label_fallback uses a label. reviewed_priority and critical_override encode explicit decisions. The mode makes missing-model-evidence handling visible.

### Q220. What happens to incomplete or missing distributions?
They are rejected for posterior pooling rather than repaired from top-label confidence. A stored label gives severity; an unknown label uses the training base rate. The UI marks fallback urgency as estimated.

### Q221. Which tickets stop accumulating dispatch urgency?
Responded, resolved and closed tickets are inactive and get zero. Reopened tickets use original arrival time. Future timestamps are clamped to nonnegative waiting time, and naive datetimes are treated as UTC.

### Q222. How are ties broken?
Active tickets come before inactive ones, then descending urgency score, then oldest created_at, then public_id. This makes ordering stable for equal scores. The staff API uses one evaluation time across a ranked result.

### Q223. Why rank before pagination?
Otherwise an old urgent ticket outside the newest page could never be selected. The server urgency mode scores the entire matching backlog and then slices the page. The frontend loads all pages and sorts locally for aging updates.

### Q224. Why refresh queue age every 30 seconds?
Waiting time changes without new model inference. The browser recalculates from stored intrinsic severity and the elapsed time since evaluation. This refreshes ordering but does not fetch every changed ticket status from the server.

### Q225. Where do conditional priors come from?
queue_priors.json is rebuilt from frozen-manifest train+dev data: 49,990 language rows, representing 9,998 tickets. It records provenance and aggregate statistics. Test rows are excluded from its estimator.

### Q226. What does smoothing accomplish?
The conditional table adds a base-rate pseudo-observation per intent, preventing fragile zero estimates for less-supported intent/priority combinations. Unseen intents use the overall base rate. The criticality estimate remains an empirical unsmoothed High fraction.

### Q227. Is queue fairness or starvation prevention proved?
No general scheduling guarantee is proved. Positive aging addresses the zero-score defect and simulations explore specific load models. Under sustained overload, bounded delay for all classes cannot be claimed from this formula alone.

### Q228. What queue simulation evidence exists?
Saved tables and run_system_eval use synthetic arrivals, five agents, assumed lognormal handling times, 1,000 tickets per replication and multiple load levels. They measure effects under those assumptions. They are distinct from concurrent HTTP load tests and real support-desk validation.

### Q229. Why do paper sections disagree about validation?
The evaluation section includes simulation results, while the conclusion and queue README still contain “specified, not validated” wording. Say simulations exist but field validation does not; verify the exact policy/configuration behind a table before quoting numerical gains.

### Q230. Why are posteriors uncalibrated for queue ordering?
The paper studies a calibration-versus-score-separation tradeoff and the application preserves raw distributions for its chosen policy. This is a specific operational design choice. Calibration can still be useful, and no universal claim that calibration harms ranking is warranted.

### Q231. What is the queue scaling limitation?
The server currently loads matching tickets and scores them in memory, while the frontend loads the full backlog. Very large backlogs need efficient score-component storage and database-side ordering or a dedicated scheduler. Current correctness does not prove unlimited scalability.

## 14. Retrieval-augmented generation

Sources: [service](../../backend/app/rag/service.py), [retrieval](../../backend/app/rag/retrieval.py), [ingestion](../../backend/app/rag/ingest.py), [dependencies](../../backend/app/rag/dependencies.py), [source manifest](../../docs/rag_sources/rag_source_manifest.csv).

### Q232. What is RAG?
Retrieval-Augmented Generation retrieves relevant documents and supplies them to a language model as evidence. Swift uses approved banking-policy captures. The model should answer from that evidence and cite it rather than invent policy from memory.

### Q233. Why use RAG instead of training policy facts into a model?
Documents can be reviewed and updated separately from model weights, and citations make sources inspectable. RAG still needs source governance, retrieval evaluation and answer checks; supplying documents does not automatically eliminate hallucinations.

### Q234. What is the current knowledge base?
The retained error-analysis corpus describes five approved English documents and 31 chunks spanning bank and regulator material. Ingesting files is a separate step. Having a manifest in the repository does not prove a running database has been populated.

### Q235. How are documents ingested?
The script checks approval and an official-source allowlist, verifies the captured raw checksum, reads cleaned Markdown, chunks it by structure, embeds each chunk and writes articles/chunks in a transaction. Articles are updated by stable source identity.

### Q236. Why preserve raw and cleaned source files?
Raw files preserve the captured source and checksum contract. Cleaned Markdown removes page noise and provides structured retrieval input. Traceability requires linking the two; checksum validation of raw content alone does not prove cleaned text was never incorrectly edited.

### Q237. How are chunks formed?
Heading context is retained, and paragraphs are grouped around a default 1,800-character limit while keeping structure where practical. This is character-based, not a fixed token count. Very large paragraphs and text before a first heading need explicit handling in a more robust chunker.

### Q238. What is BGE-M3 used for?
It produces multilingual dense query/document representations for similarity retrieval. The configured vector dimension is 1,024. These embeddings are separate from the LaBSE ticket-classification models.

### Q239. Why PostgreSQL with pgvector?
It keeps ticket metadata and knowledge retrieval in one database stack while supporting vector similarity and full-text search. That simplifies the prototype. A specialized search service may be appropriate later if retrieval scale or performance demands it.

### Q240. What is dense retrieval?
It compares embedding vectors to find semantically related chunks, including cases without exact word overlap. Swift's SQL uses cosine distance through pgvector. Similarity is a retrieval feature, not a probability that an answer is correct.

### Q241. What is lexical retrieval?
It matches query terms through PostgreSQL full-text search. It is useful for exact banking terms, while native-language queries against an English corpus may rely more heavily on dense cross-lingual retrieval.

### Q242. Why use hybrid retrieval?
Dense and lexical channels fail differently. Combining them can recover relevant content missed by either alone. The system also searches query variants and can broaden category scope when initial filters yield nothing.

### Q243. What does reciprocal rank fusion do?
It adds 1/(60+rank) for each channel where a chunk appears, then ranks by the sum. It combines ranked lists without assuming dense and lexical scores share a scale.

### Q244. Why not add raw dense and lexical scores?
Their numerical scales have different meanings. A large lexical rank score is not directly comparable with cosine similarity. RRF provides a rank-based combination with fewer scale assumptions.

### Q245. What does FlashRank do?
It reranks candidate passages in relation to the query. The configured model is ms-marco-MiniLM-L-12-v2. The repository notes English bias, so its score contributes only a small portion of evidence confidence.

### Q246. What is the current confidence formula?
It uses 0.85·best dense score + 0.10·normalized RRF + 0.05·best rerank score, plus up to 0.05 for category agreement, capped at one and rounded. This is a heuristic relevance gate, not a calibrated probability of factual correctness.

### Q247. Why was the confidence formula changed?
The retained error analysis found useful retrieval was often discarded because the old gate depended too heavily on near-zero reranker scores. Current code gives dense multilingual relevance more weight. The historical defect report explains the change; it does not quantify current live answer quality.

### Q248. What is the current evidence threshold?
The Settings value is 0.50 and the dependency wiring should be checked for deployment. The retriever constructor has a different default of 0.55, so quote the wired settings rather than assuming class defaults always govern runtime.

### Q249. What happens if embeddings fail?
The retriever tries lexical retrieval. However, its confidence formula remains dominated by dense score, so lexical-only evidence may fail the normal threshold. “There is a lexical fallback” does not mean answers remain available with equivalent quality.

### Q250. Why expand neighbouring chunks?
The selected chunk may omit context immediately before or after it. The code adds adjacent chunks and caps expansion at final_limit+3. Neighbours provide context but are not allowed as direct citation targets by the validator.

### Q251. What are the candidate and final limits?
Settings default to ten candidates and five final ranked chunks. These limit reranking and prompt cost. Neighbour expansion can add a small number of extra context chunks.

### Q252. How are stale or unapproved sources filtered?
SQL requires approved status and a review date within the configured 365-day age. This protects retrieval freshness relative to recorded reviews. It does not automatically revalidate a page against today's official policy.

### Q253. Are results restricted to the customer's bank?
The endpoint currently passes institution=None, so approved sources may span institutions. Citation metadata retains the institution and the prompt tells the model to keep policies separate. Asking the customer for bank scope would provide a stronger filter.

### Q254. What happens when no usable evidence remains?
The service returns human_escalation with a reason and no draft. It should not fabricate a policy answer. This is a route result; it currently does not persist a ticket escalation or notify a human.

### Q255. Does RAG currently consume attachment OCR?
The assistance endpoint passes original ticket text and optional follow-up text. It does not append Attachment.ocr_text to the retrieval query. OCR can influence stored predictions used as context, but direct OCR retrieval input described in older documentation is not wired here.

### Q256. Does RAG remember the whole chat?
Follow-up UI messages are kept in component state. The backend combines original ticket context with the current question, not an entire persisted conversation transcript. Reloading or navigating can lose that conversational history.

### Q257. How is response language chosen?
The endpoint passes the ticket's explicit response language on every assistance turn. This avoids letting weak romanized-language heuristics override customer preference. The UI preference offers English, Sinhala and Tamil, while internal RAG types can represent romanized variants too.

### Q258. Is RAG confidence supplied by the answer model?
No. Retrieval confidence is computed from evidence scores before generation. This avoids asking the same generator to certify its own correctness, but the heuristic is still not a complete faithfulness measurement.

### Q259. Why are articles and chunks separate?
Articles hold source identity, institution, version, review date and approval. Chunks hold indexed passage content and embeddings. Multiple chunks share article metadata, avoiding duplication and allowing source-level governance.

### Q260. What is the domain-allowlist limitation?
validate_source currently checks whether an allowed domain appears in the URL string. A strict parsed hostname check would be safer than substring matching. Because ingestion uses a curated manifest, this is a hardening issue rather than proof of a runtime exploit.

## 15. Generation, citations and safety boundaries

Sources: [prompt](../../backend/app/rag/prompts.py), [providers](../../backend/app/rag/providers.py), [guardrails](../../backend/app/rag/guardrails.py), [safety](../../backend/app/rag/safety.py), [citation validation](../../backend/app/rag/citations.py).

### Q261. Which models generate answers?
The backend supports Groq as primary, Gemini as optional fallback, and Ollama as an alternative local provider. Exact model names are configurable. Defaults in config.py differ from older RAG setup examples, so do not memorize an old example as the deployed model.

### Q262. Why provider fallback?
A provider may fail, be rate-limited or time out. Fallback can improve availability. It can also change quality and language behaviour, so the service reports which provider actually answered.

### Q263. What does temperature zero mean?
It reduces sampling variability. It does not guarantee factual accuracy or bit-identical responses from every hosted system. Grounding still depends on evidence and validation.

### Q264. How are transient provider failures retried?
The code retries transport failures and selected status codes such as 429 and 5xx with backoff. It honours short Retry-After values but fails over when the requested wait exceeds five seconds. The retry count defaults to two.

### Q265. Does the twenty-second timeout bound the whole assistance call?
No. Multiple retrieval operations, provider attempts, retries, fallback and a citation-format retry can extend total latency. A per-attempt timeout is not a global request deadline.

### Q266. What is prompt injection?
It is customer or document text attempting to change the assistant's instructions, reveal configuration or bypass policies. The project treats it as input to inspect, not authority to follow.

### Q267. How does the deterministic guardrail work?
It canonicalizes text, removes zero-width characters, normalizes Unicode, case-folds, checks leetspeak and compact signatures, and inspects base64 and ROT13 candidates. It scans original and normalized context, including the stored ticket in follow-up retrieval text.

### Q268. Why inspect stored ticket context too?
An attacker can place instructions in the original ticket and later ask an innocent question. The original ticket still enters the prompt. Scanning only the new question would miss that path.

### Q269. Does detecting 18 of 18 examples prove injection immunity?
No. It demonstrates detection on a finite retained corpus. New paraphrases, multilingual attacks and indirect document injections can differ. Treat it as regression evidence with a known scope.

### Q270. What requests are safety-routed?
The current router checks account-specific information and financial-action requests using multilingual terms and selected intent sets. It prevents general policy assistance from pretending to access private bank data or execute operations.

### Q271. Does the RAG router escalate every Negative or Critical ticket?
Not directly. QueryContext carries sentiment and priority, but route_safety does not inspect those fields as general rules. Sensitive intent or wording may escalate. The older summary “negative always escalates to a human” is too broad for this endpoint.

### Q272. What does human_escalation actually do?
It returns no draft and an escalation reason. The route currently does not update ticket.status, create an assignment or notify an agent. The UI promise of human review is therefore broader than the side effects performed by this call.

### Q273. How are factual citations represented?
The generator uses markers such as [E1]. The result includes source title, URL, institution, version, review date and chunk IDs. Repeated markers from one source are grouped into a citation object.

### Q274. What does citation validation check?
It requires valid evidence indexes and citations on factual blocks and list items, rejects neighbour-only citations, and excludes recognized headings or a general safety disclaimer. This checks structure and allowed references.

### Q275. Does valid citation formatting prove factual faithfulness?
No. A sentence can cite a real chunk that does not support its claim. The current validator does not perform semantic entailment for every fact. Separate human or governed judge evaluation is needed.

### Q276. What does citation-layout normalization do?
It repeats an existing selected citation onto uncited layout blocks. This helps local models satisfy formatting, but it does not prove that citation supports each added block. Mention this limitation if challenged about guaranteed grounding.

### Q277. When does the model get a second attempt?
If the answer fails specifically for invalid or missing citations, the service asks for a complete rewrite using the same evidence. Other validation failures escalate rather than automatically giving unrestricted additional attempts.

### Q278. What prohibited outputs are checked?
The validator rejects an insufficient-evidence marker, selected English action claims and requests for sensitive secrets. Its regex checks are limited; multilingual paraphrases may evade output rules even when prompts instruct against them.

### Q279. Are generated assistance answers saved for agent approval?
No. AssistanceResult defaults approval_required to false, and the endpoint returns it directly. Stored response-template approval is a separate workflow. This is one of the most important implementation-versus-documentation differences to explain.

### Q280. What evidence is needed to assess RAG quality?
Retrieval recall, source relevance, answer faithfulness, citation correctness, language correctness, safe escalation and latency, all broken down by language and category. HTTP 200 and a valid marker are not substitutes for these evaluations.

## 16. Authentication and authorisation

Sources: [security](../../backend/app/core/security.py), [dependencies](../../backend/app/api/dependencies.py), [auth routes](../../backend/app/api/v1/routes.py), [AuthProvider](../../frontend/src/app/providers/AuthProvider.tsx), [REST client](../../frontend/src/services/restTicketService.ts).

### Q281. What is authentication versus authorisation?
Authentication establishes who the caller is. Authorisation checks what that caller may access. A valid customer's token must not allow another customer's ticket or administrator actions.

### Q282. How are passwords stored?
The code uses pwdlib's recommended password hashing, with an Argon2 dependency. Hashing supports verification without retaining the plaintext password. It differs from reversible encryption and must not be replaced by a fast unsalted hash.

### Q283. What is a JWT access token?
It is a signed token carrying claims such as user ID, role, type, issued time and expiry. Swift signs with HS256. A signature detects tampering; it does not encrypt the token contents.

### Q284. Why pin the allowed JWT algorithm?
The decoder explicitly accepts HS256, rather than trusting an algorithm declared by an untrusted token. This reduces algorithm-confusion risks. Secret management and expiry validation still matter.

### Q285. What are token lifetimes?
The default access token lasts 15 minutes and the refresh session seven days. Access expiry limits a stolen token's lifetime. Refresh rotation supports continued sessions while allowing server-side revocation of refresh credentials.

### Q286. Where are refresh tokens stored?
The raw token is in an HttpOnly cookie. The database stores its SHA-256 hash in AuthSession with expiry and revocation fields. High-entropy random tokens can use fast hashing for lookup because they are not guessable passwords.

### Q287. How does refresh rotation work?
The backend verifies the existing token hash and session, revokes that session and creates a new refresh token/session. Reusing the old revoked token fails. Strong replay-family detection and concurrency handling would require additional controls.

### Q288. What does HttpOnly protect?
It prevents JavaScript from reading the refresh cookie directly. It reduces token extraction through XSS but does not prevent malicious script from issuing actions with an authenticated browser.

### Q289. How do production cookie settings differ?
Production cookies use Secure and SameSite=None; development uses SameSite=Lax. Secure requires HTTPS. Cross-site cookies also require explicit attention to CSRF and trusted origins.

### Q290. Is CORS authentication?
No. It controls which browser origins can read cross-origin responses. Backend access checks must still authorize each request. Non-browser clients are not stopped simply by a CORS policy.

### Q291. Is CSRF fully solved?
The access-token API uses Authorization headers, but refresh/logout use cookies and production allows cross-site cookie use. Explicit CSRF/origin controls are not visible in those handlers. Describe this as a hardening gap rather than claiming SameSite=None is protective.

### Q292. Where is the access token stored in the browser?
restTicketService holds it in module memory. AuthProvider stores a user-profile summary in sessionStorage or localStorage for restoration, not the access token. The summary is not trusted as proof of backend authority.

### Q293. What does Remember me change?
It chooses localStorage versus sessionStorage for the profile summary and removes the stale alternative. It does not change the configured refresh-cookie lifetime. Explain the implemented behaviour rather than implying a distinct long-lived token policy.

### Q294. How is a session restored?
The client calls /users/me; a 401 triggers one refresh flow, obtains a new in-memory access token and retries. AuthProvider removes stale stored profiles if restoration fails.

### Q295. Why share refreshPromise?
Concurrent failed requests can otherwise rotate the same refresh credential multiple times. A shared promise coordinates one client-side refresh and lets waiting requests reuse its result. It does not solve every race involving multiple browser tabs or concurrent backend callers.

### Q296. Why read the user's role from the database?
current_user loads the current User and checks activity rather than trusting the role claim alone. Deactivation and role changes affect authorization despite an older token claim. The token still identifies the subject.

### Q297. What happens on logout?
The refresh session is revoked and the cookie deleted; the frontend clears its access token and stored profile. A copied access token can still be valid until expiry, because access tokens are not individually blacklisted here.

### Q298. Can anyone register as an administrator?
The public registration schema allows customer or agent only. Agent registration requires a configured invitation code. Administrator creation is outside that public role choice.

### Q299. Why use constant-time comparison for the invite code?
secrets.compare_digest reduces timing differences when comparing a secret code. The code must still be configured securely and protected from sharing or brute-force attempts.

### Q300. Why return 404 for another customer's ticket?
It avoids revealing whether the guessed ticket exists. Both unknown and unauthorized objects appear unavailable. The same ownership idea applies to attachment downloads.

### Q301. Are all staff restricted to their assigned tickets?
The current staff access check permits agents and administrators to retrieve the staff ticket scope; it does not universally require assignment ownership. This is a product authorization choice that would need stricter queue/assignment policies for some banks.

### Q302. Is optimistic refresh-session rotation race-free?
Not established. The handler reads and revokes a session without an explicit row lock visible here. The frontend reduces same-tab races, but robust server-side single-use rotation should be tested under concurrent refresh requests.

## 17. Database, entities and transactions

Sources: [entities](../../backend/app/models/entities.py), [DB setup](../../backend/app/core/db.py), [migrations](../../backend/alembic/versions/0001_initial.py), [RLS migration](../../backend/alembic/versions/0002_enable_rls.py), [database schema](../../docs/database/schema.dbml).

### Q303. Why a relational database?
Tickets, customers, staff, predictions and responses have structured relationships and integrity requirements. Relational transactions and constraints make multirow changes safer and support reporting. JSON remains useful for flexible posterior dictionaries.

### Q304. Name the core tables.
users, auth_sessions, support_queues, ticket_categories, tickets, predictions, attachments, processing_jobs, ticket_events, ticket_notes, responses, audit_logs and system_settings. RAG adds knowledge_articles and knowledge_chunks.

### Q305. Why use UUID primary keys?
They provide stable identifiers without relying on sequential database IDs across components. They do not authorize access and should not be treated as a substitute for ownership checks.

### Q306. Why have a public ticket ID as well?
A readable SW-year-number identifier is convenient for users and support. The internal UUID remains the relational key. The current public number generation counts existing tickets, creating a concurrency limitation.

### Q307. What is wrong with count-plus-one public IDs?
Two simultaneous submissions can read the same count and generate the same ID. A unique constraint prevents duplication but can cause one request to fail. A database sequence or other atomic allocation is needed.

### Q308. What do foreign keys do?
They ensure referenced users, tickets or articles exist and define deletion behaviour. They prevent dangling relationships but do not enforce business permissions such as whether a user is the correct assigned agent.

### Q309. Why one-to-many Ticket relationships?
A ticket can have multiple predictions, attachments, events, notes and responses over its lifecycle. Keeping them in separate tables supports auditability and avoids repeatedly copying large data into the Ticket row.

### Q310. What prevents duplicate predictions?
There is a unique constraint on ticket_id, task and model_version. It prevents duplicate records for that run identity. A future multi-version history needs an explicit rule for selecting the active prediction because some code maps by task alone.

### Q311. Why store reviewed values separately?
It preserves the original model value and staff correction with reason and reviewer identity. The effective output prefers reviewed_value. This separates model evidence from operational judgement.

### Q312. Why are events and audit logs different?
Events describe a ticket's history and can be customer-visible. AuditLog records management/security-relevant actions with actor and entity identity. Not every response operation currently emits equally detailed audit records.

### Q313. Why keep internal notes private?
They may contain staff discussion or operational details. ticket_out returns notes only in staff view and filters events for customers. Data filtering belongs on the backend, because hiding a UI element does not prevent direct API access.

### Q314. Why are timestamps UTC-aware?
It prevents ambiguity across time zones and daylight-saving rules and supports consistent queue aging. SQLite test fixtures can lose timezone information, so urgency normalizes naive datetimes as UTC.

### Q315. What is flush versus commit?
flush sends pending changes to the database within the transaction, enabling IDs and foreign-key dependencies. commit makes the transaction durable. A flush is not a successful final save.

### Q316. Why create predictions and the ticket in one transaction?
It avoids a partially created logical ticket if processing fails before commit. External model calls themselves cannot be rolled back, and file writes lie outside the SQL transaction, so cross-system consistency needs extra care.

### Q317. What file/database consistency problem exists?
The image is written before the final database commit. A later error can leave an orphan file even if SQL work rolls back. A stronger design uses cleanup on failure or staged storage with a finalization step.

### Q318. Why use selectinload?
It eagerly loads related collections in separate batched queries, avoiding async lazy-loading errors and reducing repeated individual lookups. Loading every relationship for every list result still has cost and should be tuned.

### Q319. Why expire and reload after a change?
The SQLAlchemy session uses expire_on_commit=False, so related objects can remain stale. reloaded expires the ticket and reads it with relationship options so changed assignment or queue details are correctly returned.

### Q320. Why Alembic?
It versions schema changes and allows consistent upgrade paths. The repository has migrations for roles, administration, RAG, OCR text and prediction probabilities. Starting a new backend against an old schema without migration can fail.

### Q321. What does migration 0008 add?
It adds nullable JSON probabilities to predictions. Old rows remain valid through explicit urgency fallbacks. It does not silently regenerate predictions or send historical tickets to an external model.

### Q322. What does the RLS migration protect?
It enables row-level security without public Data API policies to block unauthorized Supabase-style API access. The application connects as the database owner and relies on FastAPI authorization; do not claim per-user RLS policies enforce every backend ticket read.

### Q323. Is database encryption implemented in application code?
The code does not implement general field encryption or encrypted local attachment storage. Managed infrastructure may provide protections, but that must be verified separately. Design requirements are not evidence of encryption at rest.

### Q324. Why use pool_pre_ping?
It checks pooled connection health before use to reduce failures from stale connections. It does not retry arbitrary failed transactions or guarantee database availability.

## 18. API design, status workflows and administration

Sources: [API schemas](../../backend/app/schemas/api.py), [routes](../../backend/app/api/v1/routes.py), [state policy](../../backend/app/domain/policies.py), [OpenAPI contract](../../docs/api/api_contract.yaml).

### Q325. Why version routes with /api/v1?
It gives the interface a version boundary so future incompatible changes can be managed. A version prefix is useful only if changes are governed consistently rather than silently breaking the same version.

### Q326. What is OpenAPI?
It describes endpoints, payload schemas, authentication and responses. FastAPI serves /openapi.json and Swagger UI. The retained YAML is a reviewed contract that can drift, so tests should compare it with actual served routes.

### Q327. What are important HTTP statuses here?
201 means created; 204 means no response body; 401 means authentication failed; 403 means the role/action is forbidden; 404 means unavailable object; 409 means conflict; 413 means too large; 415 means unsupported content; 422 means invalid input; 429 means rate-limited.

### Q328. What validation limits apply to a ticket?
Subject is 5–150 characters; message is 15–5,000. Pydantic validates server payloads, while Zod validates the frontend form. The server remains authoritative even if the browser is bypassed.

### Q329. Why a state-transition table?
It makes valid ticket lifecycle changes explicit instead of accepting any status string. Examples include assigned to resolved and resolved to reopened. The frontend mirrors it for button eligibility, and the backend enforces the status endpoint.

### Q330. What ticket statuses exist?
new, processing, in_review, assigned, escalated, response_draft, responded, resolved, closed and reopened. Initial inline processing usually reaches in_review before the customer receives the created ticket.

### Q331. Are all state changes guaranteed to use the transition table?
No. Dedicated response approval/sending and undo routes directly set states under their own checks. Auditing each route is necessary; testing only the generic status endpoint does not prove universal lifecycle enforcement.

### Q332. What is the version field for?
The status update accepts an optional version and rejects a mismatch with 409 before incrementing the ticket version. This is a partial optimistic-concurrency check, not a database-atomic compare-and-swap across all mutations.

### Q333. Does the frontend use that version consistently?
The mapped frontend Ticket does not currently retain and send it in normal status updates. Therefore do not claim the UI guarantees protection from simultaneous staff edits.

### Q334. How does response approval work?
Staff may edit a non-approved, non-sent draft. Approval stamps a reviewer and time; sending requires approved status and sets the ticket to responded. Repeated sends return the existing sent response rather than sending again.

### Q335. Can customers see an approved response before it is sent?
Yes. ticket_out exposes approved and sent responses to customers. If the desired policy is visibility only after send, the filter would need changing. Explain the actual two-state visibility.

### Q336. Are arbitrary prediction corrections strongly validated?
The schema accepts a nonempty string and reason. Priority and sentiment conversion enforce their enums, but category validation is less constrained. Invalid correction handling should be strengthened rather than claiming all inputs are checked against the 77-class taxonomy.

### Q337. What does assignment do?
It connects a ticket with an eligible staff user or queue and records history. The regular “assign to me” client can call assignment with an empty payload, relying on backend defaults. Assignment is different from model-based queue routing.

### Q338. What does the admin area do?
It exposes dashboards, user/role/activity changes, queues, audit searches and settings. These use AdministratorUser dependencies. Some stored settings are currently descriptive/configurable data without corresponding runtime consumers.

### Q339. Which admin settings do not automatically change runtime behaviour?
The stored low-confidence threshold is not read by the literal review policy; max_upload_mb is separate from Settings.max_upload_bytes; registration flags are not visibly consulted by register. Verify each consumer before claiming a setting is live.

### Q340. Why paginate ticket lists?
It bounds a single response and database query. The API limits page_size to 100. Full-backlog client loading for urgency still makes repeated requests, so server pagination does not imply the UI's total workload is bounded to one page.

### Q341. Is search SQL-injection-safe?
SQLAlchemy expressions and bound retrieval parameters avoid concatenating user input into executable SQL. LIKE wildcards can still broaden matching and large queries can cost time; SQL injection safety is not the same as performance control.

### Q342. What do health and readiness mean?
Health reports the process endpoint is alive. Readiness performs a database query. Neither proves the hosted classifier, OCR binaries, knowledge base or generation provider are ready.

## 19. Frontend state, forms and small implementation choices

Sources: [routes](../../frontend/src/app/router/Routes.tsx), [REST mapping](../../frontend/src/services/restTicketService.ts), [submission](../../frontend/src/pages/customer/SubmitTicketPage.tsx), [uploader](../../frontend/src/components/tickets/ImageUploader.tsx), [queue](../../frontend/src/pages/agent/AgentQueuePage.tsx).

### Q343. How are pages protected?
ProtectedRoute waits for session restoration, redirects unauthenticated callers, and sends users to their role's home if the requested role differs. This is navigation behaviour; backend dependencies enforce actual data permissions.

### Q344. Why React Context for auth, theme and language?
They are shared values across many pages. Context avoids passing them through every component. Ticket collections and page-specific filters remain local state where appropriate.

### Q345. What is useState doing?
It retains component state such as selected image, form progress, loaded ticket, errors and queue filters across renders. Updating state schedules a new render; it does not directly persist data to the database.

### Q346. What is useEffect doing?
It starts side effects such as fetching data, timers and browser preference listeners. Cleanup stops timers/listeners and avoids late responses updating abandoned components.

### Q347. Why use an active flag around requests?
It prevents a late promise resolution from updating state after unmount or a changed request context. It does not cancel the network request itself. AbortController would provide stronger cancellation.

### Q348. Why useMemo for filtering and reports?
It avoids repeating derived computations when their dependencies have not changed. It is not a data cache, database index or guarantee against expensive full-backlog processing.

### Q349. Why React Hook Form and Zod?
React Hook Form manages field registration and form state, while Zod defines validation rules and types. The resolver connects them. Backend Pydantic validation is still necessary.

### Q350. Why use z.literal(true) for the notice?
It makes acknowledgement required rather than accepting false as a valid boolean. This is a UI submission requirement; the TicketCreate API does not receive a corresponding persisted consent field.

### Q351. How is API data mapped?
restTicketService maps snake_case keys to UI names, confidence to rounded percentages, responses to draft/approved structures and attachments to evidence state. This centralizes contract translation.

### Q352. Why are confidence thresholds different in the UI and API?
The API stores fractions such as 0.60. The mapper displays percentages such as 60, and UI confidenceBand uses 60/80. Confusing the units could make every item appear high or low confidence.

### Q353. What is the response-state mapping?
The client identifies a recent approved/sent response for display and selects an editable/latest draft separately. Rejected responses become empty draft text. These choices should match the backend lifecycle and be covered by tests.

### Q354. Does the frontend represent every attachment?
The API can return several; mapTicket primarily takes the first for its single-image view. Backend analysis can include multiple OCR texts. The UI is therefore a narrower presentation than the persistence model.

### Q355. Are the processing steps live model telemetry?
No. The submission stepper advances on a timer while awaiting the request. It communicates activity but does not observe individual inference stages. Do not claim each highlighted step corresponds to a real completed backend event.

### Q356. Is the image progress bar actual upload progress?
No. It is timed preview preparation feedback before submission. The network upload occurs later in createTicket. Real byte progress would require a different request mechanism or progress API.

### Q357. What is the frontend image size limit?
Five MiB and PNG/JPEG only. The backend default is ten MiB and also accepts PDFs. These different limits are real implementation choices and should be aligned if a single product policy is desired.

### Q358. Does a filename containing corrupt prove image corruption?
No. validateImageFile contains that filename heuristic, which can reject valid images and miss invalid ones. Real validation requires decoding and robust content checks; the backend checks selected file signatures but not every safety property.

### Q359. Why use object URLs?
They let the browser display a selected File or authenticated download Blob without uploading it elsewhere. URL.revokeObjectURL on cleanup prevents memory leaks.

### Q360. Why not put authenticated API URLs directly in every img tag?
An img request does not automatically attach the in-memory bearer token. The agent panel fetches a Blob through the authenticated service. The customer detail still uses a direct URL, which can fail against a bearer-protected endpoint.

### Q361. Does submission with an attachment form one atomic API request?
No. The client first creates the text ticket, then posts the image and reloads the ticket. If upload fails, the text ticket may already exist even though the UI shows submission failure; retrying can create a duplicate.

### Q362. What is the queue's sorting workflow?
It loads every API page in stable newest order, deduplicates by ticket ID, filters the full set, calculates dynamic sorting, and paginates the resulting local list. This prevents the old-ticket omission caused by considering only newest-100.

### Q363. Does the 30-second timer refresh all server data?
No. It refreshes local time for urgency calculations. New tickets, staff changes and updated predictions need separate fetching or push updates. Aging and data synchronization are different responsibilities.

### Q364. Why put sort choice in URL parameters?
It makes the selected sort shareable and preserves it through navigation. The code validates permitted values before using them. Other filters are local state and do not all have the same persistence.

### Q365. Why Promise.allSettled for bulk actions?
It captures success and failure per selected ticket instead of discarding all results after one rejection. Partial success can be reflected in the UI. It does not make the batch an atomic backend transaction.

### Q366. How does theming work?
ThemeProvider supports light, dark and system preference, stores the selection and listens for media changes. theme-init.js applies an early choice to reduce an initial flash before React loads.

### Q367. How complete is localization?
LanguageProvider maps many labels into Sinhala and Tamil and falls back when a key is missing. Several messages remain hardcoded English. Interface language, detected input form and requested answer language are separate settings.

### Q368. What accessibility features exist?
Labels, aria attributes, live status, alt text, dialogs and loading states appear throughout the UI. Saved audits cover particular pages. Full keyboard, screen-reader, zoom and multilingual pronunciation testing remains separate work.

### Q369. What does ErrorBoundary do?
It catches rendering errors in its component subtree and shows a recovery UI. It does not automatically catch every asynchronous API rejection, which needs explicit promise/error handling.

### Q370. How are CSV reports produced?
The report page derives metrics from loaded tickets, quotes cells, doubles embedded quote characters, creates a Blob and downloads it. It releases the object URL afterward. This is client-side export.

### Q371. Does quoting a CSV cell prevent spreadsheet formula injection?
No. A user-supplied value starting with a formula indicator may still be interpreted by spreadsheet software. Prefix neutralization or a safer export format is an additional protection.

### Q372. What does the resolution-rate report mean?
It counts currently resolved or closed tickets in the selected creation-date period divided by ticket count. It is not necessarily a cohort time-to-resolution or SLA-compliance metric. Explain the denominator and date filter.

### Q373. Why runtime frontend configuration?
A static bundle can receive an API URL from runtime-config.js when its container starts. getApiBaseUrl checks that first, then build-time Vite configuration, then localhost. This avoids rebuilding the same assets for every environment.

## 20. Security controls and their practical limits

Sources: [rate limiter](../../backend/app/core/rate_limit.py), [app middleware](../../backend/app/main.py), [masking](../../backend/app/inference/masking.py), [upload/download routes](../../backend/app/api/v1/routes.py), [Nginx policy](../../frontend/nginx/default.conf.template).

### Q374. How are uploads validated?
The backend permits selected MIME types, reads at most maximum size plus one byte, and checks the corresponding initial magic bytes. It generates its own UUID storage name and stores a SHA-256 hash. This is useful validation but not a complete malware or decompression-bomb defence.

### Q375. Why check magic bytes as well as MIME?
The client supplies MIME and filename, so neither is trustworthy. A file claiming PNG should start with PNG's signature. A matching prefix still does not prove that the complete file is well-formed or harmless.

### Q376. Why ignore the client's filename for storage?
A generated identifier avoids collisions and malicious path selection. The original name is retained as display metadata after extracting its basename. Download authorization still matters independently of naming.

### Q377. Why hash uploaded files?
A cryptographic content hash can support integrity checks, duplicate detection or forensic comparison. Here it is stored metadata; storing it alone does not automatically deduplicate uploads.

### Q378. How does authorized download work?
The API verifies identity and customer ownership, resolves the stored path, checks it stays inside storage_root and verifies existence, then returns a FileResponse. This prevents arbitrary path reading through that endpoint.

### Q379. Is every attachment access path protected?
No. main.py also mounts storage_root under /attachments as StaticFiles without the download endpoint's authorization. A known storage path could bypass that endpoint. The secure design should remove the public mount or apply equivalent authorization.

### Q380. Is an unpredictable file path sufficient protection?
No. Random UUIDs reduce guessing but can leak through logs, shared URLs or other exposure. Authorization is required even when names are hard to guess.

### Q381. What PII does the masker handle?
It masks long card-like digit sequences, email patterns and a limited phone format, and removes selected UI boilerplate. It is regex-based and can both miss sensitive data and redact innocent sequences.

### Q382. Is all customer text masked before external calls?
No. OCR extraction is passed through redact_pii, but initial classify and RAG prompts use the original customer text. masked_model_text exists as a field but is not populated in the visible processing path. Do not claim universal outbound masking.

### Q383. Does cloud OCR receive the raw image?
Yes. Vision must receive the image before OCR text can be masked. Masking OCR output cannot remove sensitive information already sent in the image. Provider use and consent need their own design.

### Q384. Can the masker identify every Sri Lankan identifier?
No. Its patterns are limited and do not comprehensively cover NICs, account numbers, PINs, names or addresses. A structured data-minimization strategy and tested recognizers would be stronger than broad assurances.

### Q385. What rate limits exist?
Per five-minute window, login and registration allow 20, ticket creation 25, attachment upload 15 and assistance 10. These are abuse budgets in code, not a persistent account lockout policy.

### Q386. How are identities chosen for rate limits?
Valid bearer subjects use a user key; anonymous calls use the source IP. Invalid authorization is hashed into a key. This avoids retaining raw tokens, but rotating invalid headers may create new buckets unless another IP/global budget is enforced.

### Q387. What if Redis is unavailable?
The limiter falls back to process-local locked counters and logs the failure. Protection remains within that process but is not shared across workers or replicas. A distributed outage can therefore weaken the effective global limit.

### Q388. What does a 429 response include?
It returns a rate_limited error and a Retry-After header indicating how long before the current window expires. Clients should respect it rather than repeatedly retrying.

### Q389. Are the Redis increment and expiry fully atomic?
They are separate operations in the code. A failure between increment and expiry can produce a key without the intended TTL. A transactional or Lua implementation can make window initialization more robust.

### Q390. What security response headers are used?
The API adds nosniff, same-origin resource policy, no-referrer and restricted permissions. Nginx adds CSP, frame denial and cross-origin isolation-related headers. Headers complement rather than replace application authorization.

### Q391. What is CSP doing here?
Content Security Policy constrains sources of scripts, styles, images and connections. This template permits broad connection schemes and inline styles, so it is not maximally restrictive. Its cross-origin image rules can also conflict with direct API image display.

### Q392. Does a clean vulnerability audit prove the application is secure?
No. Dependency scans assess known advisories in an environment; they do not prove business authorization, safe prompts or correct workflows. Results also depend on scan date and dependency resolution.

### Q393. What credential issue should you mention?
The root includes files named like API credentials. This analysis did not read their contents. Secrets should be kept out of source control and rotated if exposed; filenames alone are not proof of a leak.

### Q394. Can you claim legal or banking compliance?
No. Implemented security controls and dataset licensing are not compliance certification. Production use requires the organization's own review of applicable requirements, provider arrangements, data retention and governance.

## 21. Deployment, configuration and operations

Sources: [Compose](../../compose.yaml), [backend image](../../backend/Dockerfile), [frontend image](../../frontend/Dockerfile), [config](../../backend/app/core/config.py), [CI](../../.github/workflows/ci.yml).

### Q395. What does Docker solve?
It packages runtime dependencies and setup reproducibly enough for deployment across machines. It does not guarantee identical ML outputs, safe defaults or automatic availability.

### Q396. What services are in Compose?
PostgreSQL with pgvector, Redis, API, worker and frontend. Health checks gate some startup dependencies. Persistent volumes store database data and attachments.

### Q397. What local ports are exposed?
The root Compose maps frontend to 8080, API to 8000 and PostgreSQL to 5432. These are development choices. Public production exposure should be limited and protected.

### Q398. Why run migrations before API startup?
The root command applies alembic upgrade head before launching Uvicorn, so API code can expect its schema. Migration failures stop startup. Multiple production replicas need coordinated migration handling.

### Q399. What does the non-root image user accomplish?
It reduces the impact of a compromised process by limiting operating-system privileges. File ownership is adjusted for attachment storage. It does not fix public static file access or application-level authorization.

### Q400. Why install Tesseract language packs in the image?
pytesseract is a Python wrapper; the executable and eng/tam/sin data must be available separately. A dependency in pyproject.toml alone does not install the OCR engine.

### Q401. Why pin scikit-learn exactly?
The backend's comments tie its serving version to serialized OCR artifacts to reduce prediction drift and cross-version loading problems. Loading trusted joblib artifacts still requires care because pickle-style formats can execute code.

### Q402. Why have optional rag and rag-local extras?
FlashRank can be installed without the full local embedding stack. Local BGE-M3 needs FlagEmbedding/PyTorch; hosted or Ollama embedding paths can avoid that installation. Match dependencies to the selected provider.

### Q403. How does configuration load?
Pydantic Settings reads SWIFT_-prefixed environment variables and .env. get_settings is cached. Values changed during a running process will not necessarily take effect without restarting or clearing the cache.

### Q404. Why normalize PostgreSQL URLs?
Managed services may provide postgres:// or postgresql:// URLs. The validator converts them to postgresql+asyncpg:// so SQLAlchemy uses the intended async driver.

### Q405. What is the worker limitation?
Compose starts Dramatiq with Redis, but process_ticket only validates a nonempty ticket ID. create_ticket calls processing inline and does not dispatch this actor. A completed worker needs database/session orchestration, idempotency and retry-safe lifecycle handling.

### Q406. What would proper asynchronous processing change?
The API could commit a queued ticket/job quickly, enqueue work, then let a worker persist results and expose status through polling or push. It requires durable dispatch, retry safety, cancellation/error states and a reviewable customer experience.

### Q407. Why are provider IDs configurable?
Different environments may use different checkpoints, model names and endpoints. This avoids hardcoding operational choices. Reproducible deployment should pin model revisions and record effective settings without logging secrets.

### Q408. What does Nginx do?
It serves static frontend assets, supports SPA fallback to index.html and adds headers/cache policies. It is not currently the application's active API reverse proxy in the shown template; the browser uses the configured API base URL.

### Q409. Why long cache time for assets but no-store for index/config?
Hashed bundle assets can be cached immutably, while index.html and runtime configuration need fresh references after deployment. Otherwise a browser can retain an old API host or bundle selection.

### Q410. What are the risks of copying all ml into the image?
It can increase image size and include unnecessary experimental artifacts. A slimmer deployment should include only required trusted model files and documented provenance. The current image copy is a practical prototype choice.

### Q411. Is it production-ready because containers start?
No. Startup proves only a narrow operational condition. Production also needs tested failure recovery, backups, secrets management, secure file serving, capacity estimates, retention and monitored provider behaviour.

## 22. Testing, evidence and monitoring

Sources: [test report](../../Testing/Swift_Master_Test_Plan_and_Report_v3.md), [CI](../../.github/workflows/ci.yml), [fixtures](../../backend/tests/conftest.py), [test inventory](SWIFT_SOURCE_MAP.md), [evaluation tools](../../backend/app/rag/evaluation.py).

### Q412. What test layers are present?
Backend unit/API/security/database/contract/observability tests, frontend component tests, retained browser/API/load/accessibility/security-scan evidence, dataset audits and offline multilingual diagnostics. These verify different properties and should not be conflated.

### Q413. What is a unit test?
It checks a small function or policy in isolation, such as fusion thresholds or urgency mathematics. It should verify behaviour and edge cases rather than merely repeat implementation statements.

### Q414. What is an integration test?
It checks components together, such as authenticated API calls with database changes. Many backend tests use an ASGI client and SQLite fixtures, which provide integration evidence without real external services.

### Q415. Why stub external providers in CI?
It avoids cost, network variability and secrets, making tests repeatable. Fake responses can verify application handling but cannot establish the actual provider's language quality, reliability or current output shape.

### Q416. What does SQLite test coverage miss?
PostgreSQL-specific vector search, full-text SQL, some enum/migration behaviour, RLS and real connection management. A production-like database lane is needed for those. SQLite tests are still valuable for fast business-rule verification.

### Q417. What do urgency tests verify?
They cover log pooling, probability completeness, aging, reviewed overrides, inactive tickets, UTC handling, tie breaking, ranking before pagination and customer scope. They verify formula behaviour, not optimal scheduling under arbitrary workloads.

### Q418. What do attachment-fusion tests verify?
Confident customer text wins, stronger OCR can replace weak text, agreement handling, reviewed-value preservation, stored-LaBSE reuse, retry after timeout and severity only increasing from attachment rules.

### Q419. What is property-based testing?
It generates many inputs to check invariants rather than only a few handpicked examples. Hypothesis is present as a development dependency. Identify an actual property test before claiming broad generated-case coverage.

### Q420. What is contract testing?
It checks that implemented endpoints and schemas match the API contract. Optional Schemathesis fuzzing explores invalid or edge payloads. A declared tool dependency does not prove every fuzzing lane ran.

### Q421. What are statement and branch coverage?
Statement coverage measures executed statements. Branch coverage measures decision paths. High statement coverage can leave failure and alternate paths untested, and neither metric proves assertions are meaningful.

### Q422. What historical test verdict is saved?
The September 20 version-3 report says conditional pass for a controlled demonstration, not production-ready. It lists backend failures/skips, limited frontend coverage and unmeasured expensive-path concurrency.

### Q423. Can I quote its backend totals without qualification?
The summary says 195 passed, two failed and three skipped but also says 199 collected; those counts do not sum consistently. Check the raw pytest evidence before presenting an exact total. Do not silently turn this into an all-pass claim.

### Q424. What frontend results are historically reported?
The version-3 report records 45 passing tests across 18 files and low overall frontend coverage. New queue tests now exist in the working tree, so that historical count is not the current suite size.

### Q425. Were all those tests rerun during this viva analysis?
No. This analysis performed source review, an inventory/parse pass and dataset/prediction audits. Historical application test results retain their date and build. Do not present them as newly executed.

### Q426. What is SAST?
Static Application Security Testing inspects source patterns without running the application. Bandit is configured. It can find classes of mistakes but needs review and does not cover all business logic.

### Q427. What is DAST?
Dynamic Application Security Testing probes a running application. Retained ZAP artifacts provide evidence for a particular build and scan configuration. A clean or low-severity result is not universal exploit resistance.

### Q428. What does the load evidence cover?
The historical report's 2,000 samples cover read-only endpoints with p95 around 39 ms. It does not establish throughput for concurrent classification, OCR or RAG generation.

### Q429. Why are expensive-path load tests important?
These paths hold database sessions, call models and consume CPU or provider quotas. Their latency and concurrency behaviour can differ greatly from health or ticket-list endpoints. Measure end-to-end latency and error rates under realistic workloads.

### Q430. What historical single-user latency is reported?
The retained API flow records ticket creation around 2.1 seconds and assistance around 26.6 seconds. These are one environment's measurements, not current guarantees or a sub-100-ms serving claim.

### Q431. What does an accessibility score of 100 establish?
It establishes that the audited page passed the selected automated checks in that run. It does not prove full WCAG compliance, every route, keyboard flow, screen-reader behaviour or Sinhala/Tamil usability.

### Q432. What did the multilingual safety diagnostic measure?
The historical report says 840 of 841 selected paired tickets escalated in every track. This tests parity on that corpus. It does not establish precision on all benign cases or future language varieties.

### Q433. Why do language-detector reports have different scores?
The report contains earlier weak romanized results, while the after-fix artifact has roughly 96.65% Singlish and 90.35% Tamilish on its corpus. That diagnostic uses detect_consumer_language, not the simpler classifier-language function. State detector, build and date.

### Q434. What is Logfire doing?
It instruments FastAPI and httpx, emits route/evidence/provider diagnostics and can send traces when a token is configured. It is observability, not a guarantee that every payload or secret is excluded from all logs.

### Q435. Why use request IDs?
They help correlate a user-visible error with logs and traces. The API returns x-request-id and a generic error body. Accepted caller-provided IDs still need sensible validation if used in downstream logging.

### Q436. What does the generic exception handler protect?
It avoids returning internal exception details in the HTTP body. It should be paired with internal logging and monitoring; hiding details alone does not fix the underlying fault.

### Q437. How do you evaluate RAG separately from classifiers?
Use answerable/unanswerable cases with source relevance labels, assess retrieval and answer quality, and measure citation correctness, language, safety and latency. The classification confusion matrix does not measure generated-answer quality.

## 23. Failure scenarios and debugging questions

Sources: [processing](../../backend/app/api/v1/routes.py), [inference](../../backend/app/inference/services.py), [RAG flow](../../backend/app/rag/service.py), [client requests](../../frontend/src/services/restTicketService.ts).

### Q438. A customer writes “see attachment”; what happens?
The short phrase may fail the API's minimum message length. With a valid longer generic message, text intent can be weak and OCR may replace it if its confidence is stronger. There is no independent image-only ticket creation endpoint.

### Q439. Text and screenshot confidently disagree; which wins?
The customer's text wins when its confidence reaches 0.60. This reflects a deliberate preference for the customer's own explanation. The screenshot still can raise priority/sentiment through rules, and agents should review conflicting evidence.

### Q440. A customer uploads a fake PNG with a .png extension.
The server checks MIME and magic prefix, not extension alone. A non-PNG prefix is rejected. A malformed image with a matching prefix can fail during decoding, so complete readability checks and exception handling need strengthening.

### Q441. The hosted model returns only five intent classes.
The label can be kept if valid, but the probability vector is treated as incomplete. Dynamic urgency can use the complete priority head or a label fallback. It must not normalize the five classes as if they cover all 77.

### Q442. A staff correction exists and a new image is uploaded.
The attachment update skips reviewed predictions. It computes effective values from staff decisions and never clears an existing review flag automatically. The workflow preserves human authority over prior model decisions.

### Q443. A customer tries another customer's ticket ID.
get_ticket returns 404 when the owner does not match. Listing is filtered by customer_id. Test both detail and attachment access rather than assuming one guarded route protects all related data.

### Q444. The refresh token is expired.
The backend rejects refresh with 401. The frontend clears its in-memory token and restoration removes stale stored user data. The UI should prompt login instead of continuing to assume the stored role is valid.

### Q445. RAG has a correct-looking citation but an invented fee.
The present structural validator may accept a marker that points to real evidence without proving entailment. The prompt forbids invented fees, but a semantic check or human evaluation is needed to detect this failure reliably.

### Q446. An approved document becomes outdated.
Retrieval excludes it when its review date ages past the configured window. Changes before that age limit are not automatically detected. A source owner and scheduled review process remain necessary.

### Q447. A follow-up asks for a transfer to be cancelled.
The stored ticket and current question are checked for safety; the route returns human_escalation rather than claiming execution. It does not actually cancel anything or necessarily change the ticket's persisted state.

### Q448. Redis goes down in a two-replica deployment.
Each process falls back to local rate counters. An attacker can potentially consume more than one process's budget. Monitoring should surface the degraded protection and a shared fallback design may be required.

### Q449. Two agents update a ticket simultaneously.
Some status requests can check a supplied version, but the normal UI does not use it consistently and checks are not atomic across every mutation. Lost updates remain a risk; a comprehensive concurrency design is needed.

### Q450. Ticket creation succeeds but attachment upload fails.
The client can show failure while the text ticket already exists. Retrying the whole form may create a second ticket. A robust UI would distinguish saved-ticket/upload failure and allow retrying attachment upload to the existing ID.

### Q451. OCR succeeds but the local SVM model file is missing.
classify_ocr_intent can fail loading the artifact. The upload route's narrow OCR error catch may not handle it. Validate serving artifacts at startup and preserve the ticket/upload with an explicit analysis failure.

### Q452. The customer image is not visible, but the agent can see it.
Check whether the customer uses a direct img URL without bearer authentication, while the agent uses an authenticated Blob download. Also check CSP and cross-origin resource headers. Treat this as an access/display issue, not necessarily OCR failure.

### Q453. The frontend queue looks stale after another agent resolves a ticket.
The timer updates urgency age, not server state. Reload or implement polling/push invalidation to fetch changed statuses. Local scoring must not substitute for data synchronization.

### Q454. What debugging order do you use?
Reproduce the symptom, trace the relevant request and request ID, inspect status/payload shape, check the database side effects, then isolate provider or UI mapping issues. Use a targeted regression test once the behaviour is understood.

## 24. Limitations, improvements and examiner challenges

Sources: [fresh audit](SOURCE_AUDIT.json), [data statement](../../paper/drafts/data_statement.md), [current code](SWIFT_SOURCE_MAP.md), [test report](../../Testing/Swift_Master_Test_Plan_and_Report_v3.md).

### Q455. What are the three highest-priority improvements?
Reconcile dataset/checkpoint label provenance; close direct attachment access and outbound-text masking gaps; make workflow claims match implementation, including RAG approval/escalation and actual asynchronous processing. Then measure costly-path concurrency and language-specific quality.

### Q456. What would improve Tamilish performance?
Collect real human-typed tickets, standardize or model spelling variation, improve annotation/translation quality and compare techniques on a representative held-out set. A score gap alone does not tell us whether tokenization, register or annotation is the main cause.

### Q457. Why not force all users to write English?
That would reduce accessibility and could alter issue meaning. The project's goal is direct multilingual support. It should evaluate where that goal remains uneven instead of hiding subgroup gaps through a language restriction.

### Q458. Why not use an LLM for every classification task?
Dedicated classifiers are more constrained and can be benchmarked with stable outputs. An LLM-only approach introduces cost, latency and prompt/version dependence. It could be a baseline, but should be compared experimentally.

### Q459. Why not always use the largest model?
Resources, latency and data quality matter. Larger capacity cannot repair mismatched labels or incomplete workflows. Select models using task-specific evidence and operating constraints.

### Q460. Is your system explainable?
It exposes labels, confidences, model versions, OCR text, staff reasons, queue components and source citations. These help inspection. It does not currently provide a complete faithful token-level explanation of every model decision.

### Q461. Does collecting corrections automatically retrain the model?
No. Corrections are stored with reviewer information. A retraining pipeline needs curated exports, quality checks, versioned data, new splits or holdouts, evaluation and deployment governance.

### Q462. What is concept drift here?
Real customer language, product policies, fraud patterns and issue distributions can change relative to training data. Monitor per-language errors, uncertainty, review rates and source freshness. A current model name is not a drift-control strategy.

### Q463. How would you add a new intent?
Update the taxonomy and annotations, collect representative examples, retrain the head and relevant priors, revise correction validation and UI labels, and reevaluate all groups. A 77-class checkpoint cannot simply infer a new output class because a database row was added.

### Q464. How would you add a language?
Collect and validate meaningful data, test tokenizer coverage and class performance, add UI/response support and revisit safety patterns. Confirm transfer instead of assuming a multilingual pretraining label guarantees adequate support.

### Q465. How would you add voice support?
Add validated audio upload or capture, an ASR provider, transcript storage with confidence/provenance, text classification and an audio-specific evaluation. The existing README mention alone does not implement this chain.

### Q466. How would you improve the RAG approval story?
Choose a clear product policy: either explicitly permitted direct policy assistance with evaluated safeguards, or persisted staff-reviewed drafts. Then make API side effects, approval_required, UI wording and documentation consistent.

### Q467. How would you make escalation operational?
Persist an escalation event/state, assign a queue or agent, notify through an implemented channel, and audit the result. A returned string or friendly fallback message alone does not ensure a support person receives the case.

### Q468. How would you improve queue evaluation?
Compare matched policies under declared simulation assumptions, verify artifacts and configuration, then run a monitored real workflow study. Measure urgent waits, routine delays, breaches and subgroup fairness rather than only list-level rank correlation.

### Q469. What is a threat to validity?
It is a reason a conclusion might not generalize or reflect what was intended. Here threats include synthetic screenshots, machine translations, weak labels, correlated language copies, test-set reuse, version mismatches and simulated service assumptions.

### Q470. What should you say when asked “Is this ready for a bank?”
“It is ready to demonstrate as a controlled support prototype, with clearly stated limitations. It is not validated for production banking use. Secure data paths, consistent workflow enforcement, capacity and reviewed answer quality still need work.”

### Q471. What if an examiner points out a genuine defect?
Acknowledge the exact behaviour, explain its consequence, point to the responsible code and describe a targeted improvement. Do not claim the defect is intentional unless the repository and product decision support that claim.

### Q472. What can you confidently defend?
The implemented routes and entities, grouped splitting rationale, measured feature/model comparisons with provenance, OCR evidence-fusion rules and the urgency formula. You can also defend the analysis process that revealed version and documentation mismatches.

## 25. Demo walkthrough and oral practice

### Q473. What is a good live demo sequence?
Log in as a customer, submit a valid multilingual ticket, inspect stored predictions, add a small screenshot, show OCR evidence, switch to an agent to review/assign/correct, demonstrate queue sorting, then edit/approve/send a stored response. Show policy assistance separately.

### Q474. Which prerequisites should be checked before the demo?
Database migrations, valid non-secret configuration, available hosted Space, local SVM/calibration artifacts, Tesseract packs or Vision configuration, ingested knowledge base and generation provider. Verify actual readiness rather than relying only on /health.

### Q475. What is a safe text-only demo example?
Use a fictional support question with enough detail, such as “My replacement card has not arrived after the expected delivery period.” Explain that intent prediction is advisory and show its model version. Avoid real account credentials or customer information.

### Q476. How can you demonstrate Critical separately from Negative?
Compare a calm message containing an explicit fraud/unauthorised keyword with an angry routine complaint. Explain the rule override and review flag. The examples demonstrate the configured rules, not guaranteed multilingual risk detection.

### Q477. How can you demonstrate OCR fusion?
Use a valid generic ticket whose text classification is weak and a clear fictional screenshot with a stronger issue signal. Then compare a confident text ticket with a conflicting screenshot to show that the text signal stays primary.

### Q478. How can you demonstrate the queue mathematically?
Show two tickets' intrinsic severities, SLA windows and wait times, calculate their urgency and point to the resulting order. Explain that the 30-second browser timer updates waiting effects without another model call.

### Q479. How can you demonstrate human correction?
Correct a priority with a reason, inspect the saved reviewer metadata and show reviewed_priority mode changing urgency. Then explain that subsequent attachments preserve reviewed values.

### Q480. What if the hosted model is cold during the demo?
Explain the five-second submission budget and the explicit unknown/rule fallback, then show the manual-review flag. Do not present fallback output as a successful LaBSE inference.

### Q481. What if the RAG provider is unavailable?
Show the generation-provider-unavailable escalation result and clarify that no answer was fabricated. Do not say an agent was notified unless that side effect has actually been implemented.

### Q482. How should you prepare for code questions?
Open the key files and practise narrating one function end to end: classify, fuse_intent, ticket_urgency, assist, request or get_ticket. Explain arguments, return type, side effects, error handling and the relevant test.

### Q483. How should you answer “Why did you choose this value?”
Say whether it came from a measured experiment, a research assumption, a development default or a product decision. For example, 0.60 is the text/review floor, alpha=16 and windows come from queue research assumptions, and 5 seconds is a submission availability budget.

### Q484. How should you answer an unmeasured performance question?
“We did not measure that scenario. The saved read-only load test does not cover it. I would measure end-to-end latency, errors and provider saturation under representative concurrent classification/OCR/RAG requests.”

### Q485. What should you avoid memorising blindly?
The root README's old scores, claims of universal approval, voice support, a completed worker, automatic category routing and full PII protection. Use the current implementation and artifact-specific evidence instead.

## 26. Small code and terminology follow-ups

### Q486. Why a frozen dataclass for Result?
It gives a compact typed value object for label, confidence, version and optional probabilities, and prevents field reassignment. A mutable dictionary stored inside it is not deeply immutable, so “frozen” is not a universal protection against mutation.

### Q487. Why Protocol for RAG dependencies?
It describes the methods an embedder, retriever or provider must support without forcing one implementation class. Fakes can satisfy the same interface in tests. This makes provider changes less invasive.

### Q488. Why lru_cache on settings and priors?
It avoids repeated parsing/loading of stable process-wide values. The tradeoff is that file or environment changes do not automatically refresh cached data.

### Q489. Why validate finite probabilities?
NaN or infinity can break normalization, sorting and scoring without an obvious exception. A value bounded syntactically is not enough if it is nonfinite; the parser checks both.

### Q490. Why add epsilon in geometric pooling?
It prevents exact zero products from eliminating a class completely and avoids numerical edge cases. The very small 1e-12 is a computational safeguard, not substantive smoothing of the training table.

### Q491. Why not round confidence before backend decisions?
Rounding can move values across thresholds or make an incomplete distribution appear to sum to one. The UI rounds only for display, while the backend retains floating-point information and checks expected class count.

### Q492. What does normalized reject?
Missing, invalid, negative, over-one or non-unit-sum dictionaries. The generic urgency helper checks mass validity, while model-response parsing adds expected class-count checks. Do not assume every generic function independently enforces all model taxonomy invariants.

### Q493. Why sort a copy of the ticket list?
sortTickets uses a new array so sorting does not mutate the React state's original list in place. This keeps derived ordering separate from loaded data.

### Q494. Why Map-based deduplication after pagination?
It removes repeated IDs when page boundaries shift or the backend returns duplicates across requests. It does not guarantee a consistent snapshot if new tickets are inserted during full-backlog loading; omissions can still occur.

### Q495. What is an N+1 query?
It retrieves one list and then separately queries each item's relationships. Eager loading reduces this pattern. A list with many relationships can still issue several batched queries and return large payloads.

### Q496. What is idempotency?
Repeating an operation has the same effective outcome as doing it once. send_response handles the already-sent case. Ticket creation lacks a client idempotency key, so retrying it can create duplicates.

### Q497. What is exponential backoff?
Wait time increases across retry attempts, reducing pressure on a struggling provider. Jitter prevents many callers from retrying at exactly the same instant. It still needs a total retry/deadline budget.

### Q498. What is a cold start?
A hosted service may need to wake or load models before answering. The submission budget allows fallback instead of a long wait. A warm performance number does not describe cold behaviour.

### Q499. What is softmax?
It converts logits into nonnegative values summing to one over model classes. It expresses a relative class distribution. It is not automatically well calibrated for correctness on out-of-distribution input.

### Q500. What is sigmoid?
It maps a scalar logit into (0,1). The OCR calibration uses it for estimated prediction correctness from SVM margin features, rather than to create a full multiclass distribution.

### Q501. What is class-weighted cross entropy?
It increases the penalty for mistakes on selected classes, helping the model attend to minority examples. It changes the learning objective, so probability calibration can change and should be assessed separately.

### Q502. What is overfitting?
It is learning patterns that perform well on training data but poorly on unseen tickets. Grouped splits, dev selection, regularization and representative evaluation reduce risk. More epochs or repeated test selection can aggravate it.

### Q503. What is an ablation?
It removes or changes one component to measure its contribution. Examples include word versus character features, OCR preprocessing, class balancing, pooling rules or score components. Keep other conditions matched to make the comparison interpretable.

### Q504. What is correlation versus causation here?
A label association or performance gap shows dependence, not why it occurs. Strong intent-priority mutual information partly reflects annotation rules. Tamilish error does not prove romanization alone caused every error.

### Q505. What is the final answer if asked “What did you learn?”
“We learned that reliable evaluation depends on grouped splits, Unicode preservation and label provenance as much as model choice. We also learned that an integrated prototype needs explicit boundaries between predictions, human decisions and customer-visible guidance. Our own source audit exposed mismatches that a headline score would hide.”

## Appendix A. Code navigation map

Use [SWIFT_SOURCE_MAP.md](SWIFT_SOURCE_MAP.md) for the complete generated first-party file/function/notebook index.

| Area | Start here | What to explain |
|---|---|---|
| Server entry | backend/app/main.py | App wiring, middleware, tracing, static mount and router prefix. |
| Environment | backend/app/core/config.py | Settings, defaults, providers, timeouts and cache. |
| Authentication | backend/app/core/security.py; backend/app/api/dependencies.py | Hashing, JWTs, active-user lookups and role guards. |
| Persistence | backend/app/core/db.py; backend/app/models/entities.py | Async sessions, relationships, constraints and audit data. |
| HTTP/business flow | backend/app/api/v1/routes.py | Customer/staff scope, processing, uploads, reviews and response actions. |
| Domain | backend/app/domain/enums.py; policies.py; urgency.py | Status graph, review flag and dispatch scoring. |
| Inference | backend/app/inference/services.py; ocr.py; masking.py | Space calls, rules, OCR, confidence and fusion. |
| RAG orchestration | backend/app/rag/service.py; dependencies.py; types.py | Routing, provider wiring and result contract. |
| RAG search | backend/app/rag/ingest.py; retrieval.py; models.py | Source governance, embeddings, FTS, fusion and reranking. |
| RAG generation | backend/app/rag/prompts.py; providers.py | Evidence-only instruction, retries and fallback. |
| RAG protections | backend/app/rag/safety.py; guardrails.py; validation.py; citations.py | Input checks, account-action boundary and citation limits. |
| RAG evaluation | backend/app/rag/evaluation.py; eval_runner.py; judge.py | Quality metrics, evaluation inputs and optional judge. |
| Worker boundary | backend/app/workers/tasks.py | Placeholder actor and missing durable dispatch. |
| Schema evolution | backend/alembic/versions | Initial schema through probabilities migration. |
| UI entry | frontend/src/main.tsx; app/router/Routes.tsx | Provider tree and role-specific navigation. |
| UI sessions | frontend/src/app/providers/AuthProvider.tsx | Restoration and profile storage. |
| UI transport | frontend/src/services/restTicketService.ts | Token refresh, mapping and action requests. |
| Customer flow | frontend/src/pages/customer | Form, gallery, detail and assistance chat. |
| Agent flow | frontend/src/pages/agent; components/agent | Queue, correction, evidence, drafts and reports. |
| Admin flow | frontend/src/pages/admin | User/queue/settings/audit operations. |
| Reusable UI | frontend/src/components/ui; components/common | Controls, accessibility and shared presentation. |
| UI decisions | frontend/src/lib/utils.ts; ticketActions.ts; agentPreferences.ts | Sorts, eligibility and browser preferences. |
| Dataset creation | datasets/translation; datasets/localization | Translation, romanization, annotation prompts and audits. |
| Data preparation | notebooks/data_preparation | Cleaning, deduplication and prompt evaluation. |
| ML harness | ml/swiftbench | Shared split, features, metrics and comparable run records. |
| ML experiments | notebooks/modeling | Baselines, encoders, probes and technique experiments. |
| Compute | ml/kaggle | Packaging, shared code and reproducible job configuration. |
| OCR research | ml/OCR; synthetic_ticket_dataset | Fictional screenshots, degradation and evaluation. |
| Paper analysis | paper/experiments; paper/results | Statistical tests, label ceilings, calibration and simulations. |
| Tests | backend/tests; frontend/src/test; Testing/test_evidence | Current test code versus dated retained execution results. |
| Deployment | compose.yaml; backend/Dockerfile; frontend/nginx | Containers, dependencies, runtime URLs and serving policy. |
| Formal documents | docs/srs; docs/architecture; docs/feasibility-study | Requirements and proposed design versus implementation. |

## Appendix B. A precise three-flow explanation

**Text ticket:** Customer form → validated API payload → stored original message → hosted LaBSE or explicit fallback → stored predictions + template → in_review → staff correction/assignment → staff edits/approves/sends stored response.

**Image evidence:** Text ticket already exists → separate upload → MIME/size/prefix checks → file storage → selected OCR engine → regex masking → local SVM attachment intent + severity rules → fusion into unreviewed predictions → commit.

**Customer assistance:** Owner-only endpoint → original ticket/current question + preferred language → guardrails and safety rules → approved/current hybrid retrieval → reranking/confidence gate → provider generation → citation/action checks → direct guidance or escalation result. It currently neither appends OCR text nor persists an escalation/approved response.

## Appendix C. What the analysis actually verified

The audit script is [tmp/viva/build_inventory.py](../../tmp/viva/build_inventory.py). It reads source structure, parses all indexed Python files, indexes notebook headings, checks dataset alignment and calculates F1/accuracy from three saved prediction CSVs using explicit count formulas. [SOURCE_AUDIT.json](SOURCE_AUDIT.json) retains machine-readable evidence.

No customer data, credential values or live provider responses were used. Existing application edits were preserved. Historical reports remain historical: no full frontend/backend test rerun, deployment, model retraining or new cloud benchmark was performed for this guide.

