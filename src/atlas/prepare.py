"""Build canonical processed tables and the data manifest.

Run: python -m atlas.prepare
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import data
from . import tle

RAW_FILES = {
    "nov2026": ("gp_starlink_2026-11-23.csv.gz", "CelesTrak GP, GROUP=starlink", "CelesTrak public data"),
    "apr2026": ("kaggle_active_2026-04-03.csv.gz", "Kaggle active-satellite snapshot (CelesTrak source)", "CC BY-SA 4.0"),
    "apr2025": ("kaggle_starlink_2025-04-11.csv.gz", "Kaggle Starlink snapshot (CelesTrak source)", "MIT"),
    "satcat": ("satcat_starlink_2026-11-23.csv.gz", "CelesTrak SATCAT, GROUP=starlink", "CelesTrak public data"),
}


def main() -> None:
    data.PROCESSED.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_utc": pd.Timestamp.now(tz="UTC").isoformat(), "snapshots": {}, "files": {}}

    for key, filename in data.SNAPSHOT_FILES.items():
        path = data.PROCESSED / filename
        src = data.RAW / RAW_FILES[key][0]
        if not src.exists():
            raise FileNotFoundError(f"missing {src}; run scripts/fetch_data.sh")
        if not path.exists():
            loader = {
                "nov2026": data.read_gp_csv,
                "apr2026": data.read_kaggle_active_2026,
                "apr2025": data.read_kaggle_starlink_2025,
            }[key]
            df = loader(src)
            df.to_csv(path, index=False, compression="gzip")
        df = pd.read_csv(path, parse_dates=["epoch"])
        manifest["snapshots"][key] = {
            "rows": int(len(df)),
            "unique_names": int(df["name_key"].nunique()),
            "epoch_min": str(df["epoch"].min()),
            "epoch_max": str(df["epoch"].max()),
            "alt_median_km": float(df["alt_km"].median()),
            "source": RAW_FILES[key][2],
        }
        manifest["files"][str(path.relative_to(data.ROOT))] = {
            "sha256": data.sha256(path), "bytes": path.stat().st_size,
        }
        manifest["files"][str(src.relative_to(data.ROOT))] = {
            "sha256": data.sha256(src), "bytes": src.stat().st_size,
            "source_url": data.SOURCE_URLS[key], "license": RAW_FILES[key][2],
        }

    satcat_src = data.RAW / RAW_FILES["satcat"][0]
    satcat_path = data.PROCESSED / "satcat.csv.gz"
    if not satcat_path.exists():
        sc = data.read_satcat(satcat_src)
        sc.to_csv(satcat_path, index=False, compression="gzip")
    sc = pd.read_csv(satcat_path)
    manifest["satcat"] = {
        "rows": int(len(sc)),
        "status_counts": {str(k): int(v) for k, v in sc["status"].value_counts().items()},
        "launch_min": str(sc["launch_date"].min()),
        "launch_max": str(sc["launch_date"].max()),
    }
    manifest["files"][str(satcat_path.relative_to(data.ROOT))] = {
        "sha256": data.sha256(satcat_path), "bytes": satcat_path.stat().st_size,
    }
    manifest["files"][str(satcat_src.relative_to(data.ROOT))] = {
        "sha256": data.sha256(satcat_src), "bytes": satcat_src.stat().st_size,
        "source_url": data.SOURCE_URLS["satcat"], "license": RAW_FILES["satcat"][2],
    }

    active_src = data.RAW / "active_catalog_2026-11-23.csv.gz"
    if not active_src.exists():
        raise FileNotFoundError(f"missing {active_src}; run scripts/fetch_data.sh")
    active = pd.read_csv(active_src)
    manifest["active_catalog"] = {
        "rows": int(len(active)),
        "starlink_rows": int(active["OBJECT_NAME"].str.contains("STARLINK", case=False, na=False).sum()),
        "source": "CelesTrak GP, GROUP=active",
    }
    manifest["files"][str(active_src.relative_to(data.ROOT))] = {
        "sha256": data.sha256(active_src), "bytes": active_src.stat().st_size,
        "source_url": data.SOURCE_URLS["active"], "license": "CelesTrak public data",
    }

    series = tle.load_series(data.RAW)
    if len(series):
        series_path = data.PROCESSED / "tle_series.csv.gz"
        series.to_csv(series_path, index=False, compression="gzip")
        manifest["tle_series"] = {
            "rows": int(len(series)),
            "satellites": int(series["name"].nunique()),
            "epoch_min": str(series["epoch"].min()),
            "epoch_max": str(series["epoch"].max()),
            "source": "Kaggle per-satellite TLE series (MIT)",
        }
        manifest["files"][str(series_path.relative_to(data.ROOT))] = {
            "sha256": data.sha256(series_path), "bytes": series_path.stat().st_size,
        }

    out = data.ROOT / "data" / "manifest.json"
    out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Data manifest",
        "",
        f"Generated: {manifest['generated_utc']}",
        "",
        "All source files are public. Raw files are frozen snapshots; the fetch",
        "script can refresh the live CelesTrak snapshot, but the study is pinned",
        "to the checksums below so results are reproducible.",
        "",
        "## Snapshots",
        "",
        "| key | rows | unique names | epoch range | median altitude (km) | license |",
        "|---|---:|---:|---|---:|---|",
    ]
    for key, s in manifest["snapshots"].items():
        lines.append(
            f"| {key} | {s['rows']:,} | {s['unique_names']:,} | {s['epoch_min'][:19]} .. {s['epoch_max'][:19]} "
            f"| {s['alt_median_km']:.1f} | {s['source']} |"
        )
    lines += ["", "## Files", "", "| file | sha256 | bytes |", "|---|---|---:|"]
    for path, meta in sorted(manifest["files"].items()):
        lines.append(f"| `{path}` | `{meta['sha256']}` | {meta['bytes']:,} |")
    (data.ROOT / "data" / "MANIFEST.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: v["rows"] for k, v in manifest["snapshots"].items()}, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
