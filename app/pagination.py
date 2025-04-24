from rest_framework.pagination import PageNumberPagination

class Pagination(PageNumberPagination):
    page_size = 25  
    page_size_query_param = 'page_size'  
     



from rest_framework.pagination import (
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination
)
from rest_framework.response import Response


class Pagination(PageNumberPagination):
    """
    Standard page number based pagination.
    Client can request a specific page using 'page' query parameter.
    Uses page numbers to paginate.
    Example URL:
    /api/items/?page=3
    """
    page_size = 5
    page_size_query_param = 'p'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class StandardLimitOffsetPagination(LimitOffsetPagination):
    """
    A limit-offset based pagination.
    Client can control the offset and limit using query parameters.

    Uses two query parameters:

    limit: Number of items per page.

    offset: Starting point in the dataset.

    Example URL:
    /api/items/?limit=10&offset=20
    """
    default_limit = 2
    limit_query_param = 'l'
    offset_query_param = 'o'
    max_limit = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class MyCursorPagination(CursorPagination):
    """
    Cursor-based pagination for ordered datasets.
    Provides more consistent performance with large datasets.
    """
    page_size = 2
    page_size_query_param = 'page_size'
    max_page_size = 50
    ordering = '-created_at'  # Default ordering field
    cursor_query_param = 'cursor'

    def get_paginated_response(self, data):
        return Response({
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class CustomPagination(PageNumberPagination):
    """
    Custom pagination with additional metadata in the response.
    """
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })

