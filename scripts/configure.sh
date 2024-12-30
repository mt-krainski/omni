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
YOUTUBE_API_KEY=
AIRFLOW__CORE__INTERNAL_API_SECRET_KEY=${SECRET_KEY}
AIRFLOW__WEBSERVER__SECRET_KEY=${SECRET_KEY}

# https://stackoverflow.com/questions/73582293/airflow-external-api-call-gives-negsignal-sigsegv-error
no_proxy=*
EOL
