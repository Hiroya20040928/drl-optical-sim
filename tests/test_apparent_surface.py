import pytest

from sim.sampler import SimulationConfig, run_simulation


def test_apparent_surface_is_from_lens_not_manual_config():
    config = SimulationConfig(
        led_id="cree_xhp70b_00_0000_0d0bn440e",
        led_count=1,
        current_ma=25.665,
        lens_id="carclo_10756_xhp70p2",
        apparent_width_mm=60.0,
        apparent_height_mm=45.0,
        ray_count=1000,
    )
    result = run_simulation(config)
    assert result.apparent_surface.shape == "circle"
    assert result.apparent_surface.diameter_mm == pytest.approx(30.0)
    assert result.r148.apparent_area_cm2 == pytest.approx(7.06858, rel=1e-5)
    assert not result.r148.area_passed


def test_optimized_cree_lower_bound_uses_front_aperture_area():
    config = SimulationConfig(
        led_id="cree_xhp70b_00_0000_0d0bn440e",
        led_count=1,
        current_ma=25.665,
        lens_id="cree_xhp70b_r148_lower_bound_60x45",
        ray_count=1000,
    )
    result = run_simulation(config)
    assert result.apparent_surface.area_cm2 == pytest.approx(27.0)
    assert result.r148.area_passed
    assert result.farfield.center_intensity_cd >= 400.0
    assert result.r148.overall_passed

