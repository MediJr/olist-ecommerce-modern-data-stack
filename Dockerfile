# Image unique du projet : ingestion, dbt, Dagster et tableau de bord (ADR 005).
# Les services de docker-compose.yml l'utilisent avec des commandes différentes.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dépendances d'abord : cette couche n'est reconstruite que si requirements.txt change.
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-deps -e .

COPY dbt ./dbt
COPY dashboard ./dashboard
COPY .streamlit ./.streamlit
COPY tests ./tests
COPY scripts ./scripts

# Utilisateur sans privilèges : un conteneur n'a aucune raison de tourner en root.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /warehouse /dagster_home /app/data/landing \
    && chown -R app:app /app /warehouse /dagster_home
USER app

# Extension S3 de DuckDB installée à la construction : pas de téléchargement à chaque démarrage.
RUN python -c "import duckdb; duckdb.sql('INSTALL httpfs')"

ENV DAGSTER_HOME=/dagster_home \
    DBT_DUCKDB_PATH=/warehouse/olist.duckdb

EXPOSE 3000 8501
CMD ["dagster", "dev", "-m", "olist_pipeline.definitions", "-h", "0.0.0.0", "-p", "3000"]
