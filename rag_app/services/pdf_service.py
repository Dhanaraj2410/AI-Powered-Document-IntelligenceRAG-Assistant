import fitz  # PyMuPDF
import os
import logging

logger = logging.getLogger(__name__)

class PDFService:
    @staticmethod
    def extract_text_from_pdf(file_path: str, doc_title: str = "") -> dict:
        """
        Extracts structured text page-by-page from a PDF file using PyMuPDF.

        Returns:
            dict: {
                "success": bool,
                "pages": [{"page": int, "text": str}],
                "page_count": int,
                "file_size": int,
                "error": str
            }
        """
        if not os.path.exists(file_path):
            return {
                "success": False,
                "pages": [],
                "page_count": 0,
                "file_size": 0,
                "error": f"File not found: {file_path}"
            }

        file_size = os.path.getsize(file_path)

        try:
            doc = fitz.open(file_path)
            pages_data = []

            for page_idx in range(len(doc)):
                page = doc[page_idx]
                page_text = page.get_text("text") or ""
                pages_data.append({
                    "page": page_idx + 1,
                    "text": page_text
                })

            doc.close()

            # Check if any readable text was extracted
            total_text_len = sum(len(p["text"].strip()) for p in pages_data)
            if total_text_len == 0:
                logger.warning(f"No readable text extracted from {file_path}. Document may be scanned/image-only.")

            return {
                "success": True,
                "pages": pages_data,
                "page_count": len(pages_data),
                "file_size": file_size,
                "error": ""
            }

        except Exception as e:
            logger.error(f"Failed to extract PDF text from {file_path}: {str(e)}", exc_info=True)
            return {
                "success": False,
                "pages": [],
                "page_count": 0,
                "file_size": file_size,
                "error": f"PDF Extraction Error: {str(e)}"
            }
