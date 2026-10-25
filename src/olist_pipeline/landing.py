"""Simulation des livraisons du partenaire : l'archive Kaggle est découpée en exports mensuels.

Dans la vraie mission, la marketplace dépose un dossier par mois (décision D1 du cadrage). Ici, on le fabrique
à partir du jeu public, en le découpant par mois d'achat. Chaque dossier se termine par un fichier _SUCCESS,
écrit en dernier : c'est le signal convenu que la livraison est complète et peut être lue.
"""

import shutil
import zipfile
from pathlib import Path

import pandas as pd

from .config import FIRST_MONTH, LANDING_DIR, LAST_MONTH, MONTHLY_TABLES, REFERENCE_FOLDER, REFERENCE_TABLES, SOURCE_ZIP, TABLES

SUCCESS_MARKER = "_SUCCESS"


def all_months(first: str = FIRST_MONTH, last: str = LAST_MONTH) -> list[str]:
    """Tous les mois de la période, y compris ceux sans aucune commande (une livraison vide reste une livraison)."""
    return [p.strftime("%Y-%m") for p in pd.period_range(first, last, freq="M")]


def read_source(zip_path: Path = SOURCE_ZIP) -> dict[str, pd.DataFrame]:
    """Lit les 9 fichiers en texte brut : rien n'est converti, rien n'est perdu.

    La source est l'archive Kaggle, ou un dossier contenant les mêmes fichiers (échantillon de la CI).
    """
    if zip_path.is_dir():
        return {
            spec.name: pd.read_csv(zip_path / spec.source_file, dtype=str, keep_default_na=False)
            for spec in TABLES.values()
        }
    if not zip_path.exists():
        raise FileNotFoundError(f"Archive introuvable : {zip_path}. Voir le README, section « Données ».")
    with zipfile.ZipFile(zip_path) as archive:
        return {
            spec.name: pd.read_csv(archive.open(spec.source_file), dtype=str, keep_default_na=False)
            for spec in TABLES.values()
        }


def split_by_month(source: dict[str, pd.DataFrame]) -> dict[str, dict[str, pd.DataFrame]]:
    """Découpe les tables mensuelles : chaque ligne suit le mois d'achat de sa commande.

    Renvoie {mois: {table: lignes}}. Une ligne sans commande connue n'appartient à aucun mois : elle est
    signalée, car elle serait perdue silencieusement.
    """
    orders = source["orders"]
    month_of_order = orders.set_index("order_id")["order_purchase_timestamp"].str[:7]
    month_of_customer = orders.set_index("customer_id")["order_purchase_timestamp"].str[:7]
    keyed = {
        "orders": (orders, orders["order_purchase_timestamp"].str[:7]),
        "customers": (source["customers"], source["customers"]["customer_id"].map(month_of_customer)),
    }
    for name in ("order_items", "order_payments", "order_reviews"):
        keyed[name] = (source[name], source[name]["order_id"].map(month_of_order))

    by_month: dict[str, dict[str, pd.DataFrame]] = {m: {} for m in all_months()}
    for name, (frame, months) in keyed.items():
        orphans = int(months.isna().sum())
        if orphans:
            raise ValueError(f"{name} : {orphans} ligne(s) rattachée(s) à aucune commande")
        groups = dict(tuple(frame.groupby(months, sort=False)))
        for month in by_month:
            by_month[month][name] = groups.get(month, frame.iloc[0:0])
    return by_month


def _write_delivery(folder: Path, frames: dict[str, pd.DataFrame]) -> Path:
    """Écrit une livraison de façon atomique : dossier temporaire, puis renommage, puis marqueur _SUCCESS."""
    tmp = folder.with_name(folder.name + ".tmp")
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    for name, frame in frames.items():
        frame.to_csv(tmp / f"{name}.csv", index=False)
    shutil.rmtree(folder, ignore_errors=True)
    tmp.rename(folder)
    (folder / SUCCESS_MARKER).touch()
    return folder


def deliver_month(frames: dict[str, pd.DataFrame], month: str, landing_dir: Path = LANDING_DIR) -> Path:
    assert set(frames) == {t.name for t in MONTHLY_TABLES}
    return _write_delivery(landing_dir / month, frames)


def deliver_reference(source: dict[str, pd.DataFrame], landing_dir: Path = LANDING_DIR) -> Path:
    return _write_delivery(landing_dir / REFERENCE_FOLDER, {t.name: source[t.name] for t in REFERENCE_TABLES})


def is_complete(folder: Path) -> bool:
    return (folder / SUCCESS_MARKER).exists()


def delivered_months(landing_dir: Path = LANDING_DIR) -> list[str]:
    """Les livraisons mensuelles complètes présentes dans la zone de dépôt."""
    if not landing_dir.exists():
        return []
    return sorted(p.name for p in landing_dir.iterdir() if p.is_dir() and p.name[:2] == "20" and is_complete(p))
