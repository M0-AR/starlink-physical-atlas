import math

from atlas import constants as k


def test_light_time_per_12ghz_cycle():
    assert abs(1.0 / k.F_KU_12 * 1e12 - 83.3333) < 0.01


def test_leo_round_trip_bounds():
    one_way = 550.0 / k.C
    assert abs(one_way * 1e3 - 1.8346) < 0.01
    assert abs(2 * one_way * 1e3 - 3.6692) < 0.01
    assert abs(4 * one_way * 1e3 - 7.3384) < 0.01


def test_geo_round_trip():
    one_way = k.H_GEO / k.C
    assert abs(one_way * 1e3 - 119.37) < 0.1
    assert abs(2 * one_way * 1e3 - 238.74) < 0.1
    assert abs(4 * one_way * 1e3 - 477.5) < 0.2


def test_circular_speed_and_period():
    r = k.RE + 550.0
    v = math.sqrt(k.MU / r)
    period = 2 * math.pi * math.sqrt(r**3 / k.MU)
    assert abs(v * 3600 - 27306) < 60
    assert abs(period / 60 - 95.65) < 0.1


def test_handover_slot_is_fifteen_seconds():
    assert k.HANDOVER_SLOT_S == 15.0
