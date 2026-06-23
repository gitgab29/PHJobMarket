from django.urls import path, include
from rest_framework.routers import DefaultRouter
from jobs.views import JobPostingViewSet, CompanyViewSet, LocationViewSet, SkillViewSet
from analytics import views as analytics_views

router = DefaultRouter()
router.register(r"jobs", JobPostingViewSet, basename="job")
router.register(r"companies", CompanyViewSet, basename="company")
router.register(r"locations", LocationViewSet, basename="location")
router.register(r"skills", SkillViewSet, basename="skill")

urlpatterns = [
    path("api/v1/", include(router.urls)),
    path("api/v1/analytics/summary/", analytics_views.dashboard_summary, name="dashboard_summary"),
    path("api/v1/analytics/salary-by-location/", analytics_views.salary_by_location, name="salary_by_location"),
    path("api/v1/analytics/salary-by-experience/", analytics_views.salary_by_experience, name="salary_by_experience"),
    path("api/v1/analytics/salary-by-source/", analytics_views.salary_by_source, name="salary_by_source"),
    path("api/v1/analytics/jobs-by-source/", analytics_views.jobs_by_source, name="jobs_by_source"),
    path("api/v1/analytics/remote-vs-onsite/", analytics_views.remote_vs_onsite, name="remote_vs_onsite"),
    path("api/v1/analytics/skill-trends/", analytics_views.skill_trends, name="skill_trends"),
]
