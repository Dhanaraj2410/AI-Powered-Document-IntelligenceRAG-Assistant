from unittest.mock import patch

from django.test import SimpleTestCase

from rag_app.services.hybrid_retriever_service import HybridRetrieverService


class HybridRetrieverServiceTestCase(SimpleTestCase):
    def test_chunk_indexing_falls_back_when_embeddings_are_unavailable(self):
        class BrokenEmbeddingService:
            @staticmethod
            def generate_embeddings(texts):
                raise RuntimeError('embedding model unavailable')

        with patch.object(
            HybridRetrieverService,
            '_embedding_service',
            return_value=BrokenEmbeddingService,
        ):
            vector_ids = HybridRetrieverService().add_document_chunks(
                texts=['first chunk', 'second chunk'],
                metadatas=[{}, {}],
                user_id=1,
                document_id=1,
            )

        self.assertEqual(vector_ids, [-1, -2])
