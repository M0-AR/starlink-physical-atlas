# Claim Ledger

This ledger maps each checkable statement in the explainer to direct measurements or to an explicit external source. Measured sentences are generated from [`results/metrics.json`](metrics.json); no number here is typed by hand.

45 claims across 8 sections.

## Status legend

| Status | Meaning |
|---|---|
| `verified` | Directly measured in this study and matching the claim. |
| `consistent` | Our measurement supports the claim but does not uniquely establish it. |
| `partially_verified` | Some components are measured; others remain external or untested. |
| `external_only` | Not tested here; relies on an operator, public report, or cited paper. |
| `contradicted` | Our measurement conflicts with the claim. |
| `not_tested` | No measurement and no adequate external source. |

## Summary

| Status | Claims |
|---|---:|
| `verified` | 20 |
| `consistent` | 7 |
| `partially_verified` | 5 |
| `external_only` | 13 |

| Section | Claims |
|---|---:|
| Population and orbit | 9 |
| Latency and service geometry | 6 |
| Spacecraft and radio | 8 |
| Network operations | 3 |
| Launch and evolution | 8 |
| Safety and environment | 4 |
| Direct-to-cell | 3 |
| Validation | 4 |

`external_only` means the statement is not tested in this study; it is not evidence that the statement is correct. `consistent` means our measurement supports the claim but does not uniquely establish it.

## Claims

### Population and orbit

#### P01 — More than 11,000 Starlink objects are in orbit.

- **Status:** `verified`
- **Measured:** 11,198 objects in the 2026-11-23 CelesTrak GP snapshot; SATCAT contains 11,198.
- **Evidence:** `metrics.snapshots.nov2026.n`, `metrics.satcat.total`, `manifest.snapshots.nov2026.rows`
- **Notes:** Counts are on-orbit objects, not historical launches.
- **Source:** transcript

#### P02 — Starlink is roughly two of every three active satellites.

- **Status:** `verified`
- **Measured:** 11,199 of 16,904 active catalog objects = 66.25%.
- **Evidence:** `metrics.active_catalog.starlink`, `metrics.active_catalog.total`, `metrics.active_catalog.share_pct`
- **Notes:** Active catalog is a separate 2026-11-23 snapshot; the numerator matches the Starlink GP count.
- **Source:** transcript

#### P03 — Orbital speed is about 27,000 km/h.

- **Status:** `verified`
- **Measured:** Median circular speed 27,474 km/h from the snapshot's semi-major axes.
- **Evidence:** `metrics.altitude.speed_median_kmh`
- **Notes:** Circular approximation; individual elliptical speeds vary.
- **Source:** transcript

#### P04 — The orbital period is about 1.5 h, or roughly 15 orbits per day.

- **Status:** `verified`
- **Measured:** Median period 93.91 min = 15.33 orbits/day.
- **Evidence:** `metrics.altitude.period_median_min`, `metrics.altitude.orbits_per_day`
- **Notes:** Keplerian period from the TLE semi-major axis.
- **Source:** transcript

#### P05 — The constellation operates near 500 km, roughly 70 times lower than GEO.

- **Status:** `consistent`
- **Measured:** Median 465.5 km (p05 354.2, p95 483.1); 97.95% below 500 km; GEO/median = 76.9x.
- **Evidence:** `metrics.altitude.median_km`, `metrics.altitude.pct_below_500`, `metrics.altitude.geo_to_median_ratio`
- **References:** `ali2026`, `ronchetti2026`
- **Notes:** The distribution is not a single 500 km shell; 2.05% of objects are at or above 500 km.
- **Source:** transcript

#### P06 — The constellation uses several inclination families and resolved altitude shells.

- **Status:** `verified`
- **Measured:** 5 inclination families (30.5, 43.0, 53.1, 70.0, 97.4), 11 resolved shells; 10,325 of 11,198 objects assigned (92.20%).
- **Evidence:** `metrics.shells.n_families`, `metrics.shells.n`, `metrics.shells.n_assigned`, `metrics.shells.coverage_pct`
- **Notes:** Shell detection uses 2 km altitude histogram peaks, a 25-object minimum, and a +/-8 km assignment window.
- **Source:** derived

#### P07 — Four large operational shells dominate the November 2026 snapshot.

- **Status:** `verified`
- **Measured:** 43.0 deg / 483 km n=3,223; 53.1 deg / 463 km n=3,548; 70.0 deg / 475 km n=608; 97.4 deg / 465 km n=1,447.
- **Evidence:** `metrics.shells.by_key.43_483.n`, `metrics.shells.by_key.53p1_463.n`, `metrics.shells.by_key.70_475.n`, `metrics.shells.by_key.97p4_465.n`
- **Notes:** These four shells account for most of the assigned population; smaller deployment shells remain.
- **Source:** derived

#### P08 — A small but non-zero population sits at or above 500 km.

- **Status:** `verified`
- **Measured:** 230 objects (2.05%): 500-515 km 93, 515-535 km 108, 535-560 km 19, >=560 km 10.
- **Evidence:** `metrics.altitude.n_above_500`, `metrics.altitude.above_500_pct`, `metrics.altitude.above_500_bands`
- **Notes:** The 230 objects are a mixture of the 70 deg 525 km shell and a small high-altitude tail; they do not overturn the 'about 500 km' statement.
- **Source:** derived

#### P09 — The plane lattice is not a single clean Walker set.

- **Status:** `consistent`
- **Measured:** Effective RAAN groups: 43 deg / 483 km 92 (spacing 3.64 deg, CV 0.25); 53.1 deg / 463 km 124 (2.09 deg, CV 0.52); 70 deg / 475 km 23; 97.4 deg / 465 km 62.
- **Evidence:** `metrics.planes.by_key.43_483`, `metrics.planes.by_key.53p1_463`, `metrics.planes.by_key.70_475`, `metrics.planes.by_key.97p4_465`
- **References:** `ronchetti2026`, `ali2026`
- **Notes:** Counts are effective RAAN clusters after J2 rectification, not design plane numbers. Mean-anomaly and twin metrics are contaminated where adjacent planes merge.
- **Source:** derived


### Latency and service geometry

#### L01 — A GEO bent-pipe at 35,786 km has a four-leg radio path above 140,000 km and about 0.48 s of light time.

- **Status:** `verified`
- **Measured:** 35,786.0 km altitude; 4 x nadir slant = 143,144.0 km; 477.48 ms.
- **Evidence:** `metrics.latency.geo_alt_km`, `metrics.latency.geo_4leg_km`, `metrics.latency.geo_4leg_ms`
- **Notes:** Vacuum light time only; no processing, queueing, or fiber.
- **Source:** derived

#### L02 — Public figures put GEO service at 600 ms or more and Starlink US peak-hour latency near 25 ms, with a 20 ms goal.

- **Status:** `external_only`
- **Measured:** Not measured; this study has no end-to-end RTT probe.
- **References:** `casparsen2026`
- **Notes:** Operator and public-network figures repeated by the explainer. Our radio-only bounds are not comparable to these end-to-end numbers.
- **Source:** transcript

#### L03 — A 550 km LEO bent-pipe has a ~7 ms radio-only RTT; the 10-site simulation bounds are 6.1-6.5 ms.

- **Status:** `verified`
- **Measured:** Ideal 550 km: 2,200.0 km / 7.34 ms; site medians lower 6.19 ms, upper 6.27 ms.
- **Evidence:** `metrics.latency.leo550_4leg_ms`, `metrics.service.median_rtt_lower_p50_ms`, `metrics.service.median_rtt_upper_p50_ms`
- **Notes:** Gateway-at-nadir (lower) and gateway-at-user (upper) bounds; excludes fiber, processing, scheduling, weather, and load.
- **Source:** derived

#### L04 — Sites see tens of Starlink satellites above a 25 deg elevation mask.

- **Status:** `verified`
- **Measured:** Median visible p50 55.0; site range 21-65.
- **Evidence:** `metrics.service.median_visible_p50`, `metrics.service.visible_p50_range`
- **Notes:** Ten sites, 24 h at 15 s, satellites between 400 and 600 km.
- **Source:** derived

#### L05 — Best-satellite handovers occur on 15-30 s scales.

- **Status:** `consistent`
- **Measured:** p50 median 30.0 s (range 15-30); p90 median 45.0 s.
- **Evidence:** `metrics.service.median_handover_interval_s`, `metrics.service.handover_p50_range_s`, `metrics.service.median_handover_p90_s`
- **References:** `casparsen2026`, `tidetcp2026`
- **Notes:** Geometric best-satellite model, not the operational scheduler. Literature reports a 15 s global reconfiguration.
- **Source:** derived

#### L06 — Fiber is about 1.5 times slower than vacuum, and a 12 GHz carrier has an 83.33 ps period.

- **Status:** `verified`
- **Measured:** Fiber slowdown 1.5x; 1/12 GHz = 83.33 ps.
- **Evidence:** `metrics.latency.fiber_slowdown`, `metrics.latency.ku_12ghz_period_ps`
- **Notes:** The 1.5x figure is a representative refractive-index value, not a measured fiber route.
- **Source:** derived


### Spacecraft and radio

#### S01 — A Gen2 mini is about 800 kg with a roughly 30 m array span and 116 m2 area; Gen1 was about 300 kg with an 8 m panel.

- **Status:** `external_only`
- **Measured:** Not measured; no mass, area, or dimension telemetry in public TLEs.
- **Notes:** Operator specification repeated by the explainer.
- **Source:** transcript

#### S02 — The user terminal is an electronically steered phased array, not a mechanically tracked dish.

- **Status:** `external_only`
- **Measured:** Not measured; no terminal teardown or beam-pattern data.
- **Notes:** Hardware claim from the explainer.
- **Source:** transcript

#### S03 — Spacecraft use star trackers and many Linux computers, including 4,000+ computers across 60 Gen1 satellites.

- **Status:** `external_only`
- **Measured:** Not measured; no onboard avionics data.
- **Notes:** Company statement repeated by the explainer.
- **Source:** transcript

#### S04 — Argon Hall thrusters provide about 170 mN with a sub-2.3 kg unit, about 2.5x Gen1 thrust and 1.5x efficiency; propellant moved from krypton to argon.

- **Status:** `external_only`
- **Measured:** Not measured; no thruster telemetry in public TLEs.
- **Notes:** 170 mN is about 17.3 g-force equivalent, below a typical 23 g AA cell; the comparison is arithmetic, the thruster specification is external.
- **Source:** transcript

#### S05 — A separate high-frequency gateway channel and improved antennas give about 4x the capacity of Gen1.

- **Status:** `external_only`
- **Measured:** Not measured; no capacity or gateway-link telemetry.
- **Notes:** Operator claim repeated by the explainer.
- **Source:** transcript

#### S06 — The user link uses about 12 GHz and electronic steering on microsecond scales.

- **Status:** `partially_verified`
- **Measured:** 12 GHz period 83.33 ps verified arithmetically; steering latency and array hardware were not measured.
- **Evidence:** `metrics.latency.ku_12ghz_period_ps`
- **Notes:** The period follows from the stated carrier; the beam-steering speed is a hardware claim.
- **Source:** derived

#### S07 — Doppler at 11.325 GHz stays near +/-230 kHz with rates below 5 kHz/s at a 25 deg mask.

- **Status:** `consistent`
- **Measured:** p95 max Doppler 233.6 kHz (range 232.8-243.8); p95 rate 4.12 kHz/s (max 4.48); sites with p95 rate >5 kHz/s: 0.00%.
- **Evidence:** `metrics.service.median_doppler_p95_khz`, `metrics.service.doppler_p95_range_khz`, `metrics.service.median_rate_p95_khz_s`, `metrics.service.frac_sites_rate_gt_5`
- **References:** `jardak2023`, `kozhaya2025`
- **Notes:** Geometric Doppler, not a receiver implementation. The 230 kHz and 5 kHz/s figures are consistent with the cited measurements.
- **Source:** derived

#### S08 — Laser links use three terminals per satellite at 100-200 Gbps; the mesh reportedly carries 260,000 links/day, spans 5,400 km, acquires in 12 s, and moves 42 PB/day at over 99% uptime.

- **Status:** `external_only`
- **Measured:** Not measured; public TLEs carry no laser telemetry.
- **Notes:** Company statements repeated by the explainer; not independently verified.
- **Source:** transcript


### Network operations

#### N01 — The network reconfigures on a roughly 15 s global schedule.

- **Status:** `consistent`
- **Measured:** Geometric handover p50 30.0 s (range 15-30); no scheduler telemetry.
- **Evidence:** `metrics.service.median_handover_interval_s`, `metrics.service.handover_p50_range_s`
- **References:** `casparsen2026`, `tidetcp2026`
- **Notes:** Our best-satellite simulation is consistent with 15 s slots but cannot prove the operational schedule.
- **Source:** literature

#### N02 — Satellites are bent-pipe relays to gateways, and the US has more than 100 gateway sites.

- **Status:** `partially_verified`
- **Measured:** Radio bounds are consistent with a bent-pipe path (6.19-6.27 ms); the gateway count is external.
- **Evidence:** `metrics.service.median_rtt_lower_p50_ms`, `metrics.service.median_rtt_upper_p50_ms`
- **Notes:** No gateway coordinates were used; the count is an operator claim.
- **Source:** transcript

#### N03 — Covering the globe from about 500 km requires thousands of satellites.

- **Status:** `consistent`
- **Measured:** A 9,938-satellite simulation yields 55.0 visible p50 per site; no counterfactual small-constellation run.
- **Evidence:** `metrics.service.meta.n_satellites`, `metrics.service.median_visible_p50`
- **References:** `ronchetti2026`, `ali2026`
- **Notes:** Coverage geometry, not a market or capacity argument.
- **Source:** derived


### Launch and evolution

#### E01 — About 4,400 satellites moved from roughly 550 to 480 km in 2026.

- **Status:** `partially_verified`
- **Measured:** Measured medians: 70 deg 572.0 -> 474.6 km (n=708, 98.31% lowered >10 km); 53.1 deg 475.2 -> 462.7 km (n=4,585); 43 deg stable at 483.0 km; 97.4 deg 549.4 -> 465.5 km.
- **Evidence:** `metrics.migration.by_family.apr2026_nov2026.70`, `metrics.migration.by_family.apr2026_nov2026.53p1`, `metrics.migration.by_family.apr2026_nov2026.43`, `metrics.migration.by_family.apr2026_nov2026.97p4`
- **References:** `ali2026`
- **Notes:** The exact 4,400 count is external. The public '550 to 480' summary is shell-specific: 483, 463, 475, and 465 km in our data.
- **Source:** transcript

#### E02 — SpaceX conducted 165 launches in 2025.

- **Status:** `external_only`
- **Measured:** Our SATCAT-derived count is 122 Starlink-dedicated launches carrying 3,139 still-on-orbit objects; total Falcon 9 launches cannot be separated from this table.
- **Evidence:** `metrics.launches.launches_2025`, `metrics.launches.sats_2025`
- **Notes:** Different denominators: 165 is an all-launch company figure, while 122 counts Starlink launches inferred from on-orbit object IDs.
- **Source:** transcript

#### E03 — About 1,000 Starlink satellites launched in the first 3.5 months of 2026.

- **Status:** `verified`
- **Measured:** 1,022 on-orbit objects with launch dates 2026-01-01 through 2026-04-15.
- **Evidence:** `metrics.launches.first_3p5m_2026`
- **Notes:** Counts surviving catalog objects, not all launched objects.
- **Source:** transcript

#### E04 — A Falcon 9 Starlink stack now carries 25-29 satellites.

- **Status:** `verified`
- **Measured:** 2025: median 27.0 (65.57% in 25-29, n=122); 2026: median 26.0 (70.11%, n=87).
- **Evidence:** `metrics.launches.per_launch.2025`, `metrics.launches.per_launch.2026`
- **Notes:** The historical 21-satellite first Gen2 stack is not re-tested.
- **Source:** transcript

#### E06 — Starship V3 is about 2 t with over 1 Tbit/s; 20 satellites flew at about 190 km in July 2026; 26 operational satellites followed in late September 2026; future flights may carry 60.

- **Status:** `partially_verified`
- **Measured:** November 2026 snapshot: 51 objects at 30.5 deg, median 345.2 km; 26 have a 2026-09-28 launch date at 345.2-345.6 km; 25 have a 2026-11-13 date at 272.0-342.9 km. Mass and throughput were not measured.
- **Evidence:** `metrics.v3_group`, `metrics.shells.by_key.30p5_345`
- **Notes:** The 26-satellite cohort is consistent with the first operational V3 launch; vehicle type, mass, and throughput remain external.
- **Source:** transcript

#### E07 — The 30.5 deg group is a fresh two-cohort deployment signature, not a long-lived operational shell.

- **Status:** `verified`
- **Measured:** 51 objects at 30.5 deg: 26 launched 2026-09-28 at 345.2-345.6 km; 25 launched 2026-11-13 at 272.0-342.9 km.
- **Evidence:** `metrics.v3_group.launch_days`, `metrics.v3_group.alt_range_by_day`
- **Notes:** The second cohort is visibly raising through the first cohort's altitude, which explains the spread rather than a stable 345 km shell.
- **Source:** derived

#### E08 — The catalog gained about 1,437 objects and lost 358 between April and November 2026.

- **Status:** `verified`
- **Measured:** 1,437 new, 358 missing, 9,761 matched over 7.69 months; identity check yes.
- **Evidence:** `metrics.population_flow.0.new`, `metrics.population_flow.0.missing`, `metrics.population_flow.0.matched`, `metrics.population_flow.0.check_identity`
- **Notes:** Missing means absent from the later snapshot, not confirmed decayed; SATCAT retains only on-orbit objects.
- **Source:** derived

#### E09 — Catalog attrition is about 0.46% per month, with about 187 new objects per month.

- **Status:** `verified`
- **Measured:** 0.46% missing per month; 186.8 new per month.
- **Evidence:** `metrics.population_flow.0.missing_pct_per_month`, `metrics.population_flow.0.new_per_month`
- **Notes:** Rates assume a constant process over the 7.69-month interval; they are descriptive, not a survival model.
- **Source:** derived


### Safety and environment

#### D01 — Starlink performed more than 355,000 avoidance maneuvers from June 2025 to May 2026, over 40 per satellite per year, with a threshold 10 times lower than industry.

- **Status:** `external_only`
- **Measured:** Not measured; our TLE panel detects 510 orbit-control steps in 15 satellites, which are not avoidance events.
- **Evidence:** `metrics.maneuvers.events`, `metrics.maneuvers.satellites`
- **Notes:** The TLE-step count is a different quantity (altitude changes, not conjunction-driven maneuvers).
- **Source:** transcript

#### D02 — Drag shortens failed-satellite lifetime by more than 80% during solar minimum.

- **Status:** `external_only`
- **Measured:** Not measured; no solar-cycle or drag model was run.
- **Notes:** Company/regulatory statement repeated by the explainer.
- **Source:** transcript

#### D03 — Lower satellites decay faster.

- **Status:** `consistent`
- **Measured:** Linearized lifetimes: 30.5 deg 3.23 yr; 53.1 deg 28.69 yr; 43 deg 131.41 yr; 70 deg 37.77 yr; 97.4 deg 31.35 yr.
- **Evidence:** `metrics.decay_by_family.30p5`, `metrics.decay_by_family.53p1`, `metrics.decay_by_family.43`, `metrics.decay_by_family.70`, `metrics.decay_by_family.97p4`
- **Notes:** Derived from TLE ndot and a linearized altitude model; not a propagator lifetime and not a solar-cycle prediction.
- **Source:** derived

#### D04 — Astronomy mitigation uses dark paint, mirror film, attitude changes, and published ephemerides.

- **Status:** `external_only`
- **Measured:** Not measured; no brightness or observatory data.
- **Notes:** Operational and policy claim repeated by the explainer.
- **Source:** transcript


### Direct-to-cell

#### C01 — Direct-to-cell is a distinct sub-constellation intended to serve ordinary 4G phones.

- **Status:** `partially_verified`
- **Measured:** 636 DTC-tagged objects in November 2026; median altitude 354.3 km; inclination 53.16 deg (Apr 2025) -> 43.00 deg (Apr 2026) -> 43.00 deg (Nov 2026).
- **Evidence:** `metrics.dtc.n_nov2026`, `metrics.dtc.alt_median_nov2026_km`, `metrics.dtc.inc_median_2026_deg`
- **Notes:** The DTC tag is a name suffix, not a service test; the plane change is measured, the phone compatibility is external.
- **Source:** transcript

#### C02 — Six DTC satellites launched in January 2024 and the first text messages followed days later; the phone transmits at about 0.2 W.

- **Status:** `external_only`
- **Measured:** Not measured; no launch or link-budget data.
- **Notes:** Company statement repeated by the explainer.
- **Source:** transcript

#### C03 — DTC service operates with carriers in the US, Canada, Japan, and Australia and uses laser backhaul.

- **Status:** `external_only`
- **Measured:** Not measured; no carrier or backhaul telemetry.
- **Notes:** Operator claim repeated by the explainer.
- **Source:** transcript


### Validation

#### M01 — The SGP4 implementation matches the official verification vectors.

- **Status:** `verified`
- **Measured:** 640 vectors across 31 cases; 1 declared propagation error; max position error 1.1708084947102836e-07 km.
- **Evidence:** `metrics.sgp4_validation.vectors_compared`, `metrics.sgp4_validation.cases_with_vectors`, `metrics.sgp4_validation.propagation_errors`, `metrics.sgp4_validation.max_pos_km`
- **References:** `vallado2006`
- **Notes:** Python sgp4 2.27 against SGP4-VER.TLE/tcppver.out.
- **Source:** derived

#### M02 — J2 nodal regression predicts RAAN to better than 0.1% at the median.

- **Status:** `verified`
- **Measured:** Median |relative error| 0.066%, p95 0.470%, max 0.915% over 27 satellites.
- **Evidence:** `metrics.j2.median_abs_rel_error_pct`, `metrics.j2.p95_abs_rel_error_pct`, `metrics.j2.max_abs_rel_error_pct`, `metrics.j2.n_satellites`
- **Notes:** A 27-satellite, 17-month TLE panel; residual spread is bimodal and not fully explained.
- **Source:** derived

#### M03 — TLE mean-motion altitudes agree with SATCAT to about 1 km.

- **Status:** `verified`
- **Measured:** n=11,198; median |difference| 0.15 km, p95 1.00 km, p99 3.18 km, max 38.07 km.
- **Evidence:** `metrics.satcat_altitude_check`
- **Notes:** SATCAT apogee/perigee midpoint versus TLE semi-major-axis altitude; the tail includes eccentric or maneuvering objects.
- **Source:** derived

#### M04 — Plane counts are stable at a 0.2 deg RAAN threshold.

- **Status:** `verified`
- **Measured:** 43 deg / 483 km: 92 groups; 53.1 deg / 463 km: 124; 70 deg / 475 km: 23; 97.4 deg / 465 km: 62.
- **Evidence:** `metrics.planes.by_key.43_483.planes`, `metrics.planes.by_key.53p1_463.planes`, `metrics.planes.by_key.70_475.planes`, `metrics.planes.by_key.97p4_465.planes`
- **References:** `ronchetti2026`
- **Notes:** The full threshold sensitivity table is results/tables/anatomy_stability_nov2026.csv; 0.05 deg is degenerate because group RAAN standard deviation is about 0.2 deg.
- **Source:** derived

## References

- `ali2026` — Muaz Ali, Utkarsh Upadhyay, Sean McCormick, Joseph Hill, Beichuan Zhang, *Starlink Constellation: Deployment, Configuration, and Dynamics*, arXiv:2603.25835. DOI: [10.48550/arXiv.2603.25835](https://doi.org/10.48550/arXiv.2603.25835)
- `casparsen2026` — Andreas Casparsen, Jonas Ellegaard Jakobsen, Jimmy Jessen Nielsen, Petar Popovski, Israel Leyva-Mayorga, *Statistical characterization and prediction of E2E latency over LEO satellite networks*, npj Wireless Technology. DOI: [10.1038/s44459-026-00044-z](https://doi.org/10.1038/s44459-026-00044-z)
- `jardak2023` — Nabil Jardak, Ronan Adam, *Practical Use of Starlink Downlink Tones for Positioning*, Sensors 23(6):3234. DOI: [10.3390/s23063234](https://doi.org/10.3390/s23063234)
- `kozhaya2025` — Sharbel E. Kozhaya, Joe Saroufim, Zaher M. Kassas, *Unveiling Starlink for PNT*, NAVIGATION 72(1). DOI: [10.33012/navi.685](https://doi.org/10.33012/navi.685)
- `ronchetti2026` — Pietro Ronchetti, Sushovan Das, Laurent Vanbever, Stefano Vissicchio, *All But Regular: Revisiting the Starlink Constellation*, ACM SIGCOMM 2026. DOI: [10.1145/3789240.3827597](https://doi.org/10.1145/3789240.3827597)
- `tidetcp2026` — Qingyang Li, Li Jiang, Zhang Yihang, Lijun Dong, Zongming Guo, Xinggong Zhang, *TideTCP: Preventing Performance Degradation During Periodic Handovers in Starlink*, IEEE Transactions on Mobile Computing. DOI: [10.1109/tmc.2026.3744390](https://doi.org/10.1109/tmc.2026.3744390)
- `vallado2006` — David A. Vallado, Paul Crawford, Richard Hujsak, T. S. Kelso, *Revisiting Spacetrack Report #3*, AIAA 2006-6753.
