import os
from datetime import datetime

from airflow.decorators import task
from notion_client import Client


@task.python
def create_pages(ti, params):
    database_id = params["database_id"]

    properties_list = ti.xcom_pull(task_ids=params["source_task_id"])

    # params["properties"] is a list of objects, where each item is a collection of
    # properties. The naming is a bit unfortunate but I don't have a better idea right
    # now.
    for properties in properties_list:
        _create_page(database_id, properties)


def _create_page(database_id, properties, icon_emoji=None, cover_url=None):
    notion = Client(auth=os.environ["NOTION_API_KEY"])

    database = notion.databases.retrieve(database_id)

    request_object = {}

    request_object["parent"] = {"type": "database_id", "database_id": database_id}

    mapped_properties = {}
    for property, value in properties.items():
        mapped_properties[property] = _map_value(
            value, database["properties"][property]
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


def _map_value(value, property_schema):
    property_map = {
        "title": _map_title,
        "rich_text": _map_rich_text,
        "date": _map_date,
        "status": _map_status,
        "url": _map_url,
    }
    return property_map[property_schema["type"]](value, property_schema)


def _map_title(value, *args, **kwargs):
    return {
        "id": "title",
        "type": "title",
        "title": [{"type": "text", "text": {"content": value, "link": None}}],
    }


def _map_rich_text(value, *args, **kwargs):
    return {
        "rich_text": [
            {
                "type": "text",
                "text": {"content": value},
            }
        ]
    }


def _map_date(value: datetime, *args, **kwargs):
    return {"type": "date", "date": {"start": value.isoformat()}}


def _map_status(value, property_schema, *args, **kwargs):
    for option in property_schema["status"]["options"]:
        if option["name"] == value:
            break
    else:
        raise ValueError(
            f"Provided name '{value}' does not match any of the existing options"
        )
    return {"status": {"name": value}}


def _map_url(value, *args, **kwargs):
    return {"url": value}
