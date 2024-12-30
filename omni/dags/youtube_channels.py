import datetime

import pendulum
from airflow.decorators import dag, task
from airflow.operators.empty import EmptyOperator
from airflow.utils.trigger_rule import TriggerRule
from slugify import slugify

from omni.tasks.notion.tasks import create_pages, get_database_contents
from omni.tasks.youtube.tasks import get_latest_videos_by_playlist_id

CREATORS = [
    {
        "creator": "Veritasium",
        "playlist_id": "UUHnyfMqiRRG1u-2MsSQLbXA",
    },
    {
        "creator": "DIY Perks",
        "playlist_id": "UUUQo7nzH1sXVpzL92VesANw",
    },
    {
        "creator": "Marques Brownlee",
        "playlist_id": "UUBJycsmduvYEL83R_U4JriQ",
    },
    {
        "creator": "Kurzgesagt - In a Nutshell",
        "playlist_id": "UUsXVk37bltHxD1rDPwtNM8Q",
    },
]
WATCHLIST_DATABASE_ID = "16b33426253f8091b73afb9760beaedb"


@dag(
    dag_id="check_youtube_channels",
    schedule_interval="0 0 * * *",
    start_date=pendulum.datetime(2024, 12, 28, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def check_youtube_channels_dag():
    """DAG to check for new YouTube videos on selected channels."""

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

    @task.short_circuit(ignore_downstream_trigger_rules=False)
    def filter_results(ti, params):
        source_task_id = params["source_task_id"]
        database_id = params["database_id"]
        creator = params["creator"]
        latest_videos_by_creator = ti.xcom_pull(task_ids=source_task_id)

        last_received_videos = get_database_contents(
            database_id,
            {
                "property": "Creator",
                "rich_text": {"equals": creator},
            },
            [{"property": "Upload Date", "direction": "descending"}],
            page_size=1,
        )
        if len(last_received_videos) == 0:
            return latest_videos_by_creator

        last_received_video = last_received_videos[0]

        new_videos = []
        for video in latest_videos_by_creator:
            if video["Video ID"] == last_received_video["Video ID"]:
                break

        return new_videos

    done = EmptyOperator(task_id="done", trigger_rule=TriggerRule.ALL_DONE)

    for creator in CREATORS:
        creator_slug = slugify(creator["creator"], separator="_")
        (
            get_latest_videos_by_playlist_id.override(
                task_id=f"get_latest_videos_{creator_slug}"
            )(
                params={"playlist_id": creator["playlist_id"]},
            )
            >> remap_values.override(task_id=f"remap_values_{creator_slug}")(
                params={"source_task_id": f"get_latest_videos_{creator_slug}"},
            )
            >> filter_results.override(task_id=f"filter_results_{creator_slug}")(
                params={
                    "source_task_id": f"remap_values_{creator_slug}",
                    "database_id": WATCHLIST_DATABASE_ID,
                    "creator": creator["creator"],
                },
            )
            >> create_pages.override(task_id=f"create_pages_{creator_slug}")(
                params={
                    "source_task_id": f"filter_results_{creator_slug}",
                    "database_id": WATCHLIST_DATABASE_ID,
                },
            )
            >> done
        )


check_youtube_channels_dag()
