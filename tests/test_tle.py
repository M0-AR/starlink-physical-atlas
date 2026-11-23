import numpy as np
import pytest

from atlas import data, tle


@pytest.fixture(scope="module")
def series():
    return tle.load_series(data.RAW)


def test_series_shape(series):
    assert len(series) == 20113
    assert series["name"].nunique() == 27
    assert series["epoch"].min().year >= 2024
    assert series["epoch"].max().year <= 2025


def test_series_altitudes_are_physical(series):
    assert series["alt_km"].between(200, 700).all()
    assert np.isfinite(series["raan"]).all()
    assert series["ecc"].between(0, 0.01).all()


def test_one_tle_per_file_minimum(series):
    counts = series.groupby("name").size()
    assert counts.min() >= 90
