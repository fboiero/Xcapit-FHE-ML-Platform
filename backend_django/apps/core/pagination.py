"""
Pagination classes for Xcapit FHE-ML Platform.

Provides standardized pagination with consistent response format
and configurable page sizes.
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Any

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """
    Standard pagination with consistent response format.

    Features:
    - Configurable page size via query parameter
    - Maximum page size limit
    - Rich metadata including total counts and navigation
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200
    page_query_param = "page"

    def get_paginated_response(self, data: list[Any]) -> Response:
        """
        Return paginated response with metadata.

        Response format:
        {
            "count": 100,
            "total_pages": 2,
            "current_page": 1,
            "page_size": 50,
            "next": "http://api/resource/?page=2",
            "previous": null,
            "results": [...]
        }
        """
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("total_pages", self.page.paginator.num_pages),
                    ("current_page", self.page.number),
                    ("page_size", self.get_page_size(self.request)),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("results", data),
                ]
            )
        )

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Return OpenAPI schema for paginated response."""
        return {
            "type": "object",
            "required": ["count", "results"],
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "Total number of items",
                    "example": 100,
                },
                "total_pages": {
                    "type": "integer",
                    "description": "Total number of pages",
                    "example": 2,
                },
                "current_page": {
                    "type": "integer",
                    "description": "Current page number",
                    "example": 1,
                },
                "page_size": {
                    "type": "integer",
                    "description": "Number of items per page",
                    "example": 50,
                },
                "next": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL to next page",
                },
                "previous": {
                    "type": "string",
                    "nullable": True,
                    "format": "uri",
                    "description": "URL to previous page",
                },
                "results": schema,
            },
        }


class LargePagination(StandardPagination):
    """Pagination for endpoints that may return large datasets."""

    page_size = 100
    max_page_size = 500


class SmallPagination(StandardPagination):
    """Pagination for endpoints with smaller response needs."""

    page_size = 20
    max_page_size = 100
