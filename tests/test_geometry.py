import numpy as np
import pytest

from atlas import geometry
from atlas.constants import C, RE


def test_gmst_j2000():
    assert np.degrees(geometry.gmst_rad(2451545.0)) == pytest.approx(280.4606, abs=1e-3)


def test_gmst_advances_one_sidereal_day():
    a = geometry.gmst_rad(2451545.0)
    b = geometry.gmst_rad(2451546.0)
    advance = np.degrees(np.mod(b - a, 2 * np.pi))
    assert advance == pytest.approx(0.9856, abs=1e-2)


def test_overhead_range_and_elevation():
    site = geometry.Site("eq", 0.0, 0.0)
    sat = np.array([RE + 550.0, 0.0, 0.0])
    elev, rng, az = geometry.elevation_range_azimuth(sat, site)
    assert elev == pytest.approx(90.0)
    assert rng == pytest.approx(550.0)
    assert np.isfinite(az)


def test_horizon_geometry():
    site = geometry.Site("eq", 0.0, 0.0)
    r = RE + 550.0
    sat = np.array([RE, np.sqrt(r**2 - RE**2), 0.0])
    elev, rng, _ = geometry.elevation_range_azimuth(sat, site)
    assert elev == pytest.approx(0.0, abs=1e-9)
    assert rng == pytest.approx(np.sqrt(r**2 - RE**2))


@pytest.mark.parametrize("h,elev,expected", [(550, 90, 550.0), (550, 25, 1123.42), (550, 0, 2705.26)])
def test_slant_range(h, elev, expected):
    assert geometry.slant_range_at_elevation(h, elev) == pytest.approx(expected, abs=0.02)


def test_doppler_sign_and_magnitude():
    # approaching: range rate negative -> positive Doppler shift
    d = geometry.doppler_hz(np.array([-5.0]), 11.325e9)
    assert d[0] == pytest.approx(188_880.0, rel=2e-4)
    assert geometry.doppler_hz(np.array([5.0]), 11.325e9)[0] < 0


def test_one_way_delay():
    assert geometry.one_way_delay_s(np.array([550.0]))[0] == pytest.approx(550.0 / C)


def test_teme_ecef_preserves_norm():
    rng = np.random.default_rng(0)
    r = rng.normal(size=(5, 3))
    v = rng.normal(size=(5, 3))
    re, ve = geometry.teme_to_ecef(r, v, 2461366.5)
    assert np.allclose(np.linalg.norm(re, axis=-1), np.linalg.norm(r, axis=-1))
    assert np.allclose(np.linalg.norm(ve, axis=-1) >= 0, True)
