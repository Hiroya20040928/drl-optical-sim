from __future__ import annotations

from dataclasses import fields
import json
from pathlib import Path
from typing import Any

from .sampler import SimulationConfig


def load_simulation_config(path: str | Path) -> SimulationConfig:
    """Load a SimulationConfig from a saved simulator JSON file.

    The GUI/report writer stores a top-level object with a ``config`` member,
    while hand-written files may contain the config object directly. Unknown
    keys are ignored so older saved files remain reproducible after new fields
    are added.
    """
    payload: Any = json.loads(Path(path).read_text(encoding="utf-8"))
    data = payload.get("config", payload) if isinstance(payload, dict) else payload
    if not isinstance(data, dict):
        raise ValueError("simulation config JSON must contain an object")

    valid_fields = {field.name for field in fields(SimulationConfig)}
    filtered = {key: value for key, value in data.items() if key in valid_fields}
    return SimulationConfig(**filtered)
