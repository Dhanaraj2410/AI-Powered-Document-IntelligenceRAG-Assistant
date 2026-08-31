import numpy as np
from django.test import TestCase
from rag_app.services.embedding_service import EmbeddingService
from rag_app.services.vector_service import VectorService

class VectorEmbeddingTestCase(TestCase):
    def test_embedding_generation_shape(self):
        texts = ["What was the company revenue in 2025?", "The company reported 500 crore revenue."]
        embeddings = EmbeddingService.generate_embeddings(texts)
        self.assertEqual(embeddings.shape, (2, 384))
        self.assertEqual(embeddings.dtype, np.float32)

    def test_vector_service_add_and_search(self):
        texts = ["Artificial intelligence and machine learning.", "Financial annual balance sheet report."]
        embeddings = EmbeddingService.generate_embeddings(texts)

        vector_service = VectorService()
        v_ids = vector_service.add_vectors(embeddings)
        self.assertEqual(len(v_ids), 2)

        query_vec = EmbeddingService.generate_single_embedding("machine learning")
        search_results = vector_service.search_vectors(query_vec, top_k=2)

        self.assertGreater(len(search_results), 0)
        self.assertIn('retrieval_score', search_results[0])
