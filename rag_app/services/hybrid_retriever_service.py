from typing import List, Dict, Optional
import logging
from rag_app.models import DocumentChunk
from django.conf import settings
from django.utils.module_loading import import_string
from .embedding_service import EmbeddingService
from .vector_service import VectorService
from .bm25_service import BM25Service

logger = logging.getLogger(__name__)

class HybridRetrieverService:
    def __init__(self):
        vector_class = import_string(getattr(settings, 'VECTOR_SERVICE_CLASS', 'rag_app.services.vector_service.VectorService'))
        self.vector_service = vector_class()

    def add_document_chunks(
        self,
        texts: List[str],
        metadatas: List[Dict[str, any]],
        user_id: int,
        document_id: int,
    ) -> List[int]:
        """Index document chunks and return stable vector IDs.

        Metadata is stored with the database chunk records by the caller. If
        the optional embedding model is unavailable, negative IDs keep the
        chunks persistable while retrieval safely falls back to BM25.
        """
        if not texts:
            return []
        try:
            embeddings = self._embedding_service().generate_embeddings(texts)
            return self.vector_service.add_vectors(embeddings)
        except Exception:
            logger.warning(
                "Could not create semantic vectors for document %s; using BM25-only retrieval.",
                document_id,
                exc_info=True,
            )
            return list(range(-1, -len(texts) - 1, -1))

    @staticmethod
    def _embedding_service():
        return import_string(getattr(settings, 'EMBEDDING_SERVICE_CLASS', 'rag_app.services.embedding_service.EmbeddingService'))

    def retrieve_relevant_chunks(
        self,
        query: str,
        user_id: int,
        document_id: Optional[int] = None,
        collection_id: Optional[int] = None,
        top_k: int = None
    ) -> List[Dict[str, any]]:
        """
        Performs Hybrid Search (FAISS Semantic Vector Search + BM25 Keyword Search)
        with strict multi-tenant user document security filtering.

        Returns:
            List[dict]: [{
                "chunk_id": int,
                "document_id": int,
                "document_title": str,
                "page_number": int,
                "content": str,
                "retrieval_score": float
            }]
        """
        top_k = top_k or getattr(settings, 'TOP_K_RETRIEVAL', 5)
        if top_k < 1:
            return []
        # 1. Base queryset filtered strictly by user and document/collection
        chunk_qs = DocumentChunk.objects.select_related('document').filter(document__user_id=user_id)

        if document_id:
            chunk_qs = chunk_qs.filter(document_id=document_id)
        elif collection_id:
            chunk_qs = chunk_qs.filter(document__collection_id=collection_id)

        user_chunks = list(chunk_qs)
        if not user_chunks:
            logger.warning(f"No document chunks found for user_id={user_id}, doc_id={document_id}, coll_id={collection_id}")
            return []

        # 2. FAISS Semantic Search.  Embeddings are an enhancement, not a
        # prerequisite for chat: BM25 below can still answer when the model
        # is unavailable (for example during a first local run without a
        # downloaded model or when the vector index is stale).
        semantic_chunks = []
        try:
            query_vector = self._embedding_service().generate_single_embedding(query)
            faiss_results = self.vector_service.search_vectors(query_vector, top_k=top_k * 3)

            # Map vector_ids to authorized DocumentChunk models
            faiss_vector_map = {r["vector_id"]: r["retrieval_score"] for r in faiss_results}
            for chunk in user_chunks:
                if chunk.vector_id in faiss_vector_map:
                    semantic_chunks.append({
                        "chunk": chunk,
                        "score": faiss_vector_map[chunk.vector_id]
                    })

            semantic_chunks.sort(key=lambda x: x["score"], reverse=True)
        except Exception:
            logger.warning("Semantic retrieval unavailable; continuing with BM25.", exc_info=True)

        # 3. BM25 Keyword Search
        chunk_dicts = [{"id": c.id, "content": c.content, "obj": c} for c in user_chunks]
        bm25_results = BM25Service.search_chunks(chunk_dicts, query, top_k=top_k * 3)

        # 4. Reciprocal Rank Fusion (RRF)
        # RRF Score = 1 / (60 + rank_faiss) + 1 / (60 + rank_bm25)
        rrf_map = {}

        for rank, item in enumerate(semantic_chunks[:top_k * 2]):
            chunk_obj = item["chunk"]
            rrf_map[chunk_obj.id] = rrf_map.get(chunk_obj.id, 0.0) + (1.0 / (60.0 + rank + 1))

        for rank, item in enumerate(bm25_results[:top_k * 2]):
            chunk_obj = item["chunk"]["obj"]
            rrf_map[chunk_obj.id] = rrf_map.get(chunk_obj.id, 0.0) + (1.0 / (60.0 + rank + 1))

        # 5. Build final sorted results list
        chunk_id_map = {c.id: c for c in user_chunks}
        fused_candidates = []

        for cid, rrf_score in rrf_map.items():
            if cid in chunk_id_map:
                c = chunk_id_map[cid]
                # Normalize RRF score to 0.0 - 1.0 range for UI score display
                normalized_score = min(round(rrf_score * 30.0, 3), 0.99)
                fused_candidates.append({
                    "chunk": c,
                    "score": normalized_score
                })

        # Fallback to pure semantic search if RRF returned no overlap
        if not fused_candidates and semantic_chunks:
            for item in semantic_chunks[:top_k]:
                fused_candidates.append({
                    "chunk": item["chunk"],
                    "score": round(float(item["score"]), 3)
                })

        fused_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = fused_candidates[:top_k * 2]

        final_results = []
        for item in top_candidates:
            c = item["chunk"]
            final_results.append({
                "chunk_id": c.id,
                "document_id": c.document.id,
                "document_title": c.document.title,
                "page_number": c.page_number,
                "section": c.section,
                "content": c.content,
                "retrieval_score": item["score"]
            })

        threshold = getattr(settings, 'RETRIEVAL_SCORE_THRESHOLD', 0.0)
        return [result for result in final_results if result['retrieval_score'] >= threshold]
