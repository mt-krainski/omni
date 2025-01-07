import os
from datetime import datetime

import requests
from airflow.decorators import task
from airflow.models.taskinstance import TaskInstance

LATEST_ARTICLES_URL = "https://api.nytimes.com/svc/news/v3/content/all/all.json"
LATEST_ARTICLES_QUERY_PARAMS = {
    "api-key": os.environ["NEW_YORK_TIMES_API_KEY"],
    "limit": 100,
}


@task.python
def get_latest_articles(ti: TaskInstance) -> dict:
    """Load latest articles from the NYT API.

    Args:
        ti (TaskInstance): Airflow Task Instance

    Returns:
        dict: dictionary of results
    """
    response = requests.get(
        LATEST_ARTICLES_URL, params=LATEST_ARTICLES_QUERY_PARAMS, timeout=60
    )
    response.raise_for_status()

    print(f"Execution date: {ti.execution_date}")

    filtered_articles = []
    for article in response.json()["results"]:
        if article["section"] == "En español":
            continue

        if article["item_type"].lower() != "article":
            continue

        if (
            pub_date := datetime.fromisoformat(article["published_date"]).date()
        ) != ti.execution_date.date():
            print(f"Found article published at {pub_date}")
            continue

        filtered_articles.append(
            {
                "title": article["title"],
                "abstract": article["abstract"],
                "url": article["url"],
            }
        )

    return filtered_articles
