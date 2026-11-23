#!/usr/bin/env bash
# Fetch a fresh live snapshot for inspection.  The study itself is pinned to
# the frozen files and checksums in data/manifest.json, so this script writes
# to data/raw/live/ and never overwrites the frozen inputs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIVE="${1:-$ROOT/data/raw/live}"
mkdir -p "$LIVE"

fetch() {
    local url="$1"
    local out="$2"
    echo "fetching $url"
    curl --fail --silent --show-error --location \
        --retry 3 --retry-delay 2 --retry-connrefused \
        "$url" --output "$out"
}

fetch "https://celestrak.org/NORAD/elements/gp.php?GROUP=starlink&FORMAT=csv" \
    "$LIVE/gp_starlink_live.csv"
fetch "https://celestrak.org/satcat/records.php?GROUP=starlink&FORMAT=csv" \
    "$LIVE/satcat_starlink_live.csv"
fetch "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=csv" \
    "$LIVE/active_catalog_live.csv"

cat <<'EOF'

Kaggle snapshots
----------------
The April 2026 and April 2025 snapshots are frozen in data/raw/.  To refresh
them, set the dataset slugs and run:

  export KAGGLE_DATASET_2026="owner/dataset-slug"
  export KAGGLE_DATASET_2025="owner/dataset-slug"
  kaggle datasets download -d "$KAGGLE_DATASET_2026" -p data/raw/live --unzip
  kaggle datasets download -d "$KAGGLE_DATASET_2025" -p data/raw/live --unzip

The 2026-04 table is derived from Starlink data and is distributed under
CC BY-SA 4.0; the 2025-04 table is MIT.  See data/MANIFEST.md and LICENSE.
EOF
