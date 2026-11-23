# Limitations

The atlas is a measurement of public orbital catalog data.  It is not an
operator model, a service-level measurement, or a collision-risk analysis.
This file expands the limitations summarized in [`README.md`](../README.md)
and explains what each one changes about the interpretation.

## 1. Snapshots, not a census

The study uses three public snapshots:

- 2025-04-11 (Kaggle, MIT),
- 2026-04-03 (Kaggle, CC BY-SA 4.0),
- 2026-11-23 (CelesTrak GP, public).

Each snapshot contains TLE epochs spread over several days, not a simultaneous
state vector for every object.  The atlas describes those snapshots, not every
object that has ever been launched.  A satellite absent from a later snapshot
is reported as catalog attrition, not confirmed decay; the SATCAT extract
contains only on-orbit objects and cannot prove a re-entry.

Launch counts have the same boundary: the 426 launches and 11,198 objects are
the surviving catalog objects with launch dates, not a complete historical
launch list.

## 2. Name matching across sources

The Kaggle snapshots do not carry NORAD catalog numbers.  Cross-snapshot
matching therefore uses the normalized Starlink name (`STARLINK-` prefix and
` [DTC]` suffix removed).  A rename, a duplicate name, or a catalog change can
create a false missing/new pair.  The population identities still hold by
construction, but the attrition rate is a catalog-matching rate, not a
survival probability.

Within the CelesTrak snapshot and the SATCAT extract, NORAD IDs are available
and are used for cross-checks.  They are not available for the Kaggle joins.

## 3. Mean elements, not precision orbit determination

Altitudes, speeds, and periods are derived from TLE mean motion with a circular
Keplerian approximation.  TLEs carry fit and round-off error, and the circular
approximation is weakest for eccentric or maneuvering objects.  The median
difference from the SATCAT apogee/perigee midpoint is 0.15 km, but the p99 is
3.18 km and the maximum is 38.07 km.  The atlas does not estimate covariance,
probability of collision, or a precision orbit.

SGP4 is verified against the official vectors, but that verifies the
implementation, not the accuracy of any individual TLE.  The service simulation
inherits the TLE errors.

## 4. Shell detection is a resolution choice

Shells are defined by a 2 km histogram, a 25-object minimum, and a +/-8 km
assignment window.  The procedure is deterministic, but it is a resolution
choice: a different bin size or window would merge or split transition groups.
The atlas reports 11 shells and 10,325 assigned objects (92.20%); 873 objects
are unassigned.  The unassigned population is not "noise" to be discarded, but
it is not forced into a shell either.

The 30.5 deg group is a clear two-cohort deployment signature, but its
classification as a particular vehicle generation remains an external claim.
The 70 deg / 525 km group is a real coherent shell, not a separate dominant
operational layer.

## 5. Effective planes, not Walker design numbers

Plane counts are RAAN clusters after J2 rectification, not published Walker
parameters.  The 0.2 deg threshold yields 92, 124, 23, and 62 effective groups
for the four largest shells.  The threshold sensitivity table shows that these
counts are stable over 0.2-0.5 deg, but the 97.4 deg shell merges at 1.0 deg,
and the 0.05 deg threshold over-splits the main shells and falls below the
10-object floor in the 351/359 km rings.

Mean-anomaly gaps and twin-satellite counts are contaminated where a 0.2 deg
RAAN threshold merges two physical planes.  They are reported as diagnostics,
not as primary evidence for a plane design.

## 6. Migration is a matched-population statistic

Migration tables describe objects that appear in both snapshots.  The median
change can be affected by which objects survive into the later snapshot; it is
not a causal statement about a maneuver campaign.  The 43 deg shell is stable
for the matched population, the 53 deg shell lowers broadly, the 70 deg shell
shows a large matched-population drop, and the 97 deg shell continues a
multi-year descent.  These are different populations and different histories.

A single global "550 to 480 km" statement loses the shell-specific structure
and is not supported as a description of every object.

## 7. Decay indicators are linearized

Decay signatures use TLE `ndot` and a linearized altitude rate.  The implied
lifetimes (3.23 years for the 30.5 deg group, 28.7 years at 53.1 deg, 131.4
years at 43 deg, 37.8 years at 70 deg, and 31.4 years at 97.4 deg) are scales,
not propagated lifetimes.  They do not model solar-cycle variation, attitude,
drag area changes, or operational disposal.  The 30.5 deg group is short-lived
by construction because it is still being raised.

## 8. Maneuver signatures are panel-limited

The TLE panel contains 510 discrete orbit-control steps across 15 satellites
(448 raises, 62 lowers), using a threshold with a 1.5 km/step floor.  The panel
is 27 satellites with 2024-2025 histories; it cannot test an operator's annual
maneuver total, and it does not observe every small correction.  The public
maneuver-count claim is therefore marked `external_only`, not confirmed or
contradicted.

## 9. Service geometry is not an operational service model

The service simulation uses ten sites, 24 hours, 15 s steps, a 25 deg elevation
mask, and a highest-elevation serving policy.  It has no gateway coordinates,
beam model, spectrum plan, scheduler, weather, load, or terminal model.  The
visible counts and handover intervals are geometric.  Operational handovers may
be constrained by beams, capacity, policy, or scheduling.

The radio-only RTT bounds are 6.19-6.27 ms for the simulated sites.  They place
the gateway at nadir (lower bound) or at the user (upper bound), and exclude
fiber, processing, scheduling, and load.  They are not end-to-end latency and
must not be compared directly with 20-25 ms public measurements.  The ideal
550 km four-leg path is 7.34 ms; the simulation is slightly lower because the
serving population is not all at 550 km.

Doppler values are geometric line-of-sight rates at 11.325 GHz, not a receiver
implementation.  The 25 deg mask and the 400-600 km filter define the sample.

## 10. The 500 km tail is a mixture

230 objects are at or above 500 km: 93 at 500-515 km, 108 at 515-535 km, 19 at
535-560 km, and 10 at or above 560 km.  The maximum is 574.6 km.  The
70 deg / 525 km shell (69 objects) is the largest coherent group in the tail;
the highest points are individual 70 deg objects, not a resolved shell.  The
"about 500 km" shorthand is an object-weighted population summary, not a hard
ceiling.  The median altitude (465.5 km) is also object-weighted, not
coverage-weighted or capacity-weighted.

## 11. External and partially verified claims

The claim ledger marks 13 claims `external_only` and 5 `partially_verified`.
These include spacecraft mass and area, thruster performance, laser-terminal
throughput, terminal hardware, launch-vehicle type, DTC carrier countries, and
operator maneuver totals.  They are included because the source material makes
them, but they are not measurements of this study.  A reader who needs those
numbers should consult the cited source, not this atlas.

## 12. Licensing and redistribution

The code is MIT; the prose and original figures are CC BY 4.0.  Tables derived
from the April 2026 Kaggle snapshot retain CC BY-SA 4.0.  The April 2025
snapshot is MIT.  CelesTrak data are public with attribution requested.  A
downstream redistribution must preserve the share-alike terms for the 2026-04
derived tables and the attribution for CelesTrak.  See [`LICENSE`](../LICENSE)
and [`data/MANIFEST.md`](../data/MANIFEST.md).

## 13. What would strengthen the study

- A continuous TLE history for the full population, not a 27-satellite panel.
- Gateway coordinates and a beam/scheduler model for operational latency.
- A SATCAT history that includes decayed objects, for confirmed attrition.
- A second independent catalog source for name/NORAD reconciliation.
- A propagation-based lifetime model with solar and drag-area variation.
- A formal uncertainty budget for shell and plane assignments.

These are outside the public-data scope of the current artifact.  The atlas
therefore keeps the strong claims narrow and labels the rest.
