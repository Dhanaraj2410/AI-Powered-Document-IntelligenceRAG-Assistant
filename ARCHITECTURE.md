# Architecture overview

The application is split into three layers:

1. Django views and DRF endpoints handle authentication, ownership checks, and
   request validation.
2. `rag_app/services/` contains extraction, cleaning, chunking, embedding,
   hybrid retrieval, reranking, prompting, and response grounding.
3. SQLite or PostgreSQL stores application metadata while FAISS, BM25, and the
   generated metadata files support retrieval over uploaded documents.

## Request path

An uploaded PDF is extracted page by page, normalized, chunked, embedded, and
indexed. A chat request expands conversational context, retrieves candidates
from dense and lexical indexes, reranks them, and sends only grounded context
to the configured LLM provider. The response includes citations and timing
metadata for inspection.

## Operational boundary

The checked-in sample index is useful for local demonstrations. Production
deployments should use persistent storage for uploaded documents and generated
indexes, plus a backup and rebuild procedure for both the database and vector
artifacts.
