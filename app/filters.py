
from rest_framework.filters import BaseFilterBackend
from django.db.models import Q

class GenericSearchFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search_query = request.query_params.get('search', None)
        category_name = request.query_params.get('category_name', None)

        if category_name:
            queryset = queryset.filter(categories__name__icontains=category_name)

        if search_query:
            queryset = queryset.filter(
                Q(user__username__icontains=search_query) |
                Q(user__phone__icontains=search_query) |
                Q(user__specialty__icontains=search_query)
            )

        return queryset



