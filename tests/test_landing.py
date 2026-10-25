"""Simulation des livraisons : chaque ligne de la source tombe dans exactement un mois."""

import pytest

from olist_pipeline import landing
from olist_pipeline.config import MONTHLY_TABLES


def test_every_row_lands_in_exactly_one_month(source):
    by_month = landing.split_by_month(source)
    for spec in MONTHLY_TABLES:
        assert sum(len(frames[spec.name]) for frames in by_month.values()) == len(source[spec.name])


def test_children_follow_the_purchase_month_of_their_order(source):
    by_month = landing.split_by_month(source)
    for month, frames in by_month.items():
        assert set(frames["order_items"]["order_id"]) <= set(frames["orders"]["order_id"])
        assert set(frames["customers"]["customer_id"]) == set(frames["orders"]["customer_id"])
        assert (frames["orders"]["order_purchase_timestamp"].str[:7] == month).all()


def test_months_without_orders_still_get_a_delivery(source):
    by_month = landing.split_by_month(source)
    assert landing.all_months()[0] == "2016-09" and landing.all_months()[-1] == "2018-10"
    assert len(by_month) == 26
    assert len(by_month["2016-11"]["orders"]) == 0        # un mois vide reste une livraison (vide)


def test_orphan_rows_are_refused(source):
    broken = dict(source)
    items = source["order_items"].copy()
    items.loc[items.index[0], "order_id"] = "commande-inconnue"
    broken["order_items"] = items
    with pytest.raises(ValueError, match="aucune commande"):
        landing.split_by_month(broken)


def test_only_complete_deliveries_are_visible(delivered):
    assert landing.delivered_months(delivered) == ["2017-01", "2017-02", "2017-03"]
    (delivered / "2017-02" / landing.SUCCESS_MARKER).unlink()       # livraison en cours de dépôt
    assert landing.delivered_months(delivered) == ["2017-01", "2017-03"]
