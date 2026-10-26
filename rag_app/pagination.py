"""
Pagination utility helpers for RAG API list responses.

Provides a consistent, metadata-enriched pagination wrapper that works with
Django REST Framework's PageNumberPagination responses.
"""
from typing import Any, Dict, List, Optional


def paginate_queryset(
    items: List[Any],
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Paginate an in-memory list of items and return enriched metadata.

    Args:
        items: Full list of items to paginate.
        page: 1-based page number (default 1).
        page_size: Number of items per page (default 20).

    Returns:
        dict with keys:
          - results   (list)  : Items on the current page.
          - page      (int)   : Current page number.
          - page_size (int)   : Items per page.
          - total     (int)   : Total number of items.
          - pages     (int)   : Total number of pages.
          - has_next  (bool)  : Whether a next page exists.
          - has_prev  (bool)  : Whether a previous page exists.
          - next_page (int|None): Next page number or None.
          - prev_page (int|None): Previous page number or None.

    Raises:
        ValueError: If *page* < 1 or *page_size* < 1.
    """
    if page < 1:
        raise ValueError(f"page must be >= 1, got {page!r}")
    if page_size < 1:
        raise ValueError(f"page_size must be >= 1, got {page_size!r}")

    total = len(items)
    pages = max(1, -(-total // page_size))  # ceiling division

    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    has_next = page < pages
    has_prev = page > 1

    return {
        "results": page_items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": pages,
        "has_next": has_next,
        "has_prev": has_prev,
        "next_page": page + 1 if has_next else None,
        "prev_page": page - 1 if has_prev else None,
    }


def extract_page_params(request, default_page_size: int = 20) -> Dict[str, int]:
    """
    Parse ``page`` and ``page_size`` query parameters from a Django request.

    Falls back to defaults if parameters are missing or invalid.

    Args:
        request: Django HTTP request object.
        default_page_size: Default page size if not supplied.

    Returns:
        dict with integer keys ``page`` and ``page_size``.
    """
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        page_size = min(100, max(1, int(request.GET.get("page_size", default_page_size))))
    except (ValueError, TypeError):
        page_size = default_page_size

    return {"page": page, "page_size": page_size}
