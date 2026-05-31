FROM apache/airflow:2.9.3-python3.11

USER root
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

USER airflow
RUN pip install --no-cache-dir \
    playwright==1.44.0 \
    beautifulsoup4==4.12.3 \
    psycopg2-binary==2.9.9 \
    requests==2.32.3 \
    dbt-postgres==1.8.2 \
    great-expectations==0.18.19

RUN playwright install chromium && playwright install-deps || true

COPY --chown=airflow:root scrapers/ /opt/airflow/scrapers/
COPY --chown=airflow:root dbt_transform/ /opt/airflow/dbt_transform/
COPY --chown=airflow:root gx/ /opt/airflow/gx/
