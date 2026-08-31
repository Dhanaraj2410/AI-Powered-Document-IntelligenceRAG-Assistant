from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class RerankerService:
    @staticmethod
    def rerank_chunks(query: str, retrieved_chunks: List[Dict[str, any]], top_n: int = 4) -> List[Dict[str, any]]:
        """
        Reranks candidate retrieved chunks using keyword density & retrieval score weighting
        to select top_n highest precision context chunks.
        """
        if not retrieved_chunks:
            return []

        query_words = set(query.lower().split())

        for item in retrieved_chunks:
            content_words = item["content"].lower().split()
            word_count = max(len(content_words), 1)

            # Keyword match density score
            match_count = sum(1 for w in query_words if w in content_words)
            density_score = match_count / min(len(query_words), 5)

            # Combined rerank score: 70% original retrieval score + 30% keyword density
            combined_score = (item["retrieval_score"] * 0.7) + (density_score * 0.3)
            item["rerank_score"] = round(combined_score, 4)

        # Sort descending by rerank_score
        retrieved_chunks.sort(key=lambda x: x.get("rerank_score", x["retrieval_score"]), reverse=True)
        return retrieved_chunks[:top_n]
