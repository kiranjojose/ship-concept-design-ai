"""Candidate hulls derived from the reference offsets (Table 3.2).

A candidate is built in two steps, so that its form coefficients come from its own
geometry and are never assumed:

1. Affine scaling: x by L/LPP_ref, y by B/B_ref, z by D/D_ref. The offset table runs
   from base to main deck, so scaling z with depth keeps the deck at D and leaves the
   draught T free. CB therefore changes with T/D even before step 2.
2. Lackenby's "1 - CP" station shift [L50], applied with the same parameter k to the
   fore and aft halves. In normalised half-length coordinates (x' = 0 at midship,
   1 at the perpendicular) each station moves to x' + (1 - x') k. For k > 0 this adds
   parallel middle body; for k < 0 it removes it. The midship section and the end
   stations are unchanged, so CM is preserved and CP changes by k (1 - CP_half).

k is solved so that the CB integrated from the candidate's offsets at its draught
equals the sampled target. The CB that is reported is the integrated one.

[L50] H. Lackenby, "On the systematic geometrical variation of ship forms",
      Trans. INA 92, 1950, 289-316.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq

from .offsets import OffsetTable

K_MIN, K_MAX = -0.35, 0.45   # search range for the Lackenby parameter


def scale_hull(hull: OffsetTable, L: float, B: float, D: float, D_ref: float) -> OffsetTable:
    """Affine scaling. B is the moulded beam (twice the largest half-breadth)."""
    sx = L / hull.lpp
    sy = B / (2.0 * hull.max_half_breadth)
    sz = D / D_ref
    return OffsetTable(x=hull.x * sx, z=hull.z * sz, y=hull.y * sy, lpp=L)


def _section_at(hull: OffsetTable, x: float) -> np.ndarray:
    """Half-breadths at longitudinal position x (PCHIP along each table waterline)."""
    return np.clip(PchipInterpolator(hull.x, hull.y, axis=0)(x), 0.0, None)


def lackenby_shift(hull: OffsetTable, k: float) -> OffsetTable:
    """1 - CP station shift with the same k fore and aft (see module docstring)."""
    if k == 0.0:
        return hull
    if not -0.9 < k < 0.9:
        raise ValueError(f"k={k} outside (-0.9, 0.9)")
    half = hull.lpp / 2.0
    xm = half
    xs, ys = [], []
    for side in (-1.0, 1.0):          # aft, fore
        sel = (hull.x - xm) * side >= -1e-9
        xp = np.abs(hull.x[sel] - xm) / half          # x' in [0, 1]
        xn = xp + (1.0 - xp) * k
        keep = xn > 1e-9
        for xi, yi in zip(xm + side * xn[keep] * half, hull.y[sel][keep]):
            xs.append(xi)
            ys.append(yi)
        if k > 0:
            # parallel middle body: the midship section is copied to the new ends of the PMB
            xs.append(xm + side * k * half)
            ys.append(_section_at(hull, xm))
    if k < 0:
        # stations nearest midship crossed over; midship gets the section that maps to x' = 0
        src = -k / (1.0 - k)
        mid = 0.5 * (_section_at(hull, xm - src * half) + _section_at(hull, xm + src * half))
        xs.append(xm)
        ys.append(mid)
    order = np.argsort(xs)
    x = np.asarray(xs)[order]
    y = np.asarray(ys)[order]
    # duplicate positions (midship counted from both halves) are merged
    uniq, idx = np.unique(np.round(x, 9), return_index=True)
    return OffsetTable(x=x[idx], z=hull.z, y=y[idx], lpp=hull.lpp)


@dataclass
class CandidateHull:
    hull: OffsetTable
    k: float
    cb_target: float
    cb_achieved: float
    converged: bool
    note: str = ""


def build_candidate_hull(parent: OffsetTable, L: float, B: float, D: float, T: float,
                         cb_target: float, D_ref: float, cb_tol: float = 1e-4) -> CandidateHull:
    """Scale the parent, then solve the Lackenby k for cb_target at draught T.

    If cb_target is outside what the shift can reach in [K_MIN, K_MAX], the hull at the
    nearer bound is returned with converged=False, so the candidate can be recorded as
    'geometry not realisable' instead of silently using a different CB."""
    from ..hydrostatics import compute_hydrostatics
    if not 0 < T < D:
        raise ValueError(f"draught {T} must be between 0 and depth {D}")
    base = scale_hull(parent, L, B, D, D_ref)

    def cb_of(k, fine=False):
        kw = {} if fine else {"nx": 401, "nz": 81}
        return compute_hydrostatics(lackenby_shift(base, k), T, **kw).cb

    lo, hi = cb_of(K_MIN), cb_of(K_MAX)
    if not lo <= cb_target <= hi:
        k = K_MIN if cb_target < lo else K_MAX
        return CandidateHull(lackenby_shift(base, k), k, cb_target, cb_of(k, True), False,
                             f"CB target outside reachable range {lo:.4f}-{hi:.4f}")
    k = brentq(lambda kk: cb_of(kk) - cb_target, K_MIN, K_MAX, xtol=1e-6)
    hull = lackenby_shift(base, k)
    cb = cb_of(k, True)
    return CandidateHull(hull, k, cb_target, cb, abs(cb - cb_target) <= cb_tol + 5e-4)
