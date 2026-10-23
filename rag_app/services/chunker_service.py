from typing import List, Dict
import re
from django.conf import settings
from .cleaner_service import CleanerService

class ChunkerService:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = getattr(settings, 'CHUNK_SIZE', 1000) if chunk_size is None else chunk_size
        self.chunk_overlap = getattr(settings, 'CHUNK_OVERLAP', 150) if chunk_overlap is None else chunk_overlap
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

            for chunk_text, section in page_chunks:
                if len(chunk_text.strip()) > 10:  # Ignore tiny noise chunks
                    chunks.append({
                        "chunk_index": global_chunk_idx,
                        "page_number": page_num,
                        "section": section,
                        "content": chunk_text.strip()
                    })
                    global_chunk_idx += 1

        return chunks

    def _split_text(self, text: str) -> List[tuple]:
        """Split on headings and paragraph boundaries, with bounded overlap."""
        lines = text.splitlines()
        sections, current_heading, body = [], "", []
        heading_re = re.compile(r"^(?:#{1,6}\s+|\d+(?:\.\d+)*[.)]?\s+|[A-Z][A-Z\d &,:()/-]{2,}$)")
        for line in lines:
            line = line.strip()
            if not line:
                if body:
                    sections.append((current_heading, " ".join(body)))
                    body = []
                continue
            if heading_re.match(line) and len(line) < 180:
                if body:
                    sections.append((current_heading, " ".join(body)))
                    body = []
                current_heading = line.lstrip('#').strip()
            else:
                body.append(line)
        if body:
            sections.append((current_heading, " ".join(body)))

        chunks = []
        carry = ""
        for heading, paragraph in sections or [("", text)]:
            prefix = f"{heading}\n" if heading else ""
            text_to_split = (carry + " " + paragraph).strip() if carry else paragraph
            if len(text_to_split) <= self.chunk_size:
                chunks.append((prefix + text_to_split, heading))
                carry = text_to_split[-self.chunk_overlap:] if self.chunk_overlap else ""
                continue
            start = 0
            while start < len(text_to_split):
                end = min(start + self.chunk_size, len(text_to_split))
                if end < len(text_to_split):
                    boundary = text_to_split.rfind(" ", start + self.chunk_size // 2, end)
                    if boundary > start:
                        end = boundary
                value = text_to_split[start:end].strip()
                if value:
                    chunks.append((prefix + value, heading))
                start = max(start + 1, end - self.chunk_overlap)
            carry = ""
        return chunks
