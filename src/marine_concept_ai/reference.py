"""The reference bulk carrier as engine inputs.

Two Holtrop input sets are built, so that differences can be traced:

  * `navcad_inputs()`  - the inputs printed on REPORT p.60 (LWL = LBP = 220.5 m,
    B = 32.7809, T = 14.29115, CB = 0.83, S = 11356.43 m2, CWP 0.894) plus the
    reported CM (0.992) and iE (38.55 deg, p.21). NavCad inputs that were not
    printed (LCB, bulb, transom, appendages) are taken from the rebuilt hull.
  * `rebuilt_hull_inputs()` - every geometric input computed from the offset table
    (Table 3.2) at the design draught. Nothing taken from the report except
    L, T and iE.

Every value that is not printed in the report is listed in `notes` with its origin.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import yaml

from .geometry import load_reference_offsets
from .hydrostatics import compute_hydrostatics, section_properties
from .resistance import HoltropInput

ROOT = Path(__file__).resolve().parents[2]
REFERENCE_YAML = ROOT / "configs" / "reference_bulk_carrier.yaml"

LPP = 220.5
T_DESIGN = 14.29
V_SERVICE_KN = 13.0
IE_REPORT_DEG = 38.55          # REPORT p.21 (2.15), BSRA charts
D_PROP_MAX_M = 9.4             # REPORT p.66, max diameter = 2/3 T (diameter itself not fixed, DISC-09)


@lru_cache(maxsize=1)
def reference_yaml() -> dict:
    return yaml.safe_load(REFERENCE_YAML.read_text())


@lru_cache(maxsize=1)
def reference_hull():
    return load_reference_offsets(LPP)


@lru_cache(maxsize=1)
def design_hydrostatics():
    return compute_hydrostatics(reference_hull(), T_DESIGN)


def appendage_estimate(L: float, T: float, B: float) -> tuple[float, float, str]:
    """Rudder only: area from the DNV guideline A = T L/100 (1 + 25 (B/L)^2),
    wetted area = 2 A, (1+k2) = 1.5 (rudder behind stern, [H82] Table 2).
    ASSUMPTION A9: the report's appendage list (NavCad Rapp 20.8 kN) is not printed."""
    a = T * L / 100.0 * (1 + 25 * (B / L) ** 2)
    return 2 * a, 1.5, "A9: rudder only, DNV area guideline, (1+k2)=1.5"


def _derived_from_hull(L, T):
    hull = reference_hull()
    h = design_hydrostatics()
    abt, hb = section_properties(hull, hull.x[-1], T)
    at, _ = section_properties(hull, hull.x[0], T)
    lcb_pct = (h.lcb_m_from_ap - L / 2) / L * 100
    return h, abt, hb, at, lcb_pct


NAVCAD_RTR_13KN_N = 11.35e3   # REPORT Table 4.2, transom resistance at 13 kn


def transom_area_matching(rtr_n: float, speed_kn: float, B: float, cwp: float, rho: float = 1025.0) -> float:
    """Immersed transom area AT (m2) for which the [H84] transom term gives `rtr_n`.

    Used to recover the unprinted NavCad AT from the printed RTR (MISS-08). This is an
    inversion of a reported value, not a measurement; it is flagged wherever used.
    """
    from scipy.optimize import brentq
    from .units import G
    V = speed_kn * 1852 / 3600

    def rtr(at):
        fnt = V / math.sqrt(2 * G * at / (B + B * cwp))
        c6 = 0.2 * (1 - 0.2 * fnt) if fnt < 5 else 0.0
        return 0.5 * rho * V ** 2 * at * c6 - rtr_n

    # rtr(at) rises monotonically from 0 once FnT < 5; search above that threshold
    at_min = (V / 5) ** 2 * (B + B * cwp) / (2 * G) * 1.0001  # FnT = 5
    return brentq(rtr, at_min, 200.0)


def navcad_inputs(at_source: str = "navcad_rtr") -> HoltropInput:
    """at_source: "navcad_rtr" (AT inverted from Table 4.2 RTR), "station0" (rebuilt hull
    section at AP, an upper bound), or "zero" (dry transom)."""
    L, B, T = 220.5, 32.7809, 14.29115
    h, abt, hb, at_st0, lcb_pct = _derived_from_hull(LPP, T_DESIGN)
    at, at_note = _transom(at_source, at_st0, B, 0.894)
    s_app, k2, app_note = appendage_estimate(L, T, B)
    return HoltropInput(
        L=L, B=B, T=T, volume=0.83 * L * B * T, lcb_pct=lcb_pct, cm=0.992, cwp=0.894,
        S=11356.43, abt=abt, hb=hb, at=at, ie_deg=IE_REPORT_DEG, s_app=s_app, k2_app=k2,
        notes={
            "printed (p.60)": "L, B, T, CB, S, CWP",
            "cm": "REPORT p.20 (0.9+0.1CB)",
            "ie_deg": "REPORT p.21",
            "lcb_pct": f"rebuilt hull, LCB {h.lcb_m_from_ap:.2f} m from AP (MISS-08)",
            "abt, hb": "rebuilt hull, immersed section at FP (station 20)",
            "at": at_note,
            "appendages": app_note,
            "c_stern": "0 (normal section), assumption A10",
        },
    )


def _transom(at_source, at_st0, B, cwp):
    if at_source == "navcad_rtr":
        at = transom_area_matching(NAVCAD_RTR_13KN_N, 13.0, B, cwp)
        return at, f"AT={at:.2f} m2 inverted from REPORT Table 4.2 RTR at 13 kn (MISS-08)"
    if at_source == "station0":
        return at_st0, f"AT={at_st0:.2f} m2 = rebuilt-hull section at AP (upper bound; real transom is aft of AP)"
    if at_source == "zero":
        return 0.0, "AT=0 (dry transom)"
    raise ValueError(at_source)


def rebuilt_hull_inputs(at_source: str = "navcad_rtr") -> HoltropInput:
    L, T = LPP, T_DESIGN
    h, abt, hb, at_st0, lcb_pct = _derived_from_hull(L, T)
    B = h.beam_wl_m
    at, at_note = _transom(at_source, at_st0, B, h.cwp)
    s_app, k2, app_note = appendage_estimate(L, T, B)
    return HoltropInput(
        L=L, B=B, T=T, volume=h.volume_m3, lcb_pct=lcb_pct, cm=h.cm, cwp=h.cwp,
        S=h.wetted_surface_m2, abt=abt, hb=hb, at=at, ie_deg=IE_REPORT_DEG,
        s_app=s_app, k2_app=k2,
        notes={
            "geometry": "all from offsets Table 3.2 at T=14.29 m (A7 waterline heights)",
            "L": "LBP used as waterline length (offsets stop at AP/FP)",
            "ie_deg": "REPORT p.21",
            "abt, hb": "rebuilt hull, immersed section at FP (station 20)",
            "at": at_note,
            "appendages": app_note,
            "c_stern": "0 (normal section), assumption A10",
        },
    )
