"""Ingestion dans la couche bronze, sur un lac local temporaire : contrat, idempotence, mois vide."""

import duckdb
import pytest

from olist_pipeline import bronze, landing
from olist_pipeline.config import TABLES


@pytest.fixture
def lake(tmp_path) -> str:
    return str(tmp_path / "lake")


def count(path: str) -> int:
    return duckdb.sql(f"select count(*) from read_parquet('{path}')").fetchall()[0][0]


def test_ingest_writes_one_parquet_partition_per_month(delivered, lake, source):
    result = bronze.ingest(TABLES["orders"], "2017-01", delivered, lake)
    assert result.path.endswith("bronze/orders/delivery_month=2017-01/orders.parquet")
    assert result.rows == count(result.path) == 150
    assert len(result.sha256) == 64


def test_bronze_keeps_raw_text_and_adds_lineage_columns(delivered, lake):
    path = bronze.ingest(TABLES["customers"], "2017-01", delivered, lake).path
    row = duckdb.sql(f"select * from read_parquet('{path}') limit 1").df().iloc[0]
    assert row["_source_file"] == "2017-01/customers.csv"
    types = dict(duckdb.sql(f"describe select * from read_parquet('{path}')").fetchall()[i][:2] for i in range(7))
    assert types["customer_zip_code_prefix"] == "VARCHAR"      # « 01037 » garde son zéro


def test_replaying_a_month_replaces_it_instead_of_duplicating(delivered, lake):
    first = bronze.ingest(TABLES["order_items"], "2017-02", delivered, lake)
    second = bronze.ingest(TABLES["order_items"], "2017-02", delivered, lake)
    assert first.path == second.path
    assert count(second.path) == first.rows


def test_reference_tables_are_a_single_snapshot(delivered, lake):
    result = bronze.ingest(TABLES["products"], None, delivered, lake)
    assert result.path.endswith("bronze/products/products.parquet")


def test_an_empty_month_is_a_valid_delivery(tmp_path, source, lake):
    landing_dir = tmp_path / "landing"
    landing.deliver_month(landing.split_by_month(source)["2016-11"], "2016-11", landing_dir)
    result = bronze.ingest(TABLES["orders"], "2016-11", landing_dir, lake)
    assert result.rows == 0 == count(result.path)


def test_schema_drift_is_refused(delivered, lake):
    path = delivered / "2017-01" / "orders.csv"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("order_status", "status", 1), encoding="utf-8")       # colonne renommée
    with pytest.raises(bronze.DeliveryError, match="en-tête inattendu"):
        bronze.ingest(TABLES["orders"], "2017-01", delivered, lake)


def test_duplicate_keys_are_refused(delivered, lake):
    path = delivered / "2017-01" / "orders.csv"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(lines + [lines[1]]), encoding="utf-8")                      # une commande en double
    with pytest.raises(bronze.DeliveryError, match="en double"):
        bronze.ingest(TABLES["orders"], "2017-01", delivered, lake)


def test_incomplete_delivery_is_not_read(delivered, lake):
    (delivered / "2017-03" / landing.SUCCESS_MARKER).unlink()
    with pytest.raises(bronze.DeliveryError, match="incomplète"):
        bronze.ingest(TABLES["orders"], "2017-03", delivered, lake)
