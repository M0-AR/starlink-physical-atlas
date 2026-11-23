# Methods

This document describes the measurement pipeline behind
[`README.md`](../README.md).  The implementation is in `src/atlas/`, the
experiment entry points are in `experiments/`, and every headline number is
assembled in `results/metrics.json`.

## 1. Inputs and provenance

The study uses three public snapshots and one catalog extract:

| Input | Role | Source | License |
|---|---|---|---|
| 2026-11-23 Starlink GP | Primary snapshot | CelesTrak | Public, attribution |
| 2026-04-03 Starlink snapshot | Migration midpoint | Kaggle | CC BY-SA 4.0 |
| 2025-04-11 Starlink snapshot | Historical baseline | Kaggle | MIT |
| 2026-11-23 SATCAT | Cross-check and metadata | CelesTrak | Public, attribution |
| 2026-11-23 active catalog | Denominator for share | CelesTrak | Public, attribution |
| 27-satellite TLE series | J2 and maneuver panel | CelesTrak | Public, attribution |

Raw files are frozen in `data/raw/`.  `data/manifest.json` records SHA256,
byte counts, row counts, epochs, and licenses.  `scripts/fetch_data.sh`
fetches a fresh live snapshot into `data/raw/live/` for inspection but never
overwrites the frozen study inputs.

Satellites are matched across snapshots by normalized Starlink name.  The
Kaggle snapshots do not carry NORAD catalog numbers, so the name is the only
cross-source key; the CelesTrak snapshots do carry NORAD IDs, which are used
for within-source joins and SATCAT cross-checks.  Names are normalized by
removing the `STARLINK-` prefix and the ` [DTC]` suffix for matching and
display.  A rename or a catalog duplicate can therefore create a false
missing/new pair; this is a stated limitation, not a measured decay.

## 2. Altitude, speed, and period

TLE mean motion `n` (rad/s) gives a circular Keplerian radius

```
a = (mu / n^2)^(1/3)
h = a - R_E
```

with `mu = 398600.4418 km^3/s^2` and `R_E = 6378.137 km`.  Circular speed and
period follow from the same radius:

```
v = sqrt(mu / a)
T = 2*pi*sqrt(a^3 / mu)
```

This is a mean-element approximation.  It is accurate enough to resolve
2 km-scale shells and agrees with SATCAT `(APOGEE + PERIGEE)/2` to a median
absolute difference of well under 1 km (see [`VALIDATION.md`](VALIDATION.md)).

## 3. Shell resolution

For each inclination family (30.5°, 43.0°, 53.1°, 70.0°, 97.4°), a 2 km
altitude histogram is built.  Peaks with at least 25 objects are retained;
objects within ±8 km of a peak are assigned to that shell.  The procedure is
deterministic and is implemented in `src/atlas/anatomy.py`.  Shells are
reported as effective populations, not as design database entries.  Objects
outside every window are counted as unassigned.

## 4. Plane structure

RAAN is corrected for J2 nodal regression to a common reference epoch:

```
dOmega/dt = -1.5 * J2 * (R_E / p)^2 * n * cos(i)
```

The corrected RAAN values are sorted and adjacent gaps are computed.  A small
gap threshold merges satellites that belong to the same effective plane; the
near-zero-gap fraction measures how often this happens.  Plane counts are read
from stable plateaus in the near-zero-gap fraction, not from a published
Walker design.  Spacing CV and occupancy describe the resulting lattice.

The mean-anomaly gap and "twin" diagnostics are reported with a caveat: a
0.2° RAAN threshold can merge two physical planes, so these statistics are
contaminated by group merging and are not used as primary evidence.

## 5. J2 validation

A 27-satellite panel with long TLE histories is propagated through time.
RAAN is unwrapped and fitted against time.  The observed slope is compared
with the standard J2 nodal-regression prediction at the satellite's mean
inclination and altitude.  The fit uses public mean elements only; it does not
estimate unmodeled forces or covariance.  The panel spans 2024–2025 and is
used to test the geometry model, not to predict future orbits.

## 6. Migration, population flow, and decay

Snapshots are joined by normalized Starlink name.  For each pair, a satellite
is classified as lowered (altitude change below −10 km), stable (within
±10 km), or raised (above +10 km).  The identities

```
matched + missing = earlier population
matched + new     = later population
```

are checked for every period.  Missing objects are reported as catalog
disappearance/attrition; SATCAT does not contain decayed objects, so the study
does not claim that every missing object re-entered.

Decay signatures use the TLE `ndot` term and a linearized altitude rate.  The
implied lifetime is a scale, not an operational prediction.

## 7. Service geometry and latency

Ten sites are propagated for 24 hours at 15 s steps against the 2026-11-23
constellation, restricted to 400–600 km.  A satellite is visible above a 25°
elevation mask.  The serving satellite is the one with the highest elevation;
a handover is a change in that satellite.

The radio path is a four-leg bent-pipe:

```
user -> satellite -> gateway -> satellite -> user
```

Two bounds are computed:

- **Lower:** gateway at the sub-satellite point.  RTT = `2*(slant + h)/c`.
- **Upper:** gateway co-located with the user.  RTT = `4*slant/c`.

The model excludes fiber, processing, scheduling, weather, and load.  It is a
geometry bound, not an end-to-end latency measurement.  Doppler is computed
from the line-of-sight range rate at 11.325 GHz; the 12 GHz reference is used
for the light-time scale.

## 8. Claim ledger and paper rendering

`configs/claims.json` stores each claim, its status, its measured template,
its evidence pointers, and its reference keys.  `experiments/06_claims.py`
renders the templates against `results/metrics.json` and writes
`results/CLAIMS.md` and `results/claims.csv`.  An unknown template path is a
hard error.

`paper/README.template.md` is rendered by `src/atlas/paper.py`.  Every
measured sentence is a `{{metrics.*}}` placeholder; unknown paths and
unresolved braces abort the build.  `README.md` is therefore generated, not
hand-edited.

## 9. Pipeline

```bash
make reproduce   # 00 -> 06, figures, README
make test        # 51 tests
make verify      # manifest checks + tests
```

The individual stages are `make validate`, `make anatomy`, `make service`,
`make dynamics`, `make metrics`, `make figures`, `make claims`, and
`make paper`.  `make data` rebuilds processed tables from the frozen raw files
and is intentionally not part of `make reproduce`.
