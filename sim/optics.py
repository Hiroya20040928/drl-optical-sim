from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .led_model import cosine_power_exponent
from .ray import RayBundle, normalize_vectors


AIR_N = 1.0


def _as_normals(normals: np.ndarray, count: int) -> np.ndarray:
    normals = np.asarray(normals, dtype=float)
    if normals.shape == (3,):
        normals = np.broadcast_to(normals, (count, 3)).copy()
    return normalize_vectors(normals)


def refract_vectors(
    directions: np.ndarray,
    normals: np.ndarray,
    n_from: float,
    n_to: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized Snell refraction with Schlick Fresnel transmission.

    Normals may point either way; they are oriented internally against the
    incident direction. The returned mask is True where total internal
    reflection occurred.
    """
    directions = normalize_vectors(np.asarray(directions, dtype=float))
    normals = _as_normals(normals, directions.shape[0])

    cos_i = -np.sum(directions * normals, axis=1)
    flip = cos_i < 0.0
    normals[flip] *= -1.0
    cos_i[flip] *= -1.0
    cos_i = np.clip(cos_i, 0.0, 1.0)

    eta = float(n_from) / float(n_to)
    sin_t2 = eta * eta * np.maximum(0.0, 1.0 - cos_i * cos_i)
    tir = sin_t2 > 1.0
    cos_t = np.sqrt(np.maximum(0.0, 1.0 - sin_t2))
    refracted = eta * directions + (eta * cos_i - cos_t)[:, None] * normals
    refracted = normalize_vectors(refracted)

    r0 = ((n_from - n_to) / (n_from + n_to)) ** 2
    reflectance = r0 + (1.0 - r0) * (1.0 - cos_i) ** 5
    transmittance = np.clip(1.0 - reflectance, 0.0, 1.0)
    transmittance[tir] = 0.0
    return refracted, tir, transmittance


def flat_plate_transmission(
    directions: np.ndarray,
    material_n: float = 1.49,
    normal: np.ndarray | None = None,
) -> np.ndarray:
    """Approximate two-interface Fresnel transmission through a flat plate."""
    normal = np.array([0.0, 0.0, -1.0]) if normal is None else np.asarray(normal, dtype=float)
    inside, tir_in, t_in = refract_vectors(directions, normal, AIR_N, material_n)
    _, tir_out, t_out = refract_vectors(inside, -normal, material_n, AIR_N)
    trans = t_in * t_out
    trans[tir_in | tir_out] = 0.0
    return trans


def propagate_to_z(bundle: RayBundle, z_mm: float) -> None:
    active = bundle.alive.copy()
    dz = bundle.directions[:, 2]
    valid = active & (np.abs(dz) > 1e-9)
    t = np.zeros(bundle.count)
    t[valid] = (float(z_mm) - bundle.origins_mm[valid, 2]) / dz[valid]
    forward = valid & (t >= 0.0)
    bundle.origins_mm[forward] = bundle.origins_mm[forward] + bundle.directions[forward] * t[forward, None]
    bundle.alive[valid & ~forward] = False


def sample_cone_about_directions(
    base_dirs: np.ndarray,
    fwhm_deg: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample cosine-power directions around each base direction."""
    base = normalize_vectors(base_dirs)
    count = base.shape[0]
    exponent = cosine_power_exponent(fwhm_deg)
    u = rng.random(count)
    phi = 2.0 * np.pi * rng.random(count)
    cos_theta = u if exponent <= 0 else u ** (1.0 / (exponent + 1.0))
    sin_theta = np.sqrt(np.maximum(0.0, 1.0 - cos_theta * cos_theta))
    local = np.column_stack([sin_theta * np.cos(phi), sin_theta * np.sin(phi), cos_theta])

    helper = np.tile(np.array([0.0, 1.0, 0.0]), (count, 1))
    near_parallel = np.abs(np.sum(helper * base, axis=1)) > 0.9
    helper[near_parallel] = np.array([1.0, 0.0, 0.0])
    tangent = normalize_vectors(np.cross(helper, base))
    bitangent = normalize_vectors(np.cross(base, tangent))
    world = local[:, 0, None] * tangent + local[:, 1, None] * bitangent + local[:, 2, None] * base
    return normalize_vectors(world)


class OpticalElement(Protocol):
    name: str

    def apply(self, rays: RayBundle, rng: np.random.Generator) -> RayBundle:
        ...


@dataclass(slots=True)
class OpticalSystem:
    elements: list[OpticalElement] = field(default_factory=list)

    def trace(self, rays: RayBundle, rng: np.random.Generator | None = None) -> RayBundle:
        rng = np.random.default_rng() if rng is None else rng
        traced = rays.copy()
        for element in self.elements:
            traced = element.apply(traced, rng)
        return traced

