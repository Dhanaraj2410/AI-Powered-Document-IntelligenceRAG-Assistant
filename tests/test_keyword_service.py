"""
Pytest tests for the KeywordExtractionService.
"""
import pytest

from rag_app.services.keyword_service import KeywordExtractionService


class TestKeywordExtractionService:
    def test_extracts_keywords_from_single_document(self):
        texts = [
            "Machine learning models are trained on large datasets to recognise patterns."
        ]
        keywords = KeywordExtractionService.extract_keywords(texts, top_n=5)
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        # Each item should be a (str, float) tuple
        for term, score in keywords:
            assert isinstance(term, str)
            assert isinstance(score, float)

    def test_returns_empty_list_for_no_texts(self):
        result = KeywordExtractionService.extract_keywords([], top_n=10)
        assert result == []

    def test_bigrams_are_included_when_ngram_range_allows(self):
        texts = ["natural language processing is a subfield of artificial intelligence."]
        keywords = KeywordExtractionService.extract_keywords(
            texts, top_n=20, ngram_range=(1, 2)
        )
        terms = [t for t, _ in keywords]
        # At least one bigram should appear
        assert any(" " in t for t in terms)

    def test_stop_words_are_excluded(self):
        texts = ["the quick brown fox jumps over the lazy dog and the cat"]
        keywords = KeywordExtractionService.extract_keywords(texts, top_n=10)
        terms = [t for t, _ in keywords]
        stop_words = {"the", "and", "over"}
        for sw in stop_words:
            assert sw not in terms

    def test_min_word_len_filters_short_tokens(self):
        texts = ["AI is a broad and growing field with many sub-domains and challenges."]
        keywords = KeywordExtractionService.extract_keywords(
            texts, top_n=20, min_word_len=5
        )
        terms = [t for t, _ in keywords]
        for term in terms:
            # For unigrams every word must meet the minimum length
            first_word = term.split()[0]
            assert len(first_word) >= 5

    def test_scores_are_positive(self):
        texts = ["Data science and machine learning are powerful tools."]
        keywords = KeywordExtractionService.extract_keywords(texts, top_n=5)
        for _, score in keywords:
            assert score > 0

    def test_top_n_limit_respected(self):
        texts = ["word " * 100]
        keywords = KeywordExtractionService.extract_keywords(texts, top_n=3)
        assert len(keywords) <= 3

    def test_multi_document_idf_penalises_common_terms(self):
        """A term that appears in all docs should have a lower TF-IDF score."""
        texts = [
            "document analysis is important for research",
            "document retrieval is a core task in information retrieval",
            "document processing helps extract key information from texts",
        ]
        keywords = KeywordExtractionService.extract_keywords(texts, top_n=15)
        terms = [t for t, _ in keywords]
        # "document" appears in all docs; it should not be the top-ranked unigram
        if terms:
            assert terms[0] != "document"
