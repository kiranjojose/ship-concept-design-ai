"""Upright, even-keel hydrostatics and wetted surface from an offset table.

Integration is done on a fine PCHIP-interpolated grid (see OffsetTable.dense_grid)
with the trapezoidal rule. Longitudinal positions are measured from AP, positive
forward. Moulded quantities unless stated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd
from scipy.integrate import trapezoid

from ..geometry.offsets import OffsetTable
from ..units import RHO_SW, SHELL_FACTOR


@dataclass
class Hydrostatics:
    draught_m: float
    volume_m3: float              # moulded
    displacement_t: float         # rho * volume (no shell factor), comparable to Table 3.4
    displacement_shell_t: float   # rho * volume * 1.006, comparable to the design equation
    lcb_m_from_ap: float
    kb_m: float
    waterplane_area_m2: float
    lcf_m_from_ap: float
    bmt_m: float
    bml_m: float
    kmt_m: float
    tpc_t_per_cm: float
    mct_t_m_per_cm: float
    beam_wl_m: float
    midship_area_m2: float
    cb: float                     # on LPP and waterline beam
    cm: float
    cp: float
    cwp: float
    wetted_surface_m2: float      # bare hull, excludes transom face
    length_basis: str = "LPP"     # length used for cb, cp, cwp and MCT
    length_m: float = 0.0

    def as_dict(self):
        return asdict(self)


def _surface_area(x, z, Y):
    """Area of the half-hull surface (x, Y(x,z), z) by triangulating the grid."""
    P = np.stack(np.broadcast_arrays(x[:, None], Y, z[None, :]), axis=-1)
    a, b, c, d = P[:-1, :-1], P[1:, :-1], P[1:, 1:], P[:-1, 1:]
    t1 = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=-1)
    t2 = 0.5 * np.linalg.norm(np.cross(c - a, d - a), axis=-1)
    # cells lying on the centreplane (all four half-breadths ~0) are not hull surface
    on_cl = (Y[:-1, :-1] < 1e-6) & (Y[1:, :-1] < 1e-6) & (Y[1:, 1:] < 1e-6) & (Y[:-1, 1:] < 1e-6)
    return float(np.sum(np.where(on_cl, 0.0, t1 + t2)))


def compute_hydrostatics(hull: OffsetTable, draught: float, rho: float = RHO_SW,
                         nz: int = 241, nx: int = 801, interp: str = "pchip") -> Hydrostatics:
    x, z, Y = hull.dense_grid(draught, nz=nz, nx=nx, interp=interp)
    rho_t = rho / 1000.0

    area = 2.0 * trapezoid(Y, z, axis=1)              # section areas A(x)
    zmom = 2.0 * trapezoid(Y * z[None, :], z, axis=1)
    vol = float(trapezoid(area, x))
    lcb = float(trapezoid(area * x, x) / vol)
    kb = float(trapezoid(zmom, x) / vol)

    yw = Y[:, -1]
    awp = float(2.0 * trapezoid(yw, x))
    lcf = float(2.0 * trapezoid(yw * x, x) / awp)
    it = float(2.0 / 3.0 * trapezoid(yw ** 3, x))
    il = float(2.0 * trapezoid(yw * x ** 2, x) - awp * lcf ** 2)
    bmt, bml = it / vol, il / vol

    beam = float(2.0 * yw.max())
    a_mid = float(np.interp(hull.lpp / 2.0, x, area))
    L = hull.lpp
    cb = vol / (L * beam * draught)
    cm = a_mid / (beam * draught)
    disp = rho_t * vol

    s = 2.0 * (_surface_area(x, z, Y) + trapezoid(Y[:, 0], x))  # sides + flat of bottom

    return Hydrostatics(
        draught_m=draught,
        volume_m3=vol,
        displacement_t=disp,
        displacement_shell_t=disp * SHELL_FACTOR,
        lcb_m_from_ap=lcb,
        kb_m=kb,
        waterplane_area_m2=awp,
        lcf_m_from_ap=lcf,
        bmt_m=bmt,
        bml_m=bml,
        kmt_m=kb + bmt,
        tpc_t_per_cm=rho_t * awp / 100.0,
        mct_t_m_per_cm=disp * bml / (100.0 * L),
        beam_wl_m=beam,
        midship_area_m2=a_mid,
        cb=cb,
        cm=cm,
        cp=cb / cm,
        cwp=awp / (L * beam),
        wetted_surface_m2=float(s),
        length_basis="LPP",
        length_m=L,
    )


def convergence_study(hull: OffsetTable, draught: float,
                      grids=((101, 31), (201, 61), (401, 121), (801, 241), (1601, 481))) -> pd.DataFrame:
    """Numerical convergence of the integration with grid refinement (nx, nz).
    Differences are relative to the finest grid. This checks the numerics only, not
    the agreement with the report."""
    rows = []
    for nx, nz in grids:
        h = compute_hydrostatics(hull, draught, nx=nx, nz=nz)
        rows.append({"nx": nx, "nz": nz, "volume_m3": h.volume_m3, "kb_m": h.kb_m, "bmt_m": h.bmt_m,
                     "lcb_m_from_ap": h.lcb_m_from_ap, "wetted_surface_m2": h.wetted_surface_m2})
    df = pd.DataFrame(rows)
    for c in ("volume_m3", "kb_m", "bmt_m", "wetted_surface_m2"):
        df[c + "_rel_to_finest"] = df[c] / df[c].iloc[-1] - 1
    return df


def hydrostatic_table(hull: OffsetTable, draughts, **kw) -> pd.DataFrame:
    return pd.DataFrame([compute_hydrostatics(hull, float(t), **kw).as_dict() for t in draughts])


def section_properties(hull: OffsetTable, x_m: float, draught: float, nz: int = 241):
    """Immersed area (both sides, m2) and centroid height above base (m) of one section."""
    _, z, Y = hull.dense_grid(draught, nz=nz, nx=max(2, hull.x.size))
    from scipy.interpolate import PchipInterpolator
    ys = np.array([PchipInterpolator(hull.z, hull.y[i])(z) for i in range(hull.x.size)])
    y = np.clip(PchipInterpolator(hull.x, ys, axis=0)(x_m), 0.0, None)
    area = float(2.0 * trapezoid(y, z))
    zc = float(2.0 * trapezoid(y * z, z) / area) if area > 0 else 0.0
    return area, zc
