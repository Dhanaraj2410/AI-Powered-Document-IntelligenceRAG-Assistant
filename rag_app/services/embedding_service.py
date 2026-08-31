import numpy as np
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    _model_instance = None

    @classmethod
    def get_model(cls):
        """Lazy loads SentenceTransformer model instance."""
        if cls._model_instance is None:
            model_name = getattr(settings, 'EMBEDDING_MODEL_NAME', 'all-MiniLM-L6-v2')
            logger.info(f"Loading SentenceTransformer embedding model: {model_name}")
            try:
                from sentence_transformers import SentenceTransformer
                cls._model_instance = SentenceTransformer(model_name)
                logger.info(f"Successfully loaded embedding model: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load SentenceTransformer model '{model_name}': {str(e)}", exc_info=True)
                raise e
        return cls._model_instance

    @classmethod
    def generate_embeddings(cls, texts: list) -> np.ndarray:
        """
        Generates normalized 384-dimensional float32 embeddings for a list of strings.

        Returns:
            np.ndarray: Matrix of shape (N, dim) normalized with L2 norm for cosine search.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        model = cls.get_model()
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

        # Convert to float32 for FAISS compatibility
        embeddings = embeddings.astype(np.float32)

        # L2 normalize vectors for Inner Product / Cosine Similarity compatibility
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1e-10
        normalized_embeddings = embeddings / norms

        return normalized_embeddings

    @classmethod
    def generate_single_embedding(cls, text: str) -> np.ndarray:
        """Generates single query vector normalized for search."""
        return cls.generate_embeddings([text])[0]
