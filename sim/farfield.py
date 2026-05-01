from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .ray import RayBundle


@dataclass(slots=True)
class FarFieldResult:
    h_edges_deg: np.ndarray
    v_edges_deg: np.ndarray
    h_centers_deg: np.ndarray
    v_centers_deg: np.ndarray
    flux_map_lm: np.ndarray
    solid_angle_sr: np.ndarray
    intensity_cd: np.ndarray
    phi_exit_lm: float
    phi_in_bins_lm: float

    @property
    def center_intensity_cd(self) -> float:
        return self.sample_intensity(0.0, 0.0)

    @property
    def imax_cd(self) -> float:
        if self.intensity_cd.size == 0:
            return 0.0
        return float(np.nanmax(self.intensity_cd))

    def sample_intensity(self, h_deg: float, v_deg: float) -> float:
        """Bilinear sample from the calculated candela map."""
        h = float(h_deg)
        v = float(v_deg)
        hc = self.h_centers_deg
        vc = self.v_centers_deg
        if h < hc[0] or h > hc[-1] or v < vc[0] or v > vc[-1]:
            return 0.0

        hi = int(np.searchsorted(hc, h))
        vi = int(np.searchsorted(vc, v))
        if hi < len(hc) and math.isclose(hc[hi], h, abs_tol=1e-12):
            h0 = h1 = hi
            th = 0.0
        else:
            h1 = min(max(hi, 1), len(hc) - 1)
            h0 = h1 - 1
            th = (h - hc[h0]) / (hc[h1] - hc[h0])

        if vi < len(vc) and math.isclose(vc[vi], v, abs_tol=1e-12):
            v0 = v1 = vi
            tv = 0.0
        else:
            v1 = min(max(vi, 1), len(vc) - 1)
            v0 = v1 - 1
            tv = (v - vc[v0]) / (vc[v1] - vc[v0])

        q00 = self.intensity_cd[v0, h0]
        q01 = self.intensity_cd[v0, h1]
        q10 = self.intensity_cd[v1, h0]
        q11 = self.intensity_cd[v1, h1]
        return float((1 - tv) * ((1 - th) * q00 + th * q01) + tv * ((1 - th) * q10 + th * q11))


def directions_to_horizontal_vertical(directions: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    directions = np.asarray(directions, dtype=float)
    x = directions[:, 0]
    y = directions[:, 1]
    z = directions[:, 2]
    h = np.degrees(np.arctan2(x, z))
    v = np.degrees(np.arctan2(y, np.sqrt(x * x + z * z)))
    return h, v


def make_edges(range_deg: tuple[float, float], bin_deg: float) -> np.ndarray:
    start, stop = range_deg
    count = int(round((stop - start) / bin_deg))
    return np.linspace(start, stop, count + 1)


def solid_angle_grid(h_edges_deg: np.ndarray, v_edges_deg: np.ndarray) -> np.ndarray:
    h_rad = np.radians(h_edges_deg)
    v_rad = np.radians(v_edges_deg)
    dh = np.diff(h_rad)
    d_sin_v = np.diff(np.sin(v_rad))
    return np.outer(d_sin_v, dh)


def accumulate_farfield(
    rays: RayBundle,
    h_range_deg: tuple[float, float] = (-30.0, 30.0),
    v_range_deg: tuple[float, float] = (-20.0, 20.0),
    bin_deg: float = 1.0,
) -> FarFieldResult:
    h_edges = make_edges(h_range_deg, bin_deg)
    v_edges = make_edges(v_range_deg, bin_deg)
    h_centers = 0.5 * (h_edges[:-1] + h_edges[1:])
    v_centers = 0.5 * (v_edges[:-1] + v_edges[1:])
    h, v = directions_to_horizontal_vertical(rays.directions)
    active = rays.alive
    in_window = (
        active
        & (h >= h_edges[0])
        & (h <= h_edges[-1])
        & (v >= v_edges[0])
        & (v <= v_edges[-1])
    )
    flux_map, _, _ = np.histogram2d(
        v[in_window],
        h[in_window],
        bins=[v_edges, h_edges],
        weights=rays.flux_lm[in_window],
    )
    omega = solid_angle_grid(h_edges, v_edges)
    intensity = np.divide(flux_map, omega, out=np.zeros_like(flux_map), where=omega > 0.0)
    return FarFieldResult(
        h_edges_deg=h_edges,
        v_edges_deg=v_edges,
        h_centers_deg=h_centers,
        v_centers_deg=v_centers,
        flux_map_lm=flux_map,
        solid_angle_sr=omega,
        intensity_cd=intensity,
        phi_exit_lm=rays.total_flux_lm(active_only=True),
        phi_in_bins_lm=float(np.sum(flux_map)),
    )


def result_from_intensity_grid(
    h_centers_deg: np.ndarray,
    v_centers_deg: np.ndarray,
    intensity_cd: np.ndarray,
    phi_exit_lm: float,
) -> FarFieldResult:
    h_step = float(np.median(np.diff(h_centers_deg))) if len(h_centers_deg) > 1 else 1.0
    v_step = float(np.median(np.diff(v_centers_deg))) if len(v_centers_deg) > 1 else 1.0
    h_edges = np.concatenate([[h_centers_deg[0] - h_step / 2.0], h_centers_deg + h_step / 2.0])
    v_edges = np.concatenate([[v_centers_deg[0] - v_step / 2.0], v_centers_deg + v_step / 2.0])
    omega = solid_angle_grid(h_edges, v_edges)
    flux_map = intensity_cd * omega
    return FarFieldResult(
        h_edges_deg=h_edges,
        v_edges_deg=v_edges,
        h_centers_deg=h_centers_deg,
        v_centers_deg=v_centers_deg,
        flux_map_lm=flux_map,
        solid_angle_sr=omega,
        intensity_cd=intensity_cd,
        phi_exit_lm=float(phi_exit_lm),
        phi_in_bins_lm=float(np.sum(flux_map)),
    )

