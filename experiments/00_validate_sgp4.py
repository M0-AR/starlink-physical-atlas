"""Experiment 00: validate the propagator against the official SGP4 vectors.

Writes results/tables/sgp4_validation.csv and sgp4_validation.json.
"""

from __future__ import annotations

import json
from pathlib import Path

from atlas.sgp4ver import evaluate, summary

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "tables"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = evaluate()
    df.to_csv(OUT / "sgp4_validation.csv", index=False)
    s = summary(df)
    (OUT / "sgp4_validation.json").write_text(json.dumps(s, indent=2) + "\n")
    print(json.dumps(s, indent=2))


if __name__ == "__main__":
    main()
