# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-23

### Added

- Reproducible pipeline for three public Starlink snapshots, SGP4 validation, shell resolution, plane anatomy, migration, dynamics, service geometry, and a 45-claim evidence ledger.
- Static GitHub Pages site with seven live product views: overview, 3D atlas, migration, planes, service geometry, beginner guide, and Neural Orbit.
- 3D constellation explorer with inclination-family filters, shell rings, altitude exaggeration, time warp, and satellite inspection.
- Neural Orbit game: four levels, twenty questions, a 3D concept graph, local speech, reduced-motion support, and saved progress.
- Generated README, seven research figures, screenshots, social card, and an animated site tour.
- Professional repository layer: CI, GitHub Pages deployment from `main` `/docs`, tagged releases, GHCR container image, issue forms, security policy, contribution guide, press kit, and citation metadata.
- Install and packaging documentation for source, release wheels, the container image, and the static site.

### Verified

- 11,198 objects in the 2026-11-23 snapshot; 66.25% of the active catalog.
- 11 altitude shells across 5 inclination families; 92.20% assignment coverage.
- SGP4 maximum position error 1.1708e-7 km over 640 official vectors.
- J2 median absolute relative error 0.066%; p95 0.47%.
- 45 claims: 20 verified, 7 consistent, 5 partially verified, 13 external-only; 0 contradicted, 0 not tested.

### Notes

- The browser atlas visualises mean elements; the scientific metrics come from the SGP4 pipeline.
- Radio-only latency bounds are not end-to-end internet latency.
- The project is independent and is not affiliated with SpaceX or Starlink.
