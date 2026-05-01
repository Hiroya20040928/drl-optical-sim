from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path

import numpy as np

from .farfield import FarFieldResult, result_from_intensity_grid


R148_H_DEG = np.array([-20.0, -10.0, -5.0, 0.0, 5.0, 10.0, 20.0])
R148_V_DEG = np.array([-10.0, -5.0, 0.0, 5.0, 10.0])
R148_MIN_CD = np.array(
    [
        [0.0, 0.0, 80.0, 80.0, 80.0, 0.0, 0.0],
        [40.0, 80.0, 180.0, 280.0, 180.0, 80.0, 40.0],
        [100.0, 280.0, 360.0, 400.0, 360.0, 280.0, 100.0],
        [40.0, 80.0, 180.0, 280.0, 180.0, 80.0, 40.0],
        [0.0, 0.0, 80.0, 80.0, 80.0, 0.0, 0.0],
    ],
    dtype=float,
)

DISCLAIMER = "設計検討用であり，最終的には実測フォトメトリが必要です。"


@dataclass(slots=True)
class R148PointResult:
    h_deg: float
    v_deg: float
    min_cd: float
    measured_cd: float
    passed: bool


@dataclass(slots=True)
class R148Evaluation:
    points: list[R148PointResult]
    max_cd: float
    max_cd_limit: float
    max_cd_passed: bool
    apparent_area_cm2: float
    area_passed: bool
    overall_passed: bool
    disclaimer: str = DISCLAIMER

    def rows(self) -> list[dict[str, object]]:
        return [
            {
                "h_deg": p.h_deg,
                "v_deg": p.v_deg,
                "min_cd": p.min_cd,
                "measured_cd": p.measured_cd,
                "passed": p.passed,
            }
            for p in self.points
        ]


def load_r148_table_csv(path: str | Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    with Path(path).open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        h_values = [float(name.replace("h_", "")) for name in reader.fieldnames[1:]]  # type: ignore[index]
        v_values: list[float] = []
        rows: list[list[float]] = []
        for row in reader:
            v_values.append(float(row["v_deg"]))
            rows.append([float(row[f"h_{int(h) if h.is_integer() else h:g}"]) for h in h_values])

    h = np.asarray(h_values, dtype=float)
    v = np.asarray(v_values, dtype=float)
    values = np.asarray(rows, dtype=float)
    order = np.argsort(v)
    return h, v[order], values[order]


def evaluate_r148(
    farfield: FarFieldResult,
    apparent_width_mm: float | None = None,
    apparent_height_mm: float | None = None,
    max_cd_limit: float = 1200.0,
    apparent_area_cm2: float | None = None,
) -> R148Evaluation:
    points: list[R148PointResult] = []
    for vi, v in enumerate(R148_V_DEG):
        for hi, h in enumerate(R148_H_DEG):
            minimum = float(R148_MIN_CD[vi, hi])
            measured = farfield.sample_intensity(float(h), float(v))
            points.append(R148PointResult(float(h), float(v), minimum, measured, measured + 1e-9 >= minimum))

    max_cd = farfield.imax_cd
    max_cd_passed = max_cd <= max_cd_limit + 1e-9
    if apparent_area_cm2 is None:
        if apparent_width_mm is None or apparent_height_mm is None:
            raise ValueError("apparent_area_cm2 or apparent_width_mm/apparent_height_mm must be provided")
        area_cm2 = float(apparent_width_mm) * float(apparent_height_mm) / 100.0
    else:
        area_cm2 = float(apparent_area_cm2)
    area_passed = 25.0 <= area_cm2 <= 200.0
    overall = all(point.passed for point in points) and max_cd_passed and area_passed
    return R148Evaluation(points, max_cd, max_cd_limit, max_cd_passed, area_cm2, area_passed, overall)


def _bilinear_table(h: np.ndarray, v: np.ndarray, table: np.ndarray, hq: float, vq: float) -> float:
    if hq < h[0] or hq > h[-1] or vq < v[0] or vq > v[-1]:
        return 0.0
    hi = int(np.searchsorted(h, hq))
    vi = int(np.searchsorted(v, vq))
    if hi < len(h) and np.isclose(h[hi], hq):
        h0 = h1 = hi
        th = 0.0
    else:
        h1 = min(max(hi, 1), len(h) - 1)
        h0 = h1 - 1
        th = (hq - h[h0]) / (h[h1] - h[h0])
    if vi < len(v) and np.isclose(v[vi], vq):
        v0 = v1 = vi
        tv = 0.0
    else:
        v1 = min(max(vi, 1), len(v) - 1)
        v0 = v1 - 1
        tv = (vq - v[v0]) / (v[v1] - v[v0])
    q00 = table[v0, h0]
    q01 = table[v0, h1]
    q10 = table[v1, h0]
    q11 = table[v1, h1]
    return float((1 - tv) * ((1 - th) * q00 + th * q01) + tv * ((1 - th) * q10 + th * q11))


def ideal_r148_farfield(
    scale: float = 1.756,
    source_flux_lm: float = 74.0,
    optical_efficiency: float = 0.8,
) -> FarFieldResult:
    """Numerical ideal mode used for regression tests and sanity checks."""
    h_centers = np.arange(-30.0, 31.0, 1.0)
    v_centers = np.arange(-20.0, 21.0, 1.0)
    intensity = np.zeros((len(v_centers), len(h_centers)), dtype=float)
    for vi, vv in enumerate(v_centers):
        for hi, hh in enumerate(h_centers):
            intensity[vi, hi] = _bilinear_table(R148_H_DEG, R148_V_DEG, R148_MIN_CD, hh, vv) * scale
    phi_exit = source_flux_lm * optical_efficiency
    return result_from_intensity_grid(h_centers, v_centers, intensity, phi_exit)


def r148_minimum_flux_lm() -> float:
    return ideal_r148_farfield(scale=1.0, source_flux_lm=1.0, optical_efficiency=1.0).phi_in_bins_lm


def energy_limited_r148_farfield(
    source_flux_lm: float,
    optical_efficiency: float,
) -> FarFieldResult:
    """Best-case energy-consistent R148-shaped distribution.

    This is a theoretical lower-bound target for a future freeform/TIR optic:
    all available exit flux is distributed in the R148 minimum-map shape.
    """
    phi_exit = float(source_flux_lm) * float(optical_efficiency)
    base_flux = r148_minimum_flux_lm()
    scale = phi_exit / base_flux if base_flux > 0.0 else 0.0
    return ideal_r148_farfield(scale=scale, source_flux_lm=source_flux_lm, optical_efficiency=optical_efficiency)
