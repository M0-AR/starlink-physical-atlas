SHELL := /bin/bash
.DEFAULT_GOAL := help

BOOTSTRAP ?= $(shell command -v python3.12 2>/dev/null || command -v python3)
PYTHON ?= $(shell if [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)
PIP := $(PYTHON) -m pip

.PHONY: help install data validate anatomy service dynamics metrics figures claims paper site-data reproduce test verify clean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Create .venv and install pinned dependencies
	$(BOOTSTRAP) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements.txt
	.venv/bin/python -m pip install -e .

data: ## Rebuild processed tables and the manifest from frozen raw data
	$(PYTHON) -m atlas.prepare

validate: ## Check sgp4 against the official verification vectors
	$(PYTHON) experiments/00_validate_sgp4.py

anatomy: ## Resolve shells, planes, and the 30.5 degree cohort
	$(PYTHON) experiments/01_anatomy.py

service: ## Run the 10-site, 24-hour service simulation
	$(PYTHON) experiments/02_service.py

dynamics: ## Fit J2, detect maneuvers, and measure migration and decay
	$(PYTHON) experiments/03_dynamics.py

metrics: ## Assemble results/metrics.json
	$(PYTHON) experiments/04_metrics.py

figures: ## Render the seven paper figures
	$(PYTHON) experiments/05_figures.py

claims: ## Render the claim ledger from configs/claims.json
	$(PYTHON) experiments/06_claims.py

paper: ## Render README.md from paper/README.template.md
	$(PYTHON) -m atlas.paper

site-data: ## Generate the browser payloads in docs/data
	$(PYTHON) experiments/07_site_data.py

reproduce: ## Run the full pipeline from frozen inputs
	$(PYTHON) experiments/00_validate_sgp4.py
	$(PYTHON) experiments/01_anatomy.py
	$(PYTHON) experiments/02_service.py
	$(PYTHON) experiments/03_dynamics.py
	$(PYTHON) experiments/04_metrics.py
	$(PYTHON) experiments/05_figures.py
	$(PYTHON) experiments/06_claims.py
	$(PYTHON) -m atlas.paper
	$(PYTHON) experiments/07_site_data.py

test: ## Run the test suite
	$(PYTHON) -m pytest -q

verify: ## Check frozen hashes and run the test suite
	bash scripts/verify.sh

clean: ## Remove generated Python caches only
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache
