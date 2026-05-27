# 10. Docker Compose Configuration

## docker-compose.yml

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: phjobmarket
      POSTGRES_USER: phjobmarket
      POSTGRES_PASSWORD: phjobmarket
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./migrations:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U phjobmarket"]
      interval: 5s
      retries: 5

  airflow-init:
    build: { context: ., dockerfile: airflow/Dockerfile }
    entrypoint: >
      bash -c "
        airflow db init &&
        airflow users create --username admin --password admin
          --firstname Admin --lastname User --role Admin --email admin@example.com
      "
    environment: &airflow-env
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://phjobmarket:phjobmarket@postgres:5432/phjobmarket
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
      AIRFLOW__CORE__DAGS_FOLDER: /opt/airflow/dags
      DB_HOST: postgres
      DB_USER: phjobmarket
      DB_PASSWORD: phjobmarket
      DB_NAME: phjobmarket
    volumes: &airflow-vols
      - ./airflow/dags:/opt/airflow/dags
      - ./scrapers:/opt/airflow/scrapers
      - ./dbt_transform:/opt/airflow/dbt_transform
    depends_on:
      postgres: { condition: service_healthy }

  airflow-webserver:
    build: { context: ., dockerfile: airflow/Dockerfile }
    command: airflow webserver --port 8080
    environment: *airflow-env
    ports: ["8080:8080"]
    volumes: *airflow-vols
    depends_on:
      airflow-init: { condition: service_completed_successfully }

  airflow-scheduler:
    build: { context: ., dockerfile: airflow/Dockerfile }
    command: airflow scheduler
    environment: *airflow-env
    volumes: *airflow-vols
    depends_on:
      airflow-init: { condition: service_completed_successfully }

  api:
    build: { context: ./api, dockerfile: Dockerfile }
    command: >
      bash -c "python manage.py collectstatic --noinput &&
               gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3"
    environment:
      DB_HOST: postgres
      DB_USER: phjobmarket
      DB_PASSWORD: phjobmarket
      DB_NAME: phjobmarket
      DJANGO_SECRET_KEY: change-me-in-production
      DEBUG: "false"
    ports: ["8000:8000"]
    depends_on:
      postgres: { condition: service_healthy }

  frontend:
    build: { context: ./frontend, dockerfile: Dockerfile }
    ports: ["3000:80"]
    depends_on: [api]

volumes:
  pgdata:
```

## Dockerfiles

```dockerfile
# airflow/Dockerfile
FROM apache/airflow:2.9.3-python3.11
USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
USER airflow
RUN pip install --no-cache-dir playwright==1.44.0 beautifulsoup4==4.12.3 psycopg2-binary==2.9.9 \
    requests==2.32.3 dbt-postgres==1.8.2 great-expectations==0.18.19
RUN playwright install chromium && playwright install-deps || true
COPY --chown=airflow:root scrapers/ /opt/airflow/scrapers/
COPY --chown=airflow:root dbt_transform/ /opt/airflow/dbt_transform/
```

```dockerfile
# api/Dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# frontend/nginx.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;
    location / { try_files $uri $uri/ /index.html; }
    location /api/ { proxy_pass http://api:8000; proxy_set_header Host $host; }
}
```

## Makefile

```makefile
.PHONY: up down build logs scrape dbt-run dbt-test lint test
up:      docker compose up -d
down:    docker compose down
build:   docker compose build
logs:    docker compose logs -f
scrape:  docker compose exec airflow-scheduler python -c \
           "from scrapers.philjobnet import PhilJobNetScraper; \
            s = PhilJobNetScraper('postgresql://phjobmarket:phjobmarket@postgres:5432/phjobmarket'); \
            print(f'Scraped {s.run()} records')"
dbt-run: docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_transform && dbt run"
dbt-test: docker compose exec airflow-scheduler bash -c "cd /opt/airflow/dbt_transform && dbt test"
```
