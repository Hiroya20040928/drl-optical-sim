import pytest

from sim.optimizer import optimize_cree_xhp70b
from sim.sampler import SimulationConfig, layout_positions_from_config


def test_grid_layout_positions_from_config():
    cfg = SimulationConfig(led_rows=2, led_cols=3, led_spacing_x_mm=10.0, led_spacing_y_mm=20.0)
    positions = layout_positions_from_config(cfg)
    assert positions.shape == (6, 3)
    assert positions[:, 0].min() == pytest.approx(-10.0)
    assert positions[:, 0].max() == pytest.approx(10.0)
    assert positions[:, 1].min() == pytest.approx(-10.0)
    assert positions[:, 1].max() == pytest.approx(10.0)


def test_cree_optimizer_lower_bound_best_power():
    results = optimize_cree_xhp70b(
        lens_ids=("cree_xhp70b_r148_lower_bound_60x45",),
        diffuser_ids=("none",),
        lens_positions_mm=(18.0,),
        layouts=((1, 1, 9.0, 9.0),),
        ray_count=1000,
    )
    best = results[0]
    assert best.passed
    assert best.rows == 1
    assert best.cols == 1
    assert best.total_current_ma == pytest.approx(25.66454457)
    assert best.power_w == pytest.approx(0.307974535)
