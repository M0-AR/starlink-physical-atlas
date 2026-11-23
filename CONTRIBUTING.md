# Contributing

Thank you for helping improve the Starlink Physical Atlas. The project values reproducible measurements, plain-language explanations, and honest uncertainty over impressive-sounding numbers.

## Before you start

- Open an issue for a large change, a new claim, a data update, or a site redesign.
- Do not include private, operational, export-controlled, or credential data.
- Do not add operational interference, tracking, or unverified headline numbers.
- For a security issue, follow [SECURITY.md](SECURITY.md) instead of opening a public issue.

## Local setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
make verify
```

To run the site:

```bash
make site-data
python3 -m http.server 8765 --directory docs
```

Open <http://127.0.0.1:8765/>. The pages fetch JSON and use ES modules, so they need an HTTP server rather than a `file://` URL.

## Required checks

Run these before opening a pull request:

```bash
make verify
make site-data
python -m build
```

`make verify` checks the frozen-input manifest, the claim ledger, the rendered README, and the test suite. If you change `paper/README.template.md` or any metric that the template uses, run `make paper` and commit the regenerated `README.md`. Never hand-edit only the README.

## Claim changes

A claim is a contract. To add, remove, or change one:

1. Update `configs/claims.json` with the status, measured template, evidence pointers, and references.
2. Regenerate the ledger with `make claims`.
3. Regenerate the README with `make paper` if the wording or counts change.
4. Add or update a test when the claim introduces a new invariant.
5. Keep `contradicted` and `not_tested` claims out of a release unless the release notes explicitly explain why.

Use these statuses consistently:

- `verified`: measured here with a reproducible check.
- `consistent`: supported by the measurement and at least one independent source.
- `partially_verified`: one part is measured here; another part remains external.
- `external_only`: not recoverable from the public snapshot; cited but not measured here.
- `contradicted`: the evidence disagrees with the claim.
- `not_tested`: no adequate evidence either way.

## Site changes

- Keep the landing-page previews real: every tab must load the actual product page.
- Preserve keyboard access, visible focus, reduced-motion behavior, and the no-WebGL fallback.
- Keep the 3D views honest: label mean-element visualisation separately from the SGP4 metrics.
- Do not hand-edit `docs/data/*.json`; regenerate with `make site-data`.
- Regenerate posters, screenshots, and the animated tour when a visible page changes. Keep the social card at 1200×630.

## Data and metric changes

- Frozen inputs live in `data/raw/` and are protected by `data/manifest.json`.
- Do not replace a frozen file silently. A data update needs a new manifest entry, a migration note, and a review of every affected claim.
- Prefer a deterministic computation over a notebook-only result. Add the step to `experiments/` and the `Makefile` when it becomes part of the release pipeline.
- State units, epochs, filters, and matching rules in the method or limitation section.

## Style

- Python: standard library typing, `pathlib`, explicit column names, and tests for invariants.
- Prose: direct, specific, and free of hype. Explain acronyms on first use.
- Charts: label units, state the sample, and do not truncate axes without saying so.
- Commits: one logical change per commit; use the imperative mood.

## Pull requests

Use the pull request template. Include the verification commands you ran, the user-visible effect, and screenshots for site or game changes. A maintainer may ask for a smaller diff or a claim-status change before merging.

## License

By contributing, you agree that code contributions are licensed under the MIT License and prose contributions under CC BY 4.0, consistent with the repository. Do not contribute material you cannot license on those terms.
