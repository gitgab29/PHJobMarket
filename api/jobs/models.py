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

    def __str__(self):
        return self.company_name


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

    def __str__(self):
        return f"{self.city}, {self.province}" if self.city else self.raw_location


class DimSkill(models.Model):
    skill_key = models.AutoField(primary_key=True)
    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=100, null=True)

    class Meta:
        managed = False
        db_table = "dim_skills"

    def __str__(self):
        return self.skill_name


class DimDate(models.Model):
    date_key = models.IntegerField(primary_key=True)
    calendar_date = models.DateField(unique=True)
    year = models.IntegerField()
    month = models.IntegerField()
    day = models.IntegerField()
    day_of_week = models.IntegerField()
    week_of_year = models.IntegerField()
    quarter = models.IntegerField()
    is_weekend = models.BooleanField()

    class Meta:
        managed = False
        db_table = "dim_date"

    def __str__(self):
        return str(self.calendar_date)


class FctJobPosting(models.Model):
    job_key = models.BigAutoField(primary_key=True)
    source = models.CharField(max_length=50)
    source_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500, null=True)
    description = models.TextField(null=True)
    company = models.ForeignKey(
        DimCompany, on_delete=models.DO_NOTHING, null=True, db_column="company_key", related_name="postings"
    )
    location = models.ForeignKey(
        DimLocation, on_delete=models.DO_NOTHING, null=True, db_column="location_key", related_name="postings"
    )
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

    def __str__(self):
        return self.title or "Untitled"


class FctSkillDemand(models.Model):
    id = models.BigAutoField(primary_key=True)
    snapshot_date = models.DateField()
    skill = models.ForeignKey(
        DimSkill, on_delete=models.DO_NOTHING, null=True, db_column="skill_key", related_name="demands"
    )
    posting_count = models.IntegerField()
    avg_salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    avg_salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    source = models.CharField(max_length=50, null=True)

    class Meta:
        managed = False
        db_table = "fct_skill_demand"

    def __str__(self):
        return f"{self.skill.skill_name if self.skill else 'Unknown'} ({self.snapshot_date})"
