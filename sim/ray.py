from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def normalize_vectors(vectors: np.ndarray) -> np.ndarray:
    """Return unit vectors, leaving zero vectors as zero."""
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.divide(vectors, norms, out=np.zeros_like(vectors, dtype=float), where=norms > 0)


@dataclass(slots=True)
class RayBundle:
    """Vectorized ray storage.

    Units are millimetres for origins and dimensionless unit vectors for
    directions. Each ray carries a luminous-flux weight in lumens.
    """

    origins_mm: np.ndarray
    directions: np.ndarray
    flux_lm: np.ndarray
    alive: np.ndarray | None = None

    def __post_init__(self) -> None:
        self.origins_mm = np.asarray(self.origins_mm, dtype=float)
        self.directions = normalize_vectors(np.asarray(self.directions, dtype=float))
        self.flux_lm = np.asarray(self.flux_lm, dtype=float)
        if self.alive is None:
            self.alive = np.ones(self.flux_lm.shape[0], dtype=bool)
        else:
            self.alive = np.asarray(self.alive, dtype=bool)
        if self.origins_mm.shape != self.directions.shape:
            raise ValueError("origins_mm and directions must have the same shape")
        if self.origins_mm.shape[0] != self.flux_lm.shape[0]:
            raise ValueError("flux_lm length must match ray count")

    @property
    def count(self) -> int:
        return int(self.flux_lm.shape[0])

    @property
    def active_count(self) -> int:
        return int(np.count_nonzero(self.alive))

    def total_flux_lm(self, active_only: bool = True) -> float:
        if active_only:
            return float(np.sum(self.flux_lm[self.alive]))
        return float(np.sum(self.flux_lm))

    def copy(self) -> "RayBundle":
        return RayBundle(
            self.origins_mm.copy(),
            self.directions.copy(),
            self.flux_lm.copy(),
            self.alive.copy() if self.alive is not None else None,
        )

    def subset(self, indices: np.ndarray | slice) -> "RayBundle":
        return RayBundle(
            self.origins_mm[indices].copy(),
            self.directions[indices].copy(),
            self.flux_lm[indices].copy(),
            self.alive[indices].copy() if self.alive is not None else None,
        )

    def preview(self, max_count: int) -> "RayBundle":
        if self.count <= max_count:
            return self.copy()
        step = max(1, self.count // max_count)
        return self.subset(slice(0, self.count, step))

