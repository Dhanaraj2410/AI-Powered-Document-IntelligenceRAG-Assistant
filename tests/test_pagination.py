"""
Pytest tests for the pagination utility helpers.
"""
import pytest
from unittest.mock import MagicMock

from rag_app.pagination import paginate_queryset, extract_page_params


class TestPaginateQueryset:
    def test_first_page_returns_correct_slice(self):
        items = list(range(50))
        result = paginate_queryset(items, page=1, page_size=10)
        assert result["results"] == list(range(10))

    def test_second_page_offset(self):
        items = list(range(50))
        result = paginate_queryset(items, page=2, page_size=10)
        assert result["results"] == list(range(10, 20))

    def test_last_partial_page(self):
        items = list(range(25))
        result = paginate_queryset(items, page=3, page_size=10)
        assert result["results"] == [20, 21, 22, 23, 24]

    def test_total_matches_input_length(self):
        items = list(range(73))
        result = paginate_queryset(items, page=1, page_size=10)
        assert result["total"] == 73

    def test_pages_count_is_ceiling(self):
        result = paginate_queryset(list(range(21)), page=1, page_size=10)
        assert result["pages"] == 3

    def test_has_next_false_on_last_page(self):
        result = paginate_queryset(list(range(10)), page=1, page_size=10)
        assert result["has_next"] is False

    def test_has_next_true_when_more_pages(self):
        result = paginate_queryset(list(range(20)), page=1, page_size=10)
        assert result["has_next"] is True

    def test_has_prev_false_on_first_page(self):
        result = paginate_queryset(list(range(20)), page=1, page_size=10)
        assert result["has_prev"] is False

    def test_has_prev_true_on_second_page(self):
        result = paginate_queryset(list(range(20)), page=2, page_size=10)
        assert result["has_prev"] is True

    def test_next_page_none_on_last(self):
        result = paginate_queryset(list(range(10)), page=1, page_size=10)
        assert result["next_page"] is None

    def test_prev_page_none_on_first(self):
        result = paginate_queryset(list(range(10)), page=1, page_size=10)
        assert result["prev_page"] is None

    def test_prev_page_correct_value(self):
        result = paginate_queryset(list(range(30)), page=3, page_size=10)
        assert result["prev_page"] == 2

    def test_next_page_correct_value(self):
        result = paginate_queryset(list(range(30)), page=1, page_size=10)
        assert result["next_page"] == 2

    def test_empty_list_returns_empty_results(self):
        result = paginate_queryset([], page=1, page_size=10)
        assert result["results"] == []
        assert result["total"] == 0
        assert result["pages"] == 1

    def test_invalid_page_raises(self):
        with pytest.raises(ValueError):
            paginate_queryset([], page=0)

    def test_invalid_page_size_raises(self):
        with pytest.raises(ValueError):
            paginate_queryset([], page_size=0)


class TestExtractPageParams:
    def _make_request(self, params: dict):
        request = MagicMock()
        request.GET = params
        return request

    def test_defaults_when_no_params(self):
        req = self._make_request({})
        params = extract_page_params(req)
        assert params["page"] == 1
        assert params["page_size"] == 20

    def test_parses_page_and_page_size(self):
        req = self._make_request({"page": "3", "page_size": "15"})
        params = extract_page_params(req)
        assert params["page"] == 3
        assert params["page_size"] == 15

    def test_page_size_capped_at_100(self):
        req = self._make_request({"page_size": "500"})
        params = extract_page_params(req)
        assert params["page_size"] == 100

    def test_invalid_page_falls_back_to_1(self):
        req = self._make_request({"page": "abc"})
        params = extract_page_params(req)
        assert params["page"] == 1

    def test_negative_page_clamped_to_1(self):
        req = self._make_request({"page": "-5"})
        params = extract_page_params(req)
        assert params["page"] == 1
