"""
Keyword Extraction Service — extracts top-N keywords / keyphrases from
document chunks using a lightweight TF-IDF approach without external ML deps.

This supplements the BM25 retrieval by building a human-readable keyword
index per document for faceted search and topic exploration.
"""
import logging
import math
import re
from collections import Counter
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Stop-word list (English)
# ---------------------------------------------------------------------------
_STOP_WORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be
    because been before being below between both but by can't cannot could
    couldn't did didn't do does doesn't doing don't down during each few for
    from further get got had hadn't has hasn't have haven't having he he'd
    he'll he's her here here's hers herself him himself his how how's i i'd
    i'll i'm i've if in into is isn't it it's its itself let's me more most
    mustn't my myself no nor not of off on once only or other ought our ours
    ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them themselves
    then there there's these they they'd they'll they're they've this those
    through to too under until up very was wasn't we we'd we'll we're we've
    were weren't what what's when when's where where's which while who who's
    whom why why's will with won't would wouldn't you you'd you'll you're
    you've your yours yourself yourselves
    """.split()
)


class KeywordExtractionService:
    """Lightweight TF-IDF keyword extractor for RAG document chunks."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @staticmethod
    def extract_keywords(
        texts: List[str],
        top_n: int = 20,
        min_word_len: int = 3,
        ngram_range: Tuple[int, int] = (1, 2),
    ) -> List[Tuple[str, float]]:
        """
        Extract top-N keywords from a corpus of text strings using TF-IDF.

        Args:
            texts: List of text strings (one per chunk or document).
            top_n: Number of keywords to return.
            min_word_len: Minimum character length for a term.
            ngram_range: Tuple (min_n, max_n) for n-gram extraction.

        Returns:
            List of (term, score) tuples sorted by descending TF-IDF score.
        """
        if not texts:
            return []

        # Tokenise each document into n-gram bags
        doc_term_counts: List[Counter] = []
        for text in texts:
            tokens = KeywordExtractionService._tokenise(text, min_word_len, ngram_range)
            doc_term_counts.append(Counter(tokens))

        # Build corpus-wide document-frequency map
        num_docs = len(doc_term_counts)
        doc_freq: Counter = Counter()
        for counter in doc_term_counts:
            doc_freq.update(counter.keys())

        # Aggregate TF-IDF across all documents
        global_scores: Dict[str, float] = {}
        for doc_idx, counter in enumerate(doc_term_counts):
            total_terms = sum(counter.values()) or 1
            for term, tf_count in counter.items():
                tf = tf_count / total_terms
                idf = math.log((num_docs + 1) / (doc_freq[term] + 1)) + 1.0
                global_scores[term] = global_scores.get(term, 0.0) + tf * idf

        ranked = sorted(global_scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_n]

    @staticmethod
    def extract_for_document(document_id: int, top_n: int = 15) -> List[str]:
        """
        Convenience method: load chunk texts for a document from the DB and
        return only the keyword strings.

        Args:
            document_id: Primary key of the Document record.
            top_n: Number of keywords to return.

        Returns:
            List of keyword strings sorted by relevance.
        """
        try:
            from rag_app.models import DocumentChunk
            chunk_texts = list(
                DocumentChunk.objects.filter(document_id=document_id)
                .values_list("content", flat=True)
                .order_by("chunk_index")[:100]
            )
            if not chunk_texts:
                return []
            scored = KeywordExtractionService.extract_keywords(chunk_texts, top_n=top_n)
            return [term for term, _ in scored]
        except Exception as exc:
            logger.error(
                "KeywordExtractionService: failed for doc_id=%s. %s", document_id, exc
            )
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(
        text: str, min_word_len: int, ngram_range: Tuple[int, int]
    ) -> List[str]:
        """Lower-case, remove punctuation and produce n-grams."""
        text = text.lower()
        words = re.findall(r"\b[a-z][a-z'-]*[a-z]\b", text)
        words = [w for w in words if len(w) >= min_word_len and w not in _STOP_WORDS]

        min_n, max_n = ngram_range
        ngrams: List[str] = []
        for n in range(min_n, max_n + 1):
            for i in range(len(words) - n + 1):
                ngrams.append(" ".join(words[i : i + n]))
        return ngrams
