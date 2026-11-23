import numpy as np

from atlas import sgp4ver


def test_reference_files_exist():
    assert (sgp4ver.PKG / "SGP4-VER.TLE").exists()
    assert (sgp4ver.PKG / "tcppver.out").exists()


def test_cases_and_reference_align():
    cases = sgp4ver.load_cases()
    ref = sgp4ver.load_reference()
    assert len(cases) >= 30
    assert len(ref) >= 30
    assert set(ref).issubset(set(cases))


def test_vanguard_1_matches_reference():
    cases = sgp4ver.load_cases()
    ref = sgp4ver.load_reference()
    l1, l2, *_ = cases[5]
    from sgp4.api import Satrec
    sat = Satrec.twoline2rv(l1, l2[:69])
    vals = ref[5][0]
    e, r, v = sat.sgp4_tsince(vals[0])
    assert e == 0
    assert np.linalg.norm(np.asarray(r) - vals[1:4]) < 1e-3


def test_full_suite_is_sub_metre():
    df = sgp4ver.evaluate()
    s = sgp4ver.summary(df)
    assert s["vectors_compared"] > 500
    assert s["max_pos_km"] < 1e-3
