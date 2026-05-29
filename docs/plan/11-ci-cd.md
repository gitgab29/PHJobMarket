# 11. GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: phjobmarket_test
          POSTGRES_USER: phjobmarket
          POSTGRES_PASSWORD: phjobmarket
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with: { python-version: "3.11", cache: pip }

      - name: Install Python dependencies
        run: |
          pip install -r scrapers/requirements.txt
          pip install -r api/requirements.txt
          pip install flake8 pytest black isort

      - name: Lint Python
        run: |
          flake8 scrapers/ api/ --max-line-length=100 --ignore=E501
          black --check scrapers/ api/
          isort --check-only scrapers/ api/

      - name: Run scraper tests
        run: pytest scrapers/tests/ -v

      - name: Run API tests
        env: { DB_HOST: localhost, DB_NAME: phjobmarket_test, DB_USER: phjobmarket, DB_PASSWORD: phjobmarket }
        run: cd api && python manage.py test

      - name: Set up Node
        uses: actions/setup-node@v4
        with: { node-version: 20, cache: npm, cache-dependency-path: frontend/package-lock.json }

      - name: Lint and build frontend
        run: cd frontend && npm ci && npm run lint && npm run build

  dbt-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_DB: phjobmarket_test
          POSTGRES_USER: phjobmarket
          POSTGRES_PASSWORD: phjobmarket
        ports: ["5432:5432"]
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install dbt-postgres==1.8.2

      - name: Create raw schema and seed data
        env: { PGPASSWORD: phjobmarket }
        run: |
          psql -h localhost -U phjobmarket -d phjobmarket_test -c "
            CREATE SCHEMA IF NOT EXISTS raw;
            CREATE TABLE raw.job_postings (
              id BIGSERIAL PRIMARY KEY, source VARCHAR(50) NOT NULL,
              source_id VARCHAR(255) NOT NULL, scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
              raw_data JSONB NOT NULL, UNIQUE (source, source_id));
            INSERT INTO raw.job_postings (source, source_id, raw_data) VALUES
            ('philjobnet', 'test_1', '{\"title\": \"Software Engineer\", \"company\": \"Test Corp\", \"location\": \"Makati City\", \"salary_raw\": \"PHP 30,000-50,000\"}'),
            ('kalibrr', 'test_2', '{\"title\": \"Data Analyst\", \"company\": \"Analytics PH\", \"location\": \"BGC, Taguig\", \"salary_raw\": \"40k-60k\", \"skills\": [\"Python\", \"SQL\"]}');
          "

      - name: Run dbt
        env: { DB_HOST: localhost, DB_USER: phjobmarket, DB_PASSWORD: phjobmarket, DB_NAME: phjobmarket_test }
        run: cd dbt_transform && dbt deps && dbt seed && dbt run && dbt test
```
