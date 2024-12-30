import logging
import os

import requests
from airflow.decorators import task

logger = logging.getLogger(__name__)


@task.python
def get_latest_videos_by_playlist_id(params: dict):
    logger.info("Test")
    logger.info(params)
    logger.info(f'{os.environ["YOUTUBE_API_KEY"]=}')

    url_base = "https://www.googleapis.com/youtube/v3/playlistItems"
    query_params = {
        "part": "snippet,contentDetails",
        "playlistId": params["playlist_id"],
        "key": os.environ["YOUTUBE_API_KEY"],
        "maxResults": 10,
    }

    response = requests.get(url_base, params=query_params)

    if not response.ok:
        raise Exception(f"Issue retrieving data from YouTube. Error:\n{response.text}")

    results = []
    for item in response.json()["items"]:
        logger.info(
            f"{item['contentDetails']['videoId']} - {item['snippet']['publishedAt']} - "
            f"{item['snippet']['title']}"
        )
        results.append(
            {
                "title": item["snippet"]["title"],
                "creator": item["snippet"]["channelTitle"],
                "video_url": (
                    f"https://youtube.com/watch?v={item['contentDetails']['videoId']}"
                ),
                "upload_date": item["snippet"]["publishedAt"],
                "video_id": item["contentDetails"]["videoId"],
                "thumbnail": item["snippet"]["thumbnails"]["high"],
            }
        )

    return results
