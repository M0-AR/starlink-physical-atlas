"""Frames, site geometry, slant range, Doppler.

All vectors are (..., 3) arrays in km and km/s. TEME -> ECEF uses the IAU-82
GMST approximation (Vallado, Fundamentals of Astrodynamics, eq. 3-47/3-48).
The DUT1 correction is neglected; at LEO this is a sub-kilometre effect and is
quantified in docs/LIMITATIONS.md.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .constants import C, OMEGA_E, RE


def gmst_rad(jd_ut1: float | np.ndarray) -> np.ndarray:
    """Greenwich mean sidereal time in radians for a Julian date (UT1 ~ UTC)."""
    jd = np.asarray(jd_ut1, dtype=float)
    tut1 = (jd - 2451545.0) / 36525.0
    seconds = (
        67310.54841
        + (876600.0 * 3600.0 + 8640184.812866) * tut1
        + 0.093104 * tut1**2
        - 6.2e-6 * tut1**3
    )
    return np.mod(seconds * (np.pi / 180.0) / 240.0, 2.0 * np.pi)


def teme_to_ecef(r_teme: np.ndarray, v_teme: np.ndarray, jd: float):
    """Rotate TEME position/velocity into ECEF at one instant.

    r_teme, v_teme: (..., 3). Returns (r_ecef, v_ecef), same shape.
    """
    theta = float(gmst_rad(jd))
    ct, st = np.cos(theta), np.sin(theta)
    x = ct * r_teme[..., 0] + st * r_teme[..., 1]
    y = -st * r_teme[..., 0] + ct * r_teme[..., 1]
    z = r_teme[..., 2].copy()
    r_ecef = np.stack([x, y, z], axis=-1)
    vx = ct * v_teme[..., 0] + st * v_teme[..., 1] + OMEGA_E * y
    vy = -st * v_teme[..., 0] + ct * v_teme[..., 1] - OMEGA_E * x
    vz = v_teme[..., 2].copy()
    v_ecef = np.stack([vx, vy, vz], axis=-1)
    return r_ecef, v_ecef


@dataclass(frozen=True)
class Site:
    """A stationary ground site in ECEF with a local ENU basis."""

    name: str
    lat_deg: float
    lon_deg: float
    alt_km: float = 0.0

    @property
    def xyz(self) -> np.ndarray:
        lat = np.deg2rad(self.lat_deg)
        lon = np.deg2rad(self.lon_deg)
        r = RE + self.alt_km
        return np.array(
            [r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)]
        )

    @property
    def up(self) -> np.ndarray:
        lat = np.deg2rad(self.lat_deg)
        lon = np.deg2rad(self.lon_deg)
        return np.array([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])

    @property
    def east(self) -> np.ndarray:
        lon = np.deg2rad(self.lon_deg)
        return np.array([-np.sin(lon), np.cos(lon), 0.0])

    @property
    def north(self) -> np.ndarray:
        lat = np.deg2rad(self.lat_deg)
        lon = np.deg2rad(self.lon_deg)
        return np.array([-np.sin(lat) * np.cos(lon), -np.sin(lat) * np.sin(lon), np.cos(lat)])


def elevation_range_azimuth(sat_xyz: np.ndarray, site: Site):
    """Topocentric elevation (deg), slant range (km) and azimuth (deg)."""
    d = sat_xyz - site.xyz
    rng = np.linalg.norm(d, axis=-1)
    up = np.einsum("...i,i->...", d, site.up)
    elev = np.degrees(np.arcsin(np.clip(up / rng, -1.0, 1.0)))
    az = np.degrees(np.arctan2(np.einsum("...i,i->...", d, site.east),
                               np.einsum("...i,i->...", d, site.north))) % 360.0
    return elev, rng, az


def range_rate(sat_xyz: np.ndarray, sat_vel: np.ndarray, site: Site) -> np.ndarray:
    """Range rate d|r_sat - r_site|/dt in km/s (positive = receding)."""
    d = sat_xyz - site.xyz
    rng = np.linalg.norm(d, axis=-1)
    return np.einsum("...i,...i->...", d, sat_vel) / rng


def slant_range_at_elevation(h_km: float, elev_deg: float) -> float:
    """Geometric slant range to a spherical shell of altitude h at elevation."""
    eps = np.deg2rad(elev_deg)
    r = RE + h_km
    return float(np.sqrt(r**2 - (RE * np.cos(eps)) ** 2) - RE * np.sin(eps))


def doppler_hz(range_rate_km_s: np.ndarray, f_hz: float) -> np.ndarray:
    """Doppler shift in Hz. Negative range rate (approaching) -> positive shift."""
    return -f_hz * np.asarray(range_rate_km_s) / C


def one_way_delay_s(range_km: np.ndarray) -> np.ndarray:
    return np.asarray(range_km) / C


def circular_gap_stats(values_deg: np.ndarray) -> dict:
    """Sorted circular gaps of angles in degrees."""
    v = np.sort(np.asarray(values_deg) % 360.0)
    gaps = np.diff(np.r_[v, v[0] + 360.0])
    return {
        "n": int(v.size),
        "p50": float(np.median(gaps)),
        "p90": float(np.percentile(gaps, 90)),
        "p99": float(np.percentile(gaps, 99)),
        "max": float(gaps.max()),
        "frac_lt_0p1": float(np.mean(gaps < 0.1)),
    }
