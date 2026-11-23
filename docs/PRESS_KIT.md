# Press kit — Starlink Physical Atlas

## One-line description

The Starlink Physical Atlas is an independent, reproducible measurement of the
Starlink constellation built from public orbital data — with a 3D atlas, a
claim-by-claim evidence ledger, and a beginner-friendly path into the physics.

## Short boilerplate

Starlink is often described with round numbers: "about 500 km", "thousands of
satellites", "20 ms latency". The Starlink Physical Atlas replaces those
shorthands with a reproducible, open-data measurement of three public snapshots.
It resolves 11 altitude shells across 5 inclination families, tracks
shell-specific migration, measures the effective plane lattice after J2
rectification, models service geometry across 10 sites, and marks every
checkable statement with an evidence status.

The project is not affiliated with, endorsed by, or connected to SpaceX or
Starlink. It uses public catalog data and published references only. It is not a
live tracker, a collision-warning service, or an operational tool.

## Key facts

| Fact | Value | Where to check |
|---|---|---|
| Starlink objects in the 2026-11-23 snapshot | 11,198 | `results/metrics.json` |
| Share of the active catalog | 66.25% (11,199 of 16,904) | `results/metrics.json` |
| Median altitude | 465.5 km | `results/metrics.json` |
| Objects below 500 km | 97.95% | `results/metrics.json` |
| Resolved altitude shells | 11 across 5 inclination families | `results/metrics.json` |
| Largest shell | 53.1° / 462.7 km, n = 3,548 | `results/metrics.json` |
| Median J2 prediction error | 0.066% | `results/metrics.json` |
| SGP4 maximum position error | 1.171e-07 km over 640 official vectors | `results/metrics.json` |
| Median visible satellites per site | 55.0 (range 21–65) | `results/metrics.json` |
| Radio-only RTT bounds | 6.19–6.27 ms | `results/metrics.json` |
| Claim ledger | 45 claims: 20 verified, 7 consistent, 5 partially verified, 13 external-only | `results/CLAIMS.md` |

The 6 ms figure is a four-leg radio-path bound, not an end-to-end internet
latency measurement. The atlas says this explicitly wherever the number appears.

## Why it is newsworthy

- It replaces a single "550 km" narrative with 11 measured shells and a
  migration table that differs by inclination family.
- It separates catalog attrition from confirmed reentry.
- It shows that the observed plane structure is coherent but not one clean
  Walker set.
- It puts a reproducible, status-labelled evidence ledger next to the headline
  numbers.
- It makes the material teachable through a 20-concept beginner path and a 3D
  concept game.

## Assets

| Asset | File |
|---|---|
| Social card (1200×630) | [`assets/social-card.png`](assets/social-card.png) |
| Landing page screenshot | [`assets/screenshots/index.png`](assets/screenshots/index.png) |
| 3D atlas screenshot | [`assets/screenshots/atlas.png`](assets/screenshots/atlas.png) |
| Neural Orbit screenshot | [`assets/screenshots/game.png`](assets/screenshots/game.png) |
| Animated tour (GIF) | [`assets/media/atlas-demo.gif`](assets/media/atlas-demo.gif) |
| Animated tour (MP4) | [`assets/media/atlas-demo.mp4`](assets/media/atlas-demo.mp4) |
| Logo mark | [`assets/favicon.svg`](assets/favicon.svg) |

The live site is <https://m0-ar.github.io/starlink-physical-atlas/>. The full
evidence and methods are in
<https://github.com/M0-AR/starlink-physical-atlas>.

## Suggested citation

```bibtex
@misc{starlink_physical_atlas_2026,
  title        = {Starlink Physical Atlas: reproducible measurements of the 2025--2026 constellation},
  author       = {M0-AR},
  year         = {2026},
  howpublished = {https://github.com/M0-AR/starlink-physical-atlas},
  note         = {Open-data physical atlas; MIT code, CC BY 4.0 prose}
}
```

## Usage terms

The code is MIT licensed. The original prose is CC BY 4.0. The April 2026
derived tables retain CC BY-SA 4.0. Preserve attribution, the share-alike terms,
and the independence statement. Do not present the atlas as an official Starlink
or SpaceX source.

## Contact

Open a GitHub issue titled `Press:` at
<https://github.com/M0-AR/starlink-physical-atlas/issues>. For confidential
matters, use the repository's private security advisory form:
<https://github.com/M0-AR/starlink-physical-atlas/security/advisories/new>.
