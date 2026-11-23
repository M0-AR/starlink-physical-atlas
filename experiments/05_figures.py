"""Experiment 05: publication figures from the frozen result tables."""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import json

import numpy as np
import pandas as pd

from atlas.anatomy import assign_family, rectify_raan
from atlas.data import load_snapshot
from atlas.dynamics import match_snapshots

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "results" / "tables"
F = ROOT / "results" / "figures"
F.mkdir(parents=True, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update({"figure.dpi": 200, "savefig.dpi": 200, "font.size": 9,
                     "axes.titlesize": 10, "axes.labelsize": 9,
                     "legend.fontsize": 8, "figure.constrained_layout.use": True})

FAM_COLOR = {"30.5": "#7f7f7f", "43.0": "#1f77b4", "53.1": "#2ca02c",
             "70.0": "#ff7f0e", "97.4": "#d62728", "other": "#cccccc"}


def fig_population() -> None:
    m = json.loads((ROOT / "results/metrics.json").read_text())
    active = m["active_catalog"]
    snaps = m["snapshots"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.8))
    ax = axes[0]
    vals = [active["total"], active["starlink"]]
    labels = ["All active\ncatalog objects", "Starlink"]
    bars = ax.bar(labels, vals, color=["#8c8c8c", "#1f77b4"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 250, f"{v:,}", ha="center", va="bottom", fontsize=8)
    ax.set_ylabel("objects")
    ax.set_title(f"Starlink share: {active['share_pct']:.2f}%")
    ax.set_ylim(0, active["total"] * 1.15)

    ax = axes[1]
    keys = ["apr2025", "apr2026", "nov2026"]
    names = ["Apr 2025", "Apr 2026", "Nov 2026"]
    vals = [snaps[k]["n"] for k in keys]
    ax.plot(names, vals, marker="o", color="#1f77b4")
    for x, v in zip(names, vals):
        ax.annotate(f"{v:,}", (x, v), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_ylabel("Starlink objects")
    ax.set_title("Catalog growth")
    ax.set_ylim(min(vals) * 0.9, max(vals) * 1.08)
    fig.savefig(F / "fig1_population.png", bbox_inches="tight")
    plt.close(fig)


def fig_shells() -> None:
    d = assign_family(load_snapshot("nov2026"))
    shells = pd.read_csv(T / "anatomy_shells_nov2026.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1.35, 1]})
    ax = axes[0]
    for fam, g in d.groupby("family"):
        if fam == "other":
            continue
        ax.scatter(g["inc"], g["alt_km"], s=2, alpha=0.25, color=FAM_COLOR.get(fam, "#999999"), label=f"{fam}deg")
    for _, r in shells.iterrows():
        ax.axhline(r["shell_km_peak"], color=FAM_COLOR.get(str(r["family"]), "#999999"),
                   lw=0.6, ls=":", alpha=0.7)
    ax.set_xlabel("inclination (deg)")
    ax.set_ylabel("mean altitude (km)")
    ax.set_title("November 2026 shells")
    ax.legend(markerscale=4, loc="lower right", ncol=2, frameon=True)

    ax = axes[1]
    ax.hist(d["alt_km"], bins=np.arange(250, 620, 5), color="#4c72b0", alpha=0.85)
    for _, r in shells.iterrows():
        if r["n"] >= 100:
            ax.axvline(r["alt_median_km"], color="#c44e52", lw=0.6, ls="--", alpha=0.7)
    ax.set_xlabel("altitude (km)")
    ax.set_ylabel("satellites / 5 km")
    ax.set_title(f"{len(shells)} resolved shells")
    fig.savefig(F / "fig2_shells.png", bbox_inches="tight")
    plt.close(fig)


def fig_migration() -> None:
    nov = load_snapshot("nov2026")
    apr26 = load_snapshot("apr2026")
    apr25 = load_snapshot("apr2025")
    hist = pd.read_csv(T / "shell_history.csv")
    dates = {"apr2025": pd.Timestamp("2025-04-11"),
             "apr2026": pd.Timestamp("2026-04-03"),
             "nov2026": pd.Timestamp("2026-11-23")}
    hist["date"] = hist["epoch"].map(dates)
    dom = hist.sort_values("n").groupby(["family", "epoch"]).tail(1)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), gridspec_kw={"width_ratios": [1, 1.2]})
    ax = axes[0]
    ax.scatter(hist["date"], hist["alt_median_km"], s=5, color="#bbbbbb", zorder=1)
    for fam, g in dom.groupby("family"):
        g = g.sort_values("date")
        ax.plot(g["date"], g["alt_median_km"], marker="o", ms=3, zorder=2,
                color=FAM_COLOR.get(str(fam), "#999999"), label=f"{fam}deg")
    ax.set_xticks(list(dates.values()))
    ax.set_xticklabels(["Apr 2025", "Apr 2026", "Nov 2026"])
    ax.set_ylabel("dominant-shell median altitude (km)")
    ax.set_title("Shell migration")
    ax.legend(ncol=2, fontsize=7)

    ax = axes[1]
    m = match_snapshots(apr26, nov).reset_index()
    for fam, color in [("43.0", "#1f77b4"), ("53.1", "#2ca02c"), ("70.0", "#ff7f0e"), ("97.4", "#d62728")]:
        s = m[m["family_a"] == fam]["d_alt_km"].dropna()
        if len(s) < 20:
            continue
        x = np.sort(s.to_numpy())
        y = np.arange(1, len(x) + 1) / len(x)
        ax.plot(x, y, color=color, lw=1.4, label=f"{fam}deg (n={len(s):,})")
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlim(-345, 205)
    ax.set_xlabel("altitude change, Apr 2026 to Nov 2026 (km)")
    ax.set_ylabel("ECDF")
    ax.set_title("Family-specific migration")
    ax.legend(fontsize=7)
    fig.savefig(F / "fig3_migration.png", bbox_inches="tight")
    plt.close(fig)


def fig_planes() -> None:
    d = assign_family(load_snapshot("nov2026"))
    plan = pd.read_csv(T / "anatomy_planes_nov2026.csv")
    plan = plan[plan["planes"] > 0]
    chosen = [("43.0", 483.0), ("53.1", 463.0), ("70.0", 475.0), ("97.4", 465.0)]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 4.8))
    for ax, (fam, alt) in zip(axes.ravel(), chosen):
        sub = d[(d["family"] == fam) & ((d["alt_km"] - alt).abs() <= 6.0)]
        if len(sub) < 30:
            ax.set_axis_off()
            continue
        raan = np.sort(rectify_raan(sub))
        ax.plot(np.arange(len(raan)), raan, lw=0.8, color=FAM_COLOR.get(fam, "#333333"))
        row = plan[(plan["family"].astype(str) == fam) & ((plan["shell_km"] - alt).abs() < 1.5)]
        nplanes = int(row["planes"].iloc[0]) if len(row) else -1
        ax.set_title(f"{fam}deg / {alt:.0f} km: {len(sub):,} sats, {nplanes} RAAN groups")
        ax.set_xlabel("rank")
        ax.set_ylabel("rectified RAAN (deg)")
        ax.set_ylim(0, 360)
    fig.savefig(F / "fig4_planes.png", bbox_inches="tight")
    plt.close(fig)


def fig_service() -> None:
    sites = pd.read_csv(T / "service_sites.csv")
    h = pd.read_csv(T / "service_handovers.csv.gz")
    p = pd.read_csv(T / "service_passes.csv.gz")
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.8))
    ax = axes[0, 0]
    ax.barh(sites["site"], sites["n_visible_p50"], color="#4c72b0")
    ax.set_xlabel("median visible satellites (25 deg mask)")
    ax.set_title("Visibility")

    ax = axes[0, 1]
    for name, g in h.groupby("site"):
        s = g["interval_s"].dropna()
        if len(s) < 10:
            continue
        x = np.sort(s.to_numpy())
        ax.plot(x, np.arange(1, len(x)+1)/len(x), lw=0.9, alpha=0.7, label=name)
    ax.set_xlim(0, 120)
    ax.set_xlabel("handover interval (s)")
    ax.set_ylabel("ECDF")
    ax.set_title("Best-satellite handovers")
    ax.legend(fontsize=5, ncol=2, loc="lower right")

    ax = axes[1, 0]
    y = np.arange(len(sites))
    lo = sites["rtt_lower_p50_ms"].to_numpy()
    hi = sites["rtt_upper_p50_ms"].to_numpy()
    ax.errorbar((lo + hi) / 2, y, xerr=(hi - lo) / 2, fmt="o", color="#c44e52", ms=4, capsize=2)
    ax.set_yticks(y)
    ax.set_yticklabels(sites["site"])
    ax.set_xlabel("radio RTT p50 bounds (ms)")
    ax.set_title("Latency bounds (nadir to co-located gateway)")

    ax = axes[1, 1]
    s = p["max_doppler_khz"].dropna()
    x = np.sort(s.to_numpy())
    ax.plot(x, np.arange(1, len(x)+1)/len(x), color="#8172b2", lw=1.2)
    ax.axvline(230, color="k", ls="--", lw=0.8, label="230 kHz")
    ax.set_xlabel("max |Doppler| per pass (kHz)")
    ax.set_ylabel("ECDF")
    ax.set_title("Doppler at 11.325 GHz")
    ax.legend(fontsize=7)
    fig.savefig(F / "fig5_service.png", bbox_inches="tight")
    plt.close(fig)


def fig_dynamics() -> None:
    ev = pd.read_csv(T / "maneuver_events.csv")
    tle = pd.read_csv(ROOT / "data/processed/tle_series.csv.gz")
    tle["epoch"] = pd.to_datetime(tle["epoch"], utc=True)
    counts = ev["name_key"].value_counts().head(4).index.tolist()
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.0), gridspec_kw={"width_ratios": [1.4, 1]})
    ax = axes[0]
    for name in counts:
        g = tle[tle["name"] == name].sort_values("epoch")
        if len(g) < 5:
            continue
        ax.plot(g["epoch"], g["alt_km"], lw=0.9, label=name)
    ax.set_ylabel("altitude (km)")
    ax.set_title("Altitude histories")
    ax.legend(fontsize=6)
    ax.tick_params(axis="x", rotation=20)

    ax = axes[1]
    ev["year"] = pd.to_datetime(ev["epoch"]).dt.year
    tab = ev.groupby(["year", "direction"]).size().unstack(fill_value=0)
    tab.plot(kind="bar", stacked=True, ax=ax, color={"raise": "#4c72b0", "lower": "#c44e52"})
    ax.set_xlabel("year")
    ax.set_ylabel("detected steps")
    ax.set_title(f"{len(ev)} steps / {ev['name_key'].nunique()} sats")
    ax.legend(title="")
    ax.tick_params(axis="x", rotation=0)
    fig.savefig(F / "fig6_dynamics.png", bbox_inches="tight")
    plt.close(fig)


def fig_validation() -> None:
    v = pd.read_csv(T / "sgp4_validation.csv")
    j = pd.read_csv(T / "j2_fit.csv")
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9))
    ax = axes[0]
    ax.hist(np.log10(v["max_pos_km"].dropna()), bins=20, color="#4c72b0", alpha=0.85)
    ax.axvline(-3, color="k", ls="--", lw=0.8, label="1 mm")
    ax.set_xlabel("log10 max position error (km)")
    ax.set_ylabel("cases")
    ax.set_title(f"SGP4 official vectors (n={int(v['vectors'].sum()):,})")
    ax.legend(fontsize=7)

    ax = axes[1]
    ax.scatter(j["days"], j["resid_std_deg"], s=16, color="#c44e52")
    ax.set_xlabel("series length (days)")
    ax.set_ylabel("J2 residual std (deg)")
    ax.set_title("J2 rectification residuals")
    ax.set_yscale("log")
    fig.savefig(F / "fig7_validation.png", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    fig_population()
    fig_shells()
    fig_migration()
    fig_planes()
    fig_service()
    fig_dynamics()
    fig_validation()
    for p in sorted(F.glob("*.png")):
        print(p.name, p.stat().st_size)


if __name__ == "__main__":
    main()
