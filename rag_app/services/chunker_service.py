from typing import List, Dict
from django.conf import settings
from .cleaner_service import CleanerService

class ChunkerService:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or getattr(settings, 'CHUNK_SIZE', 1000)
        self.chunk_overlap = chunk_overlap or getattr(settings, 'CHUNK_OVERLAP', 150)
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0 or self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be between 0 and chunk_size - 1")

    def create_chunks_from_pages(self, pages: List[Dict[str, any]]) -> List[Dict[str, any]]:
        """
        Takes list of page dicts [{"page": 1, "text": "..."}] and splits them into
        overlapping text chunks while preserving page number tracking.

        Returns:
            List[dict]: [{"chunk_index": int, "page_number": int, "content": str}]
        """
        chunks = []
        global_chunk_idx = 0

        for page_info in pages:
            page_num = page_info["page"]
            raw_text = page_info["text"]
            cleaned_text = CleanerService.clean_text(raw_text)

            if not cleaned_text:
                continue

            page_chunks = self._split_text(cleaned_text)

            for chunk_text in page_chunks:
                if len(chunk_text.strip()) > 10:  # Ignore tiny noise chunks
                    chunks.append({
                        "chunk_index": global_chunk_idx,
                        "page_number": page_num,
                        "content": chunk_text.strip()
                    })
                    global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str) -> List[str]:
        """Sliding window text chunker with overlap."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + self.chunk_size, text_length)

            # Try to break at a paragraph or sentence boundary if possible
            if end < text_length:
                last_newline = text.rfind('\n', start, end)
                if last_newline != -1 and last_newline > start + (self.chunk_size // 2):
                    end = last_newline + 1
                else:
                    last_period = text.rfind('. ', start, end)
                    if last_period != -1 and last_period > start + (self.chunk_size // 2):
                        end = last_period + 1

            chunk_content = text[start:end]
            chunks.append(chunk_content)

            # Slide window forward by (chunk_size - overlap)
            step = end - start - self.chunk_overlap
            if step <= 0:
                step = self.chunk_size // 2

            start += step

        return chunks
