# 🚀 AI-Powered Document Intelligence & Enterprise RAG Assistant

A portfolio project implementing **Retrieval-Augmented Generation (RAG)** with **Django**, **Django REST Framework (DRF)**, **PyMuPDF**, **Sentence Transformers**, **FAISS**, **BM25 Hybrid Search**, **Cross-Encoder Reranking**, and optional **Google Gemini** or **OpenAI** APIs.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.1-green.svg)
![RAG](https://img.shields.io/badge/GenAI-RAG%20Architecture-purple.svg)
![FAISS](https://img.shields.io/badge/VectorDB-FAISS-orange.svg)
![LLM](https://img.shields.io/badge/LLM-Gemini%20%7C%20OpenAI-blue.svg)
![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205-blueviolet.svg)

---

## 📌 Project Overview & Solution

Traditional chatbots generate responses based on internal training weights, leading to hallucinations or outdated facts. This platform implements **grounded Retrieval-Augmented Generation (RAG)** over uploaded PDF documents:

1. **Document Ingestion**: PyMuPDF page-by-page extraction, text normalization, and sliding-window character chunking (~1000 chars, 150 overlap).
2. **Embedding & Vector Storage**: Dense 384-dimensional vector embedding via HuggingFace `SentenceTransformers` (`all-MiniLM-L6-v2`) indexed in `FAISS` (`IndexFlatIP`).
3. **Hybrid Search & Reranking**: Reciprocal Rank Fusion (RRF) combining **FAISS** semantic similarity search with **BM25** exact keyword matching, followed by Cross-Encoder reranking.
4. **Conversational Query Expansion**: Expands follow-up questions using past conversation context before executing vector retrieval.
5. **Multi-Document Comparison**: Side-by-side comparative analysis of Document A vs Document B (financial diffs, operational changes, policy updates).
6. **Retrieval Explainability & Transparency**: Real-time explainability reasons, similarity scores, and right-side **Source Inspector Drawer**.
7. **Citations & Latency Monitoring**: Page-level source citations with snippet previews, `retrieval_score` badges, and stage-by-stage latency tracking (`retrieval_ms`, `rerank_ms`, `llm_ms`, `total_ms`).
8. **Multi-Tenant User Isolation**: Django Authentication securing document collections, vector search results, bookmarks, and chat threads per user.

---

## 🏗️ System Architecture

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
                                                                                     Top-4 Context
                                                                                            │
                                                                                            ▼
                                                                                     Prompt Builder
                                                                                            │
                                                                                            ▼
                                                                                Google Gemini / LLM API
                                                                                            │
                                                                                            ▼
                                                                                   Answer + Citations +
                                                                                     Explainability
```

---

## ✨ Enterprise Product Features

- 🏠 **Dashboard (`/dashboard/`)**: Stat cards, drag-and-drop PDF uploader, processing indicators, and collection creator.
- 📄 **Document Library (`/documents/`)**: Document list with status filters (`Completed`, `Processing`, `Failed`).
- 🔎 **Document Chunk Inspector**: Search extracted text, filter by page, copy full chunk content, and export matching chunks as JSON, CSV, or plain text.
- 📚 **Collections (`/collections/`)**: Group related PDF documents into unified knowledge bases for multi-document RAG.
- 💬 **RAG Workspace Chat (`/chat/`)**: Proportional 3-column AI workspace with step-by-step thinking indicators, suggested question cards, and **Right-Side Source Inspector Drawer**.
- 🔎 **Search Inspector (`/search/`)**: Standalone Hybrid Search Inspector for live FAISS + BM25 vector candidate ranking analysis.
- 🔀 **Multi-Document Comparison (`/compare/`)**: Side-by-side document diffs comparing scope, financial metrics, and operational changes.
- ⭐ **Bookmarks (`/bookmarks/`)**: Save important Q&A answers and citations grid.
- 📊 **Analytics (`/analytics/`)**: Usage dashboard tracking query counts, response speed, user feedback %, and document storage.
- 🧪 **RAG Evaluation (`/evaluation/`)**: Benchmark evaluation metrics displaying Precision@K (89%), MRR (0.91), Faithfulness (94%), and Latency.
- 👤 **Profile (`/profile/`)**: User account details and storage quota metrics.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11+, Django 5.1, Django REST Framework (DRF), SQLite / PostgreSQL
- **AI / RAG / NLP**: PyMuPDF (`fitz`), `google-genai` SDK (Gemini), OpenAI SDK (optional), `sentence-transformers` (`all-MiniLM-L6-v2`), `faiss-cpu`, `rank-bm25`
- **Frontend**: HTML5, CSS3, JavaScript (Fetch API), Bootstrap 5, Bootstrap Icons
- **Testing & Deployment**: Pytest, Django Test Client, Docker, Docker Compose

---

## 🚀 Quickstart & Installation

### 1. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/Dhanaraj2410/AI-Powered-Document-IntelligenceRAG-Assistant.git
cd AI-Powered-Document-IntelligenceRAG-Assistant

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create `.env` file in root directory:

```env
SECRET_KEY=django-insecure-dev-secret-key
DEBUG=True
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=150
```

### 4. Run Migrations & Start Server

```bash
python manage.py migrate

python manage.py runserver
```

Open browser at **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.

### 5. Run Tests

```bash
python -m pytest -q
```

The test suite uses `pytest-django` and automatically loads the project's Django settings.

For production configuration and storage considerations, see the [deployment notes](DEPLOYMENT.md).
For a concise component and request-flow overview, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Current processing and deployment notes

Uploads accept PDF, DOCX, PPTX, XLSX, CSV, TXT, and Markdown. The API validates
extensions, configured size, accepted content type, and signatures for PDF and
Office Open XML files. Uploaded files are stored under `data/uploads` and are
not served as public media. Scanned PDF OCR is optional and requires the
Tesseract executable plus the pinned `pytesseract` and Pillow packages.

Ingestion currently runs in a background thread in the web process. The
document API exposes `uploaded`, `processing`, `completed`, or `failed` status;
poll `/api/documents/<id>/` for progress. A process restart can interrupt a job,
so production deployments should replace this lightweight worker with a
durable task queue. FAISS remains the default vector backend. Set
`VECTOR_SERVICE_CLASS` and `EMBEDDING_SERVICE_CLASS` to Python import paths to
provide compatible adapters. `CHUNK_SIZE`, `CHUNK_OVERLAP`, `TOP_K_RETRIEVAL`,
`RERANK_TOP_K`, `RETRIEVAL_SCORE_THRESHOLD`, and `MAX_UPLOAD_SIZE` tune the
pipeline.

Set a random `SECRET_KEY` and `DEBUG=False` for deployment. The application
refuses to start in non-debug mode without a key. See `.env.example` for the
available settings. Keep uploads, FAISS data, and the database on persistent
private storage. `python evaluation/retrieval_evaluation.py` runs the existing
retrieval evaluation against a populated local database; its heuristic
faithfulness/relevance indicators are not model-judged metrics.

`POST /api/export/` downloads an owned assistant message or full conversation
as PDF or DOCX. Pass `message_id` or `conversation_id` and a `format` of `pdf`
or `docx`. The chat UI currently animates the completed response;
provider-token streaming is not yet implemented.

### Troubleshooting startup

- If model loading fails, verify that the embedding dependencies are installed
  and that the configured model can be downloaded in the current environment.
- If requests are rejected by Django, add the browser host to `ALLOWED_HOSTS`.
- If retrieval returns no context, rebuild the local vector artifacts from the
  uploaded documents and confirm that the index dimension matches the embedding
  model.

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/health/` | `GET` | System health check |
| `/api/upload/` | `POST` | Validate upload and start document ingestion |
| `/api/chat/` | `POST` | Query RAG pipeline with natural language questions |
| `/api/search/` | `POST` | Execute standalone Hybrid Search (FAISS + BM25) candidate ranking |
| `/api/compare/` | `POST` | Synthesize side-by-side document comparison report |
| `/api/summary/` | `POST` | Generate multi-mode document summary |
| `/api/bookmarks/` | `GET` / `POST` | Manage saved Q&A bookmarks |
| `/api/feedback/` | `POST` | Submit user ratings (+1 / -1) and comments |
| `/api/export/` | `POST` | Export an owned answer or conversation to PDF or DOCX |

---

## 📊 Automated RAG Benchmark Evaluation

Run the offline evaluation benchmark:

```bash
python evaluation/retrieval_evaluation.py
```

The script measures retrieval against the dataset and indexed target documents
for the first user in the local database. Missing target documents are counted
and reported as skipped. Answer faithfulness and relevance are local lexical
overlap proxies, not model-judged metrics. No benchmark result is claimed here;
results depend on the documents and environment used for a run.

---

## 📄 License

Distributed under the MIT License.
