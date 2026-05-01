from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .led_model import LEDSpec


@dataclass(frozen=True, slots=True)
class ApparentSurface:
    shape: str
    area_cm2: float
    source: str
    width_mm: float | None = None
    height_mm: float | None = None
    diameter_mm: float | None = None

    @property
    def label(self) -> str:
        if self.shape == "circle" and self.diameter_mm is not None:
            return f"circle dia {self.diameter_mm:.2f} mm"
        if self.width_mm is not None and self.height_mm is not None:
            return f"{self.width_mm:.2f} x {self.height_mm:.2f} mm"
        return f"{self.area_cm2:.2f} cm2"


def _surface_from_spec(spec: dict[str, Any], source: str) -> ApparentSurface | None:
    shape = spec.get("apparent_shape")
    if shape == "rectangle":
        width = float(spec["apparent_width_mm"])
        height = float(spec["apparent_height_mm"])
        return ApparentSurface("rectangle", width * height / 100.0, source, width_mm=width, height_mm=height)
    if shape == "circle":
        diameter = float(spec["apparent_diameter_mm"])
        return ApparentSurface("circle", math.pi * (diameter / 20.0) ** 2, source, diameter_mm=diameter)
    if "diameter_mm" in spec:
        diameter = float(spec["diameter_mm"])
        return ApparentSurface("circle", math.pi * (diameter / 20.0) ** 2, source, diameter_mm=diameter)
    if "radius_mm" in spec:
        diameter = float(spec["radius_mm"]) * 2.0
        return ApparentSurface("circle", math.pi * (diameter / 20.0) ** 2, source, diameter_mm=diameter)
    if "width_mm" in spec and "height_mm" in spec:
        width = float(spec["width_mm"])
        height = float(spec["height_mm"])
        return ApparentSurface("rectangle", width * height / 100.0, source, width_mm=width, height_mm=height)
    return None


def estimate_apparent_surface(
    led: LEDSpec,
    led_count: int,
    led_spacing_mm: float,
    lens_spec: dict[str, Any],
    diffuser_spec: dict[str, Any] | None = None,
    led_rows: int = 1,
    led_cols: int | None = None,
    led_spacing_y_mm: float | None = None,
) -> ApparentSurface:
    """Estimate apparent luminous surface from the actual optical front element.

    Priority is diffuser/front cover, then lens aperture, then bare LED package
    bounding box. This removes the previous R148 area pass/fail dependency on
    arbitrary GUI-entered dimensions.
    """
    if diffuser_spec is not None and diffuser_spec.get("id") != "none":
        surface = _surface_from_spec(diffuser_spec, f"diffuser/front cover: {diffuser_spec.get('name', diffuser_spec.get('id'))}")
        if surface is not None:
            return surface

    if lens_spec.get("id") != "none":
        surface = _surface_from_spec(lens_spec, f"lens/front aperture: {lens_spec.get('name', lens_spec.get('id'))}")
        if surface is not None:
            return surface

    cols = int(led_cols or led_count)
    rows = int(led_rows)
    spacing_y = float(led_spacing_mm if led_spacing_y_mm is None else led_spacing_y_mm)
    width = led.package_mm[0] + max(0, cols - 1) * float(led_spacing_mm)
    height = led.package_mm[1] + max(0, rows - 1) * spacing_y
    return ApparentSurface("rectangle", width * height / 100.0, "bare LED package bounding box", width_mm=width, height_mm=height)
