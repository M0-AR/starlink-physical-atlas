import numpy as np
import pandas as pd
import pytest

from atlas import data


@pytest.mark.parametrize(
    "key,rows",
    [("nov2026", 11198), ("apr2026", 10119), ("apr2025", 7153)],
)
def test_snapshot_rows(key, rows):
    df = data.load_snapshot(key)
    assert len(df) == rows
    assert df["name_key"].is_unique
    assert df["alt_km"].median() > 300
    assert df["epoch"].notna().all()


def test_columns_are_canonical():
    df = data.load_snapshot("nov2026")
    assert list(df.columns[: len(data.CANON)]) == data.CANON
    assert {"a_km", "alt_km"}.issubset(df.columns)


def test_dtc_suffix_normalisation():
    assert data.norm_name("STARLINK-1008 [DTC]") == "STARLINK-1008"
    assert data.norm_name("starlink-1008") == "STARLINK-1008"


def test_altitude_matches_satcat_median():
    nov = data.load_snapshot("nov2026").set_index("name_key")
    sc = data.load_satcat()
    sc = sc.dropna(subset=["apogee", "perigee"]).set_index("name_key")
    joined = nov.join(sc[["apogee", "perigee"]], how="inner")
    ref = (joined["apogee"] + joined["perigee"]) / 2.0
    diff = (joined["alt_km"] - ref).abs()
    assert len(diff) > 9000
    assert diff.median() < 2.0
    assert diff.quantile(0.95) < 5.0


def test_satrec_roundtrip_and_propagation():
    df = data.load_snapshot("nov2026").head(3)
    arr, keys, names = data.build_satrec_array(df)
    assert list(keys) == list(df["name_key"])
    ts = pd.Series([df["epoch"].iloc[0], df["epoch"].iloc[0] + pd.Timedelta(seconds=90)])
    jd, fr = data.jd_array(ts)
    err, r, v = arr.sgp4(jd, fr)
    assert err.shape == (3, 2)
    assert np.all(err == 0)
    assert np.isfinite(r).all()
    radii = np.linalg.norm(r, axis=-1)
    assert np.all((radii > 6300) & (radii < 7200))


def test_sma_from_mean_motion():
    a = data.sma_from_mean_motion(np.array([15.5]))
    assert a[0] == pytest.approx(6795.0, abs=30.0)
