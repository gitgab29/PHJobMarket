# 12. Week-by-Week Timeline

## Phase 1: Foundation (Weeks 1-2)

### Week 1: Project Setup + First Scraper
- [ ] Initialize git repo, directory structure, `.gitignore`, `.env.example`
- [ ] Set up Docker Compose with just PostgreSQL
- [ ] Create raw schema migration (`migrations/001_raw_schema.sql`)
- [ ] Implement `BaseScraper` class
- [ ] Implement `PhilJobNetScraper` (friendliest source)
- [ ] Write `salary_parser.py` with tests
- [ ] Test: run scraper → check `raw.job_postings` has JSONB data
- **Milestone: one scraper writes data to Postgres**

### Week 2: More Scrapers + dbt Basics
- [ ] Implement `KalibrrScraper` (API intercept)
- [ ] Implement `JobStreetScraper` (redux data extraction)
- [ ] Set up dbt project structure, `profiles.yml`
- [ ] Write staging models for PhilJobNet + Kalibrr
- [ ] Write `skill_aliases.csv` and `ph_regions.csv` seeds
- [ ] Run `dbt seed` + `dbt run` — verify staging views work
- **Milestone: 4 scrapers working, dbt staging layer compiles**

## Phase 2: Pipeline (Weeks 3-4)

### Week 3: Complete Scrapers + dbt Marts
- [ ] Implement `OnlineJobsScraper` and `IndeedScraper`
- [ ] Implement `FacebookScraper` (login flow + cookies)
- [ ] Write staging models for all remaining sources
- [ ] Write `int_jobs__unified`, `int_jobs__deduped`
- [ ] Write `int_salaries__parsed`, `int_skills__extracted`
- [ ] Write all `dim_*` and `fct_*` mart models
- [ ] Full `dbt run` → check warehouse schema
- **Milestone: full ELT pipeline from raw to star schema**

### Week 4: Airflow + Data Quality
- [ ] Add Airflow to Docker Compose
- [ ] Write `scrape_all_sources.py` DAG
- [ ] Write `dbt_transform.py` DAG
- [ ] Configure `scrape_log` table and failure callbacks
- [ ] Add dbt tests (`_marts__models.yml`)
- [ ] Set up Great Expectations suite
- [ ] Run full pipeline end-to-end via Airflow
- **Milestone: Airflow orchestrates the daily pipeline**

## Phase 3: API + Frontend (Weeks 5-7)

### Week 5: Django REST API
- [ ] Initialize Django project with DRF
- [ ] Create unmanaged models (`managed = False`)
- [ ] Write serializers, filters, views for all endpoints
- [ ] Set up CORS for localhost
- [ ] Add API Dockerfile to Docker Compose
- [ ] Test all endpoints with curl or Postman
- **Milestone: all API endpoints return real data**

### Week 6: React Dashboard (Core)
- [ ] Initialize Vite + React + TailwindCSS
- [ ] Build layout (Navbar, Sidebar)
- [ ] Build Dashboard page: stat cards + 4 charts
- [ ] Build Job Explorer page with filterable table
- [ ] Wire up `useAnalytics` hook → API → charts
- **Milestone: Dashboard and Job Explorer functional**

### Week 7: React Dashboard (Polish)
- [ ] Build Salary Insights page (3 charts)
- [ ] Build Skill Demand page (treemap + line chart)
- [ ] Build About page
- [ ] Add loading states, error boundaries
- [ ] Add frontend Dockerfile + nginx proxy
- [ ] Full Docker Compose stack end-to-end
- **Milestone: complete frontend with all pages**

## Phase 4: Polish (Week 8)

### Week 8: CI/CD, Docs, Portfolio Prep
- [ ] Set up GitHub Actions CI
- [ ] Add dbt test job to CI
- [ ] Write comprehensive README
- [ ] Write `docs/architecture.md` with diagrams
- [ ] Write `docs/data-dictionary.md`
- [ ] Record 2-3 min demo video
- [ ] Deploy to Railway/Render free tier
- [ ] Final code cleanup
- [ ] Add `.env.example` with all variables documented
- **Milestone: portfolio-ready with docs and demo**

## Buffer (if time permits)
- Simple ML model: predict salary from title + skills + location (Random Forest)
- Email alerts on Airflow DAG failures
- Data freshness monitoring dashboard
