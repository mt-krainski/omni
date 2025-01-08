import os

from airflow.decorators import task
from airflow.models import TaskInstance
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


@task.python
def send_email(ti: TaskInstance, params: dict) -> None:
    data = ti.xcom_pull(task_ids=params["source_task_id"])
    message = Mail(
        from_email=os.environ["SENDGRID_FROM_EMAIL"],
        to_emails=os.environ["SENDGRID_TO_EMAIL"],
    )
    message.dynamic_template_data = {"articles": data}
    message.template_id = os.environ["SENDGRID_TEMPLATE_ID"]

    sg = SendGridAPIClient(os.environ.get("SENDGRID_API_KEY"))
    sg.send(message)
