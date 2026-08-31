from django.test import TestCase
from rag_app.services.pdf_service import PDFService
from rag_app.services.cleaner_service import CleanerService

class PDFServiceTestCase(TestCase):
    def test_cleaner_service_whitespace(self):
        raw_text = "Revenue       increased\n\n\n significantly   "
        cleaned = CleanerService.clean_text(raw_text)
        self.assertNotIn("   ", cleaned)
        self.assertNotIn("\n\n\n", cleaned)
        self.assertIn("Revenue increased", cleaned)

    def test_nonexistent_pdf_handling(self):
        res = PDFService.extract_text_from_pdf("nonexistent_file.pdf")
        self.assertFalse(res["success"])
        self.assertIn("File not found", res["error"])
