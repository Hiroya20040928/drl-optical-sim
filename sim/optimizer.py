from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
from pathlib import Path
from typing import Iterable

import numpy as np

from .r148 import R148_MIN_CD, r148_minimum_flux_lm
from .sampler import SimulationConfig, run_simulation


@dataclass(slots=True)
class OptimizationResult:
    lens_id: str
    diffuser_id: str
    rows: int
    cols: int
    spacing_x_mm: float
    spacing_y_mm: float
    lens_position_mm: float | None
    current_per_led_ma: float
    total_current_ma: float
    power_w: float
    source_flux_lm: float
    exit_flux_lm: float
    i00_cd: float
    imax_cd: float
    apparent_area_cm2: float
    passed: bool
    note: str

    def to_row(self) -> dict[str, object]:
        return asdict(self)


def _scale_needed_for_r148(result) -> float:
    ratios: list[float] = []
    for point in result.r148.points:
        if point.min_cd <= 0.0:
            continue
        if point.measured_cd <= 0.0:
            return float("inf")
        ratios.append(point.min_cd / point.measured_cd)
    return max(ratios) if ratios else 1.0


def _candidate_layouts(
    max_rows: int = 3,
    max_cols: int = 4,
    spacings_mm: Iterable[float] = (9.0, 14.0, 20.0),
) -> Iterable[tuple[int, int, float, float]]:
    for rows in range(1, max_rows + 1):
        for cols in range(1, max_cols + 1):
            for sx in spacings_mm:
                for sy in spacings_mm:
                    yield rows, cols, sx, sy


def optimize_cree_xhp70b(
    *,
    ray_count: int = 60000,
    reference_current_ma: float = 100.0,
    lens_ids: Iterable[str] | None = None,
    diffuser_ids: Iterable[str] = ("none", "plane_diffuser", "milky_acrylic_diffuser"),
    lens_positions_mm: Iterable[float | None] = (8.0, 12.0, 16.0, 20.0, 24.0, None),
    layouts: Iterable[tuple[int, int, float, float]] | None = None,
) -> list[OptimizationResult]:
    """Search CREE XHP70B configurations for minimum electrical power.

    Physical Monte Carlo candidates are evaluated at a reference current and
    scaled linearly because the first-release LED model uses linear
    current/flux scaling. The special lower-bound target is solved
    analytically from the integrated R148 minimum luminous flux.
    """
    candidate_lens_ids = tuple(
        lens_ids
        or (
            "cree_xhp70b_r148_lower_bound_60x45",
            "ledil_c16369_hb_sq_w_xhp70p2",
            "carclo_10756_xhp70p2",
            "ledil_f15539_jenny_40_xhp70p2",
            "ledil_c12868_flare_maxi_xhp70p2",
            "oshh2045m_30deg",
            "oshh2045m_45deg",
            "spherical_acrylic",
            "none",
        )
    )
    results: list[OptimizationResult] = []
    vf_v = 12.0
    flux_nom_lm = 1710.0
    current_nom_ma = 1050.0

    for rows, cols, sx, sy in (layouts or _candidate_layouts()):
        led_count = rows * cols
        for lens_id in candidate_lens_ids:
            if lens_id == "cree_xhp70b_r148_lower_bound_60x45":
                exit_flux_required = r148_minimum_flux_lm()
                source_flux_required = exit_flux_required / 0.8
                total_current = source_flux_required / flux_nom_lm * current_nom_ma
                current_per_led = total_current / led_count
                if current_per_led > 2400.0:
                    continue
                cfg = SimulationConfig(
                    led_id="cree_xhp70b_00_0000_0d0bn440e",
                    led_count=led_count,
                    led_rows=rows,
                    led_cols=cols,
                    led_spacing_mm=sx,
                    led_spacing_x_mm=sx,
                    led_spacing_y_mm=sy,
                    current_ma=current_per_led,
                    flux_typ_lm=flux_nom_lm,
                    vf_typ_v=vf_v,
                    directivity_deg=125.0,
                    lens_id=lens_id,
                    diffuser_id="none",
                    ray_count=1000,
                    preview_ray_count=200,
                    ideal_mode=False,
                )
                sim = run_simulation(cfg)
                results.append(
                    OptimizationResult(
                        lens_id=lens_id,
                        diffuser_id="none",
                        rows=rows,
                        cols=cols,
                        spacing_x_mm=sx,
                        spacing_y_mm=sy,
                        lens_position_mm=18.0,
                        current_per_led_ma=current_per_led,
                        total_current_ma=total_current,
                        power_w=vf_v * total_current / 1000.0,
                        source_flux_lm=sim.source_flux_lm,
                        exit_flux_lm=sim.farfield.phi_exit_lm,
                        i00_cd=sim.farfield.center_intensity_cd,
                        imax_cd=sim.farfield.imax_cd,
                        apparent_area_cm2=sim.r148.apparent_area_cm2,
                        passed=sim.r148.overall_passed,
                        note="Analytical energy-consistent R148 lower-bound target; not a purchasable certified lens.",
                    )
                )
                continue

            for diffuser_id in diffuser_ids:
                for lens_position in lens_positions_mm:
                    cfg = SimulationConfig(
                        led_id="cree_xhp70b_00_0000_0d0bn440e",
                        led_count=led_count,
                        led_rows=rows,
                        led_cols=cols,
                        led_spacing_mm=sx,
                        led_spacing_x_mm=sx,
                        led_spacing_y_mm=sy,
                        current_ma=reference_current_ma,
                        flux_typ_lm=flux_nom_lm,
                        vf_typ_v=vf_v,
                        directivity_deg=125.0,
                        lens_id=lens_id,
                        lens_position_mm=lens_position,
                        diffuser_id=diffuser_id,
                        ray_count=ray_count,
                        preview_ray_count=200,
                        random_seed=20260501,
                    )
                    try:
                        sim = run_simulation(cfg)
                    except Exception as exc:
                        results.append(
                            OptimizationResult(
                                lens_id=lens_id,
                                diffuser_id=diffuser_id,
                                rows=rows,
                                cols=cols,
                                spacing_x_mm=sx,
                                spacing_y_mm=sy,
                                lens_position_mm=lens_position,
                                current_per_led_ma=float("inf"),
                                total_current_ma=float("inf"),
                                power_w=float("inf"),
                                source_flux_lm=0.0,
                                exit_flux_lm=0.0,
                                i00_cd=0.0,
                                imax_cd=0.0,
                                apparent_area_cm2=0.0,
                                passed=False,
                                note=f"simulation error: {exc}",
                            )
                        )
                        continue
                    if not sim.r148.area_passed:
                        scale = float("inf")
                        note = "apparent area fails"
                    else:
                        scale = _scale_needed_for_r148(sim)
                        note = "scaled physical approximation"
                    if not np.isfinite(scale):
                        current_per_led = float("inf")
                        total_current = float("inf")
                        power = float("inf")
                        passed = False
                        i00 = 0.0
                        imax = 0.0
                        source_flux = 0.0
                        exit_flux = 0.0
                    else:
                        current_per_led = reference_current_ma * scale
                        total_current = current_per_led * led_count
                        power = vf_v * total_current / 1000.0
                        i00 = sim.farfield.center_intensity_cd * scale
                        imax = sim.farfield.imax_cd * scale
                        source_flux = sim.source_flux_lm * scale
                        exit_flux = sim.farfield.phi_exit_lm * scale
                        passed = (
                            current_per_led <= 2400.0
                            and imax <= 1200.0 + 1e-9
                            and sim.r148.area_passed
                            and scale > 0.0
                        )
                    results.append(
                        OptimizationResult(
                            lens_id=lens_id,
                            diffuser_id=diffuser_id,
                            rows=rows,
                            cols=cols,
                            spacing_x_mm=sx,
                            spacing_y_mm=sy,
                            lens_position_mm=lens_position,
                            current_per_led_ma=current_per_led,
                            total_current_ma=total_current,
                            power_w=power,
                            source_flux_lm=source_flux,
                            exit_flux_lm=exit_flux,
                            i00_cd=i00,
                            imax_cd=imax,
                            apparent_area_cm2=sim.r148.apparent_area_cm2,
                            passed=passed,
                            note=note,
                        )
                    )
    return sorted(results, key=lambda r: (not r.passed, r.power_w, r.rows * r.cols, r.lens_id))


def save_optimization_csv(results: list[OptimizationResult], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].to_row().keys()))
        writer.writeheader()
        for result in results:
            writer.writerow(result.to_row())
