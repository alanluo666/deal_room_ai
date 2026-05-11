# Tests Folder Function Map

This document lists every Python file under `tests/`, summarizes what each file validates, and briefly explains each function in that file.

## Quick Counts

- Python files in `tests/`: **14** total (`13` test modules + `conftest.py`).
- Test functions in test modules (`test_*.py`): **91**.
- Day-11 file: `tests/test_7_data_model.py` contains **7** core tests (4 data + 3 model) plus **2** lightweight ingestion/deploy boundary checks.

## Grading View (Course Categories)

- **Unit tests:** `tests/test_vector_store.py`, utility-focused tests in `tests/test_questions.py` (`_trim_to_budget`, `_build_prompt`), utility-focused tests in `tests/test_analyze.py` (`_build_task_prompt`), plus parts of `tests/test_auth.py`.
- **Functional tests:** endpoint behavior in `tests/test_auth.py`, `tests/test_deal_rooms.py`, `tests/test_documents.py`, `tests/test_questions.py`, `tests/test_analyze.py`, `tests/test_chat.py`, `tests/test_predict.py`, and `tests/test_probes.py`.
- **Integration tests:** request logging and dependency interaction checks in `tests/test_request_logging.py`, `tests/test_probes.py`, and side-effect checks across DB/vector/file layers in `tests/test_documents.py` and `tests/test_questions.py`.
- **Security tests:** authz/isolation checks across API suites, sanitization checks in `tests/test_predict.py` and `tests/test_chat.py`, import guardrails in `tests/test_no_cloud_imports.py`, and secret-pattern scan in `tests/test_9_automation.py`.
- **Data tests (Day 11):** in `tests/test_7_data_model.py`:
  - `test_data_schema_load_csv_enforces_required_columns`
  - `test_data_distribution_synthetic_is_balanced`
  - `test_data_integrity_no_empty_texts_or_unknown_labels`
  - `test_data_semantics_synthetic_contains_label_specific_keywords`
- **Model tests (Day 11):** in `tests/test_7_data_model.py`:
  - `test_model_slice_recall_meets_floor_per_label`
  - `test_model_invariance_to_case_spacing_and_punctuation`
  - `test_model_calibration_probability_sanity_and_confidence_floor`
- **Lightweight boundary checks (ingestion/deploy):** in `tests/test_7_data_model.py`:
  - `test_ingestion_boundary_infers_doc_type_and_passes_to_build_chunks`
  - `test_deploy_boundary_predict_returns_label_and_scores_shape`

## `tests/conftest.py`
**What it tests/configures:** Shared pytest fixtures and fakes for async API tests (DB/session/client/vector/embedding/LLM overrides).

- `test_engine`: Creates an in-memory async SQLite engine with FK enforcement for tests.
- `test_session_factory`: Provides async SQLAlchemy session factory bound to test engine.
- `_flatten_where`: Normalizes Chroma-style `where` filters (including `$and`) for fake store matching.
- `fake_vector_store`: Fixture returning in-memory fake vector store.
- `fake_embedding_client`: Fixture returning fake embedding client that records calls.
- `stub_llm`: Fixture returning deterministic stub LLM for RAG tests.
- `make_client`: Builds an async HTTP client with dependency overrides for DB/vector/embed.
- `override_rag`: Overrides `rag_service_dep` with `RagService` that uses stubs/fakes.
- `client`: Convenience fixture yielding one async client instance from `make_client`.

## `tests/test_auth.py`
**What it tests:** Authentication/session cookie behavior (`register`, `login`, `me`, `logout`) and cookie security flag logic.

- `test_register_returns_201_and_sets_cookie`: Verifies successful registration and session cookie issuance.
- `test_register_duplicate_email_returns_409`: Verifies duplicate email registration is rejected.
- `test_login_happy_path`: Verifies valid credentials return success and cookie.
- `test_login_wrong_password_returns_401_and_no_cookie`: Verifies failed login does not set session.
- `test_me_without_cookie_returns_401`: Verifies unauthenticated `/auth/me` is blocked.
- `test_me_with_cookie_returns_user`: Verifies authenticated `/auth/me` returns current user.
- `test_logout_clears_cookie`: Verifies logout invalidates access after cookie clear.
- `test_set_session_cookie_uses_setting_for_secure_flag`: Verifies `Secure` attribute follows config.

## `tests/test_deal_rooms.py`
**What it tests:** Deal room CRUD/authz and basic health response contract checks.

- `_register`: Helper to register user and assert success.
- `test_create_and_list_deal_rooms`: Verifies create + list flow and ownership fields.
- `test_create_requires_auth`: Verifies unauthenticated room creation is rejected.
- `test_other_user_cannot_see_or_delete`: Verifies cross-user isolation on get/list/delete.
- `test_delete_own_deal_room`: Verifies owner can delete and resource is gone.
- `test_health_includes_db_ok`: Verifies `/health` includes readiness booleans and hides sensitive config fields.

## `tests/test_documents.py`
**What it tests:** Document upload/list/get/delete flows, validation, status/error handling, storage and vector-store side effects, authz.

- `_register`: Helper to register user.
- `_create_room`: Helper to create deal room.
- `_upload_txt`: Helper to upload a text file.
- `test_upload_requires_auth`: Verifies upload requires authentication.
- `test_upload_txt_happy_path`: Verifies successful upload, embedding calls, and chunk upserts.
- `test_list_documents_scoped_to_room`: Verifies per-room document list isolation.
- `test_get_document`: Verifies fetch single document endpoint.
- `test_upload_unsupported_mime`: Verifies unsupported MIME returns 415.
- `test_upload_empty_file`: Verifies empty upload returns 400.
- `test_upload_too_large`: Verifies upload size limit enforcement.
- `test_extraction_failure_sets_failed_status`: Verifies failed embedding/extraction marks doc as failed.
- `test_cross_user_cannot_see_documents`: Verifies document endpoints are owner-scoped.
- `test_delete_document_removes_side_effects`: Verifies delete cleans DB + vector chunks.
- `test_deal_room_delete_cascades_documents`: Verifies room deletion cascades document cleanup.
- `test_upload_persists_file_to_disk`: Verifies uploaded file persistence path/content.
- `test_health_includes_storage_and_chroma`: Verifies `/health` includes storage/chroma readiness flags.

## `tests/test_questions.py`
**What it tests:** RAG Q&A (`/ask`) and question history behavior, citations, validation, ownership, and prompt-budget utility functions.

- `_register`: Helper to register user.
- `_create_room`: Helper to create room.
- `_upload_txt`: Helper to upload source text.
- `test_ask_requires_auth`: Verifies ask requires auth.
- `test_ask_happy_path_returns_answer_and_citations`: Verifies normal ask response contract and citations.
- `test_ask_in_empty_room_returns_idk`: Verifies deterministic no-context answer and persisted history entry.
- `test_ask_non_owner_returns_404`: Verifies cross-user ask/history access blocked.
- `test_ask_isolates_per_deal_room`: Verifies retrieval/citations are room-scoped.
- `test_ask_503_when_openai_not_configured`: Verifies ask returns 503 when LLM unavailable.
- `test_ask_rejects_empty_question`: Verifies request validation for empty question.
- `test_ask_rejects_out_of_range_top_k`: Verifies `top_k` bounds validation.
- `test_questions_list_ordered_and_scoped`: Verifies history ordering and room scoping.
- `test_delete_deal_room_cascades_questions`: Verifies question rows removed when room deleted.
- `test_ask_persists_citations_json_round_trip`: Verifies citation JSON persistence fidelity.
- `test_trim_to_budget_truncates_partial_chunk_when_meaningful`: Verifies chunk trimming with meaningful partial inclusion.
- `test_trim_to_budget_drops_partial_below_threshold`: Verifies tiny trailing partial chunk is dropped.
- `test_build_prompt_when_no_chunks_contains_idk_instruction`: Verifies no-context prompt includes IDK guard.
- `test_build_prompt_includes_source_markers`: Verifies prompt rendering includes source annotations.

## `tests/test_analyze.py`
**What it tests:** Analyze task presets (`summary`, `risks`) including validation, authz, statelessness, task-specific retrieval/instructions, and prompt building.

- `_register`: Helper to register user.
- `_create_room`: Helper to create room.
- `_upload_txt`: Helper to upload content.
- `test_analyze_requires_auth`: Verifies analyze endpoint requires auth.
- `test_analyze_summary_happy_path`: Verifies summary task response/citations contract.
- `test_analyze_risks_happy_path`: Verifies risks task happy path.
- `test_analyze_empty_room_returns_idk`: Verifies deterministic no-context response.
- `test_analyze_non_owner_returns_404`: Verifies owner scoping.
- `test_analyze_rejects_invalid_task`: Verifies task enum validation.
- `test_analyze_rejects_out_of_range_top_k`: Verifies `top_k` bounds.
- `test_analyze_503_when_openai_not_configured`: Verifies graceful 503 when LLM unavailable.
- `test_analyze_does_not_mutate_questions_history`: Verifies analyze is stateless (no question writes).
- `test_analyze_passes_task_specific_instructions_to_llm`: Verifies per-task instruction routing.
- `test_analyze_uses_task_retrieval_query_not_user_text`: Verifies retrieval query derives from task presets.
- `test_build_task_prompt_without_chunks_requests_idk`: Verifies task prompt no-context behavior.
- `test_build_task_prompt_with_chunks_renders_sources`: Verifies task prompt source formatting.

## `tests/test_chat.py`
**What it tests:** Chat endpoint behavior including authz, message-shape validation, local-dev fallback, happy path grounding, and sanitized failures.

- `_register`: Helper to register user.
- `_create_room`: Helper to create room.
- `_upload_txt`: Helper to upload context document.
- `test_chat_requires_auth`: Verifies chat endpoint requires authentication.
- `test_chat_non_owner_returns_404`: Verifies cross-user access blocked.
- `test_chat_rejects_when_last_message_is_not_user`: Verifies request validation for turn order.
- `test_chat_returns_local_dev_stub_when_openai_not_configured`: Verifies offline/dev stub behavior.
- `test_chat_happy_path_returns_grounded_answer_and_citations`: Verifies grounded chat output and citation shape.
- `test_chat_generic_500_does_not_leak_internal_exception_text`: Verifies sensitive exception details are not leaked.

## `tests/test_predict.py`
**What it tests:** Legacy `/predict` endpoint auth gating and error sanitization.

- `test_predict_unauthenticated_returns_401`: Verifies auth requirement.
- `test_predict_authenticated_with_openai_disabled_returns_503`: Verifies explicit 503 when OpenAI disabled.
- `test_predict_authenticated_generic_500_is_sanitised`: Verifies generic failures return sanitized 500 detail.

## `tests/test_probes.py`
**What it tests:** Liveness/readiness contracts and dependency-health behavior.

- `test_livez_returns_200_without_auth`: Verifies liveness is simple and always healthy.
- `test_readyz_happy_path_returns_200`: Verifies readiness returns all-green payload when healthy.
- `test_readyz_returns_503_when_chroma_unhealthy`: Verifies readiness degrades to 503 with dependency failure.

## `tests/test_request_logging.py`
**What it tests:** Request-ID propagation/generation and structured request logging middleware behavior.

- `test_request_id_header_is_echoed_when_provided`: Verifies inbound request ID is echoed.
- `test_request_id_is_generated_when_missing`: Verifies server generates request ID when absent.
- `test_request_is_logged_at_info_level`: Verifies one structured `api.request` log line per request.

## `tests/test_vector_store.py`
**What it tests:** Chroma metadata wiring for `doc_type` and chunk metadata correctness.

- `_make_store`: Helper creating store with capturing fake collection.
- `test_upsert_chunks_includes_doc_type_in_metadata_when_set`: Verifies `doc_type` is written when present.
- `test_upsert_chunks_omits_doc_type_in_metadata_when_none`: Verifies backward-compatible omission when absent.
- `test_upsert_chunks_mixed_chunks_only_adds_doc_type_where_set`: Verifies mixed-batch metadata behavior.

## `tests/test_no_cloud_imports.py`
**What it tests:** Guardrail that API startup does not implicitly import cloud SDKs.

- `test_api_startup_does_not_import_google_adk`: Verifies `google_adk` not imported on startup.
- `test_api_startup_does_not_import_vertexai`: Verifies `vertexai` not imported.
- `test_api_startup_does_not_import_google_cloud_aiplatform`: Verifies GCP AI Platform SDK not imported.
- `test_api_startup_does_not_import_google_genai`: Verifies `google.genai` not imported.
- `test_forbidden_modules_list_kept_in_sync`: Verifies guardrail list and explicit assertions stay aligned.

## `tests/test_9_automation.py`
**What it tests:** Assignment-focused trimmed automation checks for `/predict`, logging, and simple repo secret scanning.

- `_register`: Helper to register user for authenticated predict calls.
- `test_predict_rejects_missing_document_text`: Verifies schema validation for required `document_text`.
- `test_predict_summary_returns_result_with_stubbed_model`: Verifies `/predict` success path with stubbed model.
- `test_predict_call_sets_mlflow_tracking_flag_in_response`: Verifies tracking flag exposed in predict response.
- `test_predict_request_is_logged_once`: Verifies one request log entry for predict path.
- `test_repository_has_no_openai_style_secret_literals`: Scans `api/*.py` for obvious hardcoded OpenAI-style key patterns.

## `tests/test_7_data_model.py`
**What it tests:** Day-11 style data/model suite (schema/distribution/integrity/semantics + slice/invariance/calibration) plus lightweight ingestion/deploy boundary checks.

- `_make_small_csv`: Helper to create tiny CSV fixtures for loader tests.
- `_train_on_synthetic`: Helper to train pipeline on deterministic synthetic data split.
- `test_data_schema_load_csv_enforces_required_columns`: Validates CSV schema requirements and missing-column failure.
- `test_data_distribution_synthetic_is_balanced`: Validates synthetic class balance distribution.
- `test_data_integrity_no_empty_texts_or_unknown_labels`: Validates basic dataset integrity constraints.
- `test_data_semantics_synthetic_contains_label_specific_keywords`: Checks semantic keyword presence per label bucket.
- `test_model_slice_recall_meets_floor_per_label`: Enforces per-class slice recall floor.
- `test_model_invariance_to_case_spacing_and_punctuation`: Validates prediction stability under benign text perturbations.
- `test_model_calibration_probability_sanity_and_confidence_floor`: Validates probability simplex and confidence sanity.
- `test_ingestion_boundary_infers_doc_type_and_passes_to_build_chunks`: Checks ingestion infers/passes `doc_type` and performs expected store calls.
- `test_deploy_boundary_predict_returns_label_and_scores_shape`: Checks deploy predictor output contract (`label`, `scores`) per instance.
