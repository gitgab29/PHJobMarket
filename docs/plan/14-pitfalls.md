# 14. Pitfalls and How to Handle Them

## Scraping

| Pitfall | What Happens | Solution |
|---|---|---|
| Site layout changes | Selectors stop matching, 0 results | Save fixture HTML for tests; detect 0-result scrapes and alert |
| IP gets blocked | 403/429 responses | Random delays, UA rotation, page caps. Skip and log if persistent |
| Facebook DOM is unstable | Selectors change weekly | Use `role="article"` and text filtering, not CSS classes |
| Indeed CAPTCHA | Can't proceed after 5-10 pages | Detect early, stop gracefully, accept partial data |
| Kalibrr SPA won't load | Empty page content | Use API intercept, add `wait_until="networkidle"` |
| Scraping too aggressively | Banned or overloading servers | Max 1 req/3sec, max 50 pages, run at 2 AM Manila |

## Data Quality

| Pitfall | What Happens | Solution |
|---|---|---|
| Duplicates across sources | Same job on Kalibrr + JobStreet counted twice | Dedupe in `int_jobs__deduped` by title+company fuzzy match. Accept some dupes for MVP |
| Salary parsing fails silently | salary_min = null for valid salaries | Comprehensive test suite; log unparseable formats |
| OnlineJobs.ph uses USD | Mixing currencies breaks averages | Explicit `salary_currency` column; filter/convert in marts |
| Reddit text is unstructured | Can't reliably extract salary | Start with regex ("my salary is", "I earn"); accept low rate |
| Skill extraction false positives | "Go to website" matches "Go" language | Word boundaries in regex (`\mgo\M`); patterns in seed file |

## Infrastructure

| Pitfall | What Happens | Solution |
|---|---|---|
| Airflow eats memory | Docker host OOM | `LocalExecutor`, `max_active_tasks=3`, give Docker 6GB+ RAM |
| Playwright in Docker fails | Missing browser deps | `playwright install-deps` in Dockerfile |
| dbt can't connect to Postgres | Wrong host/schema | Docker service names as hosts; set `search_path` in profiles |
| Migration conflicts | Django tries to manage dbt tables | `managed = False` on all warehouse models |
| Docker Compose on 8GB laptop | Services keep restarting | Drop airflow-webserver during dev; trigger DAGs via CLI |

## Fresh Grad Traps

| Pitfall | What Happens | Solution |
|---|---|---|
| Building everything before testing | 2 months in, nothing works end-to-end | Get one scraper → raw → dbt → API → one chart in week 1 |
| Overcomplicating star schema | 15 dimensions, can't populate them | Start with 5 dimensions. Add more only when needed for a chart |
| Week on Facebook scraping | Hardest and least reliable source | Mark optional. Build pipeline without it. Add last |
| No fixture tests for scrapers | Can't test without hitting live sites | Save HTML as fixtures on day 1. Test parsers against fixtures |
| Deploying too early | Debugging Docker + deployment + code at once | Everything local first. Deploy in week 8 |
| Perfect code over working code | Still refactoring BaseScraper in week 6 | Ship ugly code that works. Refactor in week 8 if time permits |
| Not committing frequently | Lose work or can't show git history | Commit after every working feature. Recruiters check history |

## .env.example

```env
DB_HOST=postgres
DB_PORT=5432
DB_NAME=phjobmarket
DB_USER=phjobmarket
DB_PASSWORD=phjobmarket
DJANGO_SECRET_KEY=change-me-to-a-random-string
DEBUG=true
ALLOWED_HOSTS=*
VITE_API_URL=http://localhost:8000/api/v1
```

## .gitignore

```gitignore
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
.env
*.env.local
.vscode/
.idea/
pgdata/
node_modules/
dist/
.cache/
airflow/logs/
airflow/airflow.db
dbt_transform/target/
dbt_transform/dbt_packages/
dbt_transform/logs/
dbt_transform/great_expectations/uncommitted/
scrapers/.fb_cookies.json
.DS_Store
Thumbs.db
```
