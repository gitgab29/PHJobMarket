from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

default_args = {
    "owner": "phjobmarket",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=3),
}

DBT_DIR = "/opt/airflow/dbt_transform"

DBT_ENV = {
    "DB_HOST": "postgres",
    "DB_PORT": "5432",
    "DB_USER": "phjobmarket",
    "DB_PASSWORD": "phjobmarket",
    "DB_NAME": "phjobmarket",
}

with DAG(
    dag_id="dbt_transform",
    default_args=default_args,
    description="Run dbt models after scraping completes",
    schedule_interval="0 20 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["dbt", "transform"],
) as dag:
    wait_for_scraping = ExternalTaskSensor(
        task_id="wait_for_scraping",
        external_dag_id="scrape_all_sources",
        external_task_id="end",
        timeout=3600,
        mode="poke",
        poke_interval=120,
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {DBT_DIR} && dbt deps --profiles-dir .",
        env=DBT_ENV,
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT_DIR} && dbt seed --profiles-dir .",
        env=DBT_ENV,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {DBT_DIR} && dbt run --full-refresh --profiles-dir .",
        env=DBT_ENV,
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_DIR} && dbt test --profiles-dir .",
        env=DBT_ENV,
    )

    dbt_docs = BashOperator(
        task_id="dbt_docs_generate",
        bash_command=f"cd {DBT_DIR} && dbt docs generate --profiles-dir .",
        env=DBT_ENV,
    )

    wait_for_scraping >> dbt_deps >> dbt_seed >> dbt_run >> dbt_test >> dbt_docs
