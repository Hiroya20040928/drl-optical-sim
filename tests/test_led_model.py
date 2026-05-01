import math

import pytest

from sim.led_model import cosine_power_exponent, full_width_half_max_from_exponent, load_leds_json
from sim.sampler import DATA_DIR


def test_cosine_power_half_angle_matches_directivity():
    directivity = 120.0
    exponent = cosine_power_exponent(directivity)
    theta_half = math.radians(directivity / 2.0)
    assert math.cos(theta_half) ** exponent == pytest.approx(0.5, rel=1e-12)
    assert full_width_half_max_from_exponent(exponent) == pytest.approx(directivity)


def test_cree_xhp70b_operating_default_is_loaded():
    leds = load_leds_json(DATA_DIR / "leds.json")
    cree = next(led for led in leds if led.id == "cree_xhp70b_00_0000_0d0bn440e")
    assert cree.current_nominal_ma == pytest.approx(1050.0)
    assert cree.current_default_ma == pytest.approx(25.665)
    assert cree.vf_typ_v == pytest.approx(12.0)
    assert cree.directivity_deg == pytest.approx(125.0)
    assert cree.flux_at_current(20.3) == pytest.approx(1710.0 * 20.3 / 1050.0)
    assert cree.flux_at_current(cree.current_default_ma) == pytest.approx(1710.0 * 25.665 / 1050.0)
