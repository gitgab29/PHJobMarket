# 1. Project Architecture Overview

```
                    ┌──────────────────────────────────────────────┐
                    │              AIRFLOW SCHEDULER                │
                    │  (orchestrates everything on daily schedule)  │
                    └──────────┬───────────────────────┬───────────┘
                               │                       │
                    ┌──────────▼──────────┐ ┌──────────▼──────────┐
                    │      SCRAPERS       │ │     REDDIT API       │
                    │  Playwright + BS4   │ │   (salary threads)   │
                    │                     │ │                      │
                    │  • PhilJobNet       │ └──────────┬───────────┘
                    │  • Kalibrr          │            │
                    │  • JobStreet        │            │
                    │  • OnlineJobs.ph    │            │
                    │  • Indeed PH        │            │
                    │  • FB Job Groups    │            │
                    └──────────┬──────────┘            │
                               │                       │
                    ┌──────────▼───────────────────────▼───────────┐
                    │           POSTGRESQL — raw schema             │
                    │  (JSONB blobs, exactly as scraped)            │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │              dbt Core                         │
                    │  staging → intermediate → marts              │
                    │  + dbt tests + Great Expectations             │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │       POSTGRESQL — warehouse schema           │
                    │  (star schema: facts + dimensions)           │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │         Django REST Framework API             │
                    │  /api/v1/jobs, /api/v1/analytics, etc.       │
                    └──────────────────────┬───────────────────────┘
                                           │
                    ┌──────────────────────▼───────────────────────┐
                    │    React + Vite + Recharts + TailwindCSS     │
                    │  Dashboard with market insights               │
                    └──────────────────────────────────────────────┘
```

**Data flow summary**: Scrapers write raw JSONB → dbt transforms to star schema → Django reads warehouse tables → React renders charts.
