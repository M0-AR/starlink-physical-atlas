"""Experiment 03: temporal dynamics, attrition, J2 validation, manoeuvres."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.anatomy import assign_family
from atlas.data import load_satcat, load_snapshot
from atlas.dynamics import (
    attrition,
    decay_rates,
    j2_series_fit,
    launch_summary,
    maneuver_events,
    match_snapshots,
    migration_summary,
    shell_history,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    nov = load_snapshot("nov2026")
    apr26 = load_snapshot("apr2026")
    apr25 = load_snapshot("apr2025")
    satcat = load_satcat()

    hist = shell_history({"apr2025": apr25, "apr2026": apr26, "nov2026": nov})
    hist.to_csv(OUT / "shell_history.csv", index=False)
    print("== shell history ==")
    print(hist.to_string(index=False))

    flow = attrition(apr26, nov)
    flow25 = attrition(apr25, apr26)
    pd.DataFrame([{"period": "apr2026->nov2026", **flow}, {"period": "apr2025->apr2026", **flow25}]).to_csv(
        OUT / "population_flow.csv", index=False
    )
    print("\n== population flow ==")
    print("Apr2026 -> Nov2026:", flow)
    print("Apr2025 -> Apr2026:", flow25)

    m26 = match_snapshots(apr26, nov)
    mig26 = migration_summary(m26)
    mig26.to_csv(OUT / "migration_apr2026_nov2026.csv", index=False)
    m25 = match_snapshots(apr25, apr26)
    mig25 = migration_summary(m25)
    mig25.to_csv(OUT / "migration_apr2025_apr2026.csv", index=False)
    print("\n== per-satellite migration, Apr2026 -> Nov2026 ==")
    print(mig26.to_string(index=False))

    launches = launch_summary(satcat)
    launches.to_csv(OUT / "launch_summary.csv", index=False)
    print("\n== SATCAT launches (on-orbit objects only) ==")
    print(launches.to_string(index=False))
    print("status counts:", satcat["status"].value_counts().to_dict())

    series = pd.read_csv(ROOT / "data" / "processed" / "tle_series.csv.gz", parse_dates=["epoch"])
    j2 = j2_series_fit(series)
    j2.to_csv(OUT / "j2_fit.csv", index=False)
    print("\n== J2 nodal regression, 27-satellite TLE panel ==")
    print(
        f"n={len(j2)}  median rel error={j2['rel_error'].median():+.4%}  "
        f"p95 |rel error|={j2['rel_error'].abs().quantile(0.95):.4%}  "
        f"max |rel error|={j2['rel_error'].abs().max():.4%}"
    )
    print(j2.sort_values("rel_error", key=lambda s: s.abs(), ascending=False).head(5).to_string(index=False))

    events, threshold = maneuver_events(series)
    events.to_csv(OUT / "maneuver_events.csv", index=False)
    print(f"\n== orbit-control events in TLE panel (threshold {threshold:.2f} km/step) ==")
    print(f"events={len(events)}  satellites={events['name_key'].nunique()}  lower={(events['direction']=='lower').sum()}  raise={(events['direction']=='raise').sum()}")
    events["year"] = pd.to_datetime(events["epoch"], utc=True).dt.year
    print(events.groupby("year").size().to_string())

    decay = decay_rates(nov)
    decay.to_csv(OUT / "decay_rates.csv", index=False)
    print("\n== altitude decay signature from ndot, Nov 2026 ==")
    print(decay.to_string(index=False))

    fam = assign_family(nov)
    v3 = fam[fam["family"] == "30.5"]
    if len(v3):
        v3m = v3.merge(satcat[["name_key", "launch_date"]], on="name_key", how="left")
        print("\n== 30.5 deg transit group ==")
        print(f"n={len(v3)}  alt_median={v3['alt_km'].median():.1f} km  "
              f"alt_min={v3['alt_km'].min():.1f}  alt_max={v3['alt_km'].max():.1f}")
        print(v3m["launch_date"].dt.strftime("%Y-%m").value_counts().sort_index().to_string())

    for label, df in [("apr2025", apr25), ("apr2026", apr26), ("nov2026", nov)]:
        n_dtc = int(df["name"].astype(str).str.contains(r"\[DTC\]", regex=True).sum())
        print(f"DTC-tagged {label}: {n_dtc}")


if __name__ == "__main__":
    main()
