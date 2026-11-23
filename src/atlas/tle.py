"""Minimal fixed-width TLE parser for the public per-satellite series."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from .constants import MU, RE


def _epoch_from_line1(line1: str) -> pd.Timestamp:
    raw = line1[18:32].strip()
    yy = int(raw[:2])
    year = 2000 + yy if yy < 57 else 1900 + yy
    doy = float(raw[2:])
    ts = datetime(year, 1, 1, tzinfo=None) + timedelta(days=doy - 1.0)
    return pd.Timestamp(ts, tz="UTC")


def parse_tle_file(path: Path) -> pd.DataFrame:
    lines = [ln.rstrip("\n") for ln in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()]
    rows = []
    i = 0
    while i < len(lines) - 2:
        name = lines[i].strip()
        l1 = lines[i + 1].strip()
        l2 = lines[i + 2].strip()
        if name and l1.startswith("1 ") and l2.startswith("2 "):
            try:
                inc = float(l2[8:16])
                raan = float(l2[17:25])
                ecc = float("0." + l2[26:33].strip())
                argp = float(l2[34:42])
                ma = float(l2[43:51])
                mm = float(l2[52:63])
                rows.append({
                    "name": name,
                    "epoch": _epoch_from_line1(l1),
                    "inc": inc,
                    "raan": raan,
                    "ecc": ecc,
                    "argp": argp,
                    "ma": ma,
                    "mm": mm,
                    "norad": int(l1[2:7]),
                })
            except ValueError:
                pass
            i += 3
        else:
            i += 1
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["a_km"] = (MU / (df["mm"] * 2.0 * np.pi / 86400.0) ** 2) ** (1.0 / 3.0)
    df["alt_km"] = df["a_km"] - RE
    return df.sort_values(["name", "epoch"]).reset_index(drop=True)


def load_series(raw_dir: Path) -> pd.DataFrame:
    files = sorted((raw_dir / "tle_series").glob("*.txt"))
    frames = [parse_tle_file(f) for f in files]
    frames = [f for f in frames if len(f)]
    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, ignore_index=True)
    out["source"] = "kaggle-starlink-2025-tle-series"
    return out
