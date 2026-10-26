"""
CHANGELOG
=========

All notable changes to the AI-Powered Document Intelligence RAG Assistant
are documented in this file.

Format based on `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_
and this project adheres to `Semantic Versioning <https://semver.org/>`_.

---

## [Unreleased]

### Added
- `RateLimiter` utility (`rate_limiter.py`): Thread-safe sliding-window token-bucket
  for throttling LLM API calls with `allow()`, `wait_for_slot()`, and `remaining`
  properties.
- `TTLCache` utility (`cache_service.py`): In-memory TTL cache with LRU eviction,
  per-entry TTL overrides, `purge_expired()`, and `make_key()` static helper.
  Module-level `query_cache` (5 min) and `embedding_cache` (30 min) singletons.
- `AuditLogMiddleware` (`middleware.py`): Structured request/response logger that
  records HTTP method, path, status code, latency (ms), and authenticated user ID.
- Health-check views (`health_views.py`):
  - `GET /health/` — liveness probe (always 200 when server is running).
  - `GET /health/ready/` — readiness probe checks DB + FAISS vector index.
  - `GET /health/version/` — returns app version, LLM provider, and debug flag.
- `ExportService` (`export_service.py`): Converts Q&A results and document summaries
  to plain text, JSON, and Markdown export formats with sanitised filenames.
- `KeywordExtractionService` (`keyword_service.py`): Zero-dependency TF-IDF keyword
  and keyphrase extraction with configurable n-gram ranges and stop-word filtering.
- `DocumentStatsService` (`stats_service.py`): Computes readability metrics
  (Flesch Reading Ease, syllable count), type-token ratio, average sentence length,
  and vocabulary size for any document or free text.
- `paginate_queryset` / `extract_page_params` helpers (`pagination.py`): Consistent
  in-memory pagination with enriched metadata (total pages, has_next/prev, etc.).
- New test modules: `test_rate_limiter`, `test_cache_service`, `test_keyword_service`,
  `test_export_service`, `test_stats_service`, `test_pagination`.
- `.env.example` extended with `LLM_RATE_LIMIT_CALLS`, `LLM_RATE_LIMIT_PERIOD`,
  `QUERY_CACHE_TTL`, `EMBEDDING_CACHE_TTL`, and `LOG_LEVEL` variables.

### Changed
- `core/settings.py`: `AuditLogMiddleware` registered immediately after
  `SecurityMiddleware` so every request is logged regardless of auth state.
- `core/settings.py`: Added `LLM_RATE_LIMIT_CALLS`, `LLM_RATE_LIMIT_PERIOD`,
  `QUERY_CACHE_TTL`, and `EMBEDDING_CACHE_TTL` configuration keys with
  environment variable overrides.

---

## [1.0.0] — Initial Release

### Added
- Full RAG pipeline: PyMuPDF extraction → recursive chunking → FAISS indexing.
- Hybrid BM25 + dense FAISS retrieval with Reciprocal Rank Fusion (RRF).
- Cross-encoder reranking for top-K retrieved candidates.
- Conversational query expansion / rewriting using recent chat history.
- Anti-hallucination prompt with untrusted-data delimiters and [Source N] citations.
- Google Gemini and OpenAI API integrations with local fallback synthesiser.
- Multi-document collections and side-by-side document comparison.
- Grounding verification service to flag unsupported claims.
- Django REST Framework API with session + basic authentication.
- Bootstrap 5 UI with source inspector drawer and latency metrics display.
- Multi-tenant user isolation for documents, collections, and conversations.
- Bookmark and feedback (thumbs up/down) models.
- EvaluationResult model for benchmark audit logs.
- Evaluation dataset JSON and evaluation pipeline.
- Docker / docker-compose support with gunicorn.
- Full pytest test suite covering services, APIs, and UI pages.
- ARCHITECTURE.md, CONTRIBUTING.md, DEPLOYMENT.md, SECURITY.md documentation.
"""
