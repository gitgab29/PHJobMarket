# Deploying PH Job Market Tracker to AWS Free Tier

A live portfolio demo (job listings + dashboard) on **one** free-tier EC2 box.

**What runs in the cloud:** `postgres` + `django` (gunicorn) + `nginx` (serves the
React build, reverse-proxies `/api`). That's it — three lightweight services.

**What does NOT run in the cloud:** Airflow. Its webserver + scheduler need 2–4 GB
RAM and won't fit a 1 GB free-tier box, and visitors never see it. It stays in the
repo as architecture. Keep data fresh by running `scrape → dbt` on demand
(see [§5](#5-refreshing-data-optional)) instead of on a nightly schedule.

---

## 0. Prove it locally first (do this before touching AWS)

Debugging on your laptop is free and fast; debugging on a 1 GB EC2 box is neither.

```bash
cp .env.prod.example .env.prod
# edit .env.prod: set DJANGO_SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS=localhost
python -c "import secrets; print(secrets.token_urlsafe(50))"   # secret key

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

Then verify:

```bash
# API up?
curl http://localhost/api/v1/analytics/summary/      # -> JSON, HTTP 200
# Django prod-readiness (run inside the container)
docker compose -f docker-compose.prod.yml exec django python manage.py check --deploy
```

Open <http://localhost> in a browser: Jobs page lists jobs, Dashboard renders charts,
no console errors. **Exit gate:** app works at `http://localhost` with `DEBUG=False`.

> The freshly-built Postgres volume is empty, so the site shows 0 jobs until you
> load data — see [§4](#4-load-the-data). For the *local* smoke test you can instead
> point `.env.prod` at your existing local DB, or just confirm the API returns 200s.

Tear down when done: `docker compose -f docker-compose.prod.yml down`
(add `-v` to also wipe the DB volume).

---

## 1. Provision the EC2 instance

1. **Launch instance** — EC2 → Launch:
   - AMI: Ubuntu Server 22.04 LTS
   - Type: `t3.micro` (or `t2.micro`) — *Free tier eligible*
   - Storage: 30 GB gp3 (free-tier cap)
   - Key pair: create/download one for SSH
2. **Security group** (firewall):
   - SSH (22) — **My IP only**
   - HTTP (80) — Anywhere
   - HTTPS (443) — Anywhere
3. **Elastic IP** — EC2 → Elastic IPs → Allocate → Associate with the instance.
   Gives a stable public IP that survives reboots.
   ⚠️ An Elastic IP that is *not* associated with a running instance is billed —
   release it if you tear the instance down.

SSH in: `ssh -i your-key.pem ubuntu@<ELASTIC_IP>`

---

## 2. Prepare the box

```bash
# --- 2 GB swap (MANDATORY on a 1 GB box) ---
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h            # confirm: ~1Gi Mem + 2.0Gi Swap

# --- Docker + compose plugin ---
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu      # then log out/in so `docker` works w/o sudo
docker compose version
```

---

## 3. Deploy the stack

The repo is **private**, so give the box read access (deploy key):

```bash
ssh-keygen -t ed25519 -C "phjobmarket-deploy" -f ~/.ssh/id_ed25519 -N ""
cat ~/.ssh/id_ed25519.pub
# GitHub → repo → Settings → Deploy keys → Add (read-only), paste the key.

git clone git@github.com:gitgab29/PHJobMarket.git
cd PHJobMarket

cp .env.prod.example .env.prod
nano .env.prod          # real DJANGO_SECRET_KEY, strong DB_PASSWORD,
                        # ALLOWED_HOSTS=<ELASTIC_IP>,<domain>
chmod 600 .env.prod

docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
docker compose -f docker-compose.prod.yml ps     # all healthy/up
```

`migrations/001_raw_schema.sql` runs automatically on first Postgres start (the
`raw` schema). The `warehouse` schema comes from the data you load next.

---

## 4. Load the data

Scraping (Playwright/Chromium) is memory-heavy — **don't** scrape on the 1 GB box
for the first load. Copy your already-populated local warehouse instead.

**On your laptop** (Postgres is on host port 15432 per the project setup):

```bash
pg_dump -h localhost -p 15432 -U phjobmarket -d phjobmarket \
  -n raw -n warehouse --no-owner --no-privileges -Fc -f phjob.dump
scp -i your-key.pem phjob.dump ubuntu@<ELASTIC_IP>:~/PHJobMarket/
```

**On the box:**

```bash
docker compose -f docker-compose.prod.yml exec -T postgres \
  pg_restore -U phjobmarket -d phjobmarket --clean --if-exists --no-owner < phjob.dump

# sanity check
docker compose -f docker-compose.prod.yml exec postgres \
  psql -U phjobmarket -d phjobmarket -c "select count(*) from warehouse.fct_job_postings;"
```

---

## 5. Verify end-to-end

```bash
curl http://<ELASTIC_IP>/api/v1/analytics/summary/        # 200 + real numbers
docker compose -f docker-compose.prod.yml exec django python manage.py check --deploy
```

In a browser from another machine, open `http://<ELASTIC_IP>/`:
Jobs shows "~3,726 jobs", Dashboard charts render, **no console / CORS errors**.

**Exit gate:** all three routes work from an external browser.

---

## 6. Harden (before sharing the link)

- **HTTPS** — point a domain at the Elastic IP, then either put **Cloudflare**
  in front (free, easiest) or terminate TLS with **certbot**. Once HTTPS is live,
  set in `.env.prod`: `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=2592000`,
  then `up -d` again. Re-run `check --deploy` → should be clean.
- **DB backups** — cron a nightly dump off the box:
  ```bash
  docker compose -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U phjobmarket -Fc phjobmarket > ~/backups/phjob-$(date +%F).dump
  ```
- **Billing alarm** — Billing → CloudWatch alarm at **$1**. Free tier has sharp
  edges (data-transfer-out cap, detached Elastic IPs). This is your seatbelt.

---

## 6b. Refreshing data (optional)

To re-scrape later, run it as a deliberate, monitored **one-shot** when the box is
otherwise idle (never while serving traffic — Chromium will exhaust the 1 GB):
build a small scraper image from `scrapers/requirements.txt` + `playwright install
chromium`, run the scrapers, then `dbt build`. Easier: run scrapers on your laptop
against a local DB and re-do the `pg_dump`/`pg_restore` from [§4](#4-load-the-data).

---

## Quick reference

| Action | Command |
|---|---|
| Start / rebuild | `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build` |
| Stop | `docker compose -f docker-compose.prod.yml down` |
| Logs | `docker compose -f docker-compose.prod.yml logs -f django` |
| Django shell check | `... exec django python manage.py check --deploy` |
| DB psql | `... exec postgres psql -U phjobmarket -d phjobmarket` |
