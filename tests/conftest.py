from pathlib import Path

import pandas as pd
import pytest

from olist_pipeline import landing

SAMPLE_DIR = Path(__file__).parent / "fixtures" / "sample"


@pytest.fixture(scope="session")
def source() -> dict[str, pd.DataFrame]:
    """L'échantillon réel versionné (450 commandes de janvier à mars 2017), lu comme l'archive Kaggle."""
    return landing.read_source(SAMPLE_DIR)


@pytest.fixture
def delivered(tmp_path, source) -> Path:
    """Une zone de dépôt temporaire contenant les référentiels et les trois livraisons mensuelles."""
    landing_dir = tmp_path / "landing"
    landing.deliver_reference(source, landing_dir)
    for month, frames in landing.split_by_month(source).items():
        if month in ("2017-01", "2017-02", "2017-03"):
            landing.deliver_month(frames, month, landing_dir)
    return landing_dir
