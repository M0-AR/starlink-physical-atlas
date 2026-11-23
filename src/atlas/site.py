"""Build the static JSON layer for the GitHub Pages atlas.

The browser never reads the research CSVs directly.  This module turns the
frozen metrics, tables, claims, and learning config into small, versioned JSON
files that can be served by GitHub Pages and audited in the repository.
"""

from __future__ import annotations

import json
import math
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.anatomy import assign_family, assign_shells
from atlas.template import render

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "results" / "tables"
METRICS = ROOT / "results" / "metrics.json"
CLAIMS = ROOT / "configs" / "claims.json"
LEARNING = ROOT / "configs" / "learning.json"
SNAPSHOT = ROOT / "data" / "processed" / "nov2026.csv.gz"
DOCS = ROOT / "docs"
DATA = DOCS / "data"
FIGURES = DOCS / "assets" / "figures"

FIGURE_META = [
    ("fig1_population.png", "Population growth and catalog composition"),
    ("fig2_shells.png", "Altitude and inclination shell anatomy"),
    ("fig3_migration.png", "Shell migration and population flow"),
    ("fig4_planes.png", "Effective plane lattice after J2 rectification"),
    ("fig5_service.png", "Coverage, handover, Doppler, and latency geometry"),
    ("fig6_dynamics.png", "Maneuvers, decay, and orbital lifetime"),
    ("fig7_validation.png", "SGP4 and SATCAT validation evidence"),
]


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, tuple):
        return [clean(v) for v in value]
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [clean(row) for row in frame.to_dict(orient="records")]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def claim_context(metrics: dict[str, Any], claims: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    status_counts = Counter(c["status"] for c in claims)
    return {
        "metrics": metrics,
        "manifest": manifest,
        "claims": {
            "total": len(claims),
            "verified": status_counts["verified"],
            "consistent": status_counts["consistent"],
            "partially_verified": status_counts["partially_verified"],
            "external_only": status_counts["external_only"],
            "contradicted": status_counts["contradicted"],
            "not_tested": status_counts["not_tested"],
        },
    }


def rendered_claims(claims: list[dict[str, Any]], context: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for claim in claims:
        item = dict(claim)
        for key in ("claim", "measured", "notes"):
            if isinstance(item.get(key), str):
                item[key] = render(item[key], context)
        out.append(item)
    return out


def build_atlas() -> dict[str, Any]:
    metrics = load_json(METRICS)
    manifest = load_json(ROOT / "data" / "manifest.json")
    claims = load_json(CLAIMS)["claims"]
    context = claim_context(metrics, claims, manifest)
    claims = rendered_claims(claims, context)

    shells = pd.read_csv(TABLES / "anatomy_shells_nov2026.csv")
    planes = pd.read_csv(TABLES / "anatomy_planes_nov2026.csv")
    migration_25 = pd.read_csv(TABLES / "migration_apr2025_apr2026.csv")
    migration_26 = pd.read_csv(TABLES / "migration_apr2026_nov2026.csv")
    service_sites = pd.read_csv(TABLES / "service_sites.csv")
    service_meta = load_json(TABLES / "service_meta.json")
    j2 = pd.read_csv(TABLES / "j2_fit.csv")
    decay = pd.read_csv(TABLES / "decay_rates.csv")
    launches = pd.read_csv(TABLES / "launch_summary.csv")
    history = pd.read_csv(TABLES / "shell_history.csv")
    flow = pd.read_csv(TABLES / "population_flow.csv")
    maneuvers = pd.read_csv(TABLES / "maneuver_events.csv")
    sgp4 = load_json(TABLES / "sgp4_validation.json")

    families = []
    for family, group in shells.groupby("family"):
        families.append(
            {
                "family": float(family),
                "n": int(group["n"].sum()),
                "n_shells": int(len(group)),
                "alt_min_km": float(group["alt_median_km"].min()),
                "alt_max_km": float(group["alt_median_km"].max()),
            }
        )

    status_counts = Counter(c["status"] for c in claims)
    claims_summary = {
        "total": len(claims),
        "statuses": dict(sorted(status_counts.items())),
        "items": claims,
    }

    service_summary = {
        "sites": len(service_sites),
        "median_visible_p50": metrics["service"]["median_visible_p50"],
        "visible_p50_range": metrics["service"]["visible_p50_range"],
        "median_handover_interval_s": metrics["service"]["median_handover_interval_s"],
        "median_handover_p90_s": metrics["service"]["median_handover_p90_s"],
        "median_rtt_lower_p50_ms": metrics["service"]["median_rtt_lower_p50_ms"],
        "median_rtt_upper_p50_ms": metrics["service"]["median_rtt_upper_p50_ms"],
        "median_doppler_p95_khz": metrics["service"]["median_doppler_p95_khz"],
        "doppler_p95_range_khz": metrics["service"]["doppler_p95_range_khz"],
        "median_rate_p95_khz_s": metrics["service"]["median_rate_p95_khz_s"],
        "rate_p95_max_khz_s": metrics["service"]["rate_p95_max_khz_s"],
    }

    return clean(
        {
            "meta": {
                "title": "Starlink Physical Atlas",
                "snapshot": "2026-11-23",
                "snapshot_epoch": metrics["snapshots"]["nov2026"]["epoch_median"],
                "generated_from": "experiments/07_site_data.py",
                "license": "MIT",
                "repo": "https://github.com/M0-AR/starlink-physical-atlas",
                "n": metrics["snapshots"]["nov2026"]["n"],
                "n_shells": metrics["shells"]["n"],
                "n_families": metrics["shells"]["n_families"],
                "claim_stats": {
                    "total": len(claims),
                    "verified": status_counts["verified"],
                    "consistent": status_counts["consistent"],
                    "partially_verified": status_counts["partially_verified"],
                    "external_only": status_counts["external_only"],
                    "contradicted": status_counts["contradicted"],
                    "not_tested": status_counts["not_tested"],
                },
            },
            "headline": {
                "objects": metrics["snapshots"]["nov2026"]["n"],
                "active_share_pct": metrics["active_catalog"]["share_pct"],
                "median_altitude_km": metrics["altitude"]["median_km"],
                "below_500_pct": metrics["altitude"]["pct_below_500"],
                "above_500": metrics["altitude"]["n_above_500"],
                "shells": metrics["shells"]["n"],
                "families": metrics["shells"]["n_families"],
                "assigned_pct": metrics["shells"]["coverage_pct"],
                "median_speed_kmh": metrics["altitude"]["speed_median_kmh"],
                "period_min": metrics["altitude"]["period_median_min"],
                "orbits_per_day": metrics["altitude"]["orbits_per_day"],
                "max_altitude_km": metrics["altitude"]["max_km"],
                "above_500_pct": metrics["altitude"]["above_500_pct"],
            },
            "snapshots": metrics["snapshots"],
            "altitude": metrics["altitude"],
            "shells": records(shells),
            "families": families,
            "planes": records(planes),
            "migration": {
                "apr2025_apr2026": records(migration_25),
                "apr2026_nov2026": records(migration_26),
                "flow": records(flow),
            },
            "service": {
                "meta": clean(service_meta),
                "summary": service_summary,
                "sites": records(service_sites),
            },
            "dynamics": {
                "j2": metrics["j2"],
                "maneuvers": metrics["maneuvers"],
                "decay": records(decay),
                "j2_fit": records(j2),
                "maneuver_events": records(maneuvers),
            },
            "launches": {
                "summary": metrics["launches"],
                "rows": records(launches),
            },
            "history": records(history),
            "validation": {
                **metrics["sgp4_validation"],
                "satcat": metrics["satcat_altitude_check"],
                "details": records(pd.read_csv(TABLES / "sgp4_validation.csv")),
                "service_meta": clean(service_meta),
                "sgp4": sgp4,
            },
            "claims": claims_summary,
            "figures": [{"file": name, "alt": alt} for name, alt in FIGURE_META],
        }
    )


def build_satellites() -> dict[str, Any]:
    frame = pd.read_csv(SNAPSHOT)
    frame = assign_family(frame)
    frame = assign_shells(frame)
    fields = ["name", "norad", "inc", "raan", "ecc", "argp", "ma", "mm", "alt_km", "a_km", "family", "shell_km"]
    rows = []
    for row in frame[fields].itertuples(index=False):
        rows.append(
            [
                str(row.name),
                int(row.norad),
                round(float(row.inc), 4),
                round(float(row.raan), 4),
                round(float(row.ecc), 7),
                round(float(row.argp), 4),
                round(float(row.ma), 4),
                round(float(row.mm), 7),
                round(float(row.alt_km), 3),
                round(float(row.a_km), 3),
                str(row.family),
                None if pd.isna(row.shell_km) else round(float(row.shell_km), 1),
            ]
        )
    return {"fields": fields, "rows": rows}


def build_learning(context: dict[str, Any]) -> dict[str, Any]:
    config = load_json(LEARNING)
    text = json.dumps(config, ensure_ascii=False)
    rendered = render(text, context)
    return json.loads(rendered)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    for name, _ in FIGURE_META:
        source = ROOT / "results" / "figures" / name
        target = FIGURES / name
        if source.exists():
            shutil.copy2(source, target)
        else:
            raise SystemExit(f"missing figure: {source}")

    atlas = build_atlas()
    metrics = load_json(METRICS)
    manifest = load_json(ROOT / "data" / "manifest.json")
    claims = load_json(CLAIMS)["claims"]
    context = claim_context(metrics, claims, manifest)

    (DATA / "atlas.json").write_text(json.dumps(atlas, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (DATA / "satellites.json").write_text(
        json.dumps(build_satellites(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    (DATA / "learning.json").write_text(
        json.dumps(build_learning(context), ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )

    for path in (DATA / "atlas.json", DATA / "satellites.json", DATA / "learning.json"):
        print(f"wrote {path.relative_to(ROOT)} ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
