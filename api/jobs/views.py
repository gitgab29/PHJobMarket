from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from jobs.filters import JobPostingFilter
from jobs.models import DimCompany, DimLocation, DimSkill, FctJobPosting, FctSkillDemand
from jobs.serializers import (
    CompanySerializer,
    LocationSerializer,
    SkillSerializer,
    JobPostingListSerializer,
    JobPostingDetailSerializer,
    SkillDemandSerializer,
)


class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FctJobPosting.objects.select_related("company", "location").all()
    filterset_class = JobPostingFilter
    search_fields = ["title", "description", "company__company_name"]
    ordering_fields = ["salary_min", "salary_max", "date_posted_key"]
    ordering = ["-date_posted_key"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobPostingDetailSerializer
        return JobPostingListSerializer


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimCompany.objects.all()
    serializer_class = CompanySerializer
    search_fields = ["company_name", "company_slug"]
    ordering_fields = ["total_postings", "company_name"]
    ordering = ["-total_postings"]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimLocation.objects.all()
    serializer_class = LocationSerializer
    filterset_fields = ["is_remote", "is_metro_manila", "region"]
    search_fields = ["city", "province", "region"]
    ordering = ["region", "city"]


class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimSkill.objects.all()
    serializer_class = SkillSerializer
    search_fields = ["skill_name"]
    ordering = ["skill_name"]

    @action(detail=False, methods=["get"])
    def top(self, request):
        limit = int(request.query_params.get("limit", 20))
        source = request.query_params.get("source")
        qs = FctSkillDemand.objects.select_related("skill").order_by("-posting_count")
        if source:
            qs = qs.filter(source=source)
        latest_date = qs.values_list("snapshot_date", flat=True).distinct().first()
        if latest_date:
            qs = qs.filter(snapshot_date=latest_date)
        serializer = SkillDemandSerializer(qs[:limit], many=True)
        return Response(serializer.data)
