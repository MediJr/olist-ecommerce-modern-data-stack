"""Ingestion : une livraison (CSV) devient une partition de la couche bronze (Parquet) du lac.

La couche bronze garde les données TELLES QUE LIVRÉES (tout en texte) : le typage et le nettoyage se font
dans dbt (couche staging). Ce module vérifie seulement que la livraison respecte son contrat.
"""

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path

from . import lake
from .config import LAKE_URI, LANDING_DIR, REFERENCE_FOLDER, TableSpec
from .landing import is_complete


class DeliveryError(Exception):
    """La livraison ne respecte pas son contrat : elle est refusée, rien n'est écrit dans le lac."""


@dataclass
class IngestResult:
    table: str
    month: str | None
    rows: int
    path: str
    sha256: str


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check_header(path: Path, spec: TableSpec) -> None:
    """Dérive de schéma (schema drift) : une colonne ajoutée, renommée ou déplacée bloque l'ingestion."""
    with path.open(encoding="utf-8", newline="") as f:
        header = next(csv.reader(f), [])
    if tuple(header) != spec.columns:
        missing = [c for c in spec.columns if c not in header]
        extra = [c for c in header if c not in spec.columns]
        raise DeliveryError(f"{path.name} : en-tête inattendu (manquantes : {missing}, en trop : {extra})")


def ingest(spec: TableSpec, month: str | None, landing_dir: Path = LANDING_DIR, uri: str = LAKE_URI) -> IngestResult:
    """Charge un fichier livré dans le lac. Rejouer le même mois REMPLACE la partition : aucun doublon possible."""
    folder = landing_dir / (month or REFERENCE_FOLDER)
    if not is_complete(folder):
        raise DeliveryError(f"Livraison {folder.name} incomplète : pas de marqueur _SUCCESS")
    path = folder / f"{spec.name}.csv"
    if not path.exists():
        raise DeliveryError(f"Fichier manquant : {path}")
    check_header(path, spec)

    con = lake.connect(uri)
    # Colonnes déclarées explicitement, toutes en texte : un mois vide (en-tête seul) se lit aussi bien qu'un mois plein.
    columns = "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in spec.columns) + "}"
    con.execute(
        "CREATE TEMP TABLE delivery AS SELECT * FROM read_csv("
        f"?, header = true, columns = {columns}, quote = '\"', escape = '\"')",
        [str(path)],
    )
    rows = con.execute("SELECT count(*) FROM delivery").fetchone()[0]

    if spec.key:
        key = ", ".join(spec.key)
        blank = con.execute(
            "SELECT count(*) FROM delivery WHERE " + " OR ".join(f"coalesce({c}, '') = ''" for c in spec.key)
        ).fetchone()[0]
        duplicates = con.execute(
            f"SELECT count(*) FROM (SELECT {key} FROM delivery GROUP BY {key} HAVING count(*) > 1)"
        ).fetchone()[0]
        if blank or duplicates:
            raise DeliveryError(f"{spec.name} {month or ''} : {blank} clé(s) vide(s), {duplicates} clé(s) en double")

    target = lake.bronze_path(spec.name, month, uri)
    lake.prepare_local_dir(target)
    # Colonnes techniques préfixées par « _ » : d'où vient la ligne, et quand elle est entrée dans le lac.
    con.execute(
        f"""
        COPY (
            SELECT *, ? AS _source_file, current_timestamp AS _ingested_at FROM delivery
        ) TO '{target}' (FORMAT parquet, COMPRESSION zstd)
        """,
        [f"{folder.name}/{path.name}"],
    )
    con.close()
    return IngestResult(spec.name, month, rows, target, sha256(path))
