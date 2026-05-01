import numpy as np
import pytest

from sim.farfield import accumulate_farfield
from sim.led_model import LEDSpec, emit_led_array


def test_no_optics_farfield_bins_conserve_flux_over_forward_hemisphere():
    spec = LEDSpec(
        id="test",
        name="Test LED",
        flux_typ_lm=100.0,
        current_nominal_ma=100.0,
        current_default_ma=100.0,
        vf_typ_v=3.0,
        directivity_deg=120.0,
        package_mm=(3.0, 3.0, 1.0),
        emitter_mm=(3.0, 3.0),
    )
    rays = emit_led_array(spec, led_count=1, spacing_mm=0.0, current_ma=100.0, ray_count=200_000, rng=np.random.default_rng(123))
    farfield = accumulate_farfield(rays, h_range_deg=(-90.0, 90.0), v_range_deg=(-90.0, 90.0), bin_deg=2.0)
    assert farfield.phi_in_bins_lm == pytest.approx(100.0, rel=5e-4)
    assert farfield.phi_exit_lm == pytest.approx(100.0, rel=1e-12)

