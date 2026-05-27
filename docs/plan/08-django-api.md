# 8. Django REST API

## 8.1 Key Settings

```python
# api/config/settings.py (key sections only)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "phjobmarket"),
        "USER": os.environ.get("DB_USER", "phjobmarket"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "phjobmarket"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "OPTIONS": {"options": "-c search_path=warehouse,public"},
    }
}

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.AnonRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {"anon": "100/hour"},
}

CORS_ALLOWED_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

## 8.2 Models (Unmanaged — dbt owns the tables)

```python
# api/jobs/models.py
from django.db import models

class DimCompany(models.Model):
    company_key = models.AutoField(primary_key=True)
    company_name = models.CharField(max_length=500)
    company_slug = models.CharField(max_length=500)
    first_seen_at = models.DateField(null=True)
    last_seen_at = models.DateField(null=True)
    total_postings = models.IntegerField(default=0)
    class Meta:
        managed = False
        db_table = "dim_companies"

class DimLocation(models.Model):
    location_key = models.AutoField(primary_key=True)
    raw_location = models.CharField(max_length=500)
    city = models.CharField(max_length=200, null=True)
    province = models.CharField(max_length=200, null=True)
    region = models.CharField(max_length=200, null=True)
    is_remote = models.BooleanField(default=False)
    is_metro_manila = models.BooleanField(default=False)
    class Meta:
        managed = False
        db_table = "dim_locations"

class DimSkill(models.Model):
    skill_key = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=100, null=True)
    class Meta:
        managed = False
        db_table = "dim_skills"

class FctJobPosting(models.Model):
    job_key = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=50)
    source_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500, null=True)
    description = models.TextField(null=True)
    company = models.ForeignKey(DimCompany, on_delete=models.DO_NOTHING, null=True, db_column="company_key")
    location = models.ForeignKey(DimLocation, on_delete=models.DO_NOTHING, null=True, db_column="location_key")
    date_posted_key = models.IntegerField(null=True)
    date_scraped_key = models.IntegerField(null=True)
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    salary_currency = models.CharField(max_length=10, default="PHP")
    salary_period = models.CharField(max_length=20, null=True)
    employment_type = models.CharField(max_length=50, null=True)
    experience_level = models.CharField(max_length=50, null=True)
    is_remote = models.BooleanField(default=False)
    url = models.TextField(null=True)
    class Meta:
        managed = False
        db_table = "fct_job_postings"

class FctSkillDemand(models.Model):
    id = models.BigAutoField(primary_key=True)
    snapshot_date = models.DateField()
    skill = models.ForeignKey(DimSkill, on_delete=models.DO_NOTHING, null=True, db_column="skill_key")
    posting_count = models.IntegerField()
    avg_salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    avg_salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    source = models.CharField(max_length=50, null=True)
    class Meta:
        managed = False
        db_table = "fct_skill_demand"
```

## 8.3 Serializers

```python
# api/jobs/serializers.py
from rest_framework import serializers
from jobs.models import DimCompany, DimLocation, DimSkill, FctJobPosting, FctSkillDemand

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DimCompany
        fields = ["company_key", "company_name", "total_postings"]

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimLocation
        fields = ["location_key", "city", "province", "region", "is_remote", "is_metro_manila"]

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimSkill
        fields = ["skill_key", "skill_name", "skill_category"]

class JobPostingListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.company_name", default=None)
    city = serializers.CharField(source="location.city", default=None)
    region = serializers.CharField(source="location.region", default=None)
    class Meta:
        model = FctJobPosting
        fields = ["job_key", "source", "title", "company_name", "city", "region",
                  "salary_min", "salary_max", "salary_currency", "salary_period",
                  "employment_type", "experience_level", "is_remote", "date_posted_key", "url"]

class JobPostingDetailSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    location = LocationSerializer()
    class Meta:
        model = FctJobPosting
        fields = "__all__"

class SkillDemandSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.skill_name")
    skill_category = serializers.CharField(source="skill.skill_category")
    class Meta:
        model = FctSkillDemand
        fields = ["id", "snapshot_date", "skill_name", "skill_category",
                  "posting_count", "avg_salary_min", "avg_salary_max", "source"]
```

## 8.4 Views

```python
# api/jobs/views.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from jobs.filters import JobPostingFilter
from jobs.models import DimCompany, DimLocation, DimSkill, FctJobPosting, FctSkillDemand
from jobs.serializers import *

class JobPostingViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FctJobPosting.objects.select_related("company", "location").all()
    filterset_class = JobPostingFilter
    search_fields = ["title", "description"]
    ordering_fields = ["salary_min", "salary_max", "date_posted_key"]
    ordering = ["-date_posted_key"]
    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobPostingDetailSerializer
        return JobPostingListSerializer

class SkillViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = DimSkill.objects.all()
    serializer_class = SkillSerializer
    search_fields = ["skill_name"]

    @action(detail=False, methods=["get"])
    def top(self, request):
        limit = int(request.query_params.get("limit", 20))
        source = request.query_params.get("source")
        qs = FctSkillDemand.objects.select_related("skill").order_by("-posting_count")
        if source:
            qs = qs.filter(source=source)
        latest_date = qs.values_list("snapshot_date", flat=True).first()
        if latest_date:
            qs = qs.filter(snapshot_date=latest_date)
        serializer = SkillDemandSerializer(qs[:limit], many=True)
        return Response(serializer.data)
```

```python
# api/analytics/views.py
from django.db.models import Avg, Count
from rest_framework.decorators import api_view
from rest_framework.response import Response
from jobs.models import FctJobPosting, FctSkillDemand

@api_view(["GET"])
def dashboard_summary(request):
    total_jobs = FctJobPosting.objects.count()
    with_salary = FctJobPosting.objects.filter(salary_min__isnull=False).count()
    remote_jobs = FctJobPosting.objects.filter(is_remote=True).count()
    sources = FctJobPosting.objects.values("source").distinct().count()
    salary_stats = FctJobPosting.objects.filter(
        salary_min__isnull=False, salary_currency="PHP", salary_period="monthly"
    ).aggregate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"))
    return Response({
        "total_jobs": total_jobs, "jobs_with_salary": with_salary,
        "remote_jobs": remote_jobs, "active_sources": sources,
        "avg_salary_min_php": round(salary_stats["avg_min"] or 0),
        "avg_salary_max_php": round(salary_stats["avg_max"] or 0),
    })

@api_view(["GET"])
def salary_by_location(request):
    data = (FctJobPosting.objects
        .filter(salary_min__isnull=False, location__city__isnull=False,
                salary_currency="PHP", salary_period="monthly")
        .values("location__city", "location__region")
        .annotate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"), job_count=Count("job_key"))
        .filter(job_count__gte=5).order_by("-avg_max"))
    return Response(list(data))

@api_view(["GET"])
def salary_by_experience(request):
    data = (FctJobPosting.objects
        .filter(salary_min__isnull=False, experience_level__isnull=False, salary_currency="PHP")
        .values("experience_level")
        .annotate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"), job_count=Count("job_key"))
        .order_by("avg_min"))
    return Response(list(data))

@api_view(["GET"])
def jobs_by_source(request):
    data = (FctJobPosting.objects.values("source").annotate(count=Count("job_key")).order_by("-count"))
    return Response(list(data))

@api_view(["GET"])
def remote_vs_onsite(request):
    total = FctJobPosting.objects.count()
    remote = FctJobPosting.objects.filter(is_remote=True).count()
    return Response({"remote": remote, "onsite": total - remote, "total": total,
                     "remote_percentage": round(remote / total * 100, 1) if total else 0})

@api_view(["GET"])
def skill_trends(request):
    skill_name = request.query_params.get("skill")
    limit = int(request.query_params.get("limit", 10))
    qs = FctSkillDemand.objects.select_related("skill")
    if skill_name:
        qs = qs.filter(skill__skill_name__icontains=skill_name)
    else:
        top_skills = qs.order_by("-posting_count").values_list("skill__skill_name", flat=True).distinct()[:limit]
        qs = qs.filter(skill__skill_name__in=list(top_skills))
    data = qs.values("snapshot_date", "skill__skill_name", "posting_count",
                     "avg_salary_min", "avg_salary_max").order_by("snapshot_date")
    return Response(list(data))
```

## 8.5 Endpoint Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/jobs/` | Paginated job list with filters |
| GET | `/api/v1/jobs/{id}/` | Job detail with company + location |
| GET | `/api/v1/companies/` | Company list with search |
| GET | `/api/v1/locations/` | Location list |
| GET | `/api/v1/skills/` | Skill list |
| GET | `/api/v1/skills/top/?limit=20` | Top skills by demand |
| GET | `/api/v1/analytics/summary/` | Dashboard header numbers |
| GET | `/api/v1/analytics/salary-by-location/` | Avg salary by city |
| GET | `/api/v1/analytics/salary-by-experience/` | Avg salary by exp level |
| GET | `/api/v1/analytics/jobs-by-source/` | Jobs count per source |
| GET | `/api/v1/analytics/remote-vs-onsite/` | Remote/onsite breakdown |
| GET | `/api/v1/analytics/skill-trends/?skill=Python` | Skill demand over time |
