"""Accès au data lake avec DuckDB, que le lac soit un stockage S3 ou un dossier local."""

from pathlib import Path

import duckdb

from .config import LAKE_URI, s3_settings


def is_s3(uri: str = LAKE_URI) -> bool:
    return uri.startswith("s3://")


def connect(uri: str = LAKE_URI) -> duckdb.DuckDBPyConnection:
    """Connexion DuckDB en mémoire, configurée pour lire et écrire dans le lac.

    DuckDB sert ici de moteur de lecture-écriture, pas de base : rien n'est conservé dans la connexion.
    """
    con = duckdb.connect()
    if is_s3(uri):
        s3 = s3_settings()
        con.execute("INSTALL httpfs; LOAD httpfs;")
        # Secret DuckDB : les clés restent en mémoire, elles ne sont écrites nulle part.
        con.execute(
            """
            CREATE OR REPLACE SECRET lake (
                TYPE s3, KEY_ID ?, SECRET ?, ENDPOINT ?, URL_STYLE 'path', USE_SSL false, REGION 'us-east-1'
            )
            """,
            [s3["key_id"], s3["secret"], s3["endpoint"]],
        )
    return con


def bronze_path(table: str, month: str | None, uri: str = LAKE_URI) -> str:
    """Emplacement d'un fichier de la couche bronze.

    Les tables mensuelles suivent la convention « Hive » (dossier clé=valeur), que DuckDB, Spark ou BigQuery
    savent lire comme une colonne : bronze/orders/delivery_month=2017-01/orders.parquet.
    """
    if month is None:
        return f"{uri}/bronze/{table}/{table}.parquet"
    return f"{uri}/bronze/{table}/delivery_month={month}/{table}.parquet"


def prepare_local_dir(path: str) -> None:
    """Sur un lac local, crée le dossier parent (sur S3, les « dossiers » n'existent pas)."""
    if not path.startswith("s3://"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
