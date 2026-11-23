"""Experiment 01: constellation anatomy from a single live snapshot.

Outputs:
  results/tables/anatomy_shells_nov2026.csv
  results/tables/anatomy_planes_nov2026.csv
  results/tables/anatomy_stability_nov2026.csv
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.anatomy import (
    assign_family,
    plane_summary,
    rectify_raan,
    shell_table,
    stability_curve,
)
from atlas.data import load_snapshot

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    nov = assign_family(load_snapshot("nov2026"))
    shells = shell_table(nov, min_count=25)
    shells.to_csv(OUT / "anatomy_shells_nov2026.csv", index=False)
    print("== altitude shells (Nov 2026) ==")
    print(shells.to_string(index=False))

    plane_rows, stab_rows = [], []
    for _, row in shells.iterrows():
        if row["n"] < 30:
            continue
        sub = nov[
            (nov["family"] == row["family"])
            & ((nov["alt_km"] - row["shell_km_peak"]).abs() <= 6.0)
        ]
        summary = plane_summary(sub, threshold_deg=0.2, min_size=10)
        summary.update({"family": row["family"], "shell_km": row["shell_km_peak"]})
        plane_rows.append(summary)
        work = sub.dropna(subset=["raan", "inc", "alt_km", "ecc"])
        stab = stability_curve(rectify_raan(work), min_size=10)
        stab.insert(0, "shell_km", row["shell_km_peak"])
        stab.insert(0, "family", row["family"])
        stab_rows.append(stab)

    planes = pd.DataFrame(plane_rows)
    planes.to_csv(OUT / "anatomy_planes_nov2026.csv", index=False)
    stab = pd.concat(stab_rows, ignore_index=True)
    stab.to_csv(OUT / "anatomy_stability_nov2026.csv", index=False)

    print("\n== plane lattice (rectified RAAN, threshold 0.2 deg, groups >= 10) ==")
    for r in plane_rows:
        print(
            f"{r['family']:>5} deg @ {r['shell_km']:5.1f} km  n={r['n']:5d}  "
            f"planes={r['planes']:3d}  occ_med={r['occupancy_median']:.1f}  "
            f"spacing={r['spacing_median_deg']:.2f} deg (CV {r['spacing_cv']:.2f})  "
            f"MA gap med={r['ma_gap_median_deg']:.2f} deg  twins={r['twins_lt_0p5deg']}"
        )
        print(
            f"      tight RAAN groups {r['tight_groups']}/{r['planes']} "
            f"({r['tight_fraction']:.2f}), tight MA gap med={r['tight_ma_gap_median_deg']:.2f} deg, "
            f"tight twins={r['tight_twins_lt_0p5deg']}"
        )
        print(
            f"      near-zero gaps: raw {r['raw']['frac_lt_0p1']:.3f} -> "
            f"rectified {r['rectified']['frac_lt_0p1']:.3f}; "
            f"p90 gap {r['raw']['p90_deg']:.2f} -> {r['rectified']['p90_deg']:.2f} deg"
        )

    print("\n== sensitivity of plane count to gap threshold ==")
    pivot = stab.pivot(index="shell_km", columns="threshold_deg", values="groups_ge_min")
    print(pivot.to_string())


if __name__ == "__main__":
    main()
