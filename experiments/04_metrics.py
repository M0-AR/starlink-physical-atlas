"""Experiment 04: collect every headline number into results/metrics.json.

The paper renderer reads this file; no number in README.md is typed by hand.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from atlas.anatomy import assign_family
from atlas.constants import C, H_GEO, MU
from atlas.data import load_satcat, load_snapshot
from atlas.geometry import slant_range_at_elevation

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
OUT = ROOT / "results" / "metrics.json"


def safe_key(value: object) -> str:
    """A dotted-template-safe key for float-valued labels (53.1 -> 53p1)."""
    try:
        text = f"{float(value):g}"
    except (TypeError, ValueError):
        text = str(value)
    return text.replace(".", "p").replace("-", "m")


def rec(df: pd.DataFrame) -> list[dict]:
    out = []
    for row in df.drop(columns=["Index"], errors="ignore").to_dict(orient="records"):
        clean = {}
        for k, v in row.items():
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                v = float(v)
            elif isinstance(v, float) and not np.isfinite(v):
                v = None
            if isinstance(v, pd.Timestamp):
                v = v.isoformat()
            clean[k] = v
        out.append(clean)
    return out


def main() -> None:
    nov = load_snapshot("nov2026")
    apr26 = load_snapshot("apr2026")
    apr25 = load_snapshot("apr2025")
    satcat = load_satcat()
    active = pd.read_csv(ROOT / "data/raw/active_catalog_2026-11-23.csv.gz")
    n_active = len(active)
    n_starlink_active = int(active["OBJECT_NAME"].str.contains("STARLINK", case=False, na=False).sum())

    shells = pd.read_csv(T / "anatomy_shells_nov2026.csv")
    planes = pd.read_csv(T / "anatomy_planes_nov2026.csv")
    history = pd.read_csv(T / "shell_history.csv")
    flow = pd.read_csv(T / "population_flow.csv")
    mig25 = pd.read_csv(T / "migration_apr2025_apr2026.csv")
    mig26 = pd.read_csv(T / "migration_apr2026_nov2026.csv")
    j2 = pd.read_csv(T / "j2_fit.csv")
    maneuvers = pd.read_csv(T / "maneuver_events.csv")
    decay = pd.read_csv(T / "decay_rates.csv")
    service = pd.read_csv(T / "service_sites.csv")
    sgp4 = json.loads((T / "sgp4_validation.json").read_text())
    service_meta = json.loads((T / "service_meta.json").read_text())
    launches = pd.read_csv(T / "launch_summary.csv")

    dtc = nov[nov["name"].str.contains(r"\[DTC\]", regex=True, na=False)]
    dtc25 = apr25[apr25["name"].str.contains(r"\[DTC\]", regex=True, na=False)]
    dtc26 = apr26[apr26["name"].str.contains(r"\[DTC\]", regex=True, na=False)]

    j2_abs = j2["rel_error"].abs()
    maneuver_year = maneuvers.assign(year=pd.to_datetime(maneuvers["epoch"]).dt.year)
    launch_2025 = launches[launches["launch_year"] == 2025]
    launch_2026 = launches[launches["launch_year"] == 2026]

    speed_kmh = np.sqrt(MU / nov["a_km"].to_numpy()) * 3600.0
    period_min = 2.0 * np.pi * np.sqrt(nov["a_km"].to_numpy() ** 3 / MU) / 60.0
    bands = [(500, 515), (515, 535), (535, 560), (560, 100000)]
    band_counts = {
        f"{lo}_{hi if hi < 100000 else 'plus'}": int(((nov["alt_km"] >= lo) & (nov["alt_km"] < hi)).sum())
        for lo, hi in bands
    }

    satcat_launch = satcat.copy()
    satcat_launch["launch_id"] = satcat_launch["object_id"].astype(str).str[:8]
    satcat_launch["launch_year"] = pd.to_datetime(satcat_launch["launch_date"], utc=True).dt.year
    per_launch = {}
    for year in (2025, 2026):
        counts = satcat_launch[satcat_launch["launch_year"] == year].groupby("launch_id").size()
        per_launch[str(year)] = {
            "n_launches": int(len(counts)),
            "median": float(counts.median()),
            "min": int(counts.min()),
            "max": int(counts.max()),
            "frac_25_to_29": round(float(((counts >= 25) & (counts <= 29)).mean()), 4),
        }
    first_window = (pd.to_datetime(satcat_launch["launch_date"], utc=True) >= pd.Timestamp("2026-01-01", tz="UTC")) & (
        pd.to_datetime(satcat_launch["launch_date"], utc=True) <= pd.Timestamp("2026-04-15", tz="UTC")
    )

    geo_slant = slant_range_at_elevation(H_GEO, 90.0)
    leo_slant = slant_range_at_elevation(550.0, 90.0)

    nov_fam = assign_family(nov)
    v3 = nov_fam[nov_fam["family"] == "30.5"].merge(
        satcat[["name_key", "launch_date"]], on="name_key", how="left"
    )
    v3["launch_day"] = pd.to_datetime(v3["launch_date"], utc=True).dt.strftime("%Y_%m_%d")
    v3_group = {
        "n": int(len(v3)),
        "alt_median_km": round(float(v3["alt_km"].median()), 1),
        "alt_min_km": round(float(v3["alt_km"].min()), 1),
        "alt_max_km": round(float(v3["alt_km"].max()), 1),
        "launch_days": {str(k): int(v) for k, v in v3["launch_day"].value_counts().sort_index().items()},
        "alt_range_by_day": {
            str(day): [round(float(g["alt_km"].min()), 1), round(float(g["alt_km"].max()), 1)]
            for day, g in v3.groupby("launch_day")
        },
    }

    sat_alt = nov[["name_key", "alt_km"]].merge(
        satcat[["name_key", "apogee", "perigee"]], on="name_key", how="inner"
    )
    sat_alt["satcat_mean_km"] = (
        pd.to_numeric(sat_alt["apogee"], errors="coerce") + pd.to_numeric(sat_alt["perigee"], errors="coerce")
    ) / 2.0
    sat_alt_diff = (sat_alt["alt_km"] - sat_alt["satcat_mean_km"]).abs().dropna()

    metrics = {
        "generated_from": "experiments/04_metrics.py",
        "snapshots": {
            "apr2025": {"n": len(apr25), "epoch_median": str(apr25["epoch"].median())},
            "apr2026": {"n": len(apr26), "epoch_median": str(apr26["epoch"].median())},
            "nov2026": {"n": len(nov), "epoch_median": str(nov["epoch"].median())},
        },
        "active_catalog": {
            "total": int(n_active),
            "starlink": n_starlink_active,
            "share_pct": round(100.0 * n_starlink_active / n_active, 2),
        },
        "satcat": {
            "total": len(satcat),
            "status_counts": {str(k): int(v) for k, v in satcat["status"].value_counts().items()},
            "launch_years": [int(x) for x in sorted(satcat["launch_date"].dropna().dt.year.unique())],
        },
        "altitude": {
            "median_km": round(float(nov["alt_km"].median()), 1),
            "p05_km": round(float(nov["alt_km"].quantile(0.05)), 1),
            "p95_km": round(float(nov["alt_km"].quantile(0.95)), 1),
            "max_km": round(float(nov["alt_km"].max()), 1),
            "pct_below_500": round(float((nov["alt_km"] < 500).mean() * 100), 2),
            "n_above_500": int((nov["alt_km"] >= 500).sum()),
            "above_500_pct": round(float((nov["alt_km"] >= 500).mean() * 100), 2),
            "above_500_bands": band_counts,
            "n_519_531": int(((nov["alt_km"] >= 519) & (nov["alt_km"] <= 531)).sum()),
            "speed_median_kmh": int(round(float(np.median(speed_kmh)))),
            "period_median_min": round(float(np.median(period_min)), 2),
            "orbits_per_day": round(1440.0 / float(np.median(period_min)), 2),
            "geo_to_median_ratio": round(H_GEO / float(nov["alt_km"].median()), 1),
        },
        "shells": {
            "n": int(len(shells)),
            "n_families": int(shells["family"].nunique()),
            "families": sorted({str(x) for x in shells["family"].unique()}),
            "n_assigned": int(shells["n"].sum()),
            "n_unassigned": int(len(nov) - shells["n"].sum()),
            "coverage_pct": round(100.0 * float(shells["n"].sum()) / len(nov), 2),
            "rows": rec(shells),
            "by_key": {
                f"{safe_key(row.family)}_{safe_key(row.shell_km_peak)}": rec(pd.DataFrame([row]))[0]
                for row in shells.itertuples()
            },
            "by_family": {
                safe_key(fam): {
                    "n": int(s["n"].sum()),
                    "n_shells": int(len(s)),
                    "alt_min_km": round(float(s["alt_median_km"].min()), 1),
                    "alt_max_km": round(float(s["alt_median_km"].max()), 1),
                }
                for fam, s in shells.groupby("family")
            },
        },
        "planes": {
            "n": int(len(planes)),
            "rows": rec(planes),
            "by_key": {
                f"{safe_key(row.family)}_{safe_key(row.shell_km)}": rec(pd.DataFrame([row]))[0]
                for row in planes.itertuples()
            },
        },
        "latency": {
            "geo_alt_km": H_GEO,
            "geo_slant_nadir_km": round(geo_slant, 1),
            "geo_4leg_km": round(4.0 * geo_slant, 1),
            "geo_4leg_ms": round(4.0 * geo_slant / C * 1000.0, 2),
            "leo550_4leg_km": round(4.0 * leo_slant, 1),
            "leo550_4leg_ms": round(4.0 * leo_slant / C * 1000.0, 2),
            "fiber_slowdown": 1.5,
            "ku_12ghz_period_ps": round(1.0e12 / 12.0e9, 2),
        },
        "shell_history": rec(history),
        "population_flow": rec(flow),
        "population_flow_by_period": {
            str(row.period): rec(pd.DataFrame([row]))[0] for row in flow.itertuples()
        },
        "migration": {
            "apr2025_apr2026": rec(mig25),
            "apr2026_nov2026": rec(mig26),
            "by_family": {
                "apr2025_apr2026": {safe_key(row.family): rec(pd.DataFrame([row]))[0] for row in mig25.itertuples()},
                "apr2026_nov2026": {safe_key(row.family): rec(pd.DataFrame([row]))[0] for row in mig26.itertuples()},
            },
        },
        "j2": {
            "n_satellites": int(len(j2)),
            "median_abs_rel_error_pct": round(float(j2_abs.median() * 100), 3),
            "p95_abs_rel_error_pct": round(float(j2_abs.quantile(0.95) * 100), 3),
            "max_abs_rel_error_pct": round(float(j2_abs.max() * 100), 3),
            "median_resid_std_deg": round(float(j2["resid_std_deg"].median()), 3),
            "p95_resid_std_deg": round(float(j2["resid_std_deg"].quantile(0.95)), 3),
            "max_resid_std_deg": round(float(j2["resid_std_deg"].max()), 3),
        },
        "maneuvers": {
            "events": int(len(maneuvers)),
            "satellites": int(maneuvers["name_key"].nunique()),
            "raises": int((maneuvers["direction"] == "raise").sum()),
            "lowers": int((maneuvers["direction"] == "lower").sum()),
            "by_year": {str(k): int(v) for k, v in maneuver_year.groupby("year").size().items()},
        },
        "decay": rec(decay),
        "decay_by_family": {safe_key(row.family): rec(pd.DataFrame([row]))[0] for row in decay.itertuples()},
        "v3_group": v3_group,
        "satcat_altitude_check": {
            "n": int(len(sat_alt_diff)),
            "median_abs_diff_km": round(float(sat_alt_diff.median()), 2),
            "p95_abs_diff_km": round(float(sat_alt_diff.quantile(0.95)), 2),
            "p99_abs_diff_km": round(float(sat_alt_diff.quantile(0.99)), 2),
            "max_abs_diff_km": round(float(sat_alt_diff.max()), 2),
        },
        "service": {
            "meta": service_meta,
            "sites": rec(service),
            "median_visible_p50": round(float(service["n_visible_p50"].median()), 1),
            "visible_p50_range": [int(service["n_visible_p50"].min()), int(service["n_visible_p50"].max())],
            "median_handover_interval_s": round(float(service["handover_interval_p50_s"].median()), 1),
            "handover_p50_range_s": [
                int(service["handover_interval_p50_s"].min()),
                int(service["handover_interval_p50_s"].max()),
            ],
            "median_handover_p90_s": round(float(service["handover_interval_p90_s"].median()), 1),
            "median_rtt_lower_p50_ms": round(float(service["rtt_lower_p50_ms"].median()), 2),
            "median_rtt_upper_p50_ms": round(float(service["rtt_upper_p50_ms"].median()), 2),
            "median_doppler_p95_khz": round(float(service["pass_max_doppler_p95_khz"].median()), 1),
            "doppler_p95_range_khz": [
                round(float(service["pass_max_doppler_p95_khz"].min()), 1),
                round(float(service["pass_max_doppler_p95_khz"].max()), 1),
            ],
            "median_rate_p95_khz_s": round(float(service["pass_max_doppler_rate_p95_khz_s"].median()), 2),
            "rate_p95_max_khz_s": round(float(service["pass_max_doppler_rate_p95_khz_s"].max()), 2),
            "frac_sites_rate_gt_5": round(float((service["pass_max_doppler_rate_p95_khz_s"] > 5).mean()), 4),
        },
        "sgp4_validation": sgp4,
        "launches": {
            "rows": rec(launches),
            "n_satellites": int(launches["satellites"].sum()),
            "n_launches": int(launches["launches"].sum()),
            "sats_2025": int(launch_2025["satellites"].sum()) if len(launch_2025) else 0,
            "launches_2025": int(launch_2025["launches"].sum()) if len(launch_2025) else 0,
            "sats_2026": int(launch_2026["satellites"].sum()) if len(launch_2026) else 0,
            "launches_2026": int(launch_2026["launches"].sum()) if len(launch_2026) else 0,
            "per_launch": per_launch,
            "first_3p5m_2026": int(first_window.sum()),
            "by_year": {
                str(int(row.launch_year)): {
                    "satellites": int(row.satellites),
                    "launches": int(row.launches),
                    "per_launch": round(float(row.satellites_per_launch), 2),
                }
                for row in launches.itertuples()
            },
        },
        "dtc": {
            "n_nov2026": int(len(dtc)),
            "n_apr2025": int(len(dtc25)),
            "n_apr2026": int(len(dtc26)),
            "alt_median_2025_km": round(float(dtc25["alt_km"].median()), 1) if len(dtc25) else None,
            "alt_median_2026_km": round(float(dtc26["alt_km"].median()), 1) if len(dtc26) else None,
            "alt_median_nov2026_km": round(float(dtc["alt_km"].median()), 1) if len(dtc) else None,
            "inc_median_2025_deg": round(float(dtc25["inc"].median()), 2) if len(dtc25) else None,
            "inc_median_2026_deg": round(float(dtc26["inc"].median()), 2) if len(dtc26) else None,
            "inc_median_nov2026_deg": round(float(dtc["inc"].median()), 2) if len(dtc) else None,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    print("active share:", metrics["active_catalog"]["share_pct"], "%")
    print("altitude median:", metrics["altitude"]["median_km"], "km; below 500:",
          metrics["altitude"]["pct_below_500"], "%")
    print("service handover median:", metrics["service"]["median_handover_interval_s"], "s")
    print("doppler p95 median:", metrics["service"]["median_doppler_p95_khz"], "kHz")


if __name__ == "__main__":
    main()
