"""Paramètres du pipeline : chemins, emplacement du lac, et contrat de chaque fichier livré.

Les secrets (clés S3) sont lus dans .env, exclu de Git.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_DIR / "data"
SOURCE_ZIP = DATA_DIR / "source" / "olist-brazilian-ecommerce.zip"   # archive Kaggle, téléchargée par le client
LANDING_DIR = DATA_DIR / "landing"                                    # livraisons mensuelles simulées (une par dossier)
DBT_DIR = PROJECT_DIR / "dbt"

load_dotenv(PROJECT_DIR / ".env")

# Entrepôt construit par dbt. Dans Docker : /warehouse/olist.duckdb, un volume partagé avec le tableau de bord.
WAREHOUSE_PATH = Path(os.getenv("DBT_DUCKDB_PATH", str(DATA_DIR / "warehouse" / "olist.duckdb")))

# Le lac est soit un stockage S3 (s3://bucket), soit un dossier local (intégration continue).
# Le code ne fait pas la différence : DuckDB lit et écrit les deux de la même façon.
LAKE_URI = os.getenv("LAKE_URI", str(DATA_DIR / "lake")).rstrip("/")

REFERENCE_FOLDER = "reference"    # les référentiels (produits, vendeurs…) sont livrés en entier, à part

# Première et dernière livraison mensuelle : mois d'achat présents dans le jeu Olist.
FIRST_MONTH = "2016-09"
LAST_MONTH = "2018-10"


@dataclass(frozen=True)
class TableSpec:
    """Contrat d'un fichier livré : nom du fichier, colonnes attendues, clé d'unicité."""
    name: str
    source_file: str
    columns: tuple[str, ...]
    key: tuple[str, ...]
    monthly: bool                # True : livré chaque mois (découpé par mois d'achat) ; False : référentiel complet


TABLES = {
    t.name: t
    for t in (
        TableSpec("orders", "olist_orders_dataset.csv",
                  ("order_id", "customer_id", "order_status", "order_purchase_timestamp", "order_approved_at",
                   "order_delivered_carrier_date", "order_delivered_customer_date", "order_estimated_delivery_date"),
                  key=("order_id",), monthly=True),
        TableSpec("order_items", "olist_order_items_dataset.csv",
                  ("order_id", "order_item_id", "product_id", "seller_id", "shipping_limit_date", "price",
                   "freight_value"),
                  key=("order_id", "order_item_id"), monthly=True),
        TableSpec("order_payments", "olist_order_payments_dataset.csv",
                  ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"),
                  key=("order_id", "payment_sequential"), monthly=True),
        # Un même review_id peut porter sur plusieurs commandes : la clé est le couple (review_id, order_id).
        TableSpec("order_reviews", "olist_order_reviews_dataset.csv",
                  ("review_id", "order_id", "review_score", "review_comment_title", "review_comment_message",
                   "review_creation_date", "review_answer_timestamp"),
                  key=("review_id", "order_id"), monthly=True),
        # customer_id est créé à chaque commande : un client réel (customer_unique_id) en a plusieurs.
        TableSpec("customers", "olist_customers_dataset.csv",
                  ("customer_id", "customer_unique_id", "customer_zip_code_prefix", "customer_city",
                   "customer_state"),
                  key=("customer_id",), monthly=True),
        TableSpec("products", "olist_products_dataset.csv",
                  ("product_id", "product_category_name", "product_name_lenght", "product_description_lenght",
                   "product_photos_qty", "product_weight_g", "product_length_cm", "product_height_cm",
                   "product_width_cm"),
                  key=("product_id",), monthly=False),
        TableSpec("sellers", "olist_sellers_dataset.csv",
                  ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
                  key=("seller_id",), monthly=False),
        TableSpec("category_translation", "product_category_name_translation.csv",
                  ("product_category_name", "product_category_name_english"),
                  key=("product_category_name",), monthly=False),
        # Plusieurs coordonnées par préfixe de code postal : pas de clé, la déduplication se fait dans dbt.
        TableSpec("geolocation", "olist_geolocation_dataset.csv",
                  ("geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng", "geolocation_city",
                   "geolocation_state"),
                  key=(), monthly=False),
    )
}

MONTHLY_TABLES = [t for t in TABLES.values() if t.monthly]
REFERENCE_TABLES = [t for t in TABLES.values() if not t.monthly]


def s3_settings() -> dict[str, str]:
    """Paramètres de connexion au stockage S3 local, lus dans .env."""
    return {
        "endpoint": os.getenv("S3_ENDPOINT", "127.0.0.1:8333"),
        "key_id": os.getenv("S3_ACCESS_KEY", ""),
        "secret": os.getenv("S3_SECRET_KEY", ""),
    }
