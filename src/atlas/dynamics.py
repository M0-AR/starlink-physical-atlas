"""Temporal dynamics: migration, attrition, J2 validation, maneuver signatures."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .anatomy import assign_family, j2_raan_rate_deg_day, shell_table
from .constants import MU, RE
from .data import norm_name


def snapshot_index(df: pd.DataFrame) -> pd.DataFrame:
    """One latest TLE per satellite, indexed by normalised name."""
    d = df.copy()
    if "name_key" not in d.columns:
        d["name_key"] = d["name"].map(norm_name)
    d["epoch"] = pd.to_datetime(d["epoch"], utc=True)
    return d.sort_values("epoch").groupby("name_key").tail(1).set_index("name_key")


def match_snapshots(a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    """Match satellites by name across two snapshots and measure change."""
    ia = assign_family(snapshot_index(a))
    ib = assign_family(snapshot_index(b))
    cols = [c for c in ["alt_km", "inc", "raan", "ma", "epoch", "family"] if c in ia.columns and c in ib.columns]
    m = ia[cols].join(ib[cols], how="inner", lsuffix="_a", rsuffix="_b")
    m["dt_days"] = (m["epoch_b"] - m["epoch_a"]).dt.total_seconds() / 86400.0
    m["d_alt_km"] = m["alt_km_b"] - m["alt_km_a"]
    m["d_inc_deg"] = m["inc_b"] - m["inc_a"]
    if "raan_a" in m.columns:
        m["d_raan_deg"] = ((m["raan_b"] - m["raan_a"] + 180.0) % 360.0) - 180.0
    return m


def migration_summary(m: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for fam, s in m.groupby("family_a"):
        rows.append({
            "family": fam,
            "matched": len(s),
            "alt_a_median_km": float(s["alt_km_a"].median()),
            "alt_b_median_km": float(s["alt_km_b"].median()),
            "d_alt_median_km": float(s["d_alt_km"].median()),
            "d_alt_p10_km": float(s["d_alt_km"].quantile(0.10)),
            "d_alt_p90_km": float(s["d_alt_km"].quantile(0.90)),
            "frac_lowered_gt10km": float((s["d_alt_km"] < -10).mean()),
            "frac_stable_10km": float((s["d_alt_km"].abs() <= 10).mean()),
            "frac_raised_gt10km": float((s["d_alt_km"] > 10).mean()),
        })
    return pd.DataFrame(rows).sort_values("matched", ascending=False).reset_index(drop=True)


def attrition(a: pd.DataFrame, b: pd.DataFrame) -> dict:
    ka = set(snapshot_index(a).index)
    kb = set(snapshot_index(b).index)
    days = (pd.to_datetime(b["epoch"], utc=True).max() - pd.to_datetime(a["epoch"], utc=True).max()).total_seconds() / 86400.0
    months = max(days / 30.4375, 1e-9)
    missing = ka - kb
    new = kb - ka
    return {
        "n_a": len(ka),
        "n_b": len(kb),
        "matched": len(ka & kb),
        "missing": len(missing),
        "new": len(new),
        "months": months,
        "missing_per_month": len(missing) / months,
        "missing_pct_per_month": 100.0 * len(missing) / len(ka) / months,
        "new_per_month": len(new) / months,
        "check_identity": len(ka) - len(missing) + len(new) == len(kb),
    }


def shell_history(snapshots: dict[str, pd.DataFrame], min_count: int = 25) -> pd.DataFrame:
    rows = []
    for label, df in snapshots.items():
        t = shell_table(assign_family(df), min_count=min_count)
        t.insert(0, "epoch", label)
        rows.append(t)
    return pd.concat(rows, ignore_index=True)


def launch_summary(satcat: pd.DataFrame) -> pd.DataFrame:
    d = satcat.copy()
    d["launch_date"] = pd.to_datetime(d["launch_date"], utc=True)
    d["launch_year"] = d["launch_date"].dt.year
    d["launch_id"] = d["object_id"].astype(str).str[:8]
    g = d.groupby("launch_year").agg(
        satellites=("name", "count"),
        launches=("launch_id", "nunique"),
    )
    g["satellites_per_launch"] = g["satellites"] / g["launches"]
    return g.reset_index()


def j2_series_fit(series: pd.DataFrame) -> pd.DataFrame:
    """Fit the nodal regression slope of each satellite and compare with J2."""
    d = series.copy()
    if "name_key" not in d.columns:
        d["name_key"] = d["name"].map(norm_name)
    d["epoch"] = pd.to_datetime(d["epoch"], utc=True)
    rows = []
    for name, s in d.groupby("name_key"):
        s = s.sort_values("epoch").dropna(subset=["raan", "inc", "alt_km", "ecc"])
        if len(s) < 30:
            continue
        t = (s["epoch"] - s["epoch"].iloc[0]).dt.total_seconds().to_numpy() / 86400.0
        raan = np.unwrap(np.deg2rad(s["raan"].to_numpy()))
        coef = np.polyfit(t, raan, 1)
        slope = float(np.degrees(coef[0]))
        pred = float(j2_raan_rate_deg_day(s["inc"].median(), s["alt_km"].median(), s["ecc"].median()))
        resid = np.degrees(raan - np.polyval(coef, t))
        rows.append({
            "name_key": name,
            "n_tle": len(s),
            "days": float(t[-1]),
            "inc_median_deg": float(s["inc"].median()),
            "alt_median_km": float(s["alt_km"].median()),
            "slope_deg_day": slope,
            "j2_pred_deg_day": pred,
            "rel_error": (slope - pred) / pred,
            "resid_std_deg": float(np.std(resid)),
            "resid_max_deg": float(np.max(np.abs(resid))),
        })
    return pd.DataFrame(rows)


def maneuver_events(series: pd.DataFrame, floor_km: float = 1.5, sigma: float = 6.0) -> tuple[pd.DataFrame, float]:
    """Flag step changes in fitted altitude between consecutive TLEs.

    The threshold is max(floor, sigma * robust scatter of the per-interval
    altitude change), so routine fit noise is not counted as a manoeuvre.
    """
    d = series.copy()
    if "name_key" not in d.columns:
        d["name_key"] = d["name"].map(norm_name)
    d["epoch"] = pd.to_datetime(d["epoch"], utc=True)
    steps = []
    for name, s in d.groupby("name_key"):
        s = s.sort_values("epoch")
        dt = s["epoch"].diff().dt.total_seconds().to_numpy() / 86400.0
        dalt = s["alt_km"].diff().to_numpy()
        ok = np.isfinite(dalt) & np.isfinite(dt) & (dt > 0)
        steps.append(pd.DataFrame({
            "name_key": name,
            "epoch": s["epoch"].to_numpy()[ok],
            "dt_days": dt[ok],
            "d_alt_km": dalt[ok],
        }))
    allsteps = pd.concat(steps, ignore_index=True)
    scatter = float(np.median(np.abs(allsteps["d_alt_km"] - allsteps["d_alt_km"].median())))
    threshold = max(floor_km, sigma * scatter)
    events = allsteps[allsteps["d_alt_km"].abs() > threshold].copy()
    events["direction"] = np.where(events["d_alt_km"] < 0, "lower", "raise")
    return events.sort_values("epoch"), threshold


def decay_rates(nov: pd.DataFrame) -> pd.DataFrame:
    """Instantaneous altitude decay rate from TLE mean-motion derivative.

    da/dt = -(2/3) (a/n) dn/dt, with ndot converted from rev/day^2 to rad/s^2.
    A positive ndot (mean motion increasing) therefore means a shrinking orbit.
    """
    d = assign_family(nov).copy()
    n = d["mm"].to_numpy() * 2.0 * np.pi / 86400.0
    a = d["a_km"].to_numpy()
    ndot = d["ndot"].to_numpy() * 2.0 * np.pi / 86400.0**2
    da_dt = -(2.0 / 3.0) * (a / n) * ndot * 86400.0  # km/day
    d["da_dt_km_day"] = da_dt
    with np.errstate(divide="ignore", invalid="ignore"):
        d["lifetime_yr_linear"] = np.where(
            da_dt < 0, (a - RE) / np.abs(da_dt) / 365.25, np.inf
        )
    rows = []
    for fam, s in d.groupby("family"):
        rows.append({
            "family": fam,
            "n": len(s),
            "frac_positive_ndot": float((s["ndot"] > 0).mean()),
            "da_dt_median_km_day": float(np.median(s["da_dt_km_day"])),
            "da_dt_p10_km_day": float(np.percentile(s["da_dt_km_day"], 10)),
            "da_dt_p90_km_day": float(np.percentile(s["da_dt_km_day"], 90)),
            "life_median_yr": float(np.median(s["lifetime_yr_linear"])),
        })
    return pd.DataFrame(rows).sort_values("n", ascending=False).reset_index(drop=True)
