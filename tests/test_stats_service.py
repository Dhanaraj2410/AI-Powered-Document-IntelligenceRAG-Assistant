"""
Pytest tests for DocumentStatsService.
"""
import pytest

from rag_app.services.stats_service import DocumentStatsService


SIMPLE_TEXT = (
    "Artificial intelligence is transforming many industries. "
    "Machine learning algorithms process large amounts of data. "
    "Natural language processing enables computers to understand human speech."
)

EMPTY_TEXT = ""


class TestDocumentStatsFromText:
    def test_word_count_is_positive(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        assert stats["word_count"] > 0

    def test_sentence_count_is_correct(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        # SIMPLE_TEXT has 3 sentences
        assert stats["sentence_count"] == 3

    def test_vocabulary_size_is_less_than_word_count(self):
        text = "the cat sat on the mat and the cat sat"
        stats = DocumentStatsService.compute_stats_from_text(text)
        assert stats["vocabulary_size"] <= stats["word_count"]

    def test_type_token_ratio_between_zero_and_one(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        assert 0.0 <= stats["type_token_ratio"] <= 1.0

    def test_flesch_score_in_valid_range(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        assert 0.0 <= stats["flesch_reading_ease"] <= 100.0

    def test_avg_words_per_sentence_positive(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        assert stats["avg_words_per_sentence"] > 0

    def test_chunk_count_reflected_in_stats(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT, chunk_count=5)
        assert stats["chunk_count"] == 5

    def test_empty_text_returns_zero_word_count(self):
        stats = DocumentStatsService.compute_stats_from_text(EMPTY_TEXT)
        assert stats["word_count"] == 0

    def test_syllable_count_positive_for_normal_text(self):
        stats = DocumentStatsService.compute_stats_from_text(SIMPLE_TEXT)
        assert stats["syllable_count"] > 0


class TestSyllableCounter:
    @pytest.mark.parametrize("word,expected_min", [
        ("a", 1),
        ("beautiful", 3),
        ("the", 1),
        ("algorithm", 4),
        ("AI", 1),
    ])
    def test_syllable_counts(self, word, expected_min):
        count = DocumentStatsService._count_syllables(word)
        assert count >= expected_min

    def test_empty_string_returns_zero(self):
        assert DocumentStatsService._count_syllables("") == 0


class TestFleschScore:
    def test_simple_text_scores_higher_than_complex(self):
        simple = DocumentStatsService.compute_stats_from_text(
            "The cat sat on the mat. Dogs run fast."
        )
        complex_ = DocumentStatsService.compute_stats_from_text(
            "Multidimensional epistemological frameworks necessitate sophisticated theoretical constructs. "
            "Computational phenomenological investigations require unprecedented methodological innovations."
        )
        assert simple["flesch_reading_ease"] > complex_["flesch_reading_ease"]
