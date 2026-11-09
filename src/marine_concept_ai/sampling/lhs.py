"""Latin-hypercube sampling of the four free design variables (L, B, T, CB)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.stats import qmc

DESIGN_VARIABLES = ("lpp_m", "breadth_m", "draught_m", "block_coefficient")
ROOT = Path(__file__).resolve().parents[3]
DESIGN_SPACE_YAML = ROOT / "configs" / "design_space.yaml"


def load_design_space(path: Path = DESIGN_SPACE_YAML) -> dict:
    cfg = yaml.safe_load(Path(path).read_text())
    ds = cfg["design_space"]
    for v in DESIGN_VARIABLES:
        lo, hi = ds[v].get("min"), ds[v].get("max")
        if lo is None or hi is None:
            raise ValueError(f"bounds for {v} are not set in {path}")
        if not lo < hi:
            raise ValueError(f"{v}: min {lo} must be below max {hi}")
    return cfg


def latin_hypercube(bounds: dict, n: int, seed: int) -> pd.DataFrame:
    """n points, one column per design variable, scaled to [min, max]. Reproducible from seed."""
    if n < 1:
        raise ValueError("n must be >= 1")
    lo = np.array([bounds[v]["min"] for v in DESIGN_VARIABLES], float)
    hi = np.array([bounds[v]["max"] for v in DESIGN_VARIABLES], float)
    u = qmc.LatinHypercube(d=len(DESIGN_VARIABLES), seed=seed).random(n)
    return pd.DataFrame(qmc.scale(u, lo, hi), columns=list(DESIGN_VARIABLES))


def random_uniform(bounds: dict, n: int, seed: int) -> pd.DataFrame:
    """n independent uniform points (baseline for comparing with the Latin hypercube)."""
    if n < 1:
        raise ValueError("n must be >= 1")
    rng = np.random.default_rng(seed)
    lo = np.array([bounds[v]["min"] for v in DESIGN_VARIABLES], float)
    hi = np.array([bounds[v]["max"] for v in DESIGN_VARIABLES], float)
    return pd.DataFrame(lo + rng.random((n, len(lo))) * (hi - lo), columns=list(DESIGN_VARIABLES))


def full_grid(bounds: dict, levels: int | dict) -> pd.DataFrame:
    """Full-factorial grid with `levels` points per variable (int, or dict per variable)."""
    lv = {v: (levels[v] if isinstance(levels, dict) else levels) for v in DESIGN_VARIABLES}
    if any(n < 2 for n in lv.values()):
        raise ValueError("need at least 2 levels per variable")
    axes = [np.linspace(bounds[v]["min"], bounds[v]["max"], lv[v]) for v in DESIGN_VARIABLES]
    mesh = np.meshgrid(*axes, indexing="ij")
    return pd.DataFrame({v: m.ravel() for v, m in zip(DESIGN_VARIABLES, mesh)})
