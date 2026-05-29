# =============================================================================
# Makefile — convenience shortcuts for common commands
#
# A Makefile maps short names to long shell commands so you don't have to
# memorize or type them every time.
#
# Usage:  make <target>
# Example: make up
#
# Each block below is a "target". The name before the colon is what you type.
# The indented line (must be a TAB, not spaces) is the command that runs.
# =============================================================================

# .PHONY tells Make that these targets are not files — they're just commands.
# Without this, Make would check if a file named "up" exists and skip the
# command if it did. We never want that behavior here.
.PHONY: up down logs psql scrape-philjobnet scrape-kalibrr scrape-jobstreet scrape-onlinejobs scrape-indeed dbt-deps dbt-seed dbt-run dbt-test dbt-debug test

# -----------------------------------------------------------------------------
# make up
# Starts all containers defined in docker-compose.yml in "detached" mode
# (-d means they run in the background, not taking over your terminal).
# -----------------------------------------------------------------------------
up:
	docker compose up -d

# -----------------------------------------------------------------------------
# make down
# Stops and removes all running containers. Your data is safe because it's
# stored in the named volume "pgdata", not inside the container itself.
# -----------------------------------------------------------------------------
down:
	docker compose down

# -----------------------------------------------------------------------------
# make logs
# Streams live output from all running containers into your terminal.
# Useful for debugging — you'll see Postgres startup messages, errors, etc.
# Press Ctrl+C to stop watching logs (it doesn't stop the containers).
# -----------------------------------------------------------------------------
logs:
	docker compose logs -f

# -----------------------------------------------------------------------------
# make psql
# Opens an interactive SQL terminal (psql) directly inside the Postgres
# container. From here you can run any SQL query, e.g.:
#   SELECT count(*) FROM raw.job_postings;
#   \dt raw.*   (list all tables in the raw schema)
#   \q          (quit psql)
# -----------------------------------------------------------------------------
psql:
	docker compose exec postgres psql -U phjobmarket -d phjobmarket

# -----------------------------------------------------------------------------
# make scrape-philjobnet
# Runs the PhilJobNet scraper directly from your local machine (not Docker).
# You need to have run `pip install -r scrapers/requirements.txt` first,
# and Postgres must be running (`make up`).
# -----------------------------------------------------------------------------
scrape-philjobnet:
	DB_URL=postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket \
	python -m scrapers.philjobnet

# -----------------------------------------------------------------------------
# make scrape-kalibrr
# Runs the Kalibrr scraper. Requires make up + pip install -r scrapers/requirements.txt
# -----------------------------------------------------------------------------
scrape-kalibrr:
	DB_URL=postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket \
	python -m scrapers.kalibrr

# -----------------------------------------------------------------------------
# make scrape-jobstreet
# Runs the JobStreet scraper.
# -----------------------------------------------------------------------------
scrape-jobstreet:
	DB_URL=postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket \
	python -m scrapers.jobstreet

# -----------------------------------------------------------------------------
# make scrape-onlinejobs
# Runs the OnlineJobs.ph scraper — remote jobs, USD salaries.
# -----------------------------------------------------------------------------
scrape-onlinejobs:
	DB_URL=postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket \
	python -m scrapers.onlineJobs

# -----------------------------------------------------------------------------
# make scrape-indeed
# Runs the Indeed PH scraper. Stops gracefully on CAPTCHA detection.
# -----------------------------------------------------------------------------
scrape-indeed:
	DB_URL=postgresql://phjobmarket:phjobmarket@127.0.0.1:15432/phjobmarket \
	python -m scrapers.indeed

# -----------------------------------------------------------------------------
# make dbt-debug
# Verifies that dbt can connect to Postgres. Run this first to check setup.
# The "--profiles-dir ." flag tells dbt to find profiles.yml in dbt_transform/
# -----------------------------------------------------------------------------
dbt-debug:
	cd dbt_transform && dbt debug --profiles-dir .

# -----------------------------------------------------------------------------
# make dbt-deps
# Installs dbt packages listed in packages.yml (e.g. dbt_utils).
# Run this once after cloning the repo or adding a new package.
# -----------------------------------------------------------------------------
dbt-deps:
	cd dbt_transform && dbt deps --profiles-dir .

# -----------------------------------------------------------------------------
# make dbt-seed
# Loads CSV files from dbt_transform/seeds/ into the database as tables.
# Run once (or whenever you update the CSVs).
# -----------------------------------------------------------------------------
dbt-seed:
	cd dbt_transform && dbt seed --profiles-dir .

# -----------------------------------------------------------------------------
# make dbt-run
# Compiles and runs all dbt models (staging → intermediate → marts).
# Staging views appear in the "staging" schema; marts in "warehouse".
# -----------------------------------------------------------------------------
dbt-run:
	cd dbt_transform && dbt run --profiles-dir .

# -----------------------------------------------------------------------------
# make dbt-test
# Runs all dbt data quality tests defined in _staging__sources.yml
# and _marts__models.yml. Expects zero failures.
# -----------------------------------------------------------------------------
dbt-test:
	cd dbt_transform && dbt test --profiles-dir .

# -----------------------------------------------------------------------------
# make test
# Runs the pytest test suite for the scrapers package.
# Requires: pip install -r scrapers/requirements.txt
# -----------------------------------------------------------------------------
test:
	cd scrapers && python -m pytest tests/ -v
