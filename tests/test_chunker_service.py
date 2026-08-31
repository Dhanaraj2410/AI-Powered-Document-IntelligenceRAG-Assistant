from django.test import TestCase
from rag_app.services.chunker_service import ChunkerService

class ChunkerServiceTestCase(TestCase):
    def setUp(self):
        self.chunker = ChunkerService(chunk_size=100, chunk_overlap=20)

    def test_chunker_preserves_page_numbers(self):
        pages = [
            {"page": 1, "text": "This is page one text content. " * 5},
            {"page": 2, "text": "This is page two text content. " * 5}
        ]
        chunks = self.chunker.create_chunks_from_pages(pages)
        self.assertGreater(len(chunks), 0)
        
        page1_chunks = [c for c in chunks if c["page_number"] == 1]
        page2_chunks = [c for c in chunks if c["page_number"] == 2]

        self.assertTrue(len(page1_chunks) > 0)
        self.assertTrue(len(page2_chunks) > 0)

    def test_chunker_empty_pages(self):
        pages = [{"page": 1, "text": ""}]
        chunks = self.chunker.create_chunks_from_pages(pages)
        self.assertEqual(len(chunks), 0)
