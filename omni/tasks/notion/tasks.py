import os
from datetime import datetime
from time import sleep
from typing import List, Optional

from airflow.decorators import task
from airflow.models.taskinstance import TaskInstance
from notion_client import Client


@task.python
def create_pages(ti: TaskInstance, params: dict) -> None:
    """Create pages in Notion based on values in XCom.

    Args:
        ti (TaskInstance): Airflow Task Instance
        params (dict): dict containing at least a "database_id" and "source_task_id"
            keys
    """
    database_id = params["database_id"]

    entries_to_be_created = ti.xcom_pull(task_ids=params["source_task_id"])

    for entry in entries_to_be_created:
        _create_page(database_id, **entry)


def _create_page(database_id, properties, icon_emoji=None, cover_url=None):
    notion = Client(auth=os.environ["NOTION_API_KEY"])

    database = notion.databases.retrieve(database_id)

    request_object = {}

    request_object["parent"] = {"type": "database_id", "database_id": database_id}

    mapped_properties = {}
    for property_name, value in properties.items():
        mapped_properties[property_name] = _convert_value_to_notion_format(
            value, database["properties"][property_name]
        )
    request_object["properties"] = mapped_properties

    if icon_emoji is not None:
        request_object["icon"] = {"type": "emoji", "emoji": icon_emoji}

    if cover_url is not None:
        request_object["cover"] = {
            "type": "external",
            "external": {"url": cover_url},
        }
    notion.pages.create(**request_object)

    # Notion's API rate limitation is around 3 requests per second. This should slow
    # down the page creations so that we don't exceed the limits.
    sleep(1)


def _convert_value_to_notion_format(value, property_schema):
    property_map = {
        "title": _convert_title_to_notion_format,
        "rich_text": _convert_rich_text_to_notion_format,
        "date": _convert_date_to_notion_format,
        "status": _convert_status_to_notion_format,
        "url": _convert_url_to_notion_format,
    }
    return property_map[property_schema["type"]](value, property_schema)


def _convert_title_to_notion_format(value, *args, **kwargs):
    return {
        "id": "title",
        "type": "title",
        "title": [{"type": "text", "text": {"content": value, "link": None}}],
    }


def _convert_rich_text_to_notion_format(value, *args, **kwargs):
    return {
        "rich_text": [
            {
                "type": "text",
                "text": {"content": value},
            }
        ]
    }


def _convert_date_to_notion_format(value: datetime, *args, **kwargs):
    return {"type": "date", "date": {"start": value.isoformat()}}


def _convert_status_to_notion_format(value, property_schema, *args, **kwargs):
    for option in property_schema["status"]["options"]:
        if option["name"] == value:
            break
    else:
        raise ValueError(
            f"Provided name '{value}' does not match any of the existing options"
        )
    return {"status": {"name": value}}


def _convert_url_to_notion_format(value, *args, **kwargs):
    return {"url": value}


def get_database_contents(
    database_id: str,
    filter_query: dict,
    sort_query: List[dict],
    page_size: Optional[int] = 100,
) -> dict:
    """Pull the contents of the database, based on provided filters.

    Args:
        database_id (str): ID of the database
        filter_query (dict): Notion API filter
        sort_query (dict): Notion API sorts
        page_size (int, optional): How many results to return. Max 100. Defaults to 100.

    Returns:
        dict: Pages in the database, formatted in the internal format
    """
    notion = Client(auth=os.environ["NOTION_API_KEY"])
    notion_database_contents = notion.databases.query(
        database_id=database_id,
        filter=filter_query,
        sorts=sort_query,
        page_size=page_size,
    )

    results = []
    for item in notion_database_contents["results"]:
        results.append(
            {
                prop: _convert_value_to_internal_format(value)
                for prop, value in item["properties"].items()
            }
        )

    return results


def _convert_value_to_internal_format(value):
    property_map = {
        "title": _convert_title_to_internal_format,
        "rich_text": _convert_rich_text_to_internal_format,
        "date": _convert_date_to_internal_format,
        "status": _convert_status_to_internal_format,
        "url": _convert_url_to_internal_format,
        "button": _convert_button_to_internal_format,
    }
    return property_map[value["type"]](value)


def _convert_title_to_internal_format(value, *args, **kwargs):
    return "".join(t["plain_text"] for t in value["title"])


def _convert_rich_text_to_internal_format(value, *args, **kwargs):
    return "".join(t["plain_text"] for t in value["rich_text"])


def _convert_date_to_internal_format(value, *args, **kwargs):
    # TODO: This doesn't take into account the possible end date.
    # For now I decided to keep this simple.
    return datetime.fromisoformat(value["date"]["start"])


def _convert_status_to_internal_format(value, *args, **kwargs):
    return value["status"]["name"]


def _convert_url_to_internal_format(value, *args, **kwargs):
    return value["url"]


def _convert_button_to_internal_format(value, *args, **kwargs):
    return "button"
