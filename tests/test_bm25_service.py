from django.test import SimpleTestCase

from rag_app.services.bm25_service import BM25Service


class BM25ServiceTestCase(SimpleTestCase):
    def test_non_positive_limit_returns_no_results(self):
        chunks = [{"content": "annual revenue report"}]
        self.assertEqual(BM25Service.search_chunks(chunks, "revenue", top_k=0), [])

