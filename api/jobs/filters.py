import django_filters
from jobs.models import FctJobPosting


class JobPostingFilter(django_filters.FilterSet):
    source = django_filters.CharFilter(field_name="source", lookup_expr="iexact")
    salary_min_gte = django_filters.NumberFilter(field_name="salary_min", lookup_expr="gte")
    salary_max_lte = django_filters.NumberFilter(field_name="salary_max", lookup_expr="lte")
    salary_currency = django_filters.CharFilter(field_name="salary_currency", lookup_expr="iexact")
    employment_type = django_filters.CharFilter(field_name="employment_type", lookup_expr="icontains")
    experience_level = django_filters.CharFilter(field_name="experience_level", lookup_expr="icontains")
    is_remote = django_filters.BooleanFilter(field_name="is_remote")
    city = django_filters.CharFilter(field_name="location__city", lookup_expr="icontains")
    region = django_filters.CharFilter(field_name="location__region", lookup_expr="icontains")
    company_name = django_filters.CharFilter(field_name="company__company_name", lookup_expr="icontains")

    class Meta:
        model = FctJobPosting
        fields = [
            "source",
            "salary_min_gte",
            "salary_max_lte",
            "salary_currency",
            "employment_type",
            "experience_level",
            "is_remote",
            "city",
            "region",
            "company_name",
        ]
