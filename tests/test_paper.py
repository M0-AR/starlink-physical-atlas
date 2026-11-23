import json
import re
from collections import Counter
from pathlib import Path

from atlas.paper import FIGURE, TEMPLATE, reference_markdown
from atlas.template import render

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_context():
    claims_config = load(ROOT / "configs" / "claims.json")
    references = load(ROOT / "configs" / "references.json")["references"]
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
    return {
        "metrics": load(ROOT / "results" / "metrics.json"),
        "manifest": load(ROOT / "data" / "manifest.json"),
        "claims": claim_stats,
        "references_md": reference_markdown(references),
    }


def test_readme_exists_and_is_substantial():
    assert README.exists()
    text = README.read_text(encoding="utf-8")
    assert len(text) > 15_000
    assert text.startswith("# Starlink Physical Atlas")


def test_readme_has_beginner_guide_contract():
    text = README.read_text(encoding="utf-8")
    assert "## 🌱 Beginner guide — read this and you are a professional" in text
    assert "(#-beginner-guide--read-this-and-you-are-a-professional)" in text
    assert "You will know more than most interview candidates." in text
    assert "Let's work this out in a step-by-step way to be sure we have the right answer" in text
    assert "donkey" not in text.lower()


def test_readme_local_links_and_assets_exist():
    text = README.read_text(encoding="utf-8")
    targets = re.findall(r"\]\(([^)]+)\)", text)
    targets += re.findall(r'(?:src|href)="([^"]+)"', text)
    missing = []
    for raw in targets:
        if raw.startswith(("#", "http://", "https://", "mailto:", "data:")):
            continue
        path = raw.split("#", 1)[0].split("?", 1)[0]
        if not path:
            continue
        if not (ROOT / path).exists():
            missing.append(raw)
    assert missing == [], "missing README targets: " + ", ".join(sorted(set(missing)))


def test_readme_embeds_existing_site_media():
    text = README.read_text(encoding="utf-8")
    for path in [
        "docs/assets/social-card.png",
        "docs/assets/screenshots/index.png",
        "docs/assets/screenshots/atlas.png",
        "docs/assets/screenshots/game.png",
        "docs/assets/media/atlas-demo.gif",
    ]:
        assert path in text
        assert (ROOT / path).exists(), path


def test_readme_has_no_unresolved_placeholders():
    text = README.read_text(encoding="utf-8")
    assert "{{" not in text
    assert "}}" not in text


def test_readme_is_exactly_the_rendered_template():
    expected = render(TEMPLATE.read_text(encoding="utf-8"), build_context())
    assert README.read_text(encoding="utf-8") == expected


def test_readme_cites_only_existing_figures():
    text = README.read_text(encoding="utf-8")
    paths = sorted(set(FIGURE.findall(text)))
    assert len(paths) == 7
    for path in paths:
        assert (ROOT / path).exists(), path


def test_readme_contains_headline_numbers_from_metrics():
    metrics = load(ROOT / "results" / "metrics.json")
    text = README.read_text(encoding="utf-8")
    assert f"{metrics['snapshots']['nov2026']['n']:,}" in text
    assert f"{metrics['altitude']['median_km']:.1f}" in text
    assert f"{metrics['shells']['n']}" in text
    assert f"{metrics['j2']['median_abs_rel_error_pct']:.3f}%" in text


def test_readme_reports_the_claim_ledger_and_references():
    text = README.read_text(encoding="utf-8")
    assert "45-claim ledger" in text
    assert "**20** verified" in text
    assert "**13** external-only" in text
    assert re.search(r"10\.\d{4,9}/", text), "expected at least one DOI in the references"
