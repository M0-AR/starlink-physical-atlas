"""Experiment 06: render the claim ledger from metrics.json.

The ledger in ``configs/claims.json`` stores hand-written claims, statuses,
evidence pointers, and reference keys.  Every measured sentence is a template
that must resolve against ``results/metrics.json``; an unresolved path is a
hard error, not a silent blank.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from atlas.template import TemplateError, render, resolve

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "claims.json"
METRICS = ROOT / "results" / "metrics.json"
MANIFEST = ROOT / "data" / "manifest.json"
REFS = ROOT / "configs" / "references.json"
OUT_CSV = ROOT / "results" / "claims.csv"
OUT_MD = ROOT / "results" / "CLAIMS.md"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def check_evidence(path: str, context: dict[str, Any]) -> None:
    """Validate metric/manifest pointers; leave table/file names untouched."""
    if path.startswith(("metrics.", "manifest.")):
        try:
            resolve(context, path)
        except TemplateError as exc:
            raise SystemExit(f"bad evidence path {path!r}: {exc}") from exc


def short_ref(entry: dict[str, Any]) -> str:
    first = str(entry.get("authors", "")).split(",")[0].strip()
    surname = first.split()[-1] if first else entry.get("id", "?")
    return f"{surname} et al. ({entry.get('year', 'n.d.')})"


def main() -> None:
    config = load_json(CONFIG)
    metrics = load_json(METRICS)
    manifest = load_json(MANIFEST)
    references = {r["id"]: r for r in load_json(REFS)["references"]}
    context = {"metrics": metrics, "manifest": manifest}

    claims = config["claims"]
    seen: set[str] = set()
    allowed = set(config["status_order"])
    rendered: list[dict[str, Any]] = []
    for claim in claims:
        cid = claim["id"]
        if cid in seen:
            raise SystemExit(f"duplicate claim id {cid}")
        seen.add(cid)
        if claim["status"] not in allowed:
            raise SystemExit(f"{cid}: unknown status {claim['status']!r}")
        if not claim.get("claim") or not claim.get("measured"):
            raise SystemExit(f"{cid}: claim and measured are required")
        for key in claim.get("references", []):
            if key not in references:
                raise SystemExit(f"{cid}: unknown reference key {key!r}")
        for path in claim.get("evidence", []):
            check_evidence(path, context)
        row = dict(claim)
        row["measured"] = render(claim["measured"], context)
        rendered.append(row)

    status_counts = Counter(row["status"] for row in rendered)
    section_counts = Counter(row["section"] for row in rendered)
    cited = sorted({key for row in rendered for key in row.get("references", [])})

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        fields = ["id", "section", "claim", "status", "measured", "evidence", "references", "notes", "source"]
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for row in rendered:
            writer.writerow({
                "id": row["id"],
                "section": row["section"],
                "claim": row["claim"],
                "status": row["status"],
                "measured": row["measured"],
                "evidence": "; ".join(row.get("evidence", [])),
                "references": "; ".join(row.get("references", [])),
                "notes": row.get("notes", ""),
                "source": row.get("source", ""),
            })

    lines = [
        "# Claim Ledger",
        "",
        "This ledger maps each checkable statement in the explainer to direct measurements or to an explicit external source. "
        "Measured sentences are generated from [`results/metrics.json`](metrics.json); no number here is typed by hand.",
        "",
        f"{len(rendered)} claims across {len(section_counts)} sections.",
        "",
        "## Status legend",
        "",
        "| Status | Meaning |",
        "|---|---|",
    ]
    legend = config["status_legend"]
    for status in config["status_order"]:
        lines.append(f"| `{status}` | {legend[status]} |")
    lines += [
        "",
        "## Summary",
        "",
        "| Status | Claims |",
        "|---|---:|",
    ]
    for status in config["status_order"]:
        if status_counts[status]:
            lines.append(f"| `{status}` | {status_counts[status]} |")
    lines += ["", "| Section | Claims |", "|---|---:|"]
    for section, count in section_counts.items():
        lines.append(f"| {section} | {count} |")
    lines += [
        "",
        "`external_only` means the statement is not tested in this study; it is not evidence that the statement is correct. "
        "`consistent` means our measurement supports the claim but does not uniquely establish it.",
        "",
        "## Claims",
    ]

    for section, _ in section_counts.items():
        lines += ["", f"### {section}", ""]
        for row in [r for r in rendered if r["section"] == section]:
            lines += [
                f"#### {row['id']} — {row['claim']}",
                "",
                f"- **Status:** `{row['status']}`",
                f"- **Measured:** {row['measured']}",
            ]
            if row.get("evidence"):
                lines.append("- **Evidence:** " + ", ".join(f"`{p}`" for p in row["evidence"]))
            if row.get("references"):
                lines.append("- **References:** " + ", ".join(f"`{k}`" for k in row["references"]))
            if row.get("notes"):
                lines.append(f"- **Notes:** {row['notes']}")
            lines.append(f"- **Source:** {row.get('source', 'n/a')}")
            lines.append("")

    lines += ["## References", ""]
    for key in cited:
        entry = references[key]
        bits = [entry.get("authors", ""), f"*{entry.get('title', '')}*", entry.get("venue", "")]
        meta = ", ".join(b for b in bits if b)
        tail = f" DOI: [{entry['doi']}](https://doi.org/{entry['doi']})" if entry.get("doi") else ""
        lines.append(f"- `{key}` — {meta}.{tail}")
    lines.append("")

    try:
        OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    except Exception as exc:
        raise SystemExit(f"could not write {OUT_MD}: {exc}") from exc

    print(f"wrote {OUT_CSV} ({len(rendered)} claims)")
    print(f"wrote {OUT_MD} ({len(rendered)} claims, {len(cited)} references)")
    for status in config["status_order"]:
        if status_counts[status]:
            print(f"  {status}: {status_counts[status]}")


if __name__ == "__main__":
    main()
