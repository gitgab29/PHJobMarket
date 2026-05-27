# 4. PostgreSQL Schema Design

## 4.1 Raw Layer (EL — Extract-Load)

```sql
-- migrations/001_raw_schema.sql

CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE raw.job_postings (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(50) NOT NULL,
    source_id       VARCHAR(255) NOT NULL,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data        JSONB NOT NULL,
    UNIQUE (source, source_id)
);

CREATE INDEX idx_raw_jobs_source ON raw.job_postings (source);
CREATE INDEX idx_raw_jobs_scraped_at ON raw.job_postings (scraped_at);
CREATE INDEX idx_raw_jobs_data_gin ON raw.job_postings USING GIN (raw_data);

CREATE TABLE raw.reddit_posts (
    id              BIGSERIAL PRIMARY KEY,
    source_id       VARCHAR(255) NOT NULL UNIQUE,
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    raw_data        JSONB NOT NULL
);

CREATE TABLE raw.scrape_log (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(50) NOT NULL,
    started_at      TIMESTAMPTZ NOT NULL,
    finished_at     TIMESTAMPTZ,
    records_scraped INTEGER DEFAULT 0,
    status          VARCHAR(20) NOT NULL DEFAULT 'running',
    error_message   TEXT
);
```

## 4.2 Warehouse Layer (star schema — built by dbt)

These tables are created and managed by dbt. Shown here for reference only.

```sql
CREATE SCHEMA IF NOT EXISTS warehouse;

-- ========== DIMENSION TABLES ==========

CREATE TABLE warehouse.dim_date (
    date_key        INTEGER PRIMARY KEY,    -- YYYYMMDD
    full_date       DATE NOT NULL,
    day_of_week     SMALLINT,
    day_name        VARCHAR(10),
    month           SMALLINT,
    month_name      VARCHAR(10),
    quarter         SMALLINT,
    year            SMALLINT,
    is_weekend      BOOLEAN
);

CREATE TABLE warehouse.dim_companies (
    company_key     SERIAL PRIMARY KEY,
    company_name    VARCHAR(500),
    company_slug    VARCHAR(500),
    first_seen_at   DATE,
    last_seen_at    DATE,
    total_postings  INTEGER DEFAULT 0
);

CREATE TABLE warehouse.dim_locations (
    location_key    SERIAL PRIMARY KEY,
    raw_location    VARCHAR(500),
    city            VARCHAR(200),
    province        VARCHAR(200),
    region          VARCHAR(200),         -- NCR, Region IV-A, etc.
    is_remote       BOOLEAN DEFAULT FALSE,
    is_metro_manila BOOLEAN DEFAULT FALSE
);

CREATE TABLE warehouse.dim_skills (
    skill_key       SERIAL PRIMARY KEY,
    skill_name      VARCHAR(200),
    skill_category  VARCHAR(100),
    aliases         TEXT[]
);

CREATE TABLE warehouse.dim_industries (
    industry_key    SERIAL PRIMARY KEY,
    industry_name   VARCHAR(200),
    sector          VARCHAR(200)
);

-- ========== FACT TABLES ==========

CREATE TABLE warehouse.fct_job_postings (
    job_key             BIGSERIAL PRIMARY KEY,
    source              VARCHAR(50) NOT NULL,
    source_id           VARCHAR(255) NOT NULL,
    title               VARCHAR(500),
    description         TEXT,
    company_key         INTEGER REFERENCES warehouse.dim_companies,
    location_key        INTEGER REFERENCES warehouse.dim_locations,
    industry_key        INTEGER REFERENCES warehouse.dim_industries,
    date_posted_key     INTEGER REFERENCES warehouse.dim_date,
    date_scraped_key    INTEGER REFERENCES warehouse.dim_date,
    salary_min          NUMERIC(12, 2),
    salary_max          NUMERIC(12, 2),
    salary_currency     VARCHAR(10) DEFAULT 'PHP',
    salary_period       VARCHAR(20),
    employment_type     VARCHAR(50),
    experience_level    VARCHAR(50),
    is_remote           BOOLEAN DEFAULT FALSE,
    url                 TEXT,
    UNIQUE (source, source_id)
);

CREATE TABLE warehouse.fct_job_skills (
    id              BIGSERIAL PRIMARY KEY,
    job_key         BIGINT REFERENCES warehouse.fct_job_postings,
    skill_key       INTEGER REFERENCES warehouse.dim_skills
);

CREATE TABLE warehouse.fct_salary_reports (
    id              BIGSERIAL PRIMARY KEY,
    source          VARCHAR(50),
    source_id       VARCHAR(255),
    reported_at     DATE,
    job_title       VARCHAR(500),
    company_name    VARCHAR(500),
    salary_min      NUMERIC(12, 2),
    salary_max      NUMERIC(12, 2),
    salary_currency VARCHAR(10) DEFAULT 'PHP',
    salary_period   VARCHAR(20),
    experience_years INTEGER,
    location_key    INTEGER REFERENCES warehouse.dim_locations
);

CREATE TABLE warehouse.fct_skill_demand (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    skill_key       INTEGER REFERENCES warehouse.dim_skills,
    posting_count   INTEGER,
    avg_salary_min  NUMERIC(12, 2),
    avg_salary_max  NUMERIC(12, 2),
    source          VARCHAR(50)
);
```
