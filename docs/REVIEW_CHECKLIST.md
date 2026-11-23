# Reviewer checklist

This is the fast path for an artifact reviewer.  It assumes a checkout of the
repository and a Python 3.12 interpreter.  The study does not need network
access: all inputs are frozen in `data/raw/`.

## 1. Environment

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e .
```

The pinned dependencies are in `requirements.txt`; the package metadata is in
`pyproject.toml`.  If the environment is already present, skip this step.

## 2. Fast verification

```bash
make verify
```

Expected output:

```text
verified 10 frozen files, 45 claims, README render
51 passed
```

`make verify` does four things:

1. Recomputes the SHA256 of every file in `data/manifest.json`.
2. Rejects a `README.md` with unresolved `{{...}}` placeholders.
3. Checks that `results/claims.csv` has 45 claims and no `contradicted` or
   `not_tested` entries.
4. Runs the full pytest suite.

If the manifest check fails, do not "fix" the checksum; inspect the changed
input.  The study is pinned to the frozen snapshots.

## 3. Full reproduction

```bash
make reproduce
```

This runs, in order:

1. `00_validate_sgp4.py` - official SGP4 vectors.
2. `01_anatomy.py` - shells, planes, 30.5 deg group.
3. `02_service.py` - 10-site, 24-hour service simulation.
4. `03_dynamics.py` - migration, attrition, J2, maneuvers, decay.
5. `04_metrics.py` - assembles `results/metrics.json`.
6. `05_figures.py` - seven figures.
7. `06_claims.py` - claim ledger.
8. `atlas.paper` - renders `README.md`.

The service stage dominates the runtime (about 75 s on the reference machine);
the full run is a few minutes.  The frozen inputs are not modified.

After the run, the key artifacts are:

| Artifact | What to check |
|---|---|
| `results/metrics.json` | every headline number used by the paper |
| `results/claims.csv` | 45 claims with status and evidence |
| `results/CLAIMS.md` | human-readable ledger |
| `results/tables/` | intermediate measurements |
| `results/figures/fig1..fig7` | seven paper figures |
| `README.md` | generated paper, no placeholders |

`make reproduce` does not run `make data`.  The processed tables and manifest
are already frozen; `make data` is only for rebuilding them from the raw files
and would update the manifest timestamp.

## 4. Numerical acceptance checks

These are the checks a reviewer can run without trusting the prose:

```bash
python - <<'PY'
import json
from pathlib import Path
m = json.loads(Path("results/metrics.json").read_text())
assert m["sgp4_validation"]["max_pos_km"] < 1e-6
assert m["j2"]["median_abs_rel_error_pct"] < 1.0
assert m["satcat_altitude_check"]["median_abs_diff_km"] < 2.0
assert m["altitude"]["n_above_500"] == sum(m["altitude"]["above_500_bands"].values())
assert m["shells"]["n_assigned"] + m["shells"]["n_unassigned"] == 11198
assert m["service"]["meta"]["sgp4_error_rate"] == 0.0
assert m["service"]["frac_sites_rate_gt_5"] == 0.0
for row in m["population_flow"]:
    assert row["check_identity"] is True
    assert row["matched"] + row["missing"] == row["n_a"]
    assert row["matched"] + row["new"] == row["n_b"]
print("numeric checks passed")
PY
```

The claim counts are checked by pytest and by `make verify`:

| Status | Count |
|---|---:|
| verified | 20 |
| consistent | 7 |
| partially_verified | 5 |
| external_only | 13 |
| contradicted | 0 |
| not_tested | 0 |

## 5. Figure and link audit

```bash
ls results/figures/fig*.png
! grep -q "{{" README.md
! grep -q "}}" README.md
test -f docs/METHODS.md
test -f docs/VALIDATION.md
test -f docs/LIMITATIONS.md
test -f docs/REVIEW_CHECKLIST.md
```

There should be seven figures.  The README links the methods, validation,
limitations, and this checklist.

## 6. Data and license audit

- `data/manifest.json` contains ten files with SHA256, byte counts, and
  licenses.
- The 2026-04 Kaggle tables are CC BY-SA 4.0; the 2025-04 tables are MIT.
- CelesTrak data are public with attribution requested.
- Code is MIT; prose and original figures are CC BY 4.0.
- `LICENSE` states the data-license carve-outs; `data/MANIFEST.md` lists the
  frozen files.

No credentials, tokens, telemetry, or personal data are used.

## 7. Claim and interpretation audit

Start with `results/CLAIMS.md`.  For each `verified` or `consistent` claim,
follow the evidence path into `results/metrics.json` or `data/manifest.json`.
For each `external_only` or `partially_verified` claim, read the cited paper or
operator source; the atlas explicitly does not measure those values.

Common reviewer questions:

- **Why is there no `contradicted` claim?**  The source's "about 500 km" is a
  shorthand for a structured population, not a single testable shell.  The
  atlas qualifies it as `consistent` and reports the 230-object tail rather
  than forcing a binary contradiction.
- **Why 6.19-6.27 ms when public measurements are 20-25 ms?**  The atlas
  reports a radio-only, four-leg geometry bound.  It excludes fiber,
  processing, scheduling, weather, and load, and is not an end-to-end latency
  measurement.
- **Why do plane counts differ from published Walker numbers?**  They are
  effective RAAN clusters after J2 rectification, not design database values.
  The sensitivity table shows the threshold dependence.
- **Why 230 objects above 500 km if the 70/525 shell has only 69?**  The tail
  is a mixture: 93 at 500-515 km, 108 at 515-535 km, 19 at 535-560 km, and 10
  at or above 560 km.  The 70/525 shell is the largest coherent group; the
  highest points are individual objects, not a resolved shell.
- **Why is matching by name?**  The Kaggle snapshots do not carry NORAD IDs.
  This is a stated limitation; attrition is a catalog-matching rate, not a
  survival probability.

## 8. Artifact-evaluation mapping

| ACM criterion | Where to look |
|---|---|
| Available | public repository, frozen `data/raw/`, `data/manifest.json` |
| Functional | `make reproduce`, `make test`, `make verify` |
| Reusable | `src/atlas/` modules, `configs/study.yaml`, docs |
| Results reproduced | `results/metrics.json`, `results/claims.csv`, README |

## 9. Optional Docker check

```bash
docker compose build
docker compose run --rm atlas make test
```

The image installs the pinned requirements, copies the frozen data, and runs
the pipeline.  The compose file mounts `results/` and `README.md` so generated
artifacts are visible on the host.

## 10. Stop conditions

The review should stop and ask for clarification if:

- a manifest checksum fails and the input cannot be explained;
- `README.md` contains an unresolved placeholder;
- the claim ledger has a `contradicted` or `not_tested` entry;
- a figure is missing;
- a headline number in the README cannot be traced to `results/metrics.json`;
- a license or attribution statement is missing.
