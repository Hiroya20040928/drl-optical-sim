import pytest

from sim.r148 import evaluate_r148, ideal_r148_farfield, load_r148_table_csv
from sim.sampler import DATA_DIR, SimulationConfig, run_simulation


def test_r148_table_csv_loads_expected_center_value():
    h, v, table = load_r148_table_csv(DATA_DIR / "r148_rl_table.csv")
    h0 = list(h).index(0.0)
    v0 = list(v).index(0.0)
    assert table[v0, h0] == pytest.approx(400.0)


def test_r148_ideal_minimum_distribution_passes_points_and_limits():
    farfield = ideal_r148_farfield(scale=1.0, source_flux_lm=74.0, optical_efficiency=0.8)
    result = evaluate_r148(farfield, apparent_width_mm=50.0, apparent_height_mm=50.0)
    assert farfield.center_intensity_cd == pytest.approx(400.0)
    assert farfield.imax_cd == pytest.approx(400.0)
    assert result.overall_passed


def test_nf2w_two_led_ideal_r148_mode_center_and_max():
    config = SimulationConfig(
        led_id="nichia_nf2w757h_v2h6_p12_5000k",
        led_count=2,
        current_ma=65.0,
        ray_count=10_000,
        ideal_mode=True,
        ideal_scale=1.756,
        ideal_optical_efficiency=0.8,
        apparent_width_mm=50.0,
        apparent_height_mm=50.0,
    )
    result = run_simulation(config)
    assert result.source_flux_lm == pytest.approx(74.0)
    assert result.optical_efficiency == pytest.approx(0.8)
    assert result.farfield.center_intensity_cd == pytest.approx(702.4, abs=0.2)
    assert result.farfield.imax_cd < 1200.0

