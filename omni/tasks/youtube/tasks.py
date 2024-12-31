import logging
import os
from typing import List

import requests
from airflow.decorators import task

logger = logging.getLogger(__name__)


@task.python
def get_latest_videos_by_playlist_id(params: dict) -> List[dict]:
    """Retrieve the latest videos by playlist id.

    Args:
        params (dict): dict containing at least a "playlist_id" key

    Raises:
        ValueError: raised when there's an issue with the YouTube API.

    Returns:
        List[dict]: list of dicts, each item representing a video
    """
    url_base = "https://www.googleapis.com/youtube/v3/playlistItems"
    query_params = {
        "part": "snippet,contentDetails",
        "playlistId": params["playlist_id"],
        "key": os.environ["YOUTUBE_API_KEY"],
        "maxResults": 10,
    }

    response = requests.get(url_base, params=query_params, timeout=30)

    if not response.ok:
        raise ValueError(f"Issue retrieving data from YouTube. Error:\n{response.text}")

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
                "thumbnail": item["snippet"]["thumbnails"]["high"]["url"],
            }
        )

    return results
