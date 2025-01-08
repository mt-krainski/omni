from typing import List

from airflow.decorators import task
from airflow.models.taskinstance import TaskInstance
from openai import OpenAI


@task.short_circuit(ignore_downstream_trigger_rules=False)
def filter_with_chatgpt(ti: TaskInstance, params: dict) -> List[dict]:
    client = OpenAI()
    data_list = ti.xcom_pull(task_ids=params["source_task_id"])
    prompt = params["prompt"]
    result_list = []
    for item in data_list:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\nData: {item}\n\n"
                        "Return only 'True' if the condition is met, otherwise 'False'."
                    ),
                },
            ],
            max_tokens=10,
            n=1,
            temperature=0,
        )
        if response.choices[0].message.content == "True":
            result_list.append(item)

    if len(result_list) == 0:
        return

    return result_list
