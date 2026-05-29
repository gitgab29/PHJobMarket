# 2. Directory Structure

```
PHJobMarket/
├── .github/
│   └── workflows/
│       ├── ci.yml                    # lint + test on every PR
│       └── dbt-test.yml             # dbt build + test
├── airflow/
│   ├── dags/
│   │   ├── scrape_all_sources.py    # main orchestration DAG
│   │   └── dbt_transform.py         # dbt run + test DAG
│   ├── plugins/
│   └── Dockerfile                   # custom Airflow image
├── scrapers/
│   ├── __init__.py
│   ├── base.py                      # BaseScraper abstract class
│   ├── philjobnet.py
│   ├── kalibrr.py
│   ├── jobstreet.py
│   ├── onlinejobs.py
│   ├── indeed.py
│   ├── facebook.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── salary_parser.py         # PH salary extraction
│   │   ├── location_normalizer.py   # "Makati City" → "Makati"
│   │   ├── proxy_manager.py         # rotation logic
│   │   └── user_agents.py           # UA rotation
│   ├── tests/
│   │   ├── test_salary_parser.py
│   │   ├── test_location_normalizer.py
│   │   └── fixtures/                # saved HTML for offline tests
│   │       ├── philjobnet_sample.html
│   │       ├── kalibrr_sample.html
│   │       └── ...
│   └── requirements.txt
├── dbt_transform/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── packages.yml
│   ├── models/
│   │   ├── staging/
│   │   │   ├── _staging__sources.yml
│   │   │   ├── _staging__models.yml
│   │   │   ├── stg_raw__philjobnet.sql
│   │   │   ├── stg_raw__kalibrr.sql
│   │   │   ├── stg_raw__jobstreet.sql
│   │   │   ├── stg_raw__onlinejobs.sql
│   │   │   ├── stg_raw__indeed.sql
│   │   │   └── stg_raw__facebook.sql
│   │   ├── intermediate/
│   │   │   ├── _intermediate__models.yml
│   │   │   ├── int_jobs__unified.sql
│   │   │   ├── int_jobs__deduped.sql
│   │   │   ├── int_salaries__parsed.sql
│   │   │   └── int_skills__extracted.sql
│   │   └── marts/
│   │       ├── _marts__models.yml
│   │       ├── dim_companies.sql
│   │       ├── dim_locations.sql
│   │       ├── dim_skills.sql
│   │       ├── dim_industries.sql
│   │       ├── dim_date.sql
│   │       ├── fct_job_postings.sql
│   │       ├── fct_salary_reports.sql
│   │       └── fct_skill_demand.sql
│   ├── macros/
│   │   ├── salary_bucket.sql
│   │   └── deduplicate.sql
│   ├── seeds/
│   │   ├── ph_regions.csv           # NCR, Region IV-A, etc.
│   │   ├── skill_aliases.csv        # "JS" → "JavaScript", etc.
│   │   └── industry_mapping.csv
│   ├── tests/
│   │   └── assert_salary_range_valid.sql
│   └── great_expectations/
│       ├── great_expectations.yml
│       └── expectations/
│           └── raw_jobs_suite.json
├── api/
│   ├── manage.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── jobs/
│   │   ├── __init__.py
│   │   ├── models.py                # unmanaged models pointing to warehouse
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── filters.py
│   │   └── tests.py
│   ├── analytics/
│   │   ├── __init__.py
│   │   ├── views.py                 # aggregation endpoints
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── tests.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── api/
│   │   │   └── client.js            # axios instance
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── JobExplorer.jsx
│   │   │   ├── SalaryInsights.jsx
│   │   │   ├── SkillDemand.jsx
│   │   │   └── About.jsx
│   │   ├── components/
│   │   │   ├── charts/
│   │   │   │   ├── SalaryDistribution.jsx
│   │   │   │   ├── TopSkillsBar.jsx
│   │   │   │   ├── JobTrendLine.jsx
│   │   │   │   ├── LocationHeatmap.jsx
│   │   │   │   ├── IndustryBreakdown.jsx
│   │   │   │   └── SourceComparison.jsx
│   │   │   ├── filters/
│   │   │   │   ├── DateRangePicker.jsx
│   │   │   │   ├── LocationFilter.jsx
│   │   │   │   └── SkillFilter.jsx
│   │   │   ├── layout/
│   │   │   │   ├── Navbar.jsx
│   │   │   │   ├── Sidebar.jsx
│   │   │   │   └── Footer.jsx
│   │   │   └── shared/
│   │   │       ├── StatCard.jsx
│   │   │       ├── LoadingSpinner.jsx
│   │   │       └── ErrorBoundary.jsx
│   │   └── hooks/
│   │       ├── useJobs.js
│   │       └── useAnalytics.js
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml
├── .env.example
├── .gitignore
├── Makefile                          # convenience commands
├── README.md
├── CONTRIBUTING.md
└── docs/
    ├── architecture.md
    ├── data-dictionary.md
    └── deployment.md
```
