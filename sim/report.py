from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Callable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .r148 import DISCLAIMER
from .sampler import SimulationResult, layout_positions_from_config, load_default_lenses


def save_config(result: SimulationResult, path: str | Path) -> None:
    payload = {
        "config": result.config.to_dict(),
        "led": {
            "id": result.led_spec.id,
            "name": result.led_spec.name,
            "flux_typ_lm": result.led_spec.flux_typ_lm,
            "current_nominal_ma": result.led_spec.current_nominal_ma,
            "vf_typ_v": result.led_spec.vf_typ_v,
            "directivity_deg": result.led_spec.directivity_deg,
            "emitter_mm": list(result.led_spec.emitter_mm),
            "package_mm": list(result.led_spec.package_mm),
        },
        "apparent_surface": {
            "shape": result.apparent_surface.shape,
            "area_cm2": result.apparent_surface.area_cm2,
            "label": result.apparent_surface.label,
            "source": result.apparent_surface.source,
            "area_model": "sum_of_repeated_front_apertures"
            if result.apparent_surface.unit_count > 1
            else "single_front_aperture_or_bounding_box",
            "width_mm": result.apparent_surface.width_mm,
            "height_mm": result.apparent_surface.height_mm,
            "diameter_mm": result.apparent_surface.diameter_mm,
            "unit_count": result.apparent_surface.unit_count,
            "unit_label": result.apparent_surface.unit_label,
            "array_envelope_width_mm": result.apparent_surface.width_mm if result.apparent_surface.unit_count > 1 else None,
            "array_envelope_height_mm": result.apparent_surface.height_mm if result.apparent_surface.unit_count > 1 else None,
        },
    }
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def save_intensity_csv(result: SimulationResult, path: str | Path) -> None:
    ff = result.farfield
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["h_deg", "v_deg", "flux_lm", "solid_angle_sr", "intensity_cd"])
        for vi, v in enumerate(ff.v_centers_deg):
            for hi, h in enumerate(ff.h_centers_deg):
                writer.writerow(
                    [
                        f"{h:.6g}",
                        f"{v:.6g}",
                        f"{ff.flux_map_lm[vi, hi]:.9g}",
                        f"{ff.solid_angle_sr[vi, hi]:.9g}",
                        f"{ff.intensity_cd[vi, hi]:.9g}",
                    ]
                )


def save_r148_csv(result: SimulationResult, path: str | Path) -> None:
    ev = result.r148
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["h_deg", "v_deg", "min_cd", "measured_cd", "passed"])
        for point in ev.points:
            writer.writerow(
                [
                    f"{point.h_deg:.6g}",
                    f"{point.v_deg:.6g}",
                    f"{point.min_cd:.6g}",
                    f"{point.measured_cd:.9g}",
                    "PASS" if point.passed else "FAIL",
                ]
            )
        writer.writerow([])
        writer.writerow(["Imax_cd", f"{ev.max_cd:.9g}", "limit_cd", f"{ev.max_cd_limit:.9g}", "PASS" if ev.max_cd_passed else "FAIL"])
        writer.writerow(["apparent_area_cm2", f"{ev.apparent_area_cm2:.9g}", "range_cm2", "25-200", "PASS" if ev.area_passed else "FAIL"])
        writer.writerow(["overall", "PASS" if ev.overall_passed else "FAIL"])


def save_heatmap_png(result: SimulationResult, path: str | Path) -> None:
    ff = result.farfield
    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=150)
    image = ax.imshow(
        ff.intensity_cd,
        origin="lower",
        extent=[ff.h_edges_deg[0], ff.h_edges_deg[-1], ff.v_edges_deg[0], ff.v_edges_deg[-1]],
        aspect="auto",
        cmap="inferno",
    )
    ax.set_xlabel("Horizontal angle h [deg]")
    ax.set_ylabel("Vertical angle v [deg]")
    ax.set_title("Far-field luminous intensity [cd]")
    fig.colorbar(image, ax=ax, label="cd")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def save_3d_preview_fallback_png(result: SimulationResult, path: str | Path) -> None:
    """Save a lightweight x-z ray preview when no OpenGL framebuffer is available."""
    fig, ax = plt.subplots(figsize=(7.0, 4.5), dpi=150)
    cfg = result.config
    surface = result.apparent_surface
    surface_w = surface.diameter_mm or surface.width_mm or cfg.apparent_width_mm
    positions = layout_positions_from_config(cfg)
    lens = next((item for item in load_default_lenses() if item.get("id") == cfg.lens_id), {})
    ax.add_patch(
        plt.Rectangle(
            (-surface_w / 2.0, -1.0),
            surface_w,
            2.0,
            color="#244d43",
            alpha=0.8,
            label="board/front reference",
        )
    )
    if cfg.lens_id != "none" and lens.get("apparent_repeats_per_led"):
        unit_w = float(lens.get("apparent_width_mm", lens.get("width_mm", 25.0)))
        for x, y, _ in positions:
            z = cfg.lens_position_mm if cfg.lens_position_mm is not None else 12.0
            ax.plot([float(x) - unit_w / 2.0, float(x) + unit_w / 2.0], [z, z], color="#64b5f6", linewidth=1.1, alpha=0.85)
    elif cfg.lens_id != "none":
        ax.add_patch(
            plt.Rectangle(
                (-surface_w / 2.0, -1.0),
                surface_w,
                2.0,
                fill=False,
                edgecolor="#64b5f6",
                linewidth=1.1,
                alpha=0.85,
            )
        )
    if result.preview_rays is not None:
        rays = result.preview_rays
        max_flux = max(float(rays.flux_lm.max()), 1e-12) if rays.count > 0 else 1.0
        for origin, direction, flux, alive in zip(rays.origins_mm, rays.directions, rays.flux_lm, rays.alive):
            if not alive:
                continue
            end = origin + direction * 80.0
            alpha = 0.06 + 0.22 * min(1.0, float(flux) / max_flux)
            ax.plot([origin[0], end[0]], [origin[2], end[2]], color="#f1c232", alpha=alpha, linewidth=0.6)
    ax.set_xlabel("x [mm]")
    ax.set_ylabel("z [mm]")
    ax.set_title("Ray preview (OpenGL fallback)")
    ax.set_aspect("equal", adjustable="box")
    half_width = max(surface_w * 0.7, 55.0)
    ax.set_xlim(-half_width, half_width)
    ax.set_ylim(-6.0, 90.0)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def save_summary_report(result: SimulationResult, path: str | Path) -> None:
    ev = result.r148
    ff = result.farfield
    status = "PASS" if ev.overall_passed else "FAIL"
    lines = [
        "# BWSC DRL Optical Simulation Summary",
        "",
        f"- LED: {result.led_spec.name}",
        f"- LED count: {result.config.led_count}",
        f"- Drive current: {result.config.current_ma:.3g} mA",
        f"- Source flux: {result.source_flux_lm:.3f} lm",
        f"- Exit flux: {ff.phi_exit_lm:.3f} lm",
        f"- Optical efficiency: {result.optical_efficiency * 100.0:.2f} %",
        f"- I(0,0): {ff.center_intensity_cd:.2f} cd",
        f"- Imax: {ff.imax_cd:.2f} cd",
        f"- Apparent surface: {result.apparent_surface.label} ({result.apparent_surface.source})",
        f"- Apparent area: {ev.apparent_area_cm2:.2f} cm2",
        f"- R148 category RL check: {status}",
    ]
    if result.config.ideal_mode or result.config.lens_id == "ideal_r148_1p756":
        lines.extend(
            [
                "",
                "> WARNING: This run used the ideal R148 target mode. The candela map is imposed from the R148 table and is not proof that the selected LED, current, and real lens can physically produce that distribution.",
            ]
        )
    if result.config.lens_id == "cree_xhp70b_r148_lower_bound_60x45":
        lines.extend(
            [
                "",
                "> WARNING: This run used the energy-consistent R148 lower-bound freeform target. It is NOT a real purchasable lens. It is a minimum-power design target, not a certified lamp or a substitute for measured photometry.",
            ]
        )
    lines.extend(
        [
            "",
            "## R148 RL Measurement Points",
            "",
            "| h [deg] | v [deg] | min [cd] | simulated [cd] | result |",
            "|---:|---:|---:|---:|:---|",
        ]
    )
    for point in ev.points:
        lines.append(
            f"| {point.h_deg:.0f} | {point.v_deg:.0f} | {point.min_cd:.0f} | {point.measured_cd:.2f} | {'PASS' if point.passed else 'FAIL'} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            f"- {DISCLAIMER}",
            "- OpenGL表示の明るさは判定に使っていません。判定は数値計算された光度[cd]のみで行います。",
            "- BWSC提出には実測フォトメトリ，色度測定，取付図，certifying engineer確認が必要です。",
        ]
    )
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def save_all_outputs(
    result: SimulationResult,
    output_dir: str | Path,
    save_3d_view: Callable[[Path], None] | None = None,
) -> dict[str, Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths = {
        "simulation_config.json": out / "simulation_config.json",
        "intensity_map.csv": out / "intensity_map.csv",
        "r148_check.csv": out / "r148_check.csv",
        "heatmap.png": out / "heatmap.png",
        "3d_view.png": out / "3d_view.png",
        "summary_report.md": out / "summary_report.md",
    }
    save_config(result, paths["simulation_config.json"])
    save_intensity_csv(result, paths["intensity_map.csv"])
    save_r148_csv(result, paths["r148_check.csv"])
    save_heatmap_png(result, paths["heatmap.png"])
    save_summary_report(result, paths["summary_report.md"])
    if save_3d_view is not None:
        save_3d_view(paths["3d_view.png"])
    else:
        save_3d_preview_fallback_png(result, paths["3d_view.png"])
    return paths
