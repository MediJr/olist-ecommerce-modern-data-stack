"""Fabrique l'échantillon versionné de l'intégration continue à partir de l'archive Kaggle.

    python scripts/make_ci_sample.py

L'archive complète n'est pas versionnée (licence, 45 Mo). La CI travaille sur un extrait COHÉRENT : quelques
centaines de commandes de trois mois, avec exactement les clients, produits, vendeurs et codes postaux qu'elles
utilisent. Ainsi, tous les tests de relations (clés étrangères) de dbt restent valides sur l'échantillon.
"""

from pathlib import Path

from olist_pipeline.config import TABLES
from olist_pipeline.landing import read_source

OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "sample"
MONTHS = ("2017-01", "2017-02", "2017-03")
ORDERS_PER_MONTH = 150


def main() -> None:
    src = read_source()
    orders = src["orders"]
    orders = orders[orders["order_purchase_timestamp"].str[:7].isin(MONTHS)]
    # Échantillon déterministe (random_state) : la CI donne toujours le même résultat.
    sample = orders.groupby(orders["order_purchase_timestamp"].str[:7], group_keys=False).sample(
        n=ORDERS_PER_MONTH, random_state=42
    )
    ids = set(sample["order_id"])
    frames = {
        "orders": sample,
        "order_items": src["order_items"][src["order_items"]["order_id"].isin(ids)],
        "order_payments": src["order_payments"][src["order_payments"]["order_id"].isin(ids)],
        "order_reviews": src["order_reviews"][src["order_reviews"]["order_id"].isin(ids)],
        "customers": src["customers"][src["customers"]["customer_id"].isin(set(sample["customer_id"]))],
    }
    frames["products"] = src["products"][src["products"]["product_id"].isin(set(frames["order_items"]["product_id"]))]
    frames["sellers"] = src["sellers"][src["sellers"]["seller_id"].isin(set(frames["order_items"]["seller_id"]))]
    frames["category_translation"] = src["category_translation"]
    zips = set(frames["customers"]["customer_zip_code_prefix"]) | set(frames["sellers"]["seller_zip_code_prefix"])
    geo = src["geolocation"][src["geolocation"]["geolocation_zip_code_prefix"].isin(zips)]
    frames["geolocation"] = geo.groupby("geolocation_zip_code_prefix").head(5)   # 5 points par code postal suffisent

    OUT.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(OUT / TABLES[name].source_file, index=False)
        print(f"{TABLES[name].source_file:<42} {len(frame):>6} lignes")


if __name__ == "__main__":
    main()
