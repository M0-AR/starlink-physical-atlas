import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
METRICS = json.loads((ROOT / "results" / "metrics.json").read_text())


def test_population_and_active_share():
    assert METRICS["snapshots"]["nov2026"]["n"] == 11198
    assert METRICS["satcat"]["total"] == 11198
    assert METRICS["active_catalog"]["total"] == 16904
    assert METRICS["active_catalog"]["starlink"] == 11199
    assert METRICS["active_catalog"]["share_pct"] == pytest.approx(66.25, abs=0.01)


def test_altitude_summary_is_a_distribution_not_a_shell():
    alt = METRICS["altitude"]
    assert 400 < alt["median_km"] < 500
    assert 90 < alt["pct_below_500"] < 100
    assert alt["n_above_500"] == sum(alt["above_500_bands"].values())
    assert alt["n_above_500"] > 0
    assert alt["geo_to_median_ratio"] > 70


def test_shells_cover_most_of_the_catalog():
    shells = METRICS["shells"]
    assert shells["n"] == len(shells["by_key"])
    assert shells["n"] == 11
    assert shells["n_families"] == 5
    assert shells["n_assigned"] + shells["n_unassigned"] == 11198
    assert shells["coverage_pct"] == pytest.approx(100 * shells["n_assigned"] / 11198, abs=0.01)
    for key in ("43_483", "53p1_463", "70_475", "97p4_465"):
        assert shells["by_key"][key]["n"] > 500


def test_migration_rows_reconcile():
    for period in ("apr2025_apr2026", "apr2026_nov2026"):
        for row in METRICS["migration"][period]:
            assert row["matched"] >= 0
            assert row["frac_lowered_gt10km"] + row["frac_stable_10km"] + row["frac_raised_gt10km"] == pytest.approx(1.0, abs=2e-3)


def test_plane_counts_are_effective_and_stable():
    planes = METRICS["planes"]["by_key"]
    assert planes["43_483"]["planes"] == 92
    assert planes["53p1_463"]["planes"] == 124
    assert planes["70_475"]["planes"] == 23
    assert planes["97p4_465"]["planes"] == 62
    for row in planes.values():
        if row["occupancy_median"] is not None:
            assert row["occupancy_median"] <= row["occupancy_max"]


def test_validation_thresholds():
    sgp4 = METRICS["sgp4_validation"]
    assert sgp4["vectors_compared"] >= 500
    assert sgp4["max_pos_km"] < 1e-6
    assert sgp4["max_vel_km_s"] < 1e-8
    assert METRICS["j2"]["median_abs_rel_error_pct"] < 1.0
    assert METRICS["j2"]["max_abs_rel_error_pct"] < 5.0
    assert METRICS["satcat_altitude_check"]["median_abs_diff_km"] < 2.0


def test_service_geometry_is_physical():
    service = METRICS["service"]
    assert service["median_visible_p50"] > 1
    assert service["visible_p50_range"][0] <= service["median_visible_p50"] <= service["visible_p50_range"][1]
    assert service["median_rtt_lower_p50_ms"] < service["median_rtt_upper_p50_ms"]
    assert service["median_rtt_upper_p50_ms"] < 10.0
    assert service["meta"]["sgp4_error_rate"] == 0.0
    assert service["frac_sites_rate_gt_5"] == 0.0


def test_launch_and_catalog_flow_are_internally_consistent():
    launches = METRICS["launches"]
    assert launches["n_launches"] == 426
    assert launches["sats_2025"] + launches["sats_2026"] <= launches["n_satellites"]
    assert 20 <= launches["per_launch"]["2025"]["median"] <= 30
    assert 20 <= launches["per_launch"]["2026"]["median"] <= 30
    for row in METRICS["population_flow"]:
        assert row["check_identity"] is True
        assert row["matched"] + row["missing"] == row["n_a"]
        assert row["matched"] + row["new"] == row["n_b"]
