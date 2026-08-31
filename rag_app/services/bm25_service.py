import re
from typing import List, Dict
from rank_bm25 import BM25Okapi
import logging

logger = logging.getLogger(__name__)

class BM25Service:
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Simple lowercase word tokenizer."""
        return re.findall(r'\w+', text.lower())

    @classmethod
    def search_chunks(cls, chunks: List[Dict[str, any]], query: str, top_k: int = 10) -> List[Dict[str, any]]:
        """
        Performs BM25 keyword search over a list of document chunk objects.

        Args:
            chunks: List of dicts or DocumentChunk models containing 'id' and 'content'.
            query: User search question.
            top_k: Max candidate chunks to return.

        Returns:
            List[dict]: [{"chunk": chunk_obj, "bm25_score": float}]
        """
        if not chunks or not query.strip():
            return []

        corpus = [cls._tokenize(c["content"] if isinstance(c, dict) else c.content) for c in chunks]
        bm25 = BM25Okapi(corpus)

        query_tokens = cls._tokenize(query)
        if not query_tokens:
            return []

        scores = bm25.get_scores(query_tokens)

        scored_results = []
        for idx, score in enumerate(scores):
            if score > 0:
                scored_results.append({
                    "chunk": chunks[idx],
                    "bm25_score": float(score)
                })

        # Sort descending by BM25 score
        scored_results.sort(key=lambda x: x["bm25_score"], reverse=True)
        return scored_results[:top_k]
