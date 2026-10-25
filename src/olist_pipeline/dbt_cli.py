"""Lance dbt avec l'environnement du projet (.env, chemin de l'entrepôt, emplacement du lac).

    python -m olist_pipeline.dbt_cli build          # équivaut à « dbt build » dans le dossier dbt/
    python -m olist_pipeline.dbt_cli docs generate

dbt ne lit pas le fichier .env tout seul : ce petit lanceur s'en charge, pour Hugo comme pour Dagster.
"""

import os
import sys
from pathlib import Path

from .config import DBT_DIR, LAKE_URI, WAREHOUSE_PATH


def dbt_environment() -> dict[str, str]:
    WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # L'exécutable dbt est à côté de l'interpréteur Python : on le rend trouvable même sans activer l'environnement.
    scripts = str(Path(sys.executable).parent)
    if scripts not in os.environ.get("PATH", "").split(os.pathsep):
        os.environ["PATH"] = scripts + os.pathsep + os.environ.get("PATH", "")
    os.environ.setdefault("DBT_DUCKDB_PATH", str(WAREHOUSE_PATH))
    os.environ["LAKE_URI"] = LAKE_URI
    os.environ.setdefault("DBT_PROFILES_DIR", str(DBT_DIR))
    return dict(os.environ)


def main() -> None:
    from dbt.cli.main import dbtRunner

    dbt_environment()
    result = dbtRunner().invoke([*sys.argv[1:], "--project-dir", str(DBT_DIR)])
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
