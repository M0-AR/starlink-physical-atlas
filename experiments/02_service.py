"""Experiment 02: service-layer geometry (visibility, handover, Doppler, RTT).

Uses the live November 2026 element set, a 24 h / 15 s grid, and ten mid- to
high-latitude sites.  Latency is a radio bounding box: gateway-at-nadir
(lower) and gateway-at-user (upper).  It is not an end-to-end measurement.

Outputs under results/tables/:
  service_sites.csv
  service_rtt_samples.csv.gz
  service_handovers.csv.gz
  service_passes.csv.gz
  service_meta.json
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import pandas as pd

from atlas.constants import F_KU_DL
from atlas.data import load_snapshot
from atlas.service import DEFAULT_SITES, simulate_service

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=5760, help="15 s steps (5760 = 24 h)")
    ap.add_argument("--sites", type=int, default=len(DEFAULT_SITES))
    ap.add_argument("--max-sats", type=int, default=None)
    ap.add_argument("--chunk", type=int, default=48)
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    df = load_snapshot("nov2026")
    work = df[(df["alt_km"] >= 400) & (df["alt_km"] <= 600)].reset_index(drop=True)
    if args.max_sats:
        work = work.iloc[: args.max_sats].reset_index(drop=True)
    sites = DEFAULT_SITES[: args.sites]
    t0 = pd.Timestamp("2026-11-23T00:00:00Z")
    timestamps = pd.Series(pd.date_range(t0, periods=args.steps, freq="15s"))

    print(f"sites={len(sites)} steps={len(timestamps)} sats={len(work)}")
    t = time.perf_counter()
    summary, rtt, handovers, passes, meta = simulate_service(
        work, timestamps, sites=sites, chunk=args.chunk
    )
    elapsed = time.perf_counter() - t
    meta["runtime_s"] = round(elapsed, 1)
    meta["n_sites"] = len(sites)

    summary.to_csv(OUT / "service_sites.csv", index=False)
    rtt.to_csv(OUT / "service_rtt_samples.csv.gz", index=False)
    handovers.to_csv(OUT / "service_handovers.csv.gz", index=False)
    passes.to_csv(OUT / "service_passes.csv.gz", index=False)
    (OUT / "service_meta.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"runtime: {elapsed:.1f}s")
    print("\n== site summary ==")
    cols = [
        "site", "n_visible_p50", "n_visible_p95", "serving_elev_p50_deg",
        "serving_range_p50_km", "rtt_lower_p50_ms", "rtt_upper_p50_ms",
        "handovers_per_hour", "handover_interval_p50_s", "handover_interval_p90_s",
        "pass_duration_p50_s", "pass_max_elev_p50_deg",
        "pass_max_doppler_p95_khz", "pass_max_doppler_rate_p95_khz_s",
        "frac_passes_doppler_gt_230khz",
    ]
    print(summary[cols].to_string(index=False))

    frac = (summary["handover_interval_p50_s"] <= 30).mean()
    print(f"\nsites with median handover interval <= 30 s: {frac:.0%}")
    print(f"median over sites of median interval: {summary['handover_interval_p50_s'].median():.0f} s")
    print(f"median over sites of RTT lower/upper p50: "
          f"{summary['rtt_lower_p50_ms'].median():.1f} / {summary['rtt_upper_p50_ms'].median():.1f} ms")
    print(f"median over sites of p95 |Doppler|: {summary['pass_max_doppler_p95_khz'].median():.0f} kHz "
          f"(Ku downlink {F_KU_DL/1e9:.3f} GHz)")


if __name__ == "__main__":
    main()
