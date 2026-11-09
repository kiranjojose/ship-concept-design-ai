"""Hull geometry rebuilt from a table of offsets (half-breadths).

The reference hull is REPORT Table 3.2 (p.49-50): faired half-breadths at stations
0..20 (AP..FP, spacing LBP/20) and at labelled BSRA waterlines.

Assumption A7 (docs/missing_data_register.md): the report gives a waterline spacing
of 2.6 m (p.48) but not the height of each labelled waterline. Heights below are
WL_n = 2.6 * n m, LWL = design draught 14.29 m and MDK = depth 19.75 m.

The offsets stop at AP and FP: the transom overhang aft of AP and any bulb nose
forward of FP are not described, so they are not modelled.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

WL_SPACING_M = 2.6  # REPORT p.48
WATERLINE_HEIGHTS_M = {
    "wl_0": 0.0,
    "wl_0.5": 0.5 * WL_SPACING_M,
    "wl_1": 1.0 * WL_SPACING_M,
    "wl_1.5": 1.5 * WL_SPACING_M,
    "wl_2": 2.0 * WL_SPACING_M,
    "wl_3": 3.0 * WL_SPACING_M,
    "wl_4": 4.0 * WL_SPACING_M,
    "wl_5": 5.0 * WL_SPACING_M,
    "wl_LWL": 14.29,   # design draught, REPORT Table 2.4
    "wl_6": 6.0 * WL_SPACING_M,
    "wl_7": 7.0 * WL_SPACING_M,
    "wl_MDK": 19.75,   # moulded depth, REPORT Table 2.4
}

_ROOT = Path(__file__).resolve().parents[3]
REFERENCE_OFFSETS_CSV = _ROOT / "data" / "reference" / "faired_offsets_table_3_2.csv"


@dataclass
class OffsetTable:
    """Half-breadths y[i, j] at x[i] (m from AP, positive forward) and z[j] (m above base)."""

    x: np.ndarray
    z: np.ndarray
    y: np.ndarray
    lpp: float

    def __post_init__(self):
        self.x = np.asarray(self.x, float)
        self.z = np.asarray(self.z, float)
        self.y = np.asarray(self.y, float)
        if self.y.shape != (self.x.size, self.z.size):
            raise ValueError("y must have shape (len(x), len(z))")
        if np.any(np.diff(self.x) <= 0) or np.any(np.diff(self.z) <= 0):
            raise ValueError("x and z must be strictly increasing")
        if np.any(self.y < 0):
            raise ValueError("half-breadths must be non-negative")

    @property
    def max_half_breadth(self) -> float:
        return float(self.y.max())

    def dense_grid(self, draught: float, nz: int = 241, nx: int = 801, interp: str = "pchip"):
        """Return (x, z, Y) with Y[i, j] the half-breadth on a fine grid up to `draught`.

        Shape-preserving (PCHIP) interpolation first vertically on each station, then
        longitudinally on each fine waterline. PCHIP never overshoots, so it does not
        create bumps between offsets. interp="linear" (piecewise-linear in both
        directions) is kept as a lower-fullness alternative for sensitivity studies.
        """
        if interp not in ("pchip", "linear"):
            raise ValueError(interp)
        if not 0 < draught <= self.z[-1] + 1e-9:
            raise ValueError(f"draught {draught} outside offset table 0..{self.z[-1]}")
        zf = np.linspace(0.0, draught, nz)
        ys = np.empty((self.x.size, nz))
        xf = np.linspace(self.x[0], self.x[-1], nx)
        if interp == "linear":
            for i in range(self.x.size):
                ys[i] = np.interp(zf, self.z, self.y[i])
            Y = np.array([np.interp(xf, self.x, ys[:, j]) for j in range(nz)]).T
            return xf, zf, np.clip(Y, 0.0, None)
        for i in range(self.x.size):
            ys[i] = PchipInterpolator(self.z, self.y[i])(zf)
        Y = PchipInterpolator(self.x, ys, axis=0)(xf)
        return xf, zf, np.clip(Y, 0.0, None)


def load_offsets_csv(path: Path, lpp: float, waterline_heights: dict[str, float] | None = None) -> OffsetTable:
    wl = waterline_heights or WATERLINE_HEIGHTS_M
    df = pd.read_csv(path, comment="#")
    cols = [c for c in df.columns if c != "station"]
    missing = [c for c in cols if c not in wl]
    if missing:
        raise KeyError(f"no height for waterline columns {missing}")
    cols = sorted(cols, key=lambda c: wl[c])
    x = df["station"].to_numpy(float) * lpp / 20.0
    z = np.array([wl[c] for c in cols])
    return OffsetTable(x=x, z=z, y=df[cols].to_numpy(float), lpp=lpp)


def load_reference_offsets(lpp: float = 220.5) -> OffsetTable:
    """Reference hull, REPORT Table 3.2, with assumption A7 for waterline heights."""
    return load_offsets_csv(REFERENCE_OFFSETS_CSV, lpp)
