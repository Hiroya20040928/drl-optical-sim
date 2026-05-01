from __future__ import annotations

from dataclasses import dataclass, field, replace
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .ray import RayBundle


def cosine_power_exponent(directivity_deg: float) -> float:
    """Convert full-width half-maximum directivity to I(theta)=I0*cos(theta)^n."""
    if directivity_deg <= 0:
        raise ValueError("directivity_deg must be positive")
    theta_half = math.radians(directivity_deg / 2.0)
    cos_half = math.cos(theta_half)
    if cos_half <= 0.0:
        return 0.0
    return math.log(0.5) / math.log(cos_half)


def full_width_half_max_from_exponent(exponent_n: float) -> float:
    if exponent_n <= 0:
        return 180.0
    theta_half = math.acos(0.5 ** (1.0 / exponent_n))
    return math.degrees(theta_half) * 2.0


def axial_intensity_cd(flux_lm: float, exponent_n: float) -> float:
    """Central luminous intensity for a cosine-power emitter over a hemisphere."""
    return flux_lm * (exponent_n + 1.0) / (2.0 * math.pi)


@dataclass(slots=True)
class LEDSpec:
    id: str
    name: str
    flux_typ_lm: float
    current_nominal_ma: float
    current_default_ma: float
    vf_typ_v: float
    directivity_deg: float
    package_mm: tuple[float, float, float]
    emitter_mm: tuple[float, float]
    manufacturer: str = ""
    cct_k: int | None = None
    flux_min_lm: float | None = None
    flux_max_lm: float | None = None
    vf_min_v: float | None = None
    vf_max_v: float | None = None
    current_max_ma: float | None = None
    board_mm: tuple[float, float] | None = None
    cri_ra_min: float | None = None
    r9_min: float | None = None
    default_leds_per_lamp: int = 1
    default_lamps: int = 1
    current_flux_curve: list[tuple[float, float]] = field(default_factory=list)
    notes: str = ""

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> "LEDSpec":
        def tuple_or_none(key: str, length: int) -> tuple[float, ...] | None:
            value = data.get(key)
            if value is None:
                return None
            if len(value) != length:
                raise ValueError(f"{key} must have {length} values")
            return tuple(float(v) for v in value)

        curve = data.get("current_flux_curve") or []
        return cls(
            id=str(data["id"]),
            name=str(data["name"]),
            manufacturer=str(data.get("manufacturer", "")),
            cct_k=data.get("cct_k"),
            flux_typ_lm=float(data["flux_typ_lm"]),
            flux_min_lm=None if data.get("flux_min_lm") is None else float(data["flux_min_lm"]),
            flux_max_lm=None if data.get("flux_max_lm") is None else float(data["flux_max_lm"]),
            current_nominal_ma=float(data["current_nominal_ma"]),
            current_default_ma=float(data.get("current_default_ma", data["current_nominal_ma"])),
            current_max_ma=None if data.get("current_max_ma") is None else float(data["current_max_ma"]),
            vf_typ_v=float(data["vf_typ_v"]),
            vf_min_v=None if data.get("vf_min_v") is None else float(data["vf_min_v"]),
            vf_max_v=None if data.get("vf_max_v") is None else float(data["vf_max_v"]),
            directivity_deg=float(data["directivity_deg"]),
            package_mm=tuple_or_none("package_mm", 3),  # type: ignore[arg-type]
            emitter_mm=tuple_or_none("emitter_mm", 2),  # type: ignore[arg-type]
            board_mm=tuple_or_none("board_mm", 2),  # type: ignore[arg-type]
            cri_ra_min=None if data.get("cri_ra_min") is None else float(data["cri_ra_min"]),
            r9_min=None if data.get("r9_min") is None else float(data["r9_min"]),
            default_leds_per_lamp=int(data.get("default_leds_per_lamp", 1)),
            default_lamps=int(data.get("default_lamps", 1)),
            current_flux_curve=[(float(p[0]), float(p[1])) for p in curve],
            notes=str(data.get("notes", "")),
        )

    @property
    def exponent_n(self) -> float:
        return cosine_power_exponent(self.directivity_deg)

    def with_overrides(
        self,
        *,
        flux_typ_lm: float | None = None,
        vf_typ_v: float | None = None,
        directivity_deg: float | None = None,
    ) -> "LEDSpec":
        return replace(
            self,
            flux_typ_lm=self.flux_typ_lm if flux_typ_lm is None else float(flux_typ_lm),
            vf_typ_v=self.vf_typ_v if vf_typ_v is None else float(vf_typ_v),
            directivity_deg=self.directivity_deg if directivity_deg is None else float(directivity_deg),
        )

    def flux_at_current(self, current_ma: float) -> float:
        """Return luminous flux for one LED at the requested current.

        If a JSON current/flux curve is present, linear interpolation is used.
        Otherwise the initial implementation uses a linear current scaling.
        """
        current_ma = float(current_ma)
        if self.current_flux_curve:
            curve = np.asarray(sorted(self.current_flux_curve), dtype=float)
            return float(np.interp(current_ma, curve[:, 0], curve[:, 1]))
        return self.flux_typ_lm * current_ma / self.current_nominal_ma


def load_leds_json(path: str | Path) -> list[LEDSpec]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [LEDSpec.from_mapping(item) for item in data["leds"]]


def led_array_positions_mm(led_count: int, spacing_mm: float) -> np.ndarray:
    if led_count <= 0:
        raise ValueError("led_count must be positive")
    x = (np.arange(led_count, dtype=float) - (led_count - 1) / 2.0) * float(spacing_mm)
    return np.column_stack([x, np.zeros(led_count), np.zeros(led_count)])


def _sample_cosine_power_directions(ray_count: int, exponent_n: float, rng: np.random.Generator) -> np.ndarray:
    u = rng.random(ray_count)
    phi = 2.0 * np.pi * rng.random(ray_count)
    if exponent_n <= 0.0:
        cos_theta = u
    else:
        cos_theta = u ** (1.0 / (exponent_n + 1.0))
    sin_theta = np.sqrt(np.maximum(0.0, 1.0 - cos_theta * cos_theta))
    return np.column_stack([sin_theta * np.cos(phi), sin_theta * np.sin(phi), cos_theta])


def emit_led_array(
    spec: LEDSpec,
    led_count: int,
    spacing_mm: float,
    current_ma: float,
    ray_count: int,
    rng: np.random.Generator | None = None,
) -> RayBundle:
    """Sample rays from rectangular LED emitting surfaces."""
    if ray_count <= 0:
        raise ValueError("ray_count must be positive")
    rng = np.random.default_rng() if rng is None else rng
    centers = led_array_positions_mm(led_count, spacing_mm)
    counts = np.full(led_count, ray_count // led_count, dtype=int)
    counts[: ray_count % led_count] += 1

    origins: list[np.ndarray] = []
    directions: list[np.ndarray] = []
    fluxes: list[np.ndarray] = []
    emitter_w, emitter_h = spec.emitter_mm
    flux_per_led = spec.flux_at_current(current_ma)
    exponent = spec.exponent_n

    for center, count in zip(centers, counts):
        xy = rng.random((count, 2)) - 0.5
        local = np.column_stack([xy[:, 0] * emitter_w, xy[:, 1] * emitter_h, np.zeros(count)])
        origins.append(local + center)
        directions.append(_sample_cosine_power_directions(count, exponent, rng))
        fluxes.append(np.full(count, flux_per_led / count, dtype=float))

    return RayBundle(np.vstack(origins), np.vstack(directions), np.concatenate(fluxes))

