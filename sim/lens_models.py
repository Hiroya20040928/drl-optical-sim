from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

from .optics import (
    AIR_N,
    flat_plate_transmission,
    propagate_to_z,
    refract_vectors,
    sample_cone_about_directions,
)
from .ray import RayBundle, normalize_vectors


def load_lenses_json(path: str | Path) -> list[dict[str, Any]]:
    return json.loads(Path(path).read_text(encoding="utf-8"))["lenses"]


@dataclass(slots=True)
class NoLens:
    name: str = "Lensなし"
    transmission: float = 1.0

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        rays.flux_lm[rays.alive] *= float(self.transmission)
        return rays


@dataclass(slots=True)
class ThinCollimatorLens:
    name: str
    target_fwhm_deg: float
    input_fwhm_deg: float = 120.0
    material_n: float = 1.49
    transmission: float = 0.9
    position_mm: float = 12.0

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        propagate_to_z(rays, self.position_mm)
        active = rays.alive
        if not np.any(active):
            return rays

        dirs = rays.directions[active]
        theta = np.arctan2(np.linalg.norm(dirs[:, :2], axis=1), np.maximum(dirs[:, 2], 1e-12))
        az = np.arctan2(dirs[:, 1], dirs[:, 0])
        input_half = math.radians(max(self.input_fwhm_deg, 1e-6) / 2.0)
        target_half = math.radians(max(self.target_fwhm_deg, 1e-6) / 2.0)
        compression = math.tan(target_half) / math.tan(input_half)
        theta_out = np.arctan(np.tan(theta) * compression)
        sin_t = np.sin(theta_out)
        out = np.column_stack([sin_t * np.cos(az), sin_t * np.sin(az), np.cos(theta_out)])

        fresnel = flat_plate_transmission(dirs, self.material_n)
        rays.directions[active] = normalize_vectors(out)
        rays.flux_lm[active] *= fresnel * float(self.transmission)
        rays.alive[active] &= rays.flux_lm[active] > 0.0
        return rays


@dataclass(slots=True)
class SphericalLens:
    name: str = "球面アクリルレンズ近似"
    radius_mm: float = 12.0
    thickness_mm: float = 5.0
    position_mm: float = 10.0
    material_n: float = 1.49
    transmission: float = 0.9

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        active_idx = np.flatnonzero(rays.alive)
        if active_idx.size == 0:
            return rays

        center = np.array([0.0, 0.0, self.position_mm + self.radius_mm])
        origins = rays.origins_mm[active_idx]
        dirs = rays.directions[active_idx]
        oc = origins - center
        b = 2.0 * np.sum(oc * dirs, axis=1)
        c = np.sum(oc * oc, axis=1) - self.radius_mm * self.radius_mm
        disc = b * b - 4.0 * c
        valid = disc >= 0.0
        t = np.full(active_idx.size, np.nan)
        sqrt_disc = np.zeros(active_idx.size)
        sqrt_disc[valid] = np.sqrt(disc[valid])
        t_near = (-b - sqrt_disc) / 2.0
        t_far = (-b + sqrt_disc) / 2.0
        t[valid] = np.where(t_near[valid] > 1e-6, t_near[valid], t_far[valid])
        valid &= t > 1e-6

        global_valid = active_idx[valid]
        global_invalid = active_idx[~valid]
        rays.alive[global_invalid] = False
        if global_valid.size == 0:
            return rays

        hit = origins[valid] + dirs[valid] * t[valid, None]
        normals = normalize_vectors(hit - center)
        inside, tir_in, t_in = refract_vectors(dirs[valid], normals, AIR_N, self.material_n)
        keep = ~tir_in
        global_tir = global_valid[~keep]
        rays.alive[global_tir] = False
        if not np.any(keep):
            return rays

        kept_idx = global_valid[keep]
        hit_kept = hit[keep]
        inside_kept = inside[keep]
        dz = inside_kept[:, 2]
        exit_z = self.position_mm + self.thickness_mm
        valid_exit = np.abs(dz) > 1e-9
        t_exit = np.zeros(kept_idx.size)
        t_exit[valid_exit] = (exit_z - hit_kept[valid_exit, 2]) / dz[valid_exit]
        valid_exit &= t_exit >= 0.0
        rays.alive[kept_idx[~valid_exit]] = False
        if not np.any(valid_exit):
            return rays

        final_idx = kept_idx[valid_exit]
        exit_points = hit_kept[valid_exit] + inside_kept[valid_exit] * t_exit[valid_exit, None]
        out, tir_out, t_out = refract_vectors(inside_kept[valid_exit], np.array([0.0, 0.0, 1.0]), self.material_n, AIR_N)
        final_keep = ~tir_out
        rays.alive[final_idx[~final_keep]] = False
        final_idx = final_idx[final_keep]
        if final_idx.size == 0:
            return rays

        rays.origins_mm[final_idx] = exit_points[final_keep]
        rays.directions[final_idx] = out[final_keep]
        rays.flux_lm[final_idx] *= t_in[keep][valid_exit][final_keep] * t_out[final_keep] * float(self.transmission)
        return rays


@dataclass(slots=True)
class DiffuserPlate:
    name: str
    scatter_fwhm_deg: float
    position_mm: float = 18.0
    material_n: float = 1.49
    transmission: float = 0.88
    absorption: float = 0.04
    scatter_about_axis: bool = False

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        propagate_to_z(rays, self.position_mm)
        active = rays.alive
        if not np.any(active):
            return rays
        dirs = rays.directions[active]
        fresnel = flat_plate_transmission(dirs, self.material_n)
        base = np.tile(np.array([0.0, 0.0, 1.0]), (dirs.shape[0], 1)) if self.scatter_about_axis else dirs
        rays.directions[active] = sample_cone_about_directions(base, self.scatter_fwhm_deg, rng)
        rays.flux_lm[active] *= fresnel * float(self.transmission) * max(0.0, 1.0 - float(self.absorption))
        rays.alive[active] &= rays.flux_lm[active] > 0.0
        return rays


@dataclass(slots=True)
class MeshOptic:
    """Future OBJ/STL freeform/TIR optic hook.

    The first release stores triangles and exposes a ray-intersection method.
    It is intentionally not wired into the GUI as an optimizer yet.
    """

    path: str | Path
    name: str = "Mesh optic"
    material_n: float = 1.49
    transmission: float = 0.9
    triangles_mm: np.ndarray | None = None

    def load(self) -> None:
        path = Path(self.path)
        if path.suffix.lower() == ".obj":
            self.triangles_mm = self._load_obj(path)
        elif path.suffix.lower() == ".stl":
            self.triangles_mm = np.empty((0, 3, 3), dtype=float)
        else:
            raise ValueError("mesh path must be .obj or .stl")

    def _load_obj(self, path: Path) -> np.ndarray:
        vertices: list[list[float]] = []
        triangles: list[list[list[float]]] = []
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            parts = line.strip().split()
            if not parts:
                continue
            if parts[0] == "v" and len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "f" and len(parts) >= 4:
                idx = [int(p.split("/")[0]) - 1 for p in parts[1:]]
                for i in range(1, len(idx) - 1):
                    triangles.append([vertices[idx[0]], vertices[idx[i]], vertices[idx[i + 1]]])
        return np.asarray(triangles, dtype=float)

    def intersect(self, rays: RayBundle) -> tuple[np.ndarray, np.ndarray]:
        if self.triangles_mm is None:
            self.load()
        if self.triangles_mm is None or self.triangles_mm.size == 0:
            return np.full(rays.count, np.inf), np.full(rays.count, -1, dtype=int)

        distances = np.full(rays.count, np.inf)
        tri_ids = np.full(rays.count, -1, dtype=int)
        eps = 1e-9
        origins = rays.origins_mm
        dirs = rays.directions
        for tri_id, tri in enumerate(self.triangles_mm):
            v0, v1, v2 = tri
            e1 = v1 - v0
            e2 = v2 - v0
            p = np.cross(dirs, e2)
            det = np.sum(e1 * p, axis=1)
            valid = np.abs(det) > eps
            inv_det = np.zeros_like(det)
            inv_det[valid] = 1.0 / det[valid]
            tvec = origins - v0
            u = np.sum(tvec * p, axis=1) * inv_det
            q = np.cross(tvec, e1)
            v = np.sum(dirs * q, axis=1) * inv_det
            t = np.sum(e2 * q, axis=1) * inv_det
            hit = valid & (u >= 0.0) & (v >= 0.0) & (u + v <= 1.0) & (t > eps) & (t < distances)
            distances[hit] = t[hit]
            tri_ids[hit] = tri_id
        return distances, tri_ids

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        distances, tri_ids = self.intersect(rays)
        hit = np.isfinite(distances) & (tri_ids >= 0) & rays.alive
        rays.origins_mm[hit] = rays.origins_mm[hit] + rays.directions[hit] * distances[hit, None]
        rays.flux_lm[hit] *= float(self.transmission)
        return rays


def lens_from_spec(spec: dict[str, Any]) -> object:
    kind = spec.get("kind", "none")
    if kind == "none":
        return NoLens(name=spec.get("name", "Lensなし"), transmission=float(spec.get("transmission", 1.0)))
    if kind == "thin_collimator":
        return ThinCollimatorLens(
            name=spec.get("name", "薄肉コリメータ"),
            target_fwhm_deg=float(spec.get("target_fwhm_deg", 45.0)),
            input_fwhm_deg=float(spec.get("input_fwhm_deg", 120.0)),
            material_n=float(spec.get("refractive_index", 1.49)),
            transmission=float(spec.get("transmission", 0.9)),
            position_mm=float(spec.get("position_mm", 12.0)),
        )
    if kind == "spherical":
        return SphericalLens(
            name=spec.get("name", "球面レンズ"),
            radius_mm=float(spec.get("radius_mm", 12.0)),
            thickness_mm=float(spec.get("thickness_mm", 5.0)),
            position_mm=float(spec.get("position_mm", 10.0)),
            material_n=float(spec.get("refractive_index", 1.49)),
            transmission=float(spec.get("transmission", 0.9)),
        )
    if kind == "plane_diffuser":
        return DiffuserPlate(
            name=spec.get("name", "平面拡散板"),
            scatter_fwhm_deg=float(spec.get("scatter_fwhm_deg", 25.0)),
            position_mm=float(spec.get("position_mm", 18.0)),
            material_n=float(spec.get("refractive_index", 1.49)),
            transmission=float(spec.get("transmission", 0.88)),
            absorption=float(spec.get("absorption", 0.04)),
            scatter_about_axis=False,
        )
    if kind == "milky_acrylic":
        return DiffuserPlate(
            name=spec.get("name", "乳白アクリル拡散板"),
            scatter_fwhm_deg=float(spec.get("scatter_fwhm_deg", 65.0)),
            position_mm=float(spec.get("position_mm", 18.0)),
            material_n=float(spec.get("refractive_index", 1.49)),
            transmission=float(spec.get("transmission", 0.62)),
            absorption=float(spec.get("absorption", 0.18)),
            scatter_about_axis=True,
        )
    raise ValueError(f"Unsupported lens kind: {kind}")

