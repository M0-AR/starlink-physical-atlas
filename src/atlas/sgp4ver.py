"""Run the official SGP4 verification vectors shipped with python-sgp4.

The package bundles `SGP4-VER.TLE` and the reference output `tcppver.out`
produced by the canonical C++ implementation. This module reproduces the
comparison without relying on the package's private test helpers.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import sgp4
from sgp4.api import Satrec

PKG = Path(sgp4.__file__).resolve().parent


def load_cases() -> dict[int, tuple[str, str, float, float, float]]:
    lines = (PKG / "SGP4-VER.TLE").read_text(encoding="ascii").splitlines()
    cases: dict[int, tuple[str, str, float, float, float]] = {}
    for i, line in enumerate(lines):
        if not line.startswith("1 "):
            continue
        l1 = line
        l2 = lines[i + 1]
        satnum = int(l1[2:7])
        tail = l2[69:].split()
        if len(tail) == 3:
            tstart, tend, tstep = (float(x) for x in tail)
        else:
            tstart, tend, tstep = 0.0, 0.0, 0.0
        cases[satnum] = (l1, l2, tstart, tend, tstep)
    return cases


def load_reference() -> dict[int, np.ndarray]:
    blocks: dict[int, list[list[float]]] = {}
    current: int | None = None
    for line in (PKG / "tcppver.out").read_text(encoding="ascii").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "xx":
            current = int(parts[0])
            blocks[current] = []
            continue
        if current is None or len(parts) < 7:
            continue
        try:
            vals = [float(x) for x in parts[:7]]
        except ValueError:
            continue
        blocks[current].append(vals)
    return {k: np.asarray(v, dtype=float) for k, v in blocks.items()}


def evaluate() -> pd.DataFrame:
    cases = load_cases()
    ref = load_reference()
    rows = []
    for satnum, (l1, l2, tstart, tend, tstep) in cases.items():
        if satnum not in ref:
            continue
        try:
            sat = Satrec.twoline2rv(l1, l2[:69])
        except Exception as exc:  # pragma: no cover - defensive
            rows.append({"satnum": satnum, "vectors": 0, "errors": 0,
                         "max_pos_km": np.nan, "max_vel_km_s": np.nan,
                         "note": f"parse: {exc}"})
            continue
        dr, dv, errors = [], [], 0
        for vals in ref[satnum]:
            t = float(vals[0])
            e, r, v = sat.sgp4_tsince(t)
            if e != 0:
                errors += 1
                continue
            dr.append(np.linalg.norm(np.asarray(r) - vals[1:4]))
            dv.append(np.linalg.norm(np.asarray(v) - vals[4:7]))
        rows.append({
            "satnum": satnum,
            "vectors": len(dr),
            "errors": errors,
            "max_pos_km": float(np.max(dr)) if dr else np.nan,
            "max_vel_km_s": float(np.max(dv)) if dv else np.nan,
            "note": "",
        })
    return pd.DataFrame(rows).sort_values("satnum").reset_index(drop=True)


def summary(df: pd.DataFrame) -> dict:
    ok = df[df["vectors"] > 0]
    return {
        "cases_declared": int(len(df)),
        "cases_with_vectors": int(len(ok)),
        "vectors_compared": int(ok["vectors"].sum()),
        "propagation_errors": int(df["errors"].sum()),
        "max_pos_km": float(ok["max_pos_km"].max()),
        "p99_pos_km": float(ok["max_pos_km"].quantile(0.99)),
        "median_pos_km": float(ok["max_pos_km"].median()),
        "max_vel_km_s": float(ok["max_vel_km_s"].max()),
        "p99_vel_km_s": float(ok["max_vel_km_s"].quantile(0.99)),
    }
