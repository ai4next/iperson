"""Tests for pagination utility."""

from app.core.pagination import paginated_response


class TestPaginatedResponse:
    def test_empty(self):
        result = paginated_response([], total=0, page=1, page_size=20)
        assert result["items"] == []
        assert result["total"] == 0
        assert result["pages"] == 1

    def test_single_page(self):
        items = [{"id": i} for i in range(5)]
        result = paginated_response(items, total=5, page=1, page_size=20)
        assert result["pages"] == 1
        assert len(result["items"]) == 5

    def test_multi_page(self):
        result = paginated_response([], total=50, page=1, page_size=20)
        assert result["pages"] == 3
        assert result["page_size"] == 20

    def test_exact_boundary(self):
        result = paginated_response([], total=40, page=1, page_size=20)
        assert result["pages"] == 2

    def test_rounding(self):
        result = paginated_response([], total=41, page=1, page_size=20)
        assert result["pages"] == 3