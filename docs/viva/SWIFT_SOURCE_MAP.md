# Swift source map

Generated from the working tree on 7 October 2026. This is a navigation index, not a claim that every file has been executed. Generated assets, dependency code, credentials and environment files are excluded.

## backend/alembic

- [backend/alembic/env.py](../../backend/alembic/env.py): run_migrations_offline (line 20); do_run_migrations (line 31); run_async_migrations (line 37)

- [backend/alembic/versions/0001_initial.py](../../backend/alembic/versions/0001_initial.py): Initial transactional ticket schema. upgrade (line 13); downgrade (line 17)

- [backend/alembic/versions/0002_enable_rls.py](../../backend/alembic/versions/0002_enable_rls.py): Protect application tables exposed through Supabase's public schema. upgrade (line 26); downgrade (line 33)

- [backend/alembic/versions/0003_merge_supervisor_into_administrator.py](../../backend/alembic/versions/0003_merge_supervisor_into_administrator.py): Merge the supervisor role into administrator. upgrade (line 12); downgrade (line 31)

- [backend/alembic/versions/0004_admin_management.py](../../backend/alembic/versions/0004_admin_management.py): Add persistent administrator settings and audit indexes. upgrade (line 10); downgrade (line 26)

- [backend/alembic/versions/0005_repair_system_settings.py](../../backend/alembic/versions/0005_repair_system_settings.py): Repair databases where revision 0004 was recorded before its table was added. upgrade (line 12); downgrade (line 27)

- [backend/alembic/versions/0006_consumer_rag.py](../../backend/alembic/versions/0006_consumer_rag.py): Approved knowledge metadata, PostgreSQL FTS, and pgvector HNSW retrieval. upgrade (line 11); downgrade (line 39)

- [backend/alembic/versions/0007_attachment_ocr_text.py](../../backend/alembic/versions/0007_attachment_ocr_text.py): Store masked OCR text on the attachment instead of appending it to the ticket text. upgrade (line 13); downgrade (line 17)

- [backend/alembic/versions/0008_prediction_probabilities.py](../../backend/alembic/versions/0008_prediction_probabilities.py): Retain complete model posteriors for dynamic ticket urgency. upgrade (line 13); downgrade (line 17)

## backend/app

- [backend/app/__init__.py](../../backend/app/__init__.py): Swift support backend. 

- [backend/app/api/__init__.py](../../backend/app/api/__init__.py): Module constants, imports or package initializer.

- [backend/app/api/dependencies.py](../../backend/app/api/dependencies.py): current_user (line 18); staff (line 36); administrator (line 45)

- [backend/app/api/v1/__init__.py](../../backend/app/api/v1/__init__.py): Module constants, imports or package initializer.

- [backend/app/api/v1/routes.py](../../backend/app/api/v1/routes.py): event (line 108); audit (line 121); prediction_out (line 131); ticket_out (line 146); ticket_options (line 220); get_ticket (line 233); reloaded (line 244); health (line 255); create_customer_ticket_assistance (line 264); ready (line 298); register (line 304); login (line 351); refresh (line 381); logout (line 421); me (line 440); create_ticket (line 445); process_ticket_record (line 467); apply_attachment_text (line 509); list_tickets (line 578); ticket_detail (line 639); add_note (line 645); set_status (line 657); assignable_agents (line 679); assign (line 688); escalate (line 708); undo_escalation (line 727); undo_resolution (line 744); review_prediction (line 758); upload_attachment (line 789); download_attachment (line 857); edit_response (line 872); approve_response (line 891); reject_response (line 911); send_response (line 924); dashboard (line 944); admin_dashboard (line 1012); admin_users (line 1042); admin_update_user (line 1055); admin_queues (line 1101); admin_create_queue (line 1123); admin_update_queue (line 1140); admin_audit_logs (line 1175); admin_settings (line 1239); admin_update_settings (line 1254); test_ocr_masking (line 1290)

- [backend/app/core/config.py](../../backend/app/core/config.py): Settings (line 8); get_settings (line 79)

- [backend/app/core/db.py](../../backend/app/core/db.py): Base (line 9); engine_options (line 16); get_db (line 27)

- [backend/app/core/rate_limit.py](../../backend/app/core/rate_limit.py): Route-specific abuse budgets with Redis enforcement and a local fallback. Limit (line 21); limit_for (line 34); RateLimiter (line 45)

- [backend/app/core/security.py](../../backend/app/core/security.py): hash_password (line 15); verify_password (line 19); create_access_token (line 23); decode_access_token (line 36); new_refresh_token (line 43); hash_refresh_token (line 48)

- [backend/app/domain/enums.py](../../backend/app/domain/enums.py): UserRole (line 4); InterfaceLanguage (line 10); LanguageForm (line 16); Priority (line 26); Sentiment (line 33); TicketStatus (line 39); JobStatus (line 52); PredictionTask (line 59); ResponseStatus (line 66)

- [backend/app/domain/policies.py](../../backend/app/domain/policies.py): can_transition (line 29); requires_manual_review (line 33)

- [backend/app/domain/urgency.py](../../backend/app/domain/urgency.py): ICATC Sections V-VI: log-pooled severity with SLA-relative multiplicative aging. load_priors (line 23); normalized (line 27); effective_distribution (line 37); as_utc (line 45); ticket_urgency (line 50); urgency_sort_key (line 120)

- [backend/app/inference/masking.py](../../backend/app/inference/masking.py): redact_pii (line 4)

- [backend/app/inference/ocr.py](../../backend/app/inference/ocr.py): Text extraction for image attachments. OcrError (line 24); OcrResult (line 29); extract_text (line 35); tesseract_ocr (line 46); google_vision_ocr (line 55); _page_confidence (line 97)

- [backend/app/inference/services.py](../../backend/app/inference/services.py): Result (line 27); detect_language (line 39); classify (line 62); classify_priority_and_sentiment (line 91); _ml_dir (line 117); classify_ocr_intent (line 124); fuse_intent (line 152); more_severe (line 179); _label_result (line 184); classify_with_space (line 211); response_template (line 256)

- [backend/app/main.py](../../backend/app/main.py): enforce_rate_limits (line 57); request_id (line 75); unhandled (line 90)

- [backend/app/models/__init__.py](../../backend/app/models/__init__.py): Module constants, imports or package initializer.

- [backend/app/models/entities.py](../../backend/app/models/entities.py): utcnow (line 32); User (line 36); AuthSession (line 50); SupportQueue (line 62); Category (line 70); Ticket (line 78); TicketEvent (line 116); TicketNote (line 129); Prediction (line 141); Attachment (line 161); ProcessingJob (line 180); Response (line 194); AuditLog (line 215); SystemSetting (line 226)

- [backend/app/rag/__init__.py](../../backend/app/rag/__init__.py): Safety-routed, evidence-grounded consumer banking RAG. 

- [backend/app/rag/citations.py](../../backend/app/rag/citations.py): build_citations (line 13); citations_are_valid (line 37); normalize_citation_layout (line 68)

- [backend/app/rag/dependencies.py](../../backend/app/rag/dependencies.py): model_components (line 17); provider (line 32); consumer_rag_service (line 50); get_consumer_rag_service (line 62)

- [backend/app/rag/eval_runner.py](../../backend/app/rag/eval_runner.py): Runs the golden set and guardrail probes through the real RAG service. RecordingRetriever (line 34); load_cases (line 46); _instrumented (line 50); _judge_provider (line 58); run_golden_cases (line 80); _golden_cases (line 89); run_guardrail_cases (line 143); _guardrail_cases (line 150); build_report (line 174); main (line 194)

- [backend/app/rag/evaluation.py](../../backend/app/rag/evaluation.py): Provider-independent multilingual RAG evaluation metrics and runner contracts. recall_at_k (line 8); reciprocal_rank (line 12); ndcg_at_k (line 16); EvaluationRecord (line 36); summarize (line 51); slice_summary (line 70)

- [backend/app/rag/guardrails.py](../../backend/app/rag/guardrails.py): Deterministic input-side prompt-injection and instruction-leak checks. _canonical (line 60); _decoded_candidates (line 66); _match (line 78); route_guardrails (line 93)

- [backend/app/rag/ingest.py](../../backend/app/rag/ingest.py): Ingest the existing approved-source manifest and structure-aware cleaned Markdown. chunk_markdown (line 22); validate_source (line 46); ingest (line 53); main (line 105)

- [backend/app/rag/judge.py](../../backend/app/rag/judge.py): LLM-as-judge grading for the eval harness. JudgeResult (line 21); judge_answer (line 28)

- [backend/app/rag/languages.py](../../backend/app/rag/languages.py): _markers (line 25); detect_consumer_language (line 40); normalize_query (line 55)

- [backend/app/rag/models.py](../../backend/app/rag/models.py): _TokenTypeSessionAdapter (line 11); BGEM3Embedder (line 29); HuggingFaceEmbedder (line 42); OllamaEmbedder (line 91); build_embedder (line 121); FlashRankReranker (line 154)

- [backend/app/rag/prompts.py](../../backend/app/rag/prompts.py): build_prompt (line 19); build_citation_retry_prompt (line 39)

- [backend/app/rag/providers.py](../../backend/app/rag/providers.py): ProviderError (line 13); OllamaProvider (line 17); _retry_delay (line 51); _post_with_retry (line 64); GroqProvider (line 87); GeminiProvider (line 129); FallbackProvider (line 167)

- [backend/app/rag/retrieval.py](../../backend/app/rag/retrieval.py): lexical_query (line 26); reciprocal_rank_fusion (line 38); PostgresHybridRetriever (line 61); evidence_confidence (line 215); lexical_websearch_query (line 239)

- [backend/app/rag/safety.py](../../backend/app/rag/safety.py): Conservative safety routing for account-specific data and financial actions. route_safety (line 43)

- [backend/app/rag/service.py](../../backend/app/rag/service.py): Retriever (line 16); AssistanceResult (line 21); ConsumerRAGService (line 34)

- [backend/app/rag/types.py](../../backend/app/rag/types.py): ConsumerLanguage (line 7); QueryContext (line 17); Evidence (line 29); Citation (line 51); RouteDecision (line 63); RetrievalResult (line 70); Embedder (line 76); Reranker (line 80); LLMProvider (line 84)

- [backend/app/rag/validation.py](../../backend/app/rag/validation.py): validate_grounding (line 10)

- [backend/app/schemas/__init__.py](../../backend/app/schemas/__init__.py): Module constants, imports or package initializer.

- [backend/app/schemas/api.py](../../backend/app/schemas/api.py): LoginRequest (line 15); RegisterRequest (line 20); UserOut (line 29); TokenResponse (line 38); TicketCreate (line 45); PredictionOut (line 51); EventOut (line 60); NoteOut (line 68); AttachmentOut (line 75); ResponseOut (line 84); UrgencyOut (line 94); TicketOut (line 109); TicketList (line 136); StatusUpdate (line 143); AssignmentRequest (line 148); EscalationRequest (line 153); NoteCreate (line 157); PredictionReview (line 161); ResponseEdit (line 166); DashboardOut (line 170); DashboardBreakdownItem (line 184); DashboardTrendPoint (line 189); AdminUserOut (line 194); AdminDashboardOut (line 204); AdminUserList (line 215); AdminUserUpdate (line 220); AdminQueueOut (line 225); AdminQueueCreate (line 234); AdminQueueUpdate (line 239); AdminAuditOut (line 245); AdminAuditList (line 255); AdminSettingOut (line 260); AdminSettingsUpdate (line 268); ErrorOut (line 272); CitationOut (line 278); ConsumerAssistanceIn (line 289); ConsumerAssistanceOut (line 293)

- [backend/app/workers/__init__.py](../../backend/app/workers/__init__.py): Module constants, imports or package initializer.

- [backend/app/workers/tasks.py](../../backend/app/workers/tasks.py): process_ticket (line 11)

## backend/evaluation

- [backend/evaluation/analysis/__init__.py](../../backend/evaluation/analysis/__init__.py): Offline and live diagnostics for the consumer RAG pipeline. 

- [backend/evaluation/analysis/env_check.py](../../backend/evaluation/analysis/env_check.py): Pre-flight for the live lane: probe every external dependency and say what is missing. _database_url (line 28); check_database (line 34); check_embedder (line 86); _groq_raw_error (line 125); _probe_provider (line 165); check_providers (line 180); main (line 211)

- [backend/evaluation/analysis/offline_guardrails.py](../../backend/evaluation/analysis/offline_guardrails.py): X1/X2 -- guardrail bypass rate and false-positive escalation load. context (line 48); caught (line 57); bypass_corpus (line 61); ticket_context_gap (line 81); load_tickets (line 97); false_positive_load (line 105); paired_safety_coverage (line 139); main (line 196)

- [backend/evaluation/analysis/offline_language.py](../../backend/evaluation/analysis/offline_language.py): L1a -- language detection accuracy, measured at scale on held-out rows. Row (line 41); load_track (line 48); confusion (line 57); accuracy (line 64); paired_bootstrap_ci (line 69); mcnemar_exact (line 85); token_diagnostics (line 95); main (line 160)

- [backend/evaluation/analysis/offline_pipeline.py](../../backend/evaluation/analysis/offline_pipeline.py): Structural diagnostics for chunking, citation validation and the confidence gate. chunking (line 54); citation_validation (line 97); confidence_gate (line 158); main (line 210)

- [backend/evaluation/analysis/probes.py](../../backend/evaluation/analysis/probes.py): Phase 2 -- build and freeze the probe set. load_tickets (line 104); select (line 118); assign_splits (line 156); build (line 165); manifest (line 191); main (line 228)

- [backend/evaluation/analysis/report.py](../../backend/evaluation/analysis/report.py): Phase 5 -- aggregate diagnostics into the committed deliverables. load (line 27); offline_rows (line 34); live_rows (line 207); main (line 278)

- [backend/evaluation/analysis/reporting.py](../../backend/evaluation/analysis/reporting.py): Shared report output for the analysis harness. git_sha (line 23); write_report (line 38); load_report (line 52)

- [backend/evaluation/analysis/run_analysis.py](../../backend/evaluation/analysis/run_analysis.py): Phase 4 -- run the probe set through the real pipeline and record every outcome. RetrievalProbeProvider (line 48); load_probes (line 57); judge_provider (line 77); run_probe (line 124); run_configuration (line 209); summarise (line 257); main_async (line 333); main (line 394)

- [backend/evaluation/analysis/taxonomy.py](../../backend/evaluation/analysis/taxonomy.py): Phase 5 -- map an observed probe outcome onto the failure taxonomy. Outcome (line 41); classify (line 71)

- [backend/evaluation/analysis/traces.py](../../backend/evaluation/analysis/traces.py): Phase 5 -- emit representative traces, one file per failure class. probe_queries (line 24); _fmt_scores (line 40); _probe_trace (line 51); live_traces (line 69); offline_traces (line 107); main (line 167)

- [backend/evaluation/analysis/wrappers.py](../../backend/evaluation/analysis/wrappers.py): Phase 3 -- timing and recording wrappers, plus configuration ablations. StageTimer (line 35); TimedEmbedder (line 72); CachingEmbedder (line 86); FailingEmbedder (line 126); TimedReranker (line 141); IdentityReranker (line 155); DenseOnlyRetriever (line 172); LexicalOnlyRetriever (line 183); TimedRetriever (line 194); TimedProvider (line 208); build_service (line 238)

## backend/scripts

- [backend/scripts/benchmark_ocr.py](../../backend/scripts/benchmark_ocr.py): Compare Google Cloud Vision against Tesseract on the same images. run_engine (line 26); benchmark (line 40); main (line 51)

- [backend/scripts/build_queue_priors.py](../../backend/scripts/build_queue_priors.py): Export aggregate intent priors from the paper's frozen train+dev split (no test rows). main (line 13)

- [backend/scripts/download_weights.py](../../backend/scripts/download_weights.py): main (line 12)

- [backend/scripts/enable_space_posteriors.py](../../backend/scripts/enable_space_posteriors.py): Apply the approved, single-line full-intent-output change to the configured Space. main (line 14)

- [backend/scripts/test_masking_endpoint.py](../../backend/scripts/test_masking_endpoint.py): test_masking_endpoint (line 13)

- [backend/scripts/test_ocr_standalone.py](../../backend/scripts/test_ocr_standalone.py): run_ocr_test (line 14)

- [backend/scripts/test_ocr_upload.py](../../backend/scripts/test_ocr_upload.py): run_tests (line 14)

- [backend/scripts/test_router.py](../../backend/scripts/test_router.py): run_tests (line 7)

- [backend/scripts/verify_space_posteriors.py](../../backend/scripts/verify_space_posteriors.py): Verify the configured live Space supports the complete ICATC log pool. main (line 16)

## backend/tests

- [backend/tests/conftest.py](../../backend/tests/conftest.py): Shared fixtures for the integration and security suites. anyio_backend (line 35); engine (line 40); sessionmaker (line 58); db (line 63); stub_classifier (line 69); app (line 88); client (line 107); make_user (line 116); customer (line 138); other_customer (line 143); agent (line 148); administrator (line 153); auth (line 157); open_ticket (line 163); auth_headers (line 179); new_ticket (line 184)

- [backend/tests/contract/test_openapi.py](../../backend/tests/contract/test_openapi.py): API contract conformance. app_paths (line 25); documented_paths (line 35); test_the_published_contract_is_valid_openapi_3 (line 48); test_no_documented_endpoint_is_missing_from_the_app (line 54); test_contract_covers_the_routes_it_claims_to_cover (line 60); test_contract_drift_has_not_grown (line 71); test_security_scheme_is_declared (line 83); test_openapi_document_is_reachable_over_http (line 89); test_error_shape_is_consistent_across_failures (line 95); api_schema (line 118); test_schema_is_well_formed (line 130); test_every_operation_has_a_unique_operation_id (line 141)

- [backend/tests/database/test_integrity.py](../../backend/tests/database/test_integrity.py): Database integrity: constraints, transactions, injection, and the migration graph. test_email_uniqueness_is_enforced_by_the_database (line 32); test_registration_race_is_rejected_at_the_api (line 59); test_public_ticket_reference_is_unique (line 72); test_deleting_a_ticket_removes_its_children (line 93); test_audit_log_survives_the_actor_being_deleted (line 113); test_failed_commit_leaves_no_partial_write (line 132); test_ticket_creation_is_atomic_when_classification_fails (line 162); test_ticket_search_is_not_sql_injectable (line 200); test_admin_user_search_is_not_sql_injectable (line 219); test_wildcards_in_search_are_treated_as_literals (line 227); test_ticket_list_does_not_issue_a_query_per_ticket (line 238); alembic_scripts (line 265); test_migration_history_has_exactly_one_head (line 271); test_every_migration_is_reachable_from_the_head (line 277); test_every_migration_declares_a_downgrade (line 285); test_engine_uses_pool_pre_ping (line 296); test_supabase_urls_get_tls (line 302); test_orm_metadata_matches_the_tables_the_migrations_create (line 308); test_retrieval_sql_interpolates_no_caller_data (line 320); test_no_raw_sql_uses_percent_or_format_interpolation (line 341)

- [backend/tests/observability/test_logfire.py](../../backend/tests/observability/test_logfire.py): Observability: Logfire instrumentation, trace correlation, and PII hygiene. test_instrumented_app_serves_requests (line 21); test_instrumentation_resolves_routes_on_a_parameterised_path (line 30); test_fastapi_instrumentation_is_actually_installed (line 38); test_logfire_runs_without_a_token (line 51); test_service_name_and_environment_are_set (line 62); test_logfire_token_is_not_hardcoded (line 72); test_every_response_carries_a_request_id (line 85); test_supplied_request_id_is_echoed_back (line 90); test_unhandled_errors_return_a_request_id_not_a_stack_trace (line 96); test_password_is_never_recorded_in_a_span (line 124); test_authorization_header_is_not_recorded_in_a_span (line 139); test_rag_routing_spans_do_not_carry_the_customer_query (line 149)

- [backend/tests/security/test_authz.py](../../backend/tests/security/test_authz.py): Access control: authentication, role separation, and object ownership. _call (line 38); test_protected_routes_reject_anonymous_callers (line 46); test_expired_token_is_rejected (line 50); test_token_signed_with_a_different_key_is_rejected (line 65); test_alg_none_token_is_rejected (line 76); test_refresh_token_cannot_be_used_as_an_access_token (line 87); test_deactivated_account_loses_access_immediately (line 96); test_customer_cannot_reach_staff_routes (line 111); test_agent_cannot_reach_administrator_routes (line 118); test_role_claim_in_token_does_not_override_stored_role (line 123); test_agent_self_promotion_is_blocked (line 130); test_customer_cannot_read_another_customers_ticket (line 140); test_ticket_list_is_scoped_to_the_caller (line 148); test_unknown_ticket_reference_is_not_a_server_error (line 159); test_attachment_of_another_customer_cannot_be_downloaded (line 164); test_attachment_owner_can_download_their_own (line 182); test_random_attachment_id_returns_not_found (line 200)

- [backend/tests/security/test_input_validation.py](../../backend/tests/security/test_input_validation.py): Input validation: payload abuse, file uploads, and output encoding. test_oversized_ticket_body_is_rejected (line 20); test_missing_required_fields_return_422_not_500 (line 29); test_type_confusion_in_the_body_is_rejected (line 43); test_deeply_nested_json_does_not_crash_the_parser (line 48); test_invalid_email_is_rejected_at_registration (line 62); test_short_password_is_rejected (line 70); test_pagination_bounds_are_enforced (line 78); test_declared_type_must_match_the_file_signature (line 92); test_disallowed_mime_types_are_refused (line 114); test_path_traversal_in_the_filename_cannot_escape_storage (line 126); test_null_byte_in_filename_is_handled (line 148); test_empty_upload_is_refused (line 160); test_script_payloads_are_returned_as_json_not_html (line 182); test_error_responses_do_not_echo_raw_html (line 203); test_cors_does_not_reflect_an_arbitrary_origin (line 213)

- [backend/tests/security/test_prompt_injection.py](../../backend/tests/security/test_prompt_injection.py): Prompt injection and instruction-leak resistance. context (line 30); caught (line 34); test_copy_pasted_jailbreak_templates_are_caught (line 54); test_ordinary_banking_questions_are_not_flagged (line 58); test_obfuscated_injection_is_caught (line 96); test_measured_detection_rate_against_the_bypass_corpus (line 100); test_guardrail_reads_raw_text_but_retrieval_reads_normalized_text (line 114); FakeRetriever (line 127); RecordingLLM (line 155); test_injection_in_the_ticket_body_is_blocked_before_the_prompt (line 167); test_injection_in_the_ticket_body_should_escalate (line 183); test_caught_injection_never_reaches_the_model (line 197); test_system_prompt_is_not_echoed_into_the_customer_reply (line 213)

- [backend/tests/security/test_rate_limiting.py](../../backend/tests/security/test_rate_limiting.py): Rate limiting and abuse resistance. test_repeated_failed_logins_are_throttled (line 17); test_account_is_locked_after_sustained_brute_force (line 29); test_registration_is_rate_limited (line 43); test_ticket_creation_is_rate_limited (line 59); test_attachment_upload_is_rate_limited (line 76); test_assistance_endpoint_is_rate_limited (line 94); test_failed_login_does_not_reveal_whether_the_account_exists (line 114); test_oversized_upload_is_refused (line 127)

- [backend/tests/test_attachment_intent.py](../../backend/tests/test_attachment_intent.py): Attachment (OCR) text as a second intent signal next to the customer's own words. test_confident_customer_text_wins_over_attachment_text (line 20); test_weak_customer_text_defers_to_a_stronger_attachment (line 26); test_agreement_keeps_the_text_label_with_the_stronger_confidence (line 32); test_weak_attachment_does_not_replace_weak_text (line 38); test_no_attachment_text_keeps_the_text_prediction (line 44); test_svm_confidence_is_calibrated_not_fixed (line 52); _stub_ocr (line 65); _upload (line 74); test_attachment_keeps_customer_text_and_reviewed_prediction (line 84); test_attachment_decides_when_the_customer_text_is_weak (line 110); _counting_classifier (line 136); test_upload_reuses_the_stored_labse_prediction (line 156); test_upload_retries_labse_after_a_submission_timeout (line 170); test_attachment_rules_raise_priority_but_never_lower_it (line 186)

- [backend/tests/test_eval_runner.py](../../backend/tests/test_eval_runner.py): test_case_files_declare_every_field_the_runner_reads (line 18); test_report_shape_is_stable_for_an_empty_run (line 27); test_golden_set_meets_minimum_thresholds (line 35); test_guardrail_probes_route_as_expected (line 43)

- [backend/tests/test_inference_space.py](../../backend/tests/test_inference_space.py): sse (line 20); FakeResponse (line 25); FakeClient (line 39); test_remote_space_prediction (line 57); test_fraud_words_raise_the_model_priority_to_critical (line 74); test_unexpected_space_labels_fall_back_to_rules (line 84); test_remote_space_failure_routes_to_manual_review (line 99); test_slow_remote_inference_does_not_block_ticket_submission (line 114)

- [backend/tests/test_policies.py](../../backend/tests/test_policies.py): test_status_transition_rules (line 6); test_manual_review_rules (line 11); test_language_detection_and_safe_templates (line 26)

- [backend/tests/test_queue_urgency.py](../../backend/tests/test_queue_urgency.py): prediction (line 15); ticket (line 20); test_log_pool_marginalizes_full_intent_and_matches_paper_formula (line 32); test_old_low_can_overtake_fresh_medium_even_with_zero_raw_severity (line 51); test_continuous_posterior_distinguishes_same_priority_label (line 61); test_manual_priority_review_bypasses_conflicting_model_distribution (line 67); test_completed_tickets_stop_competing_for_dispatch (line 77); test_critical_override_future_dates_and_naive_utc (line 87); test_equal_scores_use_oldest_then_id (line 97); test_full_space_probabilities_are_retained_but_truncated_values_are_not_fabricated (line 106); test_urgency_ranks_all_tickets_before_pagination_and_preserves_customer_scope (line 125); test_new_ticket_persists_distributions_and_staff_review_recalculates (line 153)

- [backend/tests/test_rag.py](../../backend/tests/test_rag.py): evidence (line 31); test_safety_router_escalates (line 59); test_safety_router_allows_routine_information (line 66); test_safety_router_allows_guidance_regardless_of_classification (line 85); test_rrf_deduplicates_and_rewards_shared_results (line 94); test_lexical_query_uses_bound_or_terms_and_keeps_unicode (line 104); test_flashrank_adapter_supplies_required_token_type_ids (line 111); test_flashrank_does_not_invoke_model_for_empty_candidates (line 126); test_confidence_uses_evidence_quality (line 131); test_confidence_has_no_zero_to_epsilon_discontinuity (line 139); test_safety_intent_is_language_independent (line 146); test_safety_router_escalates_native_unauthorized_transaction (line 160); test_citations_preserve_source_metadata (line 166); test_citation_layout_normalizer_repeats_only_a_model_selected_marker (line 187); test_multilingual_detection_and_normalization (line 202); FakeRetriever (line 210); FakeLLM (line 220); CitationRepairLLM (line 228); test_low_confidence_refuses_without_calling_generation (line 244); test_grounded_result_is_direct_customer_assistance (line 254); test_invalid_citation_layout_gets_one_grounded_repair_attempt (line 265); test_follow_up_retrieval_includes_original_ticket_context (line 276); test_retrieval_metrics (line 289); test_ndcg_stays_bounded_when_chunks_repeat_a_source (line 295); EmptyRows (line 310); CapturingDB (line 318); FakeEmbedder (line 327); FailingEmbedder (line 332); FakeReranker (line 337); test_institution_filter_is_passed_to_every_retrieval_channel (line 343); test_embedding_failure_falls_back_to_lexical_retrieval (line 353); test_unknown_category_retries_all_retrieval_without_filter (line 364); test_lexical_query_matches_any_meaningful_word (line 379); test_lexical_query_keeps_sinhala_words_whole (line 386); test_lexical_query_strips_websearch_operators (line 391); test_lexical_retrieval_uses_any_word_query (line 396); FakeHFResponse (line 406); FakeHFClient (line 414); test_huggingface_embedder_flattens_and_validates_vector (line 428); test_hosted_embedder_requires_token (line 436); FakeOllamaResponse (line 443); FakeOllamaClient (line 454); test_ollama_embedding_and_generation_adapters (line 472); test_guardrails_escalate_on_adversarial_input (line 494); test_guardrails_allow_ordinary_banking_questions (line 507); test_injection_never_reaches_retrieval (line 513); groq_response (line 525); FakeProviderClient (line 534); no_sleep (line 550); test_provider_retries_rate_limit_then_succeeds (line 561); test_provider_does_not_retry_client_errors (line 573); test_provider_fails_over_rather_than_waiting_out_a_long_retry_after (line 585)

- [backend/tests/test_rag_api.py](../../backend/tests/test_rag_api.py): test_customer_assistance_uses_owned_ticket_context (line 13); test_staff_cannot_call_customer_ticket_assistance (line 59); test_follow_up_assistance_preserves_the_ticket_language (line 72)

- [backend/tests/test_ticket_status.py](../../backend/tests/test_ticket_status.py): Status transitions for assignment and escalation, and what their responses report. close_ticket (line 11); test_a_closed_ticket_cannot_be_reassigned (line 20); test_a_closed_ticket_cannot_be_escalated (line 31); test_an_open_ticket_can_still_be_escalated (line 44); test_assignment_response_names_the_assigned_agent (line 56); test_escalation_response_names_the_new_queue (line 68); test_agent_picker_lists_staff_only (line 86); test_response_approval_and_send_record_activity (line 94); test_undo_escalation_returns_to_support_and_preserves_agent (line 108); test_undo_unassigned_escalation_returns_to_review (line 130); test_undo_resolution_reopens_and_retains_history (line 140); test_undo_is_staff_only_and_does_not_reopen_closed_tickets (line 155)

## datasets/localization

- [datasets/localization/localize.py](../../datasets/localization/localize.py): sub_all (line 14); amount_x1000 (line 20); extra_charge (line 24); cash_wrong_amount (line 51); cash_not_recognised (line 57); receiving_money (line 63); exchange_via_app (line 70); card_payment_wrong_exchange (line 84); wrong_rate_cash_withdrawal (line 98); balance_not_updated (line 105); transfer_not_received (line 121); country_support (line 128); transfer_timing (line 143); top_up_card_charge (line 152)

## datasets/translation

- [datasets/translation/append_sinhala.py](../../datasets/translation/append_sinhala.py): Append hand-authored colloquial Sinhala translations to main (line 24)

- [datasets/translation/append_sinhala_test.py](../../datasets/translation/append_sinhala_test.py): Append hand-authored colloquial Sinhala translations to main (line 25)

- [datasets/translation/apply_bulk_sentiment_fix.py](../../datasets/translation/apply_bulk_sentiment_fix.py): Apply the high-confidence Positive->Neutral bulk fix (sentiment_bulk_fix_candidates.csv) load_fix_indices (line 19); main (line 24)

- [datasets/translation/audit_sentiment.py](../../datasets/translation/audit_sentiment.py): Module constants, imports or package initializer.

- [datasets/translation/audit_tamilish.py](../../datasets/translation/audit_tamilish.py): Tamilish Dataset Audit Script tokenize (line 118); is_english_word (line 123); compute_cmi (line 182); detect_formal_verbs (line 207); detect_tamil_nouns (line 219); detect_formal_pronouns (line 230); detect_formal_polite (line 241); detect_formal_compounds (line 247); classify_register (line 253); audit_row (line 276); audit_file (line 322); generate_report (line 348); main (line 470)

- [datasets/translation/clean_tamilish_script.py](../../datasets/translation/clean_tamilish_script.py): datasets/translation/clean_tamilish_script.py clean_text (line 86); process_file (line 105); main (line 116)

- [datasets/translation/fix_tamil_english.py](../../datasets/translation/fix_tamil_english.py): Remove English (Latin-script) words from the native-Tamil `text` column of _compile (line 322); fix (line 339); main (line 346)

- [datasets/translation/fix_tamilish.py](../../datasets/translation/fix_tamilish.py): Fix and standardize Tamilish (Tanglish) datasets per TAMIL_STYLE.md rules. standardize_text (line 145); fix_file (line 160); main (line 180)

- [datasets/translation/generate_gold_benchmark.py](../../datasets/translation/generate_gold_benchmark.py): Generate and validate a representative Tanglish sample set (50 gold benchmark rows), select_gold_50 (line 26); generate_cmi_analysis (line 87); generate_quality_summary (line 117); main (line 166)

- [datasets/translation/generate_singlish.py](../../datasets/translation/generate_singlish.py): Generate the Singlish (romanized Sinhala) dataset from main (line 27)

- [datasets/translation/generate_singlish_test.py](../../datasets/translation/generate_singlish_test.py): Generate the Singlish (romanized Sinhala) TEST dataset from main (line 26)

- [datasets/translation/gg_translate_generate.py](../../datasets/translation/gg_translate_generate.py): Trilingual + romanized translation pipeline for the Swift banking-ticket read_english (line 67); out_path (line 73); rows_done (line 77); translate_retry (line 86); build (line 105); pick_diverse (line 176); main (line 196)

- [datasets/translation/hybrid_sentiment_baseline.py](../../datasets/translation/hybrid_sentiment_baseline.py): Hybrid sentiment/priority baseline: VADER (lexicon model) + domain rule-based score_text (line 71); compute_category_mode_priority (line 126); main (line 134)

- [datasets/translation/relabel_sentiment_v6.py](../../datasets/translation/relabel_sentiment_v6.py): Re-label sentiment across the corpus with the v6 prompt. call_claude (line 46); batch_prompt (line 63); stage (line 76); apply (line 133); main (line 170)

- [datasets/translation/relabel_sentiment_v8.py](../../datasets/translation/relabel_sentiment_v8.py): Re-label sentiment across the corpus with the v8 prompt. looks_rate_limited (line 66); call_claude (line 79); call_claude_patient (line 110); batch_prompt (line 126); _load_english (line 139); stage (line 148); apply (line 216); main (line 259)

- [datasets/translation/romanize.py](../../datasets/translation/romanize.py): Romanization module: Sinhala -> Singlish, Tamil -> Tamilish. romanize (line 29)

- [datasets/translation/run_prompt_eval.py](../../datasets/translation/run_prompt_eval.py): Score a labeling prompt against the human-annotated gold set. contract (line 82); load_gold (line 86); split_gold (line 97); call_claude (line 107); build_batch_prompt (line 124); label (line 143); topic_auc (line 171); score (line 191); main (line 221)

- [datasets/translation/singlish_diff.py](../../datasets/translation/singlish_diff.py): Find rows where the hand-edited `singlish/train_labeled.csv` main (line 29)

- [datasets/translation/singlish_overrides.py](../../datasets/translation/singlish_overrides.py): Word-level overrides applied on top of the deterministic aksharamukha 

- [datasets/translation/singlishify.py](../../datasets/translation/singlishify.py): Sinhala -> Singlish for a full sentence: word-level override dict first singlishify (line 16)

- [datasets/translation/update_sinhala.py](../../datasets/translation/update_sinhala.py): Apply hand-authored Sinhala corrections (re-worded to match a user's Singlish main (line 26)

## frontend/src

- [frontend/src/app/providers/AuthProvider.tsx](../../frontend/src/app/providers/AuthProvider.tsx): AuthProvider; useAuth

- [frontend/src/app/providers/LanguageProvider.tsx](../../frontend/src/app/providers/LanguageProvider.tsx): UiLanguage; LanguageProvider; useLanguage

- [frontend/src/app/providers/ThemeProvider.tsx](../../frontend/src/app/providers/ThemeProvider.tsx): Theme; ThemeProvider; useTheme

- [frontend/src/app/router/Routes.tsx](../../frontend/src/app/router/Routes.tsx): ProtectedRoute; AppRoutes

- [frontend/src/components/agent/AgentPanels.tsx](../../frontend/src/components/agent/AgentPanels.tsx): ImageEvidencePanel; PredictionCard; InternalNotes; ResponseEditor

- [frontend/src/components/auth/AuthAccountPrompt.tsx](../../frontend/src/components/auth/AuthAccountPrompt.tsx): AuthAccountPrompt

- [frontend/src/components/common/Controls.tsx](../../frontend/src/components/common/Controls.tsx): Logo; ThemeSwitcher; LanguageSelector; SearchInput; ConfirmationDialog

- [frontend/src/components/feedback/ErrorBoundary.tsx](../../frontend/src/components/feedback/ErrorBoundary.tsx): ErrorBoundary

- [frontend/src/components/layout/Layouts.tsx](../../frontend/src/components/layout/Layouts.tsx): ProfileMenu; CustomerLayout; SidebarLink; AgentLayout; AdministratorLayout; PageHeader

- [frontend/src/components/tickets/ImageUploader.tsx](../../frontend/src/components/tickets/ImageUploader.tsx): Result; validateImageFile; ImageUploader

- [frontend/src/components/tickets/TicketComponents.tsx](../../frontend/src/components/tickets/TicketComponents.tsx): humanize; StatusBadge; PriorityBadge; SentimentBadge; UrgencyLabel; LanguageBadge; ConfidenceIndicator; TicketTimeline; TicketFilters; TicketTable; TableLoadingRows; TicketTableSkeleton; TicketCards; Pagination; LoadingSkeleton; LoadingSpinner; EmptyState; ErrorState; ProcessingStepper

- [frontend/src/components/ui/Avatar.tsx](../../frontend/src/components/ui/Avatar.tsx): AvatarProps; Avatar

- [frontend/src/components/ui/Badge.tsx](../../frontend/src/components/ui/Badge.tsx): BadgeTone; BadgeProps; Badge

- [frontend/src/components/ui/Button.tsx](../../frontend/src/components/ui/Button.tsx): ButtonVariant; ButtonSize; ButtonProps; Button; IconButton

- [frontend/src/components/ui/Card.tsx](../../frontend/src/components/ui/Card.tsx): CardProps; Card

- [frontend/src/components/ui/DataTable.tsx](../../frontend/src/components/ui/DataTable.tsx): DataTableColumn; DataTableProps; DataTable

- [frontend/src/components/ui/Dialog.tsx](../../frontend/src/components/ui/Dialog.tsx): DialogProps; Dialog

- [frontend/src/components/ui/Input.tsx](../../frontend/src/components/ui/Input.tsx): InputProps; Input

- [frontend/src/components/ui/KpiStat.tsx](../../frontend/src/components/ui/KpiStat.tsx): KpiStatProps; KpiStat

- [frontend/src/components/ui/PriorityQueueRow.tsx](../../frontend/src/components/ui/PriorityQueueRow.tsx): QueuePriority; PriorityQueueRowProps; PriorityQueueRow

- [frontend/src/components/ui/Select.tsx](../../frontend/src/components/ui/Select.tsx): SelectOption; SelectProps; Select

- [frontend/src/components/ui/Tabs.tsx](../../frontend/src/components/ui/Tabs.tsx): TabItem; TabsProps; Tabs

- [frontend/src/components/ui/Tooltip.tsx](../../frontend/src/components/ui/Tooltip.tsx): TooltipProps; Tooltip

- [frontend/src/components/ui/TopNav.tsx](../../frontend/src/components/ui/TopNav.tsx): TopNavItem; TopNavProps; TopNav

- [frontend/src/lib/agentPreferences.ts](../../frontend/src/lib/agentPreferences.ts): AgentPreferences; AGENT_PREFERENCES_KEY; DEFAULT_AGENT_PREFERENCES; loadAgentPreferences

- [frontend/src/lib/config.ts](../../frontend/src/lib/config.ts): getApiBaseUrl; getAppName

- [frontend/src/lib/constants.ts](../../frontend/src/lib/constants.ts): TICKET_STATUSES; TICKET_PRIORITIES; TICKET_SENTIMENTS; SUPPORTED_LANGUAGES; TICKET_CATEGORIES; EMPTY_FILTERS

- [frontend/src/lib/ticketActions.ts](../../frontend/src/lib/ticketActions.ts): canChangeTicketStatus; canAssignTicket

- [frontend/src/lib/utils.ts](../../frontend/src/lib/utils.ts): cn; confidenceBand; formatDate; filterTickets; TicketSort; urgencyScore; isTicketSort; sortTickets; delay

- [frontend/src/main.tsx](../../frontend/src/main.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/pages/admin/AdminDashboardPage.tsx](../../frontend/src/pages/admin/AdminDashboardPage.tsx): AdminDashboardPage

- [frontend/src/pages/admin/AdminManagementPages.tsx](../../frontend/src/pages/admin/AdminManagementPages.tsx): AdminUsersPage; AdminQueuesPage; AdminAuditPage; AdminSettingsPage

- [frontend/src/pages/agent/AgentDashboardPage.tsx](../../frontend/src/pages/agent/AgentDashboardPage.tsx): AgentDashboardPage

- [frontend/src/pages/agent/AgentQueuePage.tsx](../../frontend/src/pages/agent/AgentQueuePage.tsx): AgentQueuePage

- [frontend/src/pages/agent/AgentReportsPage.tsx](../../frontend/src/pages/agent/AgentReportsPage.tsx): Period; AgentReportsPage

- [frontend/src/pages/agent/AgentSettingsPage.tsx](../../frontend/src/pages/agent/AgentSettingsPage.tsx): AgentSettingsPage

- [frontend/src/pages/agent/AgentTicketDetailPage.tsx](../../frontend/src/pages/agent/AgentTicketDetailPage.tsx): AgentTicketDetailPage

- [frontend/src/pages/customer/CustomerTicketDetailPage.tsx](../../frontend/src/pages/customer/CustomerTicketDetailPage.tsx): assistanceFallback; CustomerTicketDetailPage

- [frontend/src/pages/customer/CustomerTicketsPage.tsx](../../frontend/src/pages/customer/CustomerTicketsPage.tsx): TimeFilter; CustomerTicketGallery; CustomerTicketsPage

- [frontend/src/pages/customer/SubmitTicketPage.tsx](../../frontend/src/pages/customer/SubmitTicketPage.tsx): Data; SubmitTicketPage

- [frontend/src/pages/LoginPage.tsx](../../frontend/src/pages/LoginPage.tsx): FormData; LoginPage

- [frontend/src/pages/RegisterPage.tsx](../../frontend/src/pages/RegisterPage.tsx): FormData; RegisterPage

- [frontend/src/pages/UtilityPages.tsx](../../frontend/src/pages/UtilityPages.tsx): PlaceholderPage; NotFoundPage

- [frontend/src/services/restTicketService.ts](../../frontend/src/services/restTicketService.ts): ApiPrediction; ApiResponse; ApiTicket; request; mapTicket; restTicketService

- [frontend/src/services/serviceSelector.ts](../../frontend/src/services/serviceSelector.ts): ticketService

- [frontend/src/services/ticketService.ts](../../frontend/src/services/ticketService.ts): AdjacentTickets; TicketService

- [frontend/src/test/auth.test.tsx](../../frontend/src/test/auth.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/config.test.ts](../../frontend/src/test/config.test.ts): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/processing.test.tsx](../../frontend/src/test/processing.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/queuePage.test.tsx](../../frontend/src/test/queuePage.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/queueUrgency.test.ts](../../frontend/src/test/queueUrgency.test.ts): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/setup.ts](../../frontend/src/test/setup.ts): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/theme.test.tsx](../../frontend/src/test/theme.test.tsx): Probe; Switch

- [frontend/src/test/ticketActions.test.ts](../../frontend/src/test/ticketActions.test.ts): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ticketCommands.test.tsx](../../frontend/src/test/ticketCommands.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Avatar.test.tsx](../../frontend/src/test/ui/Avatar.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Badge.test.tsx](../../frontend/src/test/ui/Badge.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Button.test.tsx](../../frontend/src/test/ui/Button.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Card.test.tsx](../../frontend/src/test/ui/Card.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/DataTable.test.tsx](../../frontend/src/test/ui/DataTable.test.tsx): Row

- [frontend/src/test/ui/Dialog.test.tsx](../../frontend/src/test/ui/Dialog.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Input.test.tsx](../../frontend/src/test/ui/Input.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/KpiStat.test.tsx](../../frontend/src/test/ui/KpiStat.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/PriorityQueueRow.test.tsx](../../frontend/src/test/ui/PriorityQueueRow.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Select.test.tsx](../../frontend/src/test/ui/Select.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Tabs.test.tsx](../../frontend/src/test/ui/Tabs.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/Tooltip.test.tsx](../../frontend/src/test/ui/Tooltip.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/ui/TopNav.test.tsx](../../frontend/src/test/ui/TopNav.test.tsx): React/TypeScript module; inspect exports and handlers.

- [frontend/src/test/upload.test.ts](../../frontend/src/test/upload.test.ts): React/TypeScript module; inspect exports and handlers.

- [frontend/src/types/env.d.ts](../../frontend/src/types/env.d.ts): ImportMetaEnv; ImportMeta; Window

- [frontend/src/types/index.ts](../../frontend/src/types/index.ts): UserRole; SupportedLanguage; TicketPriority; TicketSentiment; TicketStatus; ConfidenceBand; User; Customer; Agent; TicketPrediction; PredictionCorrection; Attachment; ImageEvidence; TicketEvent; InternalNote; ResponseDraft; ApprovedResponse; Ticket; DashboardMetrics; AdminDashboardMetrics; AdminUserRecord; AdminQueue; AdminAudit; AdminSetting; TicketSubmission; RagCitation; RagAssistanceResult; FilterState

## ml/kaggle

- [ml/kaggle/.stage/ml/swiftbench/__init__.py](../../ml/kaggle/.stage/ml/swiftbench/__init__.py): swiftbench — the shared harness for the Swift classifier bake-off. __getattr__ (line 44)

- [ml/kaggle/.stage/ml/swiftbench/baselines.py](../../ml/kaggle/.stage/ml/swiftbench/baselines.py): Model-free floors. majority (line 22); build_intent_lookup (line 32); intent_lookup (line 44); intent_chained (line 58)

- [ml/kaggle/.stage/ml/swiftbench/config.py](../../ml/kaggle/.stage/ml/swiftbench/config.py): Frozen shared state for the bake-off. 

- [ml/kaggle/.stage/ml/swiftbench/data.py](../../ml/kaggle/.stage/ml/swiftbench/data.py): Loading the five language folders under one schema. load_language (line 18); load_languages (line 42); label_column (line 49); xy (line 59); check_alignment (line 64)

- [ml/kaggle/.stage/ml/swiftbench/imbalance.py](../../ml/kaggle/.stage/ml/swiftbench/imbalance.py): Class-balancing arms. class_weight_for (line 22); resample (line 27)

- [ml/kaggle/.stage/ml/swiftbench/metrics.py](../../ml/kaggle/.stage/ml/swiftbench/metrics.py): Task-aware scoring. score (line 39); per_class_table (line 83); confusion (line 89)

- [ml/kaggle/.stage/ml/swiftbench/models.py](../../ml/kaggle/.stage/ml/swiftbench/models.py): Estimator factory. feature_union (line 31); build (line 56)

- [ml/kaggle/.stage/ml/swiftbench/probe.py](../../ml/kaggle/.stage/ml/swiftbench/probe.py): Linear probing: how much task signal is in a backbone *before* fine-tuning. poolings_for (line 78); resolve (line 130); probe_name (line 147); _cache_path (line 162); _pool (line 166); embed (line 189); features (line 269); _normalise (line 302); ProbeFit (line 324); fit (line 342); score (line 441); run (line 481); sweep (line 496); sweep_C (line 526); deltas (line 547)

- [ml/kaggle/.stage/ml/swiftbench/results.py](../../ml/kaggle/.stage/ml/swiftbench/results.py): One JSON per run, filename derived from run identity. _slug (line 25); run_id (line 31); save (line 37); load_all (line 67); leaderboard (line 91)

- [ml/kaggle/.stage/ml/swiftbench/splits.py](../../ml/kaggle/.stage/ml/swiftbench/splits.py): The frozen train/dev/test split. _sha (line 28); build (line 34); ensure (line 69); sha (line 80); get (line 84)

- [ml/kaggle/.stage/ml/swiftbench/tokenize.py](../../ml/kaggle/.stage/ml/swiftbench/tokenize.py): Word tokenization that does not destroy Sinhala and Tamil. script_of (line 50); tokenize (line 59); char_preservation (line 73)

- [ml/kaggle/.stage/ml/swiftbench/train_classical.py](../../ml/kaggle/.stage/ml/swiftbench/train_classical.py): One classical run: fit on train, score on dev, record the result. run (line 14); sweep (line 49); sweep_regimes (line 85)

- [ml/kaggle/.stage/ml/swiftbench/train_encoder.py](../../ml/kaggle/.stage/ml/swiftbench/train_encoder.py): One encoder fine-tuning run: fit, score, record -- the mirror of `train_classical`. device (line 76); EncoderRun (line 87); _encode (line 99); _batches (line 103); run (line 109); _infer (line 420)

- [ml/kaggle/.stage/ml/swiftbench/tuning.py](../../ml/kaggle/.stage/ml/swiftbench/tuning.py): Statistical rigour: confidence intervals, thresholds, cross-validation. bootstrap_ci (line 34); tune_threshold (line 77); _positive_scores (line 124); cross_validate (line 144); summarise_cv (line 198)

- [ml/kaggle/kernels/multitask.py](../../ml/kaggle/kernels/multitask.py): Kernel body: joint multi-task Gemma-3 fine-tuning (`swiftbench.train_multitask`). find_payload (line 28); find_swiftbench (line 50)

- [ml/kaggle/kernels/multitask_b.py](../../ml/kaggle/kernels/multitask_b.py): Kernel body: joint multi-task Gemma-3 fine-tuning (`swiftbench.train_multitask`). find_payload (line 28); find_swiftbench (line 50)

- [ml/kaggle/kernels/perlang.py](../../ml/kaggle/kernels/perlang.py): Kernel body: fine-tune the encoder roster on Kaggle's T4s. find_payload (line 28); find_swiftbench (line 60); record (line 129)

- [ml/kaggle/kernels/perlang_lora.py](../../ml/kaggle/kernels/perlang_lora.py): Kernel body: fine-tune the encoder roster on Kaggle's T4s. find_payload (line 28); find_swiftbench (line 60); record (line 133)

- [ml/kaggle/kernels/train_encoders.py](../../ml/kaggle/kernels/train_encoders.py): Kernel body: fine-tune the encoder roster on Kaggle's T4s. find_payload (line 28); find_swiftbench (line 60)

- [ml/kaggle/kernels/train_encoders_b.py](../../ml/kaggle/kernels/train_encoders_b.py): Kernel body: fine-tune the encoder roster on Kaggle's T4s. find_payload (line 28); find_swiftbench (line 60)

- [ml/kaggle/runner.py](../../ml/kaggle/runner.py): Run Swift training on Kaggle's T4 GPUs from inside this project. sh (line 50); username (line 61); slug (line 93); doctor (line 98); stage_payload (line 132); sync (line 191); write_kernel (line 207); run (line 268); status (line 295); label_names (line 308); stamp_labels (line 318); fetch (line 344); logs (line 436); main (line 445)

## ml/OCR

- [ml/OCR/analyze_ocr_results.py](../../ml/OCR/analyze_ocr_results.py): main (line 6)

- [ml/OCR/build_custom_dictionary.py](../../ml/OCR/build_custom_dictionary.py): build_dictionary (line 11)

- [ml/OCR/compare_ocr_engines.py](../../ml/OCR/compare_ocr_engines.py): Put two OCR metric files side by side and say which engine wins where. load (line 19); summarize (line 26); main (line 46)

- [ml/OCR/evaluate_google_vision.py](../../ml/OCR/evaluate_google_vision.py): Evaluate Google Cloud Vision on the same 2,000-image benchmark as Tesseract. get_language_hints (line 32); load_api_key (line 43); select_rows (line 58); score (line 81); build_request (line 93); read_annotation (line 102); run_batch (line 109); evaluate (line 139); parse_args (line 185)

- [ml/OCR/evaluate_ocr.py](../../ml/OCR/evaluate_ocr.py): main (line 12)

- [ml/OCR/evaluate_tesseract.py](../../ml/OCR/evaluate_tesseract.py): get_tesseract_lang (line 9); main (line 20)

- [ml/OCR/install_tesseract.py](../../ml/OCR/install_tesseract.py): install_tesseract (line 6)

- [ml/OCR/measure_end_to_end_intent.py](../../ml/OCR/measure_end_to_end_intent.py): main (line 10)

- [ml/OCR/measure_end_to_end_ocr.py](../../ml/OCR/measure_end_to_end_ocr.py): Measure what each OCR engine costs the intent router, engine against engine. load_engine_frames (line 32); score (line 53); report (line 60); main (line 85)

- [ml/OCR/measure_intent_accuracy.py](../../ml/OCR/measure_intent_accuracy.py): Intent accuracy against the TRUE label, per router and per OCR engine. load_true_categories (line 70); load_frame (line 77); is_correct (line 95); accuracy (line 99); main (line 105)

- [ml/OCR/prepare_ocr_dataset.py](../../ml/OCR/prepare_ocr_dataset.py): main (line 7)

## ml/scripts

- [ml/scripts/calibrate_svm_confidence.py](../../ml/scripts/calibrate_svm_confidence.py): Fit a confidence calibration for the production TF-IDF SVM intent router. load_test (line 39); features (line 56); ece (line 61); main (line 71)

- [ml/scripts/compare_tokenizers.py](../../ml/scripts/compare_tokenizers.py): Tokenizer Comparison & Sequence Length Analysis for Trilingual Banking Support Ticket Dataset. load_data (line 43); sample_dataset (line 77); evaluate_tokenizers (line 107); generate_markdown_report (line 214); main (line 282)

- [ml/scripts/probe_slm_tokenizers.py](../../ml/scripts/probe_slm_tokenizers.py): Tokenizer-fertility screen for the SLM candidates in `ml/reports/SLM_RESEARCH.md` §5. char_preservation (line 67); mark_preservation (line 91); zwj_survives (line 110); main (line 121)

- [ml/scripts/run_all_baselines.py](../../ml/scripts/run_all_baselines.py): Run Complete Classical ML Baseline Experiment Matrix (12 runs): main (line 32)

- [ml/scripts/run_v8_classical.py](../../ml/scripts/run_v8_classical.py): Classical baselines re-run against the v8 sentiment labels, frozen split. bootstrap_ci (line 53); fit_and_score (line 85); main (line 158)

- [ml/scripts/train_baseline.py](../../ml/scripts/train_baseline.py): Train & Evaluate Classical ML Baselines (TF-IDF Word + Character n-grams) load_dataset (line 47); build_pipeline (line 105); evaluate_pipeline (line 156); main (line 182)

- [ml/scripts/train_transformer.py](../../ml/scripts/train_transformer.py): ml/scripts/train_transformer.py load_and_prepare_dataset (line 48); compute_metrics (line 107); save_environment_info (line 127); main (line 144)

- [ml/scripts/validate_baseline_suite.py](../../ml/scripts/validate_baseline_suite.py): validate_baseline_suite.py — Complete 15-Section Validation & Finalization Suite get_dataset_dir (line 69); load_all_data (line 73); validate_schema (line 108); check_leakage (line 169); check_test_consistency (line 205); build_feature_union (line 237); train_and_evaluate_all (line 257); evaluate_combined_by_language (line 402); analyze_tamilish_errors (line 459); run_feature_ablation (line 509); validate_hyperparameters (line 567); compute_bootstrap_cis (line 618); validate_saved_models (line 669); calculate_promotion_thresholds (line 704); generate_final_report (line 733); main (line 855)

## ml/swiftbench

- [ml/swiftbench/__init__.py](../../ml/swiftbench/__init__.py): swiftbench — the shared harness for the Swift classifier bake-off. __getattr__ (line 46)

- [ml/swiftbench/baselines.py](../../ml/swiftbench/baselines.py): Model-free floors. majority (line 22); build_intent_lookup (line 32); intent_lookup (line 44); intent_chained (line 58)

- [ml/swiftbench/config.py](../../ml/swiftbench/config.py): Frozen shared state for the bake-off. 

- [ml/swiftbench/data.py](../../ml/swiftbench/data.py): Loading the five language folders under one schema. load_language (line 18); load_languages (line 42); label_column (line 49); xy (line 59); check_alignment (line 64)

- [ml/swiftbench/imbalance.py](../../ml/swiftbench/imbalance.py): Class-balancing arms. class_weight_for (line 22); resample (line 27)

- [ml/swiftbench/metrics.py](../../ml/swiftbench/metrics.py): Task-aware scoring. score (line 39); per_class_table (line 83); confusion (line 89)

- [ml/swiftbench/models.py](../../ml/swiftbench/models.py): Estimator factory. feature_union (line 51); build (line 76)

- [ml/swiftbench/probe.py](../../ml/swiftbench/probe.py): Linear probing: how much task signal is in a backbone *before* fine-tuning. poolings_for (line 78); resolve (line 130); probe_name (line 147); _cache_path (line 162); _pool (line 166); embed (line 189); features (line 269); _normalise (line 302); ProbeFit (line 324); fit (line 342); score (line 441); run (line 481); sweep (line 496); sweep_C (line 526); deltas (line 547)

- [ml/swiftbench/results.py](../../ml/swiftbench/results.py): One JSON per run, filename derived from run identity. _slug (line 25); run_id (line 31); save (line 37); save_predictions (line 79); load_predictions (line 101); load_all (line 110); leaderboard (line 134)

- [ml/swiftbench/splits.py](../../ml/swiftbench/splits.py): The frozen train/dev/test split. _sha (line 28); build (line 34); ensure (line 69); sha (line 80); get (line 84)

- [ml/swiftbench/tokenize.py](../../ml/swiftbench/tokenize.py): Word tokenization that does not destroy Sinhala and Tamil. script_of (line 50); tokenize (line 59); char_preservation (line 73)

- [ml/swiftbench/train_classical.py](../../ml/swiftbench/train_classical.py): One classical run: fit on train, score on dev, record the result. run (line 14); sweep (line 49); sweep_regimes (line 85)

- [ml/swiftbench/train_encoder.py](../../ml/swiftbench/train_encoder.py): One encoder fine-tuning run: fit, score, record -- the mirror of `train_classical`. device (line 94); EncoderRun (line 105); _encode (line 121); _batches (line 125); run (line 131); _infer (line 509)

- [ml/swiftbench/train_multitask.py](../../ml/swiftbench/train_multitask.py): Joint multi-task fine-tuning: one Gemma-3 backbone serving intent, sentiment, and priority. _task_labels (line 51); _class_weight (line 59); _pool_last_token (line 66); _lora_backbone (line 83); MultiTaskRun (line 109); run_shared_heads (line 119); _coerce_to_task_vocabulary (line 339); _prefixed_frame (line 360); run_shared_head (line 375)

- [ml/swiftbench/tuning.py](../../ml/swiftbench/tuning.py): Statistical rigour: confidence intervals, thresholds, cross-validation. bootstrap_ci (line 34); tune_threshold (line 77); _positive_scores (line 124); cross_validate (line 144); summarise_cv (line 198)

## notebooks/baselines

- [notebooks/baselines/Baseline_Experiments.ipynb](../../notebooks/baselines/Baseline_Experiments.ipynb): Day 3 Lab: Tokenizer Comparison & Classical Machine-Learning Baselines; Overview of Day 3 Objectives:; 1. Tokenizer Comparison & `max_length` Recommendation; Key Tokenizer Takeaways:; 2. Interactive Tokenizer Fragmentation Demo

## notebooks/data_preparation

- [notebooks/data_preparation/clean_common.py](../../notebooks/data_preparation/clean_common.py): Shared helpers for the data-cleaning fix scripts (fix_labeling / dedup_reword / path (line 30); load_rows (line 34); save_rows (line 39); existing_splits (line 46); apply_label_updates (line 50); apply_source_text_updates (line 76); call_claude (line 96); run_batches (line 115); v5_prompt (line 123); delete_report (line 127)

- [notebooks/data_preparation/data_cleaning.ipynb](../../notebooks/data_preparation/data_cleaning.ipynb): Data Cleaning & Quality Audit — Trilingual BANKING77 Bake-off; Issue summary; 1. Conflicting-label duplicates  ⚠️ main concern; 2. Train / test leakage; 3. Untranslated rows

- [notebooks/data_preparation/data_cleaning.py](../../notebooks/data_preparation/data_cleaning.py): Data-quality audit for the trilingual BANKING77 classifier bake-off. path (line 52); load (line 56); get_label_mismatches (line 70); get_untranslated (line 89); get_conflicting_duplicates (line 104); get_exact_duplicates (line 131); get_leakage (line 145); header (line 163); write_csv (line 167); report (line 176); main (line 264)

- [notebooks/data_preparation/dataset_characteristics_english.ipynb](../../notebooks/data_preparation/dataset_characteristics_english.ipynb): Dataset Characteristics — English Train Split; 1. Schema and integrity; Duplicates; Label hygiene; 2. Text characteristics

- [notebooks/data_preparation/dedup_banking77.ipynb](../../notebooks/data_preparation/dedup_banking77.ipynb): STEP 2 — Duplicate Resolution: BANKING77 Source vs. Translation Collapse; 0. Proof of the `id` <-> original-dataset correspondence; 1. Action A — True BANKING77 duplicates; Apply — drop the redundant ids (keep lowest id per group), all five languages; 2. Action B — Translation collapses

- [notebooks/data_preparation/dedup_common.py](../../notebooks/data_preparation/dedup_common.py): Shared helpers for `dedup_banking77.ipynb` (STEP 2 — within-split duplicate load_original (line 35); verify_id_alignment (line 40); true_duplicate_groups (line 49); true_dup_drop_ids (line 64); collapse_groups (line 73); apply_true_dup_removal (line 96); build_reword_prompt (line 146); reword_groups (line 154); apply_reword_results (line 164)

- [notebooks/data_preparation/fix_labeling.py](../../notebooks/data_preparation/fix_labeling.py): STEP 1 — Fix conflicting sentiment/priority labels (LLM). same_category_conflict_groups (line 28); build_prompt (line 47); main (line 60)

- [notebooks/data_preparation/prompt_benchmark_findings.ipynb](../../notebooks/data_preparation/prompt_benchmark_findings.ipynb): Prompt Iteration Findings — Sentiment & Priority Labeling; Accuracy by version; Root cause of the priority gap: category-tier miscalibration; Sentiment: the "charged twice" conflict; Full-dataset re-classification

## notebooks/modeling

- [notebooks/modeling/00_setup_checks.ipynb](../../notebooks/modeling/00_setup_checks.ipynb): 00 — Setup checks; Schema and id-alignment; Split integrity; Label distributions

- [notebooks/modeling/01_run_sentiment.ipynb](../../notebooks/modeling/01_run_sentiment.ipynb): Sentiment — baselines on dev; 1. The floor: always answer "Neutral"; 2. TF-IDF × class-balancing arms; 3. Results; The accuracy trap, plotted

- [notebooks/modeling/02_run_priority.ipynb](../../notebooks/modeling/02_run_priority.ipynb): Priority — baselines on dev; 1. Floors — majority, oracle, and the honest chained bar; Oracle vs chained; 2. Direct text → priority, TF-IDF × arms; 3. Results — does direct beat chained?

- [notebooks/modeling/03_benchmark_sentiment.ipynb](../../notebooks/modeling/03_benchmark_sentiment.ipynb): Sentiment — full bake-off; The three training regimes; 1. Model-free floors; 2. The sweep; 3. Which regime wins?

- [notebooks/modeling/04_benchmark_priority.ipynb](../../notebooks/modeling/04_benchmark_priority.ipynb): Priority — full bake-off; The three training regimes; 1. Model-free floors; 2. The sweep; 3. Which regime wins?

- [notebooks/modeling/05_label_ceiling.ipynb](../../notebooks/modeling/05_label_ceiling.ipynb): The label ceiling — what are we actually measuring against?; 1. Agreement between v5 and the human annotator; Where v5 and the human disagree on sentiment; 2. The ceiling against measured model performance; 3. What this means

- [notebooks/modeling/06_improve_sentiment.ipynb](../../notebooks/modeling/06_improve_sentiment.ipynb): Sentiment — fixing the methodology; 1. How much evidence is actually in dev?; The bake-off champion, with an error bar; 2. Cross-validation — a tighter estimate; 3. Threshold tuning — the cheapest win available

- [notebooks/modeling/07_encoder_bakeoff.ipynb](../../notebooks/modeling/07_encoder_bakeoff.ipynb): Encoder bake-off — the candidates from `model-research.md` §4; 1. Tokenizer fertility — the cheap screen; `[UNK]` rate — the disqualifier; Verdict from the cheap screen; 2. Fine-tuning screen

- [notebooks/modeling/08_word_tokenizer_comparison.ipynb](../../notebooks/modeling/08_word_tokenizer_comparison.ipynb): 08 — Word tokenizer comparison; The defect; Three candidates; 1. What each one does to a real ticket; 2. Character preservation

- [notebooks/modeling/10_final_test_eval.ipynb](../../notebooks/modeling/10_final_test_eval.ipynb): 10 — Final test evaluation: sentiment & priority; 1. Integrity — is test clean?; 2. The evaluation; 3. Why test is lower than dev; 4. Decision threshold

- [notebooks/modeling/11_encoder_xlmr_base.ipynb](../../notebooks/modeling/11_encoder_xlmr_base.ipynb): 11 — XLM-R base; Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/12_encoder_mmbert.ipynb](../../notebooks/modeling/12_encoder_mmbert.ipynb): 12 — mmBERT base; Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/13_encoder_labse.ipynb](../../notebooks/modeling/13_encoder_labse.ipynb): 13 — LaBSE; Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/14_encoder_canine_c.ipynb](../../notebooks/modeling/14_encoder_canine_c.ipynb): 14 — CANINE-c (character-level); Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/15_encoder_sinbert_large.ipynb](../../notebooks/modeling/15_encoder_sinbert_large.ipynb): 15 — SinBERT-large (Sinhala-only); Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/16_encoder_sinhalaberto.ipynb](../../notebooks/modeling/16_encoder_sinhalaberto.ipynb): 16 — SinhalaBERTo (Sinhala-only); Baseline to beat; Fine-tune; Where it fails; Verdict

- [notebooks/modeling/17_encoder_linear_probe.ipynb](../../notebooks/modeling/17_encoder_linear_probe.ipynb): 17 — Linear probing the encoder roster; Two traps this notebook already fell into; Fine-tune numbers to subtract from; Extraction; Does `C = 1.0` cost us anything?

- [notebooks/modeling/20_technique_lexicon_correction.ipynb](../../notebooks/modeling/20_technique_lexicon_correction.ipynb): 20 — Technique: lexicon correction; One honest difference, stated up front; 1. Mine the lexicon; 2. The correction layer; 3. Tune `alpha` and the threshold — inside train only

- [notebooks/modeling/21_technique_strategy_a_transliteration.ipynb](../../notebooks/modeling/21_technique_strategy_a_transliteration.ipynb): 21 — Technique: Strategy A (reverse transliteration); Read this before quoting any number below; 1. The transliterator; 2. Did it actually produce Sinhala?; 3. Strategy A vs Strategy B

- [notebooks/modeling/22_technique_codeswitch_augmentation.ipynb](../../notebooks/modeling/22_technique_codeswitch_augmentation.ipynb): 22 — Technique: code-switch augmentation (Strategy C); 1. The operators; 2. Build the augmented training sets; 3. Does it help?; 4. Verdict

- [notebooks/modeling/23_technique_adapters_unfrozen.ipynb](../../notebooks/modeling/23_technique_adapters_unfrozen.ipynb): 23 — Technique: adapters with an unfrozen backbone; The expectation this notebook is built around; 1. Three arms; 2. Run the arms; 3. Verdict

- [notebooks/modeling/30_leaderboard.ipynb](../../notebooks/modeling/30_leaderboard.ipynb): 30 — Leaderboard: every model and technique; 1. Sentiment — dev; 2. Priority — dev; 3. Techniques; 4. What gets promoted to test

- [notebooks/modeling/32_final_test_classical.ipynb](../../notebooks/modeling/32_final_test_classical.ipynb): 32 — Final test evaluation: classical champions; Reading this

- [notebooks/modeling/33_final_test_encoders.ipynb](../../notebooks/modeling/33_final_test_encoders.ipynb): 33 — Final test evaluation: encoder roster; Reading this honestly

- [notebooks/modeling/34_per_language_findings.ipynb](../../notebooks/modeling/34_per_language_findings.ipynb): 34 — Per-language & specialization findings; 1. Mono vs multi, full fine-tuning; 2. LoRA vs full fine-tuning (LaBSE); 3. Romanized tracks: does a code-mix model help?; Findings

- [notebooks/modeling/35_priority_encoders.ipynb](../../notebooks/modeling/35_priority_encoders.ipynb): 35 — Priority: encoder roster vs classical; 1. Priority — pooled dev (bake-off); 2. Priority — one-shot test (fit train+dev); Finding

- [notebooks/modeling/36_classical_extended.ipynb](../../notebooks/modeling/36_classical_extended.ipynb): 36 — Extended classical baseline roster; Step 1 — arm selection on dev; Step 2 — one-shot test evaluation; Step 3 — the full classical table; Step 4 — why gradient boosting is measured but not tabled

- [notebooks/modeling/99_model_selection.ipynb](../../notebooks/modeling/99_model_selection.ipynb): 99 — Model selection; 1. Everything recorded so far; 2. Champion per task; 3. Headroom — how much is left for an encoder to win?; 4. The fine-tuning decision

## paper/experiments

- [paper/experiments/build_annotation_batches.py](../../paper/experiments/build_annotation_batches.py): Draw the inter-annotator agreement batch, and score it when it comes back. build (line 53); cohen_kappa (line 99); krippendorff_alpha (line 107); score (line 136); main (line 178)

- [paper/experiments/build_figures.py](../../paper/experiments/build_figures.py): Every figure the paper needs, generated from the tables rather than from run records. save (line 46); fig_encoder_gain_by_script (line 54); fig_per_language_sentiment (line 93); fig_ceiling (line 132); fig_tokenizer (line 176); fig_intent_epochs (line 201); fig_queue_disparity (line 260); fig_alpha_frontier (line 312); fig_attainment (line 336); main (line 367)

- [paper/experiments/build_rating_sheets.py](../../paper/experiments/build_rating_sheets.py): Blind rating sheets for the translation comparison, and the scorer for them. collect (line 54); build (line 82); score (line 131); main (line 197)

- [paper/experiments/build_results_tables.py](../../paper/experiments/build_results_tables.py): Generate the paper's results tables from the run records. infer_label_version (line 50); load (line 69); fmt (line 119); main_pooled (line 127); per_language (line 157); balancing_arms (line 180); coverage (line 195); to_markdown (line 216); write (line 242); main (line 254)

- [paper/experiments/build_translation_sample.py](../../paper/experiments/build_translation_sample.py): Draw the shared evaluation sample for the translation-quality comparison. draw (line 86); main (line 113)

- [paper/experiments/calibration.py](../../paper/experiments/calibration.py): Layer 4 -- calibration, per language. ece (line 42); rows_for (line 53); main (line 74); fit_temperature (line 123); apply_temperature (line 139); temperature_study (line 146)

- [paper/experiments/corpus_stats.py](../../paper/experiments/corpus_stats.py): Corpus composition table -- the paper's Table 1. script_fraction (line 66); main (line 82)

- [paper/experiments/dedup_ablation.py](../../paper/experiments/dedup_ablation.py): Does the result survive removing test rows whose text also appears in training? normalise (line 40); overlapping_ids (line 46); main (line 66)

- [paper/experiments/encoder_gain_by_script.py](../../paper/experiments/encoder_gain_by_script.py): Where does the encoder's advantage over classical actually come from? load (line 63); paired_delta (line 98); diff_in_diff (line 131); main (line 179)

- [paper/experiments/english_content_by_track.py](../../paper/experiments/english_content_by_track.py): How much of each track is literally English, measured in words rather than characters. english_vocabulary (line 42); main (line 48)

- [paper/experiments/error_analysis.py](../../paper/experiments/error_analysis.py): Error analysis for the paper's analysis section. find (line 44); with_text (line 49); intent_confusions (line 55); negative_errors (line 72); priority_boundary (line 83); error_by_language (line 99); main (line 116)

- [paper/experiments/fetch_gptoss_translations.py](../../paper/experiments/fetch_gptoss_translations.py): Collect the local GPT-OSS system's translations via the Ollama API (task B2). call_ollama (line 44); parse_csv_reply (line 59); rows_block (line 84); build_prompt (line 91); load_prompt_rows (line 111); fetch_lang (line 118); fill_missing (line 148); main (line 186)

- [paper/experiments/intent_test_predictions.py](../../paper/experiments/intent_test_predictions.py): Per-row intent test predictions, recovered from the saved K6b checkpoints. recorded_macro_f1 (line 53); infer (line 63); main (line 90)

- [paper/experiments/label_ceiling.py](../../paper/experiments/label_ceiling.py): The label ceiling: how good a classifier could possibly look on these labels. norm (line 50); join_gold (line 54); bootstrap (line 81); cohen_kappa (line 89); main (line 97)

- [paper/experiments/language_gap.py](../../paper/experiments/language_gap.py): Is the per-language deficit real, or is it sampling noise? paired_mcnemar (line 49); paired_bootstrap_headline (line 62); main (line 100)

- [paper/experiments/negative_is_topic.py](../../paper/experiments/negative_is_topic.py): Is the Negative label polarity, or is it a topic? main (line 46)

- [paper/experiments/policy_bakeoff.py](../../paper/experiments/policy_bakeoff.py): Literature-grounded bake-off: how should a support queue be ordered? _train_dev (line 103); _conditional_table (line 110); _load (line 119); build_frame (line 123); label_model (line 152); _stack_features (line 205); fit_label_models (line 211); _Reordered (line 236); _align (line 241); policy_index (line 255); SimConfig (line 329); simulate (line 342); summarise (line 387)

- [paper/experiments/queue_sim.py](../../paper/experiments/queue_sim.py): Discrete-event queue simulation -- what the classifier scores are actually worth. SimConfig (line 49); _service_times (line 64); simulate (line 70); summarise (line 147); run_grid (line 189); attainment (line 209)

- [paper/experiments/register_by_track.py](../../paper/experiments/register_by_track.py): Loanword retention for all four non-English tracks, on the full test split. main (line 38)

- [paper/experiments/register_metrics.py](../../paper/experiments/register_metrics.py): Register and code-mixing metrics -- the axis a domain corpus can legitimately win on. latin_fraction (line 52); retention (line 59); main (line 76)

- [paper/experiments/run_policy_bakeoff.py](../../paper/experiments/run_policy_bakeoff.py): Run the literature bake-off: 5 label models x 6 published policies. main (line 26); _save (line 153)

- [paper/experiments/run_system_eval.py](../../paper/experiments/run_system_eval.py): Evaluate the Ticket Urgency Score -- all five layers of SYSTEM_PLAN section 3. save (line 48); ndcg_at_k (line 61); ranking_metrics (line 70); fit_weights (line 89); main (line 144)

- [paper/experiments/save_posteriors.py](../../paper/experiments/save_posteriors.py): Persist per-ticket posterior distributions -- the input the scoring function needs. device (line 68); encoder_posteriors (line 75); classical_posteriors (line 104); write (line 116); check (line 136); main (line 151)

- [paper/experiments/save_test_predictions.py](../../paper/experiments/save_test_predictions.py): Persist per-row test predictions for the classical roster. main (line 42)

- [paper/experiments/score_translations.py](../../paper/experiments/score_translations.py): Reference-free automatic scoring for the translation comparison. script_fraction (line 49); collect (line 62); labse_cosine (line 76); comet_kiwi (line 101); main (line 114)

- [paper/experiments/scoring.py](../../paper/experiments/scoring.py): The Ticket Urgency Score (TUS) -- the paper's system contribution. Weights (line 58); load_posteriors (line 77); load_criticality (line 83); expected_severity (line 89); build_signal_frame (line 99); content_score (line 144); urgency (line 151); oracle_content_score (line 157); simplex_grid (line 174)

- [paper/experiments/significance.py](../../paper/experiments/significance.py): Paired significance tests between systems on the test set. discover (line 49); _encode (line 58); _headline_from_counts (line 65); _selftest (line 88); paired_bootstrap (line 105); mcnemar (line 154); to_markdown (line 173); main (line 186)

- [paper/experiments/tokenizer_to_downstream.py](../../paper/experiments/tokenizer_to_downstream.py): Does a tokenizer diagnostic predict downstream performance? For [UNK], yes. downstream (line 46); main (line 61)

- [paper/experiments/validate_translations.py](../../paper/experiments/validate_translations.py): Check returned translation files before they are scored (tracker B2v). script_fraction (line 34); check (line 49); main (line 106)

## scripts/clean_rag_sources.py

- [scripts/clean_rag_sources.py](../../scripts/clean_rag_sources.py): Clean validated RAG HTML sources into focused Markdown documents. Result (line 90); words (line 107); normalized_text (line 111); yaml_string (line 115); sha256 (line 120); find_raw_file (line 128); noise_signature (line 138); remove_noise (line 143); remove_repeated_links (line 165); inline_markdown (line 180); table_markdown (line 205); list_markdown (line 227); block_markdown (line 249); clean_source (line 294); read_manifest (line 370); manifest_text (line 376); report_text (line 386); parse_args (line 437); main (line 447)

## synthetic_ticket_dataset/evaluate_fireworks.py

- [synthetic_ticket_dataset/evaluate_fireworks.py](../../synthetic_ticket_dataset/evaluate_fireworks.py): Evaluate generated banking screenshots with Fireworks AI. parse_args (line 78); image_data_url (line 88); request_worker (line 94); request_prediction (line 148); confusion_matrix (line 209); save_confusion_plot (line 220); main (line 250)

## synthetic_ticket_dataset/generate_dataset.py

- [synthetic_ticket_dataset/generate_dataset.py](../../synthetic_ticket_dataset/generate_dataset.py): Generate a deterministic synthetic mobile-banking support screenshot dataset. find_fonts (line 157); font (line 170); localized_message (line 179); display_language (line 193); wrap_text (line 199); add_noise (line 213); draw_icon (line 224); make_details (line 238); render_screen (line 253); create_label (line 344); create_preview (line 373); validate_dataset (line 391); generate_dataset (line 449); main (line 473)
