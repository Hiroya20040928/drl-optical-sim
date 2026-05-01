import json

import pytest

from sim.config_io import load_simulation_config
from sim.sampler import SimulationConfig


def test_load_saved_simulation_config_payload(tmp_path):
    path = tmp_path / "simulation_config.json"
    path.write_text(
        json.dumps(
            {
                "config": {
                    "led_id": "cree_xhp70b_00_0000_0d0bn440e",
                    "led_count": 6,
                    "led_rows": 2,
                    "led_cols": 3,
                    "current_ma": 19.866463101643998,
                    "lens_id": "ledil_c16369_hb_sq_w_xhp70p2",
                    "unknown_future_key": "ignored",
                }
            }
        ),
        encoding="utf-8",
    )

    config = load_simulation_config(path)

    assert isinstance(config, SimulationConfig)
    assert config.led_id == "cree_xhp70b_00_0000_0d0bn440e"
    assert config.led_count == 6
    assert config.led_rows == 2
    assert config.led_cols == 3
    assert config.current_ma == pytest.approx(19.866463101643998)
    assert config.lens_id == "ledil_c16369_hb_sq_w_xhp70p2"


def test_load_direct_simulation_config_object(tmp_path):
    path = tmp_path / "direct.json"
    path.write_text(json.dumps({"ray_count": 12345, "bin_deg": 0.5}), encoding="utf-8")

    config = load_simulation_config(path)

    assert config.ray_count == 12345
    assert config.bin_deg == pytest.approx(0.5)
