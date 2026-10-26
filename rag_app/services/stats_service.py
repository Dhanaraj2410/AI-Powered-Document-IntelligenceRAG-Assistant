"""
Document statistics utility — computes per-document metrics from stored chunks.

Provides readability scores (Flesch-Kincaid), word/sentence counts, average
chunk length, and vocabulary richness — all without external ML dependencies.
"""
import logging
import math
import re
from typing import Dict, List

logger = logging.getLogger(__name__)


class DocumentStatsService:
    """
    Computes lightweight text statistics for a processed document.

    All methods are static; no instantiation is required.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def compute_stats(document_id: int) -> Dict:
        """
        Load all chunks for a document and return a statistics dict.

        Args:
            document_id: Primary key of the Document model record.

        Returns:
            dict with keys:
              - word_count (int)
              - sentence_count (int)
              - avg_words_per_sentence (float)
              - avg_chunk_length_chars (float)
              - chunk_count (int)
              - vocabulary_size (int)
              - type_token_ratio (float)   # vocabulary richness 0-1
              - flesch_reading_ease (float)
              - syllable_count (int)
        """
        try:
            from rag_app.models import DocumentChunk
            chunks = list(
                DocumentChunk.objects.filter(document_id=document_id)
                .values_list("content", flat=True)
            )
        except Exception as exc:
            logger.error("DocumentStatsService: DB error for doc %s. %s", document_id, exc)
            return {"error": str(exc)}

        if not chunks:
            return {"error": "No chunks found for document."}

        full_text = " ".join(chunks)
        return DocumentStatsService.compute_stats_from_text(full_text, chunk_count=len(chunks))

    @staticmethod
    def compute_stats_from_text(text: str, chunk_count: int = 1) -> Dict:
        """
        Compute statistics directly from a text string.

        Args:
            text: The combined document text.
            chunk_count: Number of chunks the text was split into.

        Returns:
            Dict of computed metrics.
        """
        words = DocumentStatsService._tokenise_words(text)
        sentences = DocumentStatsService._split_sentences(text)

        word_count = len(words)
        sentence_count = max(len(sentences), 1)
        syllable_count = sum(DocumentStatsService._count_syllables(w) for w in words)

        vocab = set(w.lower() for w in words)
        vocabulary_size = len(vocab)
        ttr = vocabulary_size / word_count if word_count else 0.0

        avg_words_per_sentence = word_count / sentence_count
        avg_chunk_length_chars = len(text) / chunk_count if chunk_count else 0.0

        fre = DocumentStatsService._flesch_reading_ease(
            word_count, sentence_count, syllable_count
        )

        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 2),
            "avg_chunk_length_chars": round(avg_chunk_length_chars, 1),
            "chunk_count": chunk_count,
            "vocabulary_size": vocabulary_size,
            "type_token_ratio": round(ttr, 4),
            "flesch_reading_ease": round(fre, 2),
            "syllable_count": syllable_count,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise_words(text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z']+\b", text)

    @staticmethod
    def _split_sentences(text: str) -> List[str]:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in sentences if s.strip()]

    @staticmethod
    def _count_syllables(word: str) -> int:
        """Approximate syllable count using vowel-group heuristic."""
        word = word.lower().strip("'")
        if not word:
            return 0
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for ch in word:
            is_vowel = ch in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        # Silent trailing 'e'
        if word.endswith("e") and count > 1:
            count -= 1
        return max(1, count)

    @staticmethod
    def _flesch_reading_ease(
        word_count: int, sentence_count: int, syllable_count: int
    ) -> float:
        """
        Flesch Reading Ease formula.
        Score 90–100 = very easy; 0–30 = very difficult.
        """
        if word_count == 0 or sentence_count == 0:
            return 0.0
        asl = word_count / sentence_count          # avg sentence length
        asw = syllable_count / word_count          # avg syllables per word
        score = 206.835 - 1.015 * asl - 84.6 * asw
        return max(0.0, min(100.0, score))
