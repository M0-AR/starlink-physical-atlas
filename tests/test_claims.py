import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from atlas.template import TemplateError, render, resolve

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "configs" / "claims.json").read_text())
METRICS = json.loads((ROOT / "results" / "metrics.json").read_text())
MANIFEST = json.loads((ROOT / "data" / "manifest.json").read_text())
REFS = {r["id"]: r for r in json.loads((ROOT / "configs" / "references.json").read_text())["references"]}
CONTEXT = {"metrics": METRICS, "manifest": MANIFEST}


def test_schema_and_status_legend():
    assert CONFIG["schema_version"] == 1
    assert CONFIG["status_order"] == [
        "verified",
        "consistent",
        "partially_verified",
        "external_only",
        "contradicted",
        "not_tested",
    ]
    assert set(CONFIG["status_legend"]) == set(CONFIG["status_order"])


def test_claim_ids_are_unique_and_sections_are_present():
    ids = [c["id"] for c in CONFIG["claims"]]
    assert len(ids) == len(set(ids))
    assert all(c.get("section") for c in CONFIG["claims"])
    assert all(c.get("claim") for c in CONFIG["claims"])


def test_every_claim_has_a_known_status_and_a_measured_sentence():
    allowed = set(CONFIG["status_order"])
    for claim in CONFIG["claims"]:
        assert claim["status"] in allowed, claim["id"]
        assert claim.get("measured"), claim["id"]
        assert "{{" not in render(claim["measured"], CONTEXT), claim["id"]


def test_references_and_evidence_resolve():
    for claim in CONFIG["claims"]:
        for key in claim.get("references", []):
            assert key in REFS, f"{claim['id']} cites unknown reference {key}"
        for path in claim.get("evidence", []):
            if path.startswith(("metrics.", "manifest.")):
                try:
                    resolve(CONTEXT, path)
                except TemplateError as exc:
                    pytest.fail(f"{claim['id']} has bad evidence path {path!r}: {exc}")


def test_status_counts_match_the_published_ledger():
    counts = Counter(c["status"] for c in CONFIG["claims"])
    assert len(CONFIG["claims"]) == 45
    assert counts["verified"] == 20
    assert counts["consistent"] == 7
    assert counts["partially_verified"] == 5
    assert counts["external_only"] == 13
    assert counts["contradicted"] == 0
    assert counts["not_tested"] == 0


def test_generated_csv_matches_the_config():
    path = ROOT / "results" / "claims.csv"
    assert path.exists()
    with path.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == len(CONFIG["claims"])
    assert {row["id"] for row in rows} == {c["id"] for c in CONFIG["claims"]}
    assert {row["status"] for row in rows} <= set(CONFIG["status_order"])
    for row in rows:
        assert row["measured"]
        assert "{{" not in row["measured"]


def test_generated_markdown_contains_every_claim_and_cited_reference():
    text = (ROOT / "results" / "CLAIMS.md").read_text(encoding="utf-8")
    assert text.startswith("# Claim Ledger")
    for claim in CONFIG["claims"]:
        assert f"#### {claim['id']} — " in text
    cited = {key for c in CONFIG["claims"] for key in c.get("references", [])}
    assert cited
    for key in cited:
        assert f"`{key}`" in text
