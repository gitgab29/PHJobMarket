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
.PHONY: up down logs psql scrape-philjobnet test

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
# make test
# Runs the pytest test suite for the scrapers package.
# Requires: pip install -r scrapers/requirements.txt
# -----------------------------------------------------------------------------
test:
	cd scrapers && python -m pytest tests/ -v
