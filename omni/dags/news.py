import datetime

import pendulum
from airflow.decorators import dag

from omni.tasks.new_york_times.tasks import get_latest_articles


@dag(
    dag_id="check_news",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2025, 1, 6, tz="UTC"),
    catchup=True,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def check_news_dag():
    """DAG to check for relevant news."""
    get_latest_articles()


check_news_dag()
