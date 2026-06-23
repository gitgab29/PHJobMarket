from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Default 25 per page, but callers may request a larger page (e.g. the
    frontend loads all companies/locations to populate filter dropdowns)."""

    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 2000
