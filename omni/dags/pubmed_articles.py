import datetime

import pendulum
from airflow.decorators import dag

from omni.tasks.pubmed.tasks import search_papers


@dag(
    dag_id="check_pubmed_articles",
    schedule_interval="0 12 * * 1",
    start_date=pendulum.datetime(2024, 1, 7, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def check_pubmed_articles_dag():
    """DAG to check for new PubMed articles."""

    search_papers(params={"search_term": "caregiving"})


check_pubmed_articles_dag()
