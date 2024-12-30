import datetime

import pendulum
from airflow.decorators import dag, task
from airflow.operators.python import PythonOperator

from omni.tasks.notion.tasks import create_pages
from omni.tasks.youtube.tasks import get_latest_videos_by_playlist_id


@dag(
    dag_id="check_youtube_channels",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2024, 12, 28, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def CheckYoutubeChannels():

    @task.python
    def remap_values(ti, params):
        source_task_id = params["source_task_id"]
        data = ti.xcom_pull(task_ids=source_task_id)

        return [
            {
                "Name": item["title"],
                "Video URL": item["video_url"],
                "Creator": item["creator"],
                "Upload Date": datetime.datetime.fromisoformat(
                    item["upload_date"]
                ).date(),
                "Video ID": item["video_id"],
            }
            for item in data
        ]

    (
        get_latest_videos_by_playlist_id(
            params={"playlist_id": "UUHnyfMqiRRG1u-2MsSQLbXA"}
        )
        >> remap_values(params={"source_task_id": "get_latest_videos_by_playlist_id"})
        >> create_pages(
            params={
                "source_task_id": "remap_values",
                "database_id": "16b33426253f8091b73afb9760beaedb",
            }
        )
    )


CheckYoutubeChannels()
