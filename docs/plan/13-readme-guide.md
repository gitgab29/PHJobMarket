# 13. README and Documentation Guide

## README Structure (for maximum portfolio impact)

Your README is the first thing recruiters see. Optimize for a 30-second scan and a 5-minute deep read.

### Template

```markdown
# PH Job Market Tracker

> Real-time ETL pipeline aggregating job postings from 7 Philippine data sources
> into a star-schema data warehouse with interactive analytics dashboard.

![Dashboard Screenshot](docs/screenshots/dashboard.png)

## What This Demonstrates

| Skill | How It's Used |
|---|---|
| **Web Scraping** | Playwright + BS4 across 7 sources with anti-detection |
| **Data Engineering** | Raw JSONB → dbt staging → intermediate → star schema marts |
| **Orchestration** | Airflow DAGs with retries, logging, failure callbacks |
| **Data Quality** | dbt tests + Great Expectations validation |
| **API Design** | Django REST Framework with filters, pagination, search |
| **Frontend** | React + Recharts dashboard with 10+ interactive charts |
| **DevOps** | Docker Compose (8 services), GitHub Actions CI/CD |

## Architecture
[ASCII diagram from 01-architecture.md]

## Quick Start
[docker compose up commands]

## Data Sources
[Table of 7 sources with type, method, frequency]

## Data Model
[Star schema diagram + fact/dimension table descriptions]

## Key Technical Decisions
1. JSONB raw layer — if a site format changes, only fix the dbt staging model
2. dbt over raw SQL — version-controlled, tested, dependency-aware
3. Unmanaged Django models — clean separation from dbt
4. Salary parsing in Python AND SQL — Python for tests, SQL for pipeline

## API Endpoints
[Table from 08-django-api.md]

## Dashboard Pages
[4 screenshots]

## Development
[make commands]

## Project Structure
[Abbreviated directory tree]
```

## Portfolio Impact Maximizers

1. **Demo video (2-3 min)**: Record a Loom walking through the dashboard. Recruiters who won't clone your repo will watch a video.

2. **Screenshots in README**: At least 4 — dashboard overview, chart close-up, Airflow DAG graph, dbt lineage graph.

3. **dbt docs site**: `dbt docs generate && dbt docs serve` → screenshot the lineage graph. This visual is impressive and most fresh grads don't have it.

4. **Specific numbers**: "Aggregates **3,000+ job postings** from **7 sources** with **40+ skill categories** tracked" — concrete > vague.

5. **Blog post**: Write a short Medium/dev.to post about one challenge (salary parsing, cross-source dedup). Link from README.

## Additional Docs

- **`docs/architecture.md`** — Pipeline deep dive with data flow diagrams
- **`docs/data-dictionary.md`** — Every table and column with descriptions, types, examples
- **`docs/deployment.md`** — Step-by-step Railway/Render deployment guide
