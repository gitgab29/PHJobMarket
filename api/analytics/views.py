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
        "total_jobs": total_jobs,
        "jobs_with_salary": with_salary,
        "remote_jobs": remote_jobs,
        "active_sources": sources,
        "avg_salary_min_php": round(salary_stats["avg_min"] or 0),
        "avg_salary_max_php": round(salary_stats["avg_max"] or 0),
    })


@api_view(["GET"])
def salary_by_location(request):
    data = (
        FctJobPosting.objects.filter(
            salary_min__isnull=False,
            location__city__isnull=False,
            salary_currency="PHP",
            salary_period="monthly",
        )
        .values("location__city", "location__region")
        .annotate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"), job_count=Count("job_key"))
        .filter(job_count__gte=5)
        .order_by("-avg_min")
    )
    return Response([
        {
            "city": r["location__city"],
            "region": r["location__region"],
            "avg_salary_min": float(r["avg_min"]) if r["avg_min"] is not None else None,
            "avg_salary_max": float(r["avg_max"]) if r["avg_max"] is not None else None,
            "job_count": r["job_count"],
        }
        for r in data
    ])


@api_view(["GET"])
def salary_by_experience(request):
    data = (
        FctJobPosting.objects.filter(
            salary_min__isnull=False,
            experience_level__isnull=False,
            salary_currency="PHP",
        )
        .values("experience_level")
        .annotate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"), job_count=Count("job_key"))
        .order_by("avg_min")
    )
    return Response([
        {
            "experience_level": r["experience_level"],
            "avg_salary_min": float(r["avg_min"]) if r["avg_min"] is not None else None,
            "avg_salary_max": float(r["avg_max"]) if r["avg_max"] is not None else None,
            "job_count": r["job_count"],
        }
        for r in data
    ])


@api_view(["GET"])
def salary_by_source(request):
    """Average PHP monthly salary per source — used by the dashboard in place of
    experience level, which is not populated in the warehouse yet."""
    data = (
        FctJobPosting.objects.filter(
            salary_min__isnull=False,
            salary_currency="PHP",
            salary_period="monthly",
        )
        .values("source")
        .annotate(avg_min=Avg("salary_min"), avg_max=Avg("salary_max"), job_count=Count("job_key"))
        .order_by("-avg_min")
    )
    return Response([
        {
            "source": r["source"],
            "avg_salary_min": float(r["avg_min"]) if r["avg_min"] is not None else None,
            "avg_salary_max": float(r["avg_max"]) if r["avg_max"] is not None else None,
            "job_count": r["job_count"],
        }
        for r in data
    ])


@api_view(["GET"])
def jobs_by_source(request):
    data = FctJobPosting.objects.values("source").annotate(count=Count("job_key")).order_by("-count")
    return Response(list(data))


@api_view(["GET"])
def remote_vs_onsite(request):
    total = FctJobPosting.objects.count()
    remote = FctJobPosting.objects.filter(is_remote=True).count()
    return Response({
        "remote": remote,
        "onsite": total - remote,
        "total": total,
        "remote_percentage": round(remote / total * 100, 1) if total else 0,
    })


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
    data = (
        qs.values("snapshot_date", "skill__skill_name", "posting_count", "avg_salary_min", "avg_salary_max")
        .order_by("snapshot_date")
    )
    return Response(list(data))
