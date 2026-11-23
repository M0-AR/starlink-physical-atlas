"""Data ingestion, canonical schema, and SGP4 propagation helpers.

Three public snapshots are used:
  nov2026  - live CelesTrak GP snapshot, epoch 2026-11-19..23
  apr2026  - Kaggle CelesTrak active-satellite snapshot, epoch 2026-03-17..04-05
  apr2025  - Kaggle Starlink snapshot, epoch 2025-03-27..04-11

Every row is reduced to a canonical schema so that the rest of the code does
not depend on the source column naming. Raw files are never modified.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sgp4 import omm
from sgp4.api import Satrec, SatrecArray, jday

from .constants import MU, RE

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

CANON = [
    "name", "name_key", "norad", "object_id", "epoch", "inc", "raan", "ecc",
    "argp", "ma", "mm", "bstar", "ndot", "nddot", "alt_provided", "lat", "lon",
    "source",
]

SNAPSHOT_FILES = {
    "nov2026": "nov2026.csv.gz",
    "apr2026": "apr2026.csv.gz",
    "apr2025": "apr2025.csv.gz",
}

SOURCE_URLS = {
    "nov2026": "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=csv",
    "apr2026": "https://www.kaggle.com/datasets/bhaktimudgal/celestrak-active-satellite-dataset-april-2026",
    "apr2025": "https://www.kaggle.com/datasets/vijayj0shi/starlink-satellite-tlecsv-dataset-april-2025",
    "satcat": "https://celestrak.org/satcat/records.php?GROUP=starlink&FORMAT=csv",
    "active": "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv",
}


def norm_name(value: object) -> str:
    """Normalise a satellite name and drop the CelesTrak [DTC] annotation."""
    s = str(value).strip().upper()
    s = re.sub(r"\s*\[DTC\]\s*$", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def sma_from_mean_motion(mm_rev_day: Iterable[float] | np.ndarray) -> np.ndarray:
    n = np.asarray(mm_rev_day, dtype=float) * 2.0 * np.pi / 86400.0
    return (MU / n**2) ** (1.0 / 3.0)


def _numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _finish(df: pd.DataFrame, source: str) -> pd.DataFrame:
    df = df.copy()
    df["name"] = df["name"].astype(str).str.strip()
    df["name_key"] = df["name"].map(norm_name)
    df["epoch"] = pd.to_datetime(df["epoch"], utc=True)
    df = _numeric(df, ["norad", "inc", "raan", "ecc", "argp", "ma", "mm", "bstar", "ndot", "nddot", "alt_provided", "lat", "lon"])
    for c in CANON:
        if c not in df.columns:
            df[c] = np.nan
    df["source"] = source
    df = df[CANON].copy()
    df = df.dropna(subset=["name", "epoch", "mm"])
    df = df[(df["mm"] > 0) & (df["ecc"] >= 0) & (df["ecc"] < 1)]
    df["a_km"] = sma_from_mean_motion(df["mm"].to_numpy())
    df["alt_km"] = df["a_km"] - RE
    df = df.sort_values(["name_key", "epoch"]).reset_index(drop=True)
    return df


def read_gp_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={
        "OBJECT_NAME": "name", "NORAD_CAT_ID": "norad", "OBJECT_ID": "object_id",
        "EPOCH": "epoch", "INCLINATION": "inc", "RA_OF_ASC_NODE": "raan",
        "ECCENTRICITY": "ecc", "ARG_OF_PERICENTER": "argp",
        "MEAN_ANOMALY": "ma", "MEAN_MOTION": "mm", "BSTAR": "bstar",
        "MEAN_MOTION_DOT": "ndot", "MEAN_MOTION_DDOT": "nddot",
    })
    return _finish(df, "celestrak-gp-2026-11-23")


def read_kaggle_active_2026(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df[df["name"].astype(str).str.contains("STARLINK", case=False, na=False)]
    df = df.rename(columns={
        "name": "name", "epoch": "epoch", "inclination_deg": "inc",
        "raan_deg": "raan", "eccentricity": "ecc",
        "arg_perigee_deg": "argp", "mean_anomaly_deg": "ma",
        "mean_motion_rev_per_day": "mm", "altitude_km": "alt_provided",
    })
    df["norad"] = np.nan
    df["object_id"] = ""
    df["bstar"] = 0.0
    df["ndot"] = 0.0
    df["nddot"] = 0.0
    return _finish(df, "kaggle-active-2026-04-03")


def read_kaggle_starlink_2025(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={
        "Satellite_Name": "name", "Epoch": "epoch", "Inclination_deg": "inc",
        "Eccentricity": "ecc", "Mean_Motion_orbits_per_day": "mm",
        "Altitude_km": "alt_provided", "Latitude": "lat", "Longitude": "lon",
    })
    df["norad"] = np.nan
    df["object_id"] = ""
    df["raan"] = np.nan
    df["argp"] = np.nan
    df["ma"] = np.nan
    df["bstar"] = 0.0
    df["ndot"] = 0.0
    df["nddot"] = 0.0
    return _finish(df, "kaggle-starlink-2025-04-11")


def read_satcat(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df = df.rename(columns={
        "OBJECT_NAME": "name", "NORAD_CAT_ID": "norad", "OBJECT_ID": "object_id",
        "OPS_STATUS_CODE": "status", "LAUNCH_DATE": "launch_date",
        "DECAY_DATE": "decay_date", "APOGEE": "apogee", "PERIGEE": "perigee",
        "INCLINATION": "inc", "PERIOD": "period_min",
    })
    df["name_key"] = df["name"].map(norm_name)
    for c in ["norad", "apogee", "perigee", "inc", "period_min"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    for c in ["launch_date", "decay_date"]:
        df[c] = pd.to_datetime(df[c], errors="coerce", utc=True)
    return df


def load_snapshot(key: str) -> pd.DataFrame:
    """Load a processed snapshot, falling back to raw parsing if needed."""
    if key not in SNAPSHOT_FILES:
        raise KeyError(f"unknown snapshot {key!r}")
    path = PROCESSED / SNAPSHOT_FILES[key]
    if path.exists():
        return pd.read_csv(path, parse_dates=["epoch"])
    raw = {
        "nov2026": RAW / "gp_starlink_2026-11-23.csv.gz",
        "apr2026": RAW / "kaggle_active_2026-04-03.csv.gz",
        "apr2025": RAW / "kaggle_starlink_2025-04-11.csv.gz",
    }[key]
    if not raw.exists():
        raise FileNotFoundError(f"missing raw dataset {raw}; run scripts/fetch_data.sh")
    return {
        "nov2026": read_gp_csv,
        "apr2026": read_kaggle_active_2026,
        "apr2025": read_kaggle_starlink_2025,
    }[key](raw)


def load_satcat() -> pd.DataFrame:
    path = PROCESSED / "satcat.csv.gz"
    if path.exists():
        df = pd.read_csv(path, parse_dates=["launch_date", "decay_date"])
        return df
    raw = RAW / "satcat_starlink_2026-11-23.csv.gz"
    return read_satcat(raw)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def jd_from_timestamp(ts) -> tuple[float, float]:
    t = pd.Timestamp(ts)
    if t.tzinfo is not None:
        t = t.tz_convert("UTC").tz_localize(None)
    return jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond * 1e-6)


def jd_array(timestamps: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    vals = [jd_from_timestamp(t) for t in timestamps]
    return np.array([v[0] for v in vals]), np.array([v[1] for v in vals])


def omm_fields(row: pd.Series | dict) -> dict:
    r = row.to_dict() if isinstance(row, pd.Series) else dict(row)
    epoch = pd.Timestamp(r["epoch"])
    if epoch.tzinfo is not None:
        epoch = epoch.tz_convert("UTC").tz_localize(None)
    def num(key: str, default: float = 0.0) -> float:
        v = r.get(key, default)
        return default if v is None or (isinstance(v, float) and np.isnan(v)) else float(v)
    oid = str(r.get("object_id") or "2026-001A")
    if len(oid) < 3:
        oid = "2026-001A"
    try:
        norad_i = int(float(r.get("norad")))
        if norad_i <= 0:
            raise ValueError
    except (TypeError, ValueError):
        norad_i = int(hashlib.sha1(str(r.get("name_key", "")).encode()).hexdigest()[:6], 16)
    return {
        "NORAD_CAT_ID": str(norad_i),
        "CLASSIFICATION_TYPE": "U",
        "OBJECT_ID": oid,
        "EPHEMERIS_TYPE": "0",
        "ELEMENT_SET_NO": "999",
        "REV_AT_EPOCH": "1",
        "EPOCH": epoch.strftime("%Y-%m-%dT%H:%M:%S.%f"),
        "MEAN_MOTION": num("mm"),
        "ECCENTRICITY": num("ecc"),
        "INCLINATION": num("inc"),
        "RA_OF_ASC_NODE": num("raan"),
        "ARG_OF_PERICENTER": num("argp"),
        "MEAN_ANOMALY": num("ma"),
        "BSTAR": num("bstar"),
        "MEAN_MOTION_DOT": num("ndot"),
        "MEAN_MOTION_DDOT": num("nddot"),
    }


def build_satrec(row: pd.Series | dict) -> Satrec:
    sat = Satrec()
    omm.initialize(sat, omm_fields(row))
    return sat


def build_satrec_array(df: pd.DataFrame) -> tuple[SatrecArray, np.ndarray, np.ndarray]:
    sats = [build_satrec(r) for _, r in df.iterrows()]
    arr = SatrecArray(sats)
    return arr, df["name_key"].to_numpy(), df["name"].to_numpy()


def propagate_ecef(
    df: pd.DataFrame,
    timestamps: pd.Series,
    chunk: int = 60,
):
    """Yield (err, r_ecef, v_ecef) chunks of shape (nsat, ntime) and (nsat, ntime, 3)."""
    from .geometry import teme_to_ecef

    arr, keys, names = build_satrec_array(df)
    jd, fr = jd_array(timestamps)
    ntime = len(timestamps)
    for start in range(0, ntime, chunk):
        stop = min(start + chunk, ntime)
        err, r, v = arr.sgp4(jd[start:stop], fr[start:stop])
        r_ecef = np.empty_like(r)
        v_ecef = np.empty_like(v)
        for j in range(stop - start):
            r_ecef[:, j, :], v_ecef[:, j, :] = teme_to_ecef(
                r[:, j, :], v[:, j, :], jd[start + j] + fr[start + j]
            )
        yield err, r_ecef, v_ecef, keys, names, timestamps.iloc[start:stop].to_numpy()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def gzip_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, "rb") as fin, gzip.open(dst, "wb", compresslevel=9) as fout:
        fout.write(fin.read())
