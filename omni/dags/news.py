import datetime
import os

import pendulum
from airflow.decorators import dag

from omni.tasks.chatgpt.tasks import filter_with_chatgpt
from omni.tasks.new_york_times.tasks import get_latest_articles
from omni.tasks.sendgrid.tasks import send_email

PROMPT = os.environ["NEWS_FILTER_PROMPT"]


@dag(
    dag_id="check_news",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2025, 1, 6, tz="UTC"),
    catchup=True,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def check_news_dag():
    """DAG to check for relevant news."""
    (
        get_latest_articles()
        >> filter_with_chatgpt(
            params={
                "source_task_id": "get_latest_articles",
                "prompt": PROMPT,
            }
        )
        >> send_email(
            params={
                "source_task_id": "filter_with_chatgpt",
            }
        )
    )


check_news_dag()
