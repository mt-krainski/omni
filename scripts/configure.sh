#!/usr/bin/env bash

# This script prepares the development envrionment.
# It installs all relevant plugins, additional packages
# and creates a template .env file.

poetry install

poetry -q self add poetry-plugin-dotenv
poetry run pre-commit install

SECRET_KEY=$(poe -q generate-secret-key)

cat > .env <<EOL
AIRFLOW_HOME=$(pwd)/.airflow
NOTION_API_KEY=
NOTION_WATCHLIST_DB_ID=
YOUTUBE_API_KEY=
AIRFLOW__CORE__INTERNAL_API_SECRET_KEY=${SECRET_KEY}
AIRFLOW__WEBSERVER__SECRET_KEY=${SECRET_KEY}
NEW_YORK_TIMES_API_KEY=
OPENAI_API_KEY=
NEWS_FILTER_PROMPT=
SENDGRID_API_KEY=
SENDGRID_TEMPLATE_ID=
SENDGRID_FROM_EMAIL=
SENDGRID_TO_EMAIL=

# https://stackoverflow.com/questions/73582293/airflow-external-api-call-gives-negsignal-sigsegv-error
no_proxy=*
EOL
