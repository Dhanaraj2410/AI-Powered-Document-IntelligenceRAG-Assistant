import logging
import time
from typing import Optional, List, Dict, Any
from .hybrid_retriever_service import HybridRetrieverService
from .reranker_service import RerankerService

logger = logging.getLogger(__name__)

class SearchService:
    @staticmethod
    def execute_search(
        query: str,
        user_id: int,
        document_id: Optional[int] = None,
        collection_id: Optional[int] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes standalone Hybrid Search (FAISS + BM25) and Cross-Encoder Reranking
        for live inspection of vector candidate rankings.
        """
        t_start = time.time()
        retriever = HybridRetrieverService()

        # 1. Hybrid Search (FAISS + BM25)
        candidates = retriever.retrieve_relevant_chunks(
            query=query,
            user_id=user_id,
            document_id=document_id,
            collection_id=collection_id,
            top_k=top_k * 2
        )

        # 2. Cross-Encoder Rerank
        reranked = RerankerService.rerank_chunks(query, candidates, top_n=top_k)

        t_end = time.time()
        latency_ms = int((t_end - t_start) * 1000)

        results_data = []
        for rank_idx, item in enumerate(reranked, 1):
            results_data.append({
                "rank": rank_idx,
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "document_title": item["document_title"],
                "page_number": item["page_number"],
                "retrieval_score": item["retrieval_score"],
                "content": item["content"]
            })

        return {
            "success": True,
            "query": query,
            "result_count": len(results_data),
            "latency_ms": latency_ms,
            "results": results_data
        }
