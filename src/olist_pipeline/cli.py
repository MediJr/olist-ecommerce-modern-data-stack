"""Ligne de commande, utile sans l'interface Dagster (intégration continue, dépannage).

    python -m olist_pipeline.cli deliver --month 2017-01      # simule la livraison d'un mois par le partenaire
    python -m olist_pipeline.cli deliver --all                # toutes les livraisons, plus les référentiels
    python -m olist_pipeline.cli ingest --month 2017-01       # charge un mois dans la couche bronze
    python -m olist_pipeline.cli ingest --all                 # tous les mois livrés, plus les référentiels

En exploitation normale, c'est Dagster qui lance l'ingestion (capteur sur la zone de dépôt).
"""

import argparse
import sys
from pathlib import Path

from . import bronze, landing
from .config import LANDING_DIR, MONTHLY_TABLES, REFERENCE_FOLDER, REFERENCE_TABLES, SOURCE_ZIP


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="olist_pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("deliver", "ingest"):
        p = sub.add_parser(name)
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--month", help="mois au format AAAA-MM")
        group.add_argument("--all", action="store_true")
        p.add_argument("--landing", type=Path, default=LANDING_DIR)
    sub.choices["deliver"].add_argument("--zip", type=Path, default=SOURCE_ZIP)
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")     # accents lisibles dans la console Windows

    if args.command == "deliver":
        source = landing.read_source(args.zip)
        by_month = landing.split_by_month(source)
        months = list(by_month) if args.all else [args.month]
        # Les référentiels sont livrés une fois (ou quand ils changent), pas à chaque mois.
        if args.all or not landing.is_complete(args.landing / REFERENCE_FOLDER):
            landing.deliver_reference(source, args.landing)
            print("livré : référentiels")
        for month in months:
            landing.deliver_month(by_month[month], month, args.landing)
            print(f"livré : {month}  ({len(by_month[month]['orders']):,} commandes)")
        return

    months = landing.delivered_months(args.landing) if args.all else [args.month]
    for spec in REFERENCE_TABLES:
        result = bronze.ingest(spec, None, args.landing)
        print(f"bronze  {result.table:<22} référentiel  {result.rows:>9,} lignes")
    for month in months:
        for spec in MONTHLY_TABLES:
            result = bronze.ingest(spec, month, args.landing)
            print(f"bronze  {result.table:<22} {month}      {result.rows:>9,} lignes")


if __name__ == "__main__":
    main()
