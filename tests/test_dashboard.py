"""Test de fumée du tableau de bord : il s'affiche sans erreur, en français et en anglais.

Il a besoin d'un entrepôt construit (dbt build) : il est ignoré sinon. Dans la CI, il tourne après dbt.
"""

from pathlib import Path

import pytest

from olist_pipeline.config import WAREHOUSE_PATH

APP = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"

pytestmark = pytest.mark.skipif(not WAREHOUSE_PATH.exists(), reason="entrepôt non construit (lancer dbt build)")


def test_dashboard_renders_without_error():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP), default_timeout=120).run()
    assert not app.exception
    assert app.title[0].value == "Le e-commerce brésilien en cinq questions"
    assert len(app.tabs) == 5

    app.sidebar.radio[0].set_value("en").run()
    assert not app.exception
    assert app.title[0].value == "Brazilian e-commerce in five questions"
