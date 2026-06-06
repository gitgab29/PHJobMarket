from rest_framework import serializers
from jobs.models import DimCompany, DimLocation, DimSkill, FctJobPosting, FctSkillDemand


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = DimCompany
        fields = ["company_key", "company_name", "company_slug", "first_seen_at", "last_seen_at", "total_postings"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimLocation
        fields = [
            "location_key",
            "raw_location",
            "city",
            "province",
            "region",
            "is_remote",
            "is_metro_manila",
        ]


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimSkill
        fields = ["skill_key", "skill_name", "skill_category"]


class JobPostingListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.company_name", default=None, read_only=True)
    city = serializers.CharField(source="location.city", default=None, read_only=True)
    region = serializers.CharField(source="location.region", default=None, read_only=True)

    class Meta:
        model = FctJobPosting
        fields = [
            "job_key",
            "source",
            "title",
            "company_name",
            "city",
            "region",
            "salary_min",
            "salary_max",
            "salary_currency",
            "salary_period",
            "employment_type",
            "experience_level",
            "is_remote",
            "date_posted_key",
            "url",
        ]


class JobPostingDetailSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    location = LocationSerializer(read_only=True)

    class Meta:
        model = FctJobPosting
        fields = "__all__"


class SkillDemandSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source="skill.skill_name", read_only=True)
    skill_category = serializers.CharField(source="skill.skill_category", read_only=True)

    class Meta:
        model = FctSkillDemand
        fields = [
            "id",
            "snapshot_date",
            "skill_name",
            "skill_category",
            "posting_count",
            "avg_salary_min",
            "avg_salary_max",
            "source",
        ]
