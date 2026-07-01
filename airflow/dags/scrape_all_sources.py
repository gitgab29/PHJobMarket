from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule

default_args = {
    "owner": "phjobmarket",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "execution_timeout": timedelta(minutes=30),
}

DB_CONN = "postgresql://phjobmarket:phjobmarket@postgres:5432/phjobmarket"


def run_scraper(scraper_class_path: str, **kwargs):
    import importlib
    import logging
    logger = logging.getLogger(__name__)

    module_path, class_name = scraper_class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    scraper_cls = getattr(module, class_name)

    scraper = scraper_cls(db_conn_string=DB_CONN)
    count = scraper.run()
    logger.info("Scraper %s returned %d records", class_name, count)
    kwargs["ti"].xcom_push(key="record_count", value=count)
    return count


def log_scrape_result(source: str, **kwargs):
    import psycopg2
    ti = kwargs["ti"]
    count = ti.xcom_pull(task_ids=f"scrape_{source}", key="record_count") or 0
    conn = psycopg2.connect(DB_CONN)
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO raw.scrape_log (source, started_at, finished_at, records_scraped, status)
               VALUES (%s, %s, NOW(), %s, 'success')""",
            (source, kwargs["execution_date"], count),
        )
    conn.commit()
    conn.close()


def on_failure_callback(context):
    import psycopg2
    source = context["task"].task_id.replace("scrape_", "")
    error = str(context.get("exception", "Unknown error"))
    conn = psycopg2.connect(DB_CONN)
    with conn.cursor() as cur:
        cur.execute(
            """INSERT INTO raw.scrape_log (source, started_at, finished_at, records_scraped, status, error_message)
               VALUES (%s, %s, NOW(), 0, 'failed', %s)""",
            (source, context["execution_date"], error[:1000]),
        )
    conn.commit()
    conn.close()


SCRAPERS = {
    "philjobnet": "scrapers.philjobnet.PhilJobNetScraper",
    "kalibrr": "scrapers.kalibrr.KalibrrScraper",
    "jobstreet": "scrapers.jobstreet.JobStreetScraper",
    "onlinejobs": "scrapers.onlineJobs.OnlineJobsScraper",
    "indeed": "scrapers.indeed.IndeedScraper",
    "facebook": "scrapers.facebook.FacebookScraper",
}

with DAG(
    dag_id="scrape_all_sources",
    default_args=default_args,
    description="Scrape all PH job sources daily",
    schedule_interval="0 18 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_tasks=3,
    tags=["scraping", "etl"],
) as dag:
    start = EmptyOperator(task_id="start")
    end = EmptyOperator(task_id="end", trigger_rule=TriggerRule.ALL_DONE)

    for source, class_path in SCRAPERS.items():
        scrape_task = PythonOperator(
            task_id=f"scrape_{source}",
            python_callable=run_scraper,
            op_kwargs={"scraper_class_path": class_path},
            on_failure_callback=on_failure_callback,
        )
        log_task = PythonOperator(
            task_id=f"log_{source}",
            python_callable=log_scrape_result,
            op_kwargs={"source": source},
            trigger_rule=TriggerRule.ALL_SUCCESS,
        )
        start >> scrape_task >> log_task >> end
