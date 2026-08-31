# Enterprise Implementation Plan: AI-Powered Document Intelligence & Enterprise RAG Assistant (V2)

Build an enterprise-grade, portfolio-defining **AI Document Intelligence & Enterprise RAG Platform** using **Django**, **Django REST Framework (DRF)**, **PyMuPDF**, **Sentence Transformers**, **FAISS + BM25 Hybrid Search**, **Cross-Encoder Reranking**, **OpenAI API**, and **Bootstrap 5 UI** with multi-tenant authentication, multi-document collections, anti-hallucination verification, latency breakdown monitoring, and an interactive RAG Evaluation Dashboard.

## User Review Required

> [!IMPORTANT]
> - **Enterprise Architecture**: Django Monolith + DRF REST APIs + HTML5/CSS3/JavaScript (Bootstrap 5) with Role-Based Access Control (Admin/User).
> - **Hybrid Search & Reranking**: Combines **FAISS** (semantic vector search) + **BM25** (exact keyword search) with reciprocal rank fusion, followed by a **Reranker** stage for high-precision context assembly.
> - **Anti-Hallucination Layer**: Prompt constraints + post-generation grounding check to eliminate ungrounded answers.
> - **Latency & Evaluation Suite**: Records stage-by-stage response time (Retrieval ms, Reranking ms, LLM ms) and exposes an in-app **RAG Evaluation Dashboard** displaying Precision@K, Faithfulness, and Answer Relevance.
> - **Environment & Docker Compose**: Configured via `.env` (`OPENAI_MODEL`, `OPENAI_API_KEY`, `EMBEDDING_MODEL_NAME`) and deployed with `docker-compose.yml`.

---

## Architecture & Enterprise Data Flow

```text
                                  USER
                                    │
                                    ▼
                   ┌──────────────────────────────────┐
                   │  Django Web UI (Bootstrap 5+JS) │
                   └────────────────┬─────────────────┘
                                    │
                                    ▼
                   ┌──────────────────────────────────┐
                   │ Django REST Framework (DRF APIs) │
                   └────────────────┬─────────────────┘
                                    │
         ┌──────────────────────────┴──────────────────────────┐
         ▼                                                     ▼
Django Security & Auth                                  RAG ENGINE V2
(User & Doc Scoped)                                            │
         │                        ┌────────────────────────────┼────────────────────────────┐
         ▼                        ▼                            ▼                            ▼
PostgreSQL / SQLite            PyMuPDF                      Sentence                     FAISS +
    Database                  Extractor                   Transformer                     BM25
 (Doc/Chunk/Log)                  │                            │                        Hybrid Search
                                  ▼                            ▼                            │
                             Text Chunks                  Embeddings                        ▼
                                  │                            │                    Top-10 Candidates
                                  └────────────────────────────┼────────────────────────────┤
                                                                                            ▼
                                                                                   Reranker Service
                                                                                  (Cross-Encoder/Score)
                                                                                            │
                                                                                            ▼
                                                                                     Top-3 Context
                                                                                            │
                                                                                            ▼
                                                                                     Prompt Builder
                                                                                            │
                                                                                            ▼
                                                                                   LLM + Anti-Hallucination
                                                                                            │
                                                                                            ▼
                                                                                   Answer + Citations +
                                                                                     Latency Metrics
```

---

## Directory Structure

```text
AI-Document-RAG-Assistant/
├── manage.py
├── docker-compose.yml
├── Dockerfile
│
├── core/                        # Django Configuration App
│   ├── __init__.py
│   ├── settings.py              # Django settings, DRF settings, RAG configs
│   ├── urls.py                  # Main routing
│   ├── wsgi.py
│   └── asgi.py
│
├── rag_app/                     # Core RAG Application
│   ├── __init__.py
│   ├── admin.py                 # Admin registration with Analytics Dashboard widgets
│   ├── apps.py
│   ├── models.py                # Collection, Document, DocumentChunk, Conversation, Message, EvaluationResult
│   ├── urls.py                  # Web template routes
│   ├── views.py                 # Web template views (Dashboard, Chat, Evaluation, Auth)
│   ├── migrations/              # DB Migrations
│   │
│   ├── api/                     # Django REST Framework API Layer
│   │   ├── __init__.py
│   │   ├── serializers.py       # DRF Serializers
│   │   ├── views_api.py         # DRF ViewSets & Endpoints
│   │   └── urls_api.py          # /api/ routing
│   │
│   └── services/                # Modular Service Layer
│       ├── __init__.py
│       ├── pdf_service.py       # PyMuPDF text extraction per page
│       ├── cleaner_service.py   # Text cleaning & normalization
│       ├── chunker_service.py   # Character chunker (1000 chars, 150 overlap)
│       ├── embedding_service.py # SentenceTransformers (all-MiniLM-L6-v2)
│       ├── bm25_service.py      # BM25 keyword indexer & ranker
│       ├── vector_service.py    # FAISS vector index & disk storage management
│       ├── hybrid_retriever_service.py # FAISS + BM25 Reciprocal Rank Fusion retriever
│       ├── reranker_service.py  # Cross-Encoder score-based context reranker
│       ├── prompt_service.py    # Context assembly & anti-hallucination system prompt builder
│       ├── llm_service.py       # OpenAI API call with configurable model & error handling
│       ├── grounding_service.py # Post-generation answer-to-context grounding validator
│       └── rag_service.py       # Pipeline orchestrator, multi-mode summarizer, latency tracker
│
├── templates/                   # HTML Templates (Bootstrap 5)
│   ├── base.html
│   ├── index.html               # Hero / Landing Page
│   ├── login.html               # Login Page
│   ├── register.html            # Registration Page
│   ├── dashboard.html           # Document Collections, Ingestion Tracker & Reprocessing
│   ├── document_detail.html     # Document Viewer & Multi-mode Summarizer
│   ├── chat.html                # Multi-turn RAG Chat UI with Citations Drawer & Latency Breakdown
│   └── evaluation.html          # Interactive RAG Evaluation & Performance Dashboard
│
├── static/                      # Custom Styling & Dynamic JS
│   ├── css/
│   │   └── style.css            # Dark/Light responsive UI styling
│   └── js/
│       └── app.js               # Dynamic AJAX fetch calls, chat stream, citations, evaluation graphs
│
├── data/                        # Uploaded PDFs & User Vector DB Indices
│   ├── uploads/
│   └── vector_store/
│
├── evaluation/                  # AI RAG Benchmark Suite
│   ├── evaluation_dataset.json  # 100+ QA Benchmark pairs
│   ├── retrieval_evaluation.py  # Precision@K & MRR metric evaluator
│   └── answer_evaluation.py     # Faithfulness & relevance evaluator
│
├── tests/                       # Pytest & Django Unit Test Suite
│   ├── __init__.py
│   ├── test_pdf_service.py
│   ├── test_chunker_service.py
│   ├── test_embedding_service.py
│   ├── test_vector_service.py
│   ├── test_hybrid_retriever.py
│   ├── test_reranker.py
│   ├── test_rag_service.py
│   └── test_api.py
│
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Detailed Data Models (`rag_app/models.py`)

- `DocumentCollection`:
  - `id`, `user` (FK to User), `name`, `description`, `created_at`, `updated_at`.
- `Document`:
  - `id`, `user` (FK to User), `collection` (FK to DocumentCollection, nullable), `title`, `file`, `file_size`, `page_count`, `chunk_count`, `status` (`uploaded`, `processing`, `completed`, `failed`), `processing_error` (default=""), `created_at`, `updated_at`.
- `DocumentChunk`:
  - `id`, `document` (FK to Document), `chunk_index`, `page_number`, `content`, `vector_id` (int), `index_version` (int, default=1), `created_at`.
- `Conversation`:
  - `id`, `user` (FK to User), `document` (FK to Document, nullable), `collection` (FK to DocumentCollection, nullable), `title`, `created_at`, `updated_at`.
- `Message`:
  - `id`, `conversation` (FK to Conversation), `role` (`user`, `assistant`), `content`, `sources` (JSONField: `[{doc_title, page_number, retrieval_score, chunk_preview}]`), `latency_metrics` (JSONField: `{retrieval_ms, rerank_ms, llm_ms, total_ms}`), `created_at`.
- `EvaluationResult`:
  - `id`, `evaluation_date`, `precision_at_k`, `mrr_score`, `faithfulness_score`, `relevance_score`, `avg_latency_sec`, `total_test_cases`, `created_at`.

---

## Comprehensive Phased Execution Plan

### 🟢 Phase 1 — Core Monolith & Multi-Tenant Security (V1 Core)
1. Django Project setup (`core`, `rag_app`).
2. ORM models (`Collection`, `Document`, `DocumentChunk`, `Conversation`, `Message`, `EvaluationResult`) & migrations.
3. Django Authentication (`register`, `login`, `logout`) & Bootstrap 5 base templates.
4. `pdf_service`, `cleaner_service`, `chunker_service` (sliding window ~1000 chars, 150 overlap).
5. `embedding_service` (`SentenceTransformer('all-MiniLM-L6-v2')`) & `vector_service` (`FAISS`).
6. Single & multi-document ingestion pipeline with `status` and `processing_error` logging.

### 🟡 Phase 2 — Multi-Document RAG & Advanced Citation Engine
1. Multi-document collections grouping & querying across collections.
2. `prompt_service` with anti-hallucination instruction set.
3. `llm_service` using OpenAI API via `.env` (`OPENAI_MODEL`) with graceful error handling.
4. `rag_service` orchestrator managing multi-turn conversation memory.
5. DRF REST APIs (`/api/documents/upload/`, `/api/chat/`, `/api/summary/`, `/api/conversations/`).
6. Interactive Chat UI featuring expandable citations drawer showing exact snippet preview, document title, page number, and `retrieval_score`.
7. Multi-mode Document Summarizer (Executive Summary, Key Points, Technical Summary, Risks & Issues).

### 🔴 Phase 3 — Hybrid Search, Reranking & Anti-Hallucination Guardrails
1. `bm25_service.py`: Exact keyword indexer using BM25.
2. `hybrid_retriever_service.py`: Reciprocal Rank Fusion (RRF) combining FAISS semantic scores + BM25 keyword scores.
3. `reranker_service.py`: Cross-encoder / similarity score-based reranker selecting top 3-5 high-precision context chunks.
4. `grounding_service.py`: Post-generation answer-to-context grounding check verifying answer claims against retrieved text snippets.
5. Response-time latency recording (`retrieval_ms`, `rerank_ms`, `llm_ms`, `total_ms`) stored per message.

### 🔵 Phase 4 — Analytics, RAG Evaluation Suite & Docker Compose
1. Interactive RAG Evaluation Dashboard view (`/evaluation/`) displaying benchmark charts, Precision@K, Faithfulness, and Latency metrics.
2. `evaluation/retrieval_evaluation.py` & `evaluation/answer_evaluation.py` benchmark scripts.
3. Admin Analytics Dashboard in Django Admin.
4. Reprocessing action (`/api/documents/<id>/reprocess/`).
5. Pytest unit tests suite across all service layers.
6. Containerization with `docker-compose.yml` (Django, DB, Vector Index Storage) and portfolio-grade `README.md`.

---

## Verification Plan

### Automated Tests
1. Run `python manage.py test tests`: Execute unit tests for PDF reader, chunker, FAISS vector store, BM25 hybrid search, reranker, and REST APIs.
2. Run RAG evaluation suite: `python evaluation/retrieval_evaluation.py` and verify metrics output.

### Manual Verification
1. Register user `enterprise_user` and upload a multi-PDF collection.
2. Query across the collection; verify BM25 + FAISS hybrid search and reranking context selection.
3. Inspect citations drawer to verify snippet previews, page numbers, and `retrieval_score` badges.
4. Verify anti-hallucination handling when asking an out-of-scope question ("I could not find this information in the uploaded documents").
5. Inspect the Latency breakdown and RAG Evaluation Dashboard tab.
