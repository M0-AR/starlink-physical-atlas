"""Constellation anatomy: inclination families, altitude shells, plane lattice.

The central methodological point is *common-epoch RAAN rectification*: a TLE
snapshot spans several days, and RAAN precesses under J2 at ~4.5 deg/day, so
raw RAAN values from different epochs smear the plane lattice by up to ~18 deg.
We remove the secular J2 drift to a common epoch before measuring planes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from .constants import J2, MU, RE

FAMILY_BINS = [
    ("30.5", 29.0, 32.0),
    ("43.0", 42.0, 44.0),
    ("53.1", 52.0, 54.0),
    ("70.0", 69.0, 71.0),
    ("97.4", 96.0, 99.0),
]


def j2_raan_rate_deg_day(inc_deg, alt_km, ecc):
    """Secular J2 nodal regression rate in degrees/day."""
    a = RE + np.asarray(alt_km, dtype=float)
    n = np.sqrt(MU / a**3)
    p = a * (1.0 - np.asarray(ecc, dtype=float) ** 2)
    return np.degrees(-1.5 * J2 * (RE / p) ** 2 * n * np.cos(np.deg2rad(inc_deg))) * 86400.0


def assign_family(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    labels = np.full(len(out), "other", dtype=object)
    inc = out["inc"].to_numpy()
    for label, lo, hi in FAMILY_BINS:
        labels[(inc >= lo) & (inc < hi)] = label
    out["family"] = labels
    return out


def altitude_peaks(df: pd.DataFrame, min_count: int = 25) -> list[float]:
    """Histogram peaks of altitude, used to split a family into shells."""
    alt = df["alt_km"].to_numpy()
    alt = alt[(alt > 250) & (alt < 650)]
    if len(alt) < min_count:
        return []
    h, edges = np.histogram(alt, bins=np.arange(250, 650, 2.0))
    peaks, _ = find_peaks(h, height=min_count, distance=4)
    return [float(edges[i] + 1.0) for i in peaks]


def assign_shells(df: pd.DataFrame, min_count: int = 25) -> pd.DataFrame:
    """Assign each satellite to its nearest altitude peak within 8 km."""
    out = df.copy()
    out["shell_km"] = np.nan
    for family, sub in out.groupby("family"):
        if family == "other":
            continue
        peaks = altitude_peaks(sub, min_count=min_count)
        if not peaks:
            continue
        peaks = np.asarray(peaks)
        d = np.abs(sub["alt_km"].to_numpy()[:, None] - peaks[None, :])
        idx = np.argmin(d, axis=1)
        nearest = d[np.arange(len(sub)), idx]
        shell = peaks[idx]
        shell = np.where(nearest <= 8.0, shell, np.nan)
        out.loc[sub.index, "shell_km"] = shell
    return out


def shell_table(df: pd.DataFrame, min_count: int = 25) -> pd.DataFrame:
    d = assign_shells(df, min_count=min_count)
    rows = []
    for (family, shell), sub in d.dropna(subset=["shell_km"]).groupby(["family", "shell_km"]):
        if len(sub) < min_count:
            continue
        rows.append({
            "family": family,
            "shell_km_peak": shell,
            "n": len(sub),
            "alt_median_km": float(sub["alt_km"].median()),
            "alt_p05_km": float(sub["alt_km"].quantile(0.05)),
            "alt_p95_km": float(sub["alt_km"].quantile(0.95)),
            "inc_median_deg": float(sub["inc"].median()),
            "ecc_median": float(sub["ecc"].median()),
            "period_median_min": float((2 * np.pi * np.sqrt((RE + sub["alt_km"]) ** 3 / MU) / 60).median()),
            "speed_median_kmh": float((np.sqrt(MU / (RE + sub["alt_km"])) * 3600).median()),
        })
    return pd.DataFrame(rows).sort_values(["family", "alt_median_km"]).reset_index(drop=True)


def rectify_raan(df: pd.DataFrame, tref=None) -> np.ndarray:
    """J2-rectify RAAN to a common epoch; returns degrees in [0, 360)."""
    if tref is None:
        tref = df["epoch"].median()
    dt_days = (pd.Timestamp(tref) - df["epoch"]).dt.total_seconds().to_numpy() / 86400.0
    rate = j2_raan_rate_deg_day(df["inc"].to_numpy(), df["alt_km"].to_numpy(), df["ecc"].to_numpy())
    return np.mod(df["raan"].to_numpy() + rate * dt_days, 360.0)


def rectify_ma(df: pd.DataFrame, tref=None) -> np.ndarray:
    """Propagate mean anomaly to a common epoch with the TLE mean motion.

    MA wraps every orbit, so a raw snapshot spanning days is phase-scrambled.
    The TLE mean motion is precise enough that the fractional phase at the
    common epoch is recovered to well below a degree over a four-day span.
    """
    if tref is None:
        tref = df["epoch"].median()
    dt_days = (pd.Timestamp(tref) - df["epoch"]).dt.total_seconds().to_numpy() / 86400.0
    n_deg_day = 360.0 * df["mm"].to_numpy()
    return np.mod(df["ma"].to_numpy() + n_deg_day * dt_days, 360.0)


def circular_gap_quantiles(values_deg: np.ndarray) -> dict:
    v = np.sort(np.asarray(values_deg, dtype=float) % 360.0)
    gaps = np.diff(np.r_[v, v[0] + 360.0])
    return {
        "n": int(v.size),
        "p50_deg": float(np.median(gaps)),
        "p90_deg": float(np.percentile(gaps, 90)),
        "p99_deg": float(np.percentile(gaps, 99)),
        "max_deg": float(gaps.max()),
        "frac_lt_0p1": float(np.mean(gaps < 0.1)),
    }


def circular_std_deg(values_deg: np.ndarray) -> float:
    r = np.deg2rad(np.asarray(values_deg, dtype=float))
    resultant = np.hypot(np.mean(np.cos(r)), np.mean(np.sin(r)))
    return float(np.degrees(np.sqrt(-2.0 * np.log(max(resultant, 1e-12)))))


def gap_groups(values_deg: np.ndarray, threshold_deg: float) -> list[np.ndarray]:
    """Split sorted circular angles wherever the gap exceeds a threshold."""
    v = np.sort(np.asarray(values_deg, dtype=float) % 360.0)
    if v.size == 0:
        return []
    gaps = np.diff(np.r_[v, v[0] + 360.0])
    cut = int(np.argmax(gaps))
    v = np.r_[v[cut + 1:], v[: cut + 1] + 360.0]
    breaks = np.where(np.diff(v) > threshold_deg)[0]
    return [g % 360.0 for g in np.split(v, breaks + 1)]


def stability_curve(values_deg: np.ndarray, thresholds=(0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5),
                    min_size: int = 10) -> pd.DataFrame:
    rows = []
    for thr in thresholds:
        groups = [g for g in gap_groups(values_deg, thr) if len(g) >= min_size]
        sizes = np.array([len(g) for g in groups], dtype=int)
        centers = np.sort(np.array([np.mean(g) for g in groups], dtype=float))
        gaps = np.diff(np.r_[centers, centers[0] + 360.0]) if len(centers) > 1 else np.array([])
        rows.append({
            "threshold_deg": thr,
            "groups_ge_min": int(len(groups)),
            "median_size": float(np.median(sizes)) if len(sizes) else np.nan,
            "max_size": int(sizes.max()) if len(sizes) else 0,
            "median_spacing_deg": float(np.median(gaps)) if len(gaps) else np.nan,
            "spacing_cv": float(gaps.std() / gaps.mean()) if len(gaps) else np.nan,
        })
    return pd.DataFrame(rows)


def plane_summary(df: pd.DataFrame, threshold_deg: float = 0.2, min_size: int = 10) -> dict:
    """Measure the plane lattice of one shell after rectification."""
    work = df.dropna(subset=["raan", "inc", "alt_km", "ecc"]).copy()
    if len(work) < min_size:
        return {"n": int(len(work)), "planes": 0}
    raw = work["raan"].to_numpy()
    tref = work["epoch"].median()
    ref = rectify_raan(work, tref)
    ma_ref = rectify_ma(work, tref)
    raw_stats = circular_gap_quantiles(raw)
    ref_stats = circular_gap_quantiles(ref)
    groups = [g for g in gap_groups(ref, threshold_deg) if len(g) >= min_size]
    sizes = np.array([len(g) for g in groups], dtype=int)
    centers = np.sort(np.array([np.mean(g) for g in groups]))
    gaps = np.diff(np.r_[centers, centers[0] + 360.0]) if len(centers) > 1 else np.array([])

    # In-plane mean-anomaly spacing.  A 0.2 deg RAAN threshold can merge two
    # nearby planes, so we also report the subset of groups that are tight in
    # RAAN (circular std < 0.05 deg), where the MA gaps are interpretable.
    ma_gaps, twins = [], 0
    tight_ma_gaps, tight_twins = [], 0
    raan_stds, tight_groups = [], 0
    for g in groups:
        idx = np.where(np.isin(ref, g))[0]
        sd = circular_std_deg(g)
        raan_stds.append(sd)
        ma = np.sort(ma_ref[idx] % 360.0)
        if ma.size >= 3:
            gg = np.diff(np.r_[ma, ma[0] + 360.0])
            ma_gaps.extend(gg.tolist())
            twins += int(np.sum(gg < 0.5))
            if sd < 0.05:
                tight_groups += 1
                tight_twins += int(np.sum(gg < 0.5))
                tight_ma_gaps.extend(gg.tolist())

    return {
        "n": int(len(work)),
        "tref": str(pd.Timestamp(tref)),
        "raw": raw_stats,
        "rectified": ref_stats,
        "planes": int(len(groups)),
        "occupancy_median": float(np.median(sizes)) if len(sizes) else np.nan,
        "occupancy_max": int(sizes.max()) if len(sizes) else 0,
        "spacing_median_deg": float(np.median(gaps)) if len(gaps) else np.nan,
        "spacing_cv": float(gaps.std() / gaps.mean()) if len(gaps) else np.nan,
        "raan_std_median_deg": float(np.median(raan_stds)) if raan_stds else np.nan,
        "tight_groups": int(tight_groups),
        "tight_fraction": float(tight_groups / len(groups)) if groups else np.nan,
        "ma_gap_median_deg": float(np.median(ma_gaps)) if ma_gaps else np.nan,
        "ma_gap_p10_deg": float(np.percentile(ma_gaps, 10)) if ma_gaps else np.nan,
        "ma_gap_p90_deg": float(np.percentile(ma_gaps, 90)) if ma_gaps else np.nan,
        "twins_lt_0p5deg": int(twins),
        "tight_ma_gap_median_deg": float(np.median(tight_ma_gaps)) if tight_ma_gaps else np.nan,
        "tight_twins_lt_0p5deg": int(tight_twins),
    }
