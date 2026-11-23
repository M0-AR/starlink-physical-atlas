"""Render README.md from the paper template and generated metrics.

Every measured sentence in the template is a ``{{metrics.*}}`` placeholder.
Unknown paths or unresolved braces abort the build so a stale number cannot
reach the published README.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from atlas.template import TemplateError, render

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "paper" / "README.template.md"
METRICS = ROOT / "results" / "metrics.json"
MANIFEST = ROOT / "data" / "manifest.json"
CLAIMS = ROOT / "configs" / "claims.json"
REFS = ROOT / "configs" / "references.json"
OUT = ROOT / "README.md"
FIGURE = re.compile(r"results/figures/[A-Za-z0-9_./-]+\.png")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def reference_markdown(references: list[dict[str, Any]]) -> str:
    lines = []
    for ref in references:
        authors = ref.get("authors", "")
        title = ref.get("title", "")
        venue = ref.get("venue", "")
        year = ref.get("year", "")
        doi = ref.get("doi")
        text = f"{authors}. *{title}*. {venue}, {year}."
        if doi:
            text += f" DOI: [{doi}](https://doi.org/{doi})."
        elif ref.get("url"):
            text += f" [Link]({ref['url']})."
        lines.append(f"- {text}")
    return "\n".join(lines)


def main() -> None:
    metrics = load_json(METRICS)
    manifest = load_json(MANIFEST)
    claims_config = load_json(CLAIMS)
    references = load_json(REFS)["references"]

    status_counts = Counter(c["status"] for c in claims_config["claims"])
    cited = {key for c in claims_config["claims"] for key in c.get("references", [])}
    claim_stats = {
        "total": len(claims_config["claims"]),
        "verified": status_counts["verified"],
        "consistent": status_counts["consistent"],
        "partially_verified": status_counts["partially_verified"],
        "external_only": status_counts["external_only"],
        "contradicted": status_counts["contradicted"],
        "not_tested": status_counts["not_tested"],
        "cited_references": len(cited),
        "references_total": len(references),
    }

    template = TEMPLATE.read_text(encoding="utf-8")
    context = {
        "metrics": metrics,
        "manifest": manifest,
        "claims": claim_stats,
        "references_md": reference_markdown(references),
    }
    try:
        rendered = render(template, context)
    except TemplateError as exc:
        raise SystemExit(f"README render failed: {exc}") from exc

    missing = [path for path in sorted(set(FIGURE.findall(template))) if not (ROOT / path).exists()]
    if missing:
        raise SystemExit("missing figures: " + ", ".join(missing))

    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT} ({len(rendered)} bytes)")
    print(f"claims: {claim_stats['total']} total, {claim_stats['verified']} verified, "
          f"{claim_stats['consistent']} consistent, {claim_stats['partially_verified']} partially verified, "
          f"{claim_stats['external_only']} external-only")
    print(f"references: {len(references)} total, {len(cited)} cited by claims")


if __name__ == "__main__":
    main()
