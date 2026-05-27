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
