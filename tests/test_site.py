import json
import re
import struct
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
APP = DOCS / "app"

PAGES = [
    DOCS / "index.html",
    DOCS / "preview.html",
    APP / "overview.html",
    APP / "atlas.html",
    APP / "migration.html",
    APP / "planes.html",
    APP / "service.html",
    APP / "learn.html",
    APP / "game.html",
    APP / "all.html",
]

POSTERS = [
    DOCS / "assets" / "posters" / f"{name}.png"
    for name in ("overview", "atlas", "migration", "planes", "service", "learn", "game")
]

LOCAL = re.compile(r'\s(?:href|src)="([^"]+)"')


def test_pages_and_pages_metadata_exist():
    assert (DOCS / ".nojekyll").exists()
    for page in PAGES:
        assert page.exists(), page
        text = page.read_text(encoding="utf-8")
        assert "<h1" in text, page
        assert 'rel="icon"' in text, page
        assert "assets/favicon.svg" in text, page


def test_preview_is_an_alias_to_the_landing_page():
    text = (DOCS / "preview.html").read_text(encoding="utf-8")
    assert "index.html#preview" in text


def test_every_local_page_link_and_asset_exists():
    missing = []
    for page in PAGES:
        text = page.read_text(encoding="utf-8")
        for raw in LOCAL.findall(text):
            if raw.startswith(("#", "http://", "https://", "mailto:", "data:")) or "${" in raw:
                continue
            path = urlparse(raw).path
            if not path:
                continue
            target = (page.parent / path).resolve()
            if not target.exists():
                missing.append(f"{page.relative_to(ROOT)} -> {raw}")
    assert missing == [], "\n".join(missing)


def test_landing_page_has_seven_lazy_preview_tabs():
    text = (DOCS / "index.html").read_text(encoding="utf-8")
    assert text.count('role="tab"') == 7
    assert text.count('role="tabpanel"') == 7
    assert text.count("data-src=") == 7
    for name in ("overview", "atlas", "migration", "planes", "service", "learn", "game"):
        assert f'src="assets/posters/{name}.png"' in text
        assert f'data-src="app/{name}.html"' in text


def test_preview_fallback_and_caption_contract():
    text = (DOCS / "index.html").read_text(encoding="utf-8")
    assert text.count("Launch interactive demo") == 7
    assert "Launch full screen" not in text
    assert 'id="preview-caption-text"' in text
    assert 'aria-live="polite"' in text
    assert 'class="preview-tip"' in text
    site = (DOCS / "assets" / "js" / "site.js").read_text(encoding="utf-8")
    assert "PREVIEW_CAPTIONS" in site
    assert "caption.textContent" in site
    assert "11,198" not in site


def test_posters_and_media_are_not_empty():
    for poster in POSTERS:
        assert poster.exists(), poster
        assert poster.stat().st_size > 50_000, poster
    for media in [
        DOCS / "assets" / "social-card.png",
        DOCS / "assets" / "media" / "atlas-demo.gif",
        DOCS / "assets" / "media" / "atlas-demo.mp4",
    ]:
        assert media.exists(), media
        assert media.stat().st_size > 100_000, media


def test_social_card_is_1200_by_630():
    data = (DOCS / "assets" / "social-card.png").read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (1200, 630)


def test_generated_payloads_match_the_frozen_snapshot():
    atlas = json.loads((DOCS / "data" / "atlas.json").read_text(encoding="utf-8"))
    learning = json.loads((DOCS / "data" / "learning.json").read_text(encoding="utf-8"))
    satellites = json.loads((DOCS / "data" / "satellites.json").read_text(encoding="utf-8"))

    assert atlas["snapshots"]["nov2026"]["n"] == 11_198
    assert len(atlas["shells"]) == 11
    assert len(atlas["families"]) == 5
    assert len(atlas["planes"]) == 10
    assert len(atlas["figures"]) == 7
    assert len(learning["levels"]) == 4
    assert len(learning["concepts"]) == 20
    assert len(learning["questions"]) == 20
    assert len(satellites["rows"]) == 11_198
    assert len(satellites["fields"]) == 12


def test_service_page_plots_both_rtt_and_doppler():
    text = (APP / "service.html").read_text(encoding="utf-8")
    assert "Doppler p95" in text
    assert "pass_max_doppler_p95_khz" in text
    assert 'yAxisID: "y1"' in text
    assert "radio RTT (ms)" in text
    assert "Doppler p95 (kHz)" in text
