from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .apparent_surface import ApparentSurface, estimate_apparent_surface
from .farfield import FarFieldResult, accumulate_farfield
from .led_model import LEDSpec, emit_led_array, load_leds_json
from .lens_models import lens_from_spec, load_lenses_json
from .optics import OpticalSystem
from .r148 import R148Evaluation, energy_limited_r148_farfield, evaluate_r148, ideal_r148_farfield
from .ray import RayBundle


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(slots=True)
class SimulationConfig:
    led_id: str = "nichia_nf2w757h_v2h6_p12_5000k"
    led_count: int = 2
    led_spacing_mm: float = 8.0
    current_ma: float = 65.0
    flux_typ_lm: float | None = None
    vf_typ_v: float | None = None
    directivity_deg: float | None = None
    lens_id: str = "none"
    lens_position_mm: float | None = None
    diffuser_id: str = "none"
    apparent_width_mm: float = 60.0
    apparent_height_mm: float = 45.0
    ray_count: int = 50000
    bin_deg: float = 1.0
    h_range_min_deg: float = -30.0
    h_range_max_deg: float = 30.0
    v_range_min_deg: float = -20.0
    v_range_max_deg: float = 20.0
    preview_ray_count: int = 1200
    random_seed: int = 20250501
    ideal_mode: bool = False
    ideal_scale: float = 1.756
    ideal_optical_efficiency: float = 0.8

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class SimulationResult:
    config: SimulationConfig
    led_spec: LEDSpec
    source_flux_lm: float
    farfield: FarFieldResult
    r148: R148Evaluation
    optical_efficiency: float
    preview_rays: RayBundle | None
    apparent_surface: ApparentSurface


def load_default_leds() -> list[LEDSpec]:
    return load_leds_json(DATA_DIR / "leds.json")


def load_default_lenses() -> list[dict[str, Any]]:
    return load_lenses_json(DATA_DIR / "lenses.json")


def _find_led(leds: list[LEDSpec], led_id: str) -> LEDSpec:
    for led in leds:
        if led.id == led_id:
            return led
    raise KeyError(f"LED id not found: {led_id}")


def _find_lens(lenses: list[dict[str, Any]], lens_id: str) -> dict[str, Any]:
    for lens in lenses:
        if lens.get("id") == lens_id:
            return dict(lens)
    if lens_id == "none":
        return {"id": "none", "name": "Lensなし", "kind": "none", "transmission": 1.0}
    raise KeyError(f"Lens id not found: {lens_id}")


def _build_optical_system(config: SimulationConfig, lens_db: list[dict[str, Any]], led_directivity_deg: float) -> OpticalSystem:
    elements: list[object] = []
    if config.lens_id != "none":
        lens_spec = _find_lens(lens_db, config.lens_id)
        if lens_spec.get("kind") != "ideal_r148":
            if config.lens_position_mm is not None and "position_mm" in lens_spec:
                lens_spec["position_mm"] = config.lens_position_mm
            lens_spec["input_fwhm_deg"] = led_directivity_deg
            elements.append(lens_from_spec(lens_spec))
    if config.diffuser_id != "none":
        diffuser_spec = _find_lens(lens_db, config.diffuser_id)
        if config.lens_position_mm is not None and "position_mm" in diffuser_spec:
            diffuser_spec["position_mm"] = max(config.lens_position_mm + 2.0, float(diffuser_spec["position_mm"]))
        elements.append(lens_from_spec(diffuser_spec))
    return OpticalSystem(elements)


def run_simulation(
    config: SimulationConfig,
    led_db: list[LEDSpec] | None = None,
    lens_db: list[dict[str, Any]] | None = None,
) -> SimulationResult:
    led_db = load_default_leds() if led_db is None else led_db
    lens_db = load_default_lenses() if lens_db is None else lens_db
    led = _find_led(led_db, config.led_id).with_overrides(
        flux_typ_lm=config.flux_typ_lm,
        vf_typ_v=config.vf_typ_v,
        directivity_deg=config.directivity_deg,
    )
    source_flux = led.flux_at_current(config.current_ma) * int(config.led_count)

    lens_spec = _find_lens(lens_db, config.lens_id)
    diffuser_spec = _find_lens(lens_db, config.diffuser_id) if config.diffuser_id != "none" else None
    apparent_surface = estimate_apparent_surface(
        led,
        config.led_count,
        config.led_spacing_mm,
        lens_spec,
        diffuser_spec,
    )

    lens_kind = lens_spec.get("kind")
    if config.ideal_mode or lens_kind == "ideal_r148":
        farfield = ideal_r148_farfield(
            scale=config.ideal_scale,
            source_flux_lm=source_flux,
            optical_efficiency=config.ideal_optical_efficiency,
        )
        r148 = evaluate_r148(farfield, apparent_area_cm2=apparent_surface.area_cm2)
        optical_efficiency = farfield.phi_exit_lm / source_flux if source_flux > 0 else 0.0
        preview = emit_led_array(
            led,
            config.led_count,
            config.led_spacing_mm,
            config.current_ma,
            min(config.preview_ray_count, max(1, config.ray_count)),
            np.random.default_rng(config.random_seed),
        )
        return SimulationResult(config, led, source_flux, farfield, r148, optical_efficiency, preview, apparent_surface)

    if lens_kind == "r148_lower_bound":
        efficiency = float(lens_spec.get("transmission", 1.0))
        farfield = energy_limited_r148_farfield(source_flux_lm=source_flux, optical_efficiency=efficiency)
        r148 = evaluate_r148(farfield, apparent_area_cm2=apparent_surface.area_cm2)
        optical_efficiency = farfield.phi_exit_lm / source_flux if source_flux > 0 else 0.0
        preview = emit_led_array(
            led,
            config.led_count,
            config.led_spacing_mm,
            config.current_ma,
            min(config.preview_ray_count, max(1, config.ray_count)),
            np.random.default_rng(config.random_seed),
        )
        return SimulationResult(config, led, source_flux, farfield, r148, optical_efficiency, preview, apparent_surface)

    rng = np.random.default_rng(config.random_seed)
    rays = emit_led_array(
        led,
        config.led_count,
        config.led_spacing_mm,
        config.current_ma,
        int(config.ray_count),
        rng,
    )
    system = _build_optical_system(config, lens_db, led.directivity_deg)
    traced = system.trace(rays, rng)
    farfield = accumulate_farfield(
        traced,
        h_range_deg=(config.h_range_min_deg, config.h_range_max_deg),
        v_range_deg=(config.v_range_min_deg, config.v_range_max_deg),
        bin_deg=config.bin_deg,
    )
    r148 = evaluate_r148(farfield, apparent_area_cm2=apparent_surface.area_cm2)
    optical_efficiency = farfield.phi_exit_lm / source_flux if source_flux > 0 else 0.0
    return SimulationResult(config, led, source_flux, farfield, r148, optical_efficiency, traced.preview(config.preview_ray_count), apparent_surface)


def default_config_for_led(led: LEDSpec) -> SimulationConfig:
    return SimulationConfig(
        led_id=led.id,
        led_count=led.default_leds_per_lamp,
        current_ma=led.current_default_ma,
        flux_typ_lm=led.flux_typ_lm,
        vf_typ_v=led.vf_typ_v,
        directivity_deg=led.directivity_deg,
    )
