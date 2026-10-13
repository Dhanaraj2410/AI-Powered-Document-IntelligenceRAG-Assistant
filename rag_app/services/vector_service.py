import faiss
import numpy as np
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class VectorService:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index_dir = getattr(settings, 'VECTOR_STORE_DIR', os.path.join(settings.BASE_DIR, 'data', 'vector_store'))
        self.index_file = os.path.join(self.index_dir, 'index.faiss')

    def _get_or_create_index(self) -> faiss.Index:
        """Loads FAISS index from disk if present, else creates new IndexFlatIP."""
        if os.path.exists(self.index_file):
            try:
                index = faiss.read_index(self.index_file)
                logger.info(f"Loaded existing FAISS index with {index.ntotal} vectors.")
                return index
            except Exception as e:
                logger.error(f"Error reading FAISS index from disk: {str(e)}. Creating new index.")
        
        # IndexFlatIP measures Inner Product (equivalent to Cosine Similarity when vectors are L2-normalized)
        index = faiss.IndexFlatIP(self.dimension)
        logger.info(f"Initialized new FAISS IndexFlatIP of dimension {self.dimension}.")
        return index

    def add_vectors(self, embeddings: np.ndarray, start_vector_id: int = None) -> list:
        """
        Adds normalized embeddings matrix to FAISS index.

        Returns:
            list[int]: Vector IDs assigned in FAISS (0-indexed sequence matching ntotal).
        """
        if embeddings is None or len(embeddings) == 0:
            return []

        if embeddings.ndim != 2 or embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Expected embeddings with shape (N, {self.dimension}); got {embeddings.shape}."
            )

        embeddings = embeddings.astype(np.float32)
        index = self._get_or_create_index()
        current_count = index.ntotal

        index.add(embeddings)
        new_count = index.ntotal

        vector_ids = list(range(current_count, new_count))
        self._save_index(index)

        logger.info(f"Added {len(embeddings)} vectors to FAISS. Index total: {new_count}")
        return vector_ids

    def search_vectors(self, query_vector: np.ndarray, top_k: int = 5) -> list:
        """
        Searches FAISS index for top_k most similar vectors.

        Returns:
            list[dict]: [{"vector_id": int, "retrieval_score": float}]
        """
        if top_k <= 0:
            return []

        if not os.path.exists(self.index_file):
            logger.warning("FAISS index file does not exist yet.")
            return []

        index = self._get_or_create_index()
        if index.ntotal == 0:
            return []

        if query_vector.ndim == 1:
            query_vector = np.expand_dims(query_vector, axis=0)

        if query_vector.ndim != 2 or query_vector.shape != (1, self.dimension):
            raise ValueError(
                f"Expected one query vector with shape (1, {self.dimension}); got {query_vector.shape}."
            )

        query_vector = query_vector.astype(np.float32)
        k_to_search = min(top_k, index.ntotal)

        distances, indices = index.search(query_vector, k_to_search)

        results = []
        for idx, score in zip(indices[0], distances[0]):
            if idx != -1:
                results.append({
                    "vector_id": int(idx),
                    "retrieval_score": round(float(score), 4)
                })

        return results

    def _save_index(self, index: faiss.Index):
        """Persists FAISS index to disk."""
        try:
            os.makedirs(self.index_dir, exist_ok=True)
            faiss.write_index(index, self.index_file)
            logger.info(f"Saved FAISS index ({index.ntotal} vectors) to {self.index_file}")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {str(e)}", exc_info=True)
