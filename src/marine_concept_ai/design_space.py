"""Evaluate one design candidate (L, B, T, CB target) with a common geometry and weight model.

Every candidate goes through the same chain, so candidates and the reference are
compared on one basis:

  geometry   reference offsets -> scale (L, B, D) -> Lackenby shift to the CB target
             (geometry.transform). CB, CM, CWP, LCB, KM, S are integrated from the hull.
  depth      D = L / 11.165 (reference L/D). D is not a free variable in Sprint 2.
  weight     Watson-Gilfillan as in REPORT Table 2.3 (weights.watson_gilfillan), with the
             candidate's integrated CB and displacement.
  deadweight displacement (moulded volume x 1.025 x 1.006) - lightship, for every
             combination of geometry scenario x weight scenario.
  checks     constraints.check_design; a check that cannot be made is UNKNOWN.
  power      Holtrop-Mennen PE (both versions) as an INDICATOR only. It is not used to
             rank or filter candidates until the p.170 benchmark is closed.

Assumptions introduced in Sprint 2 (also in docs/design_space_sprint2.md):
  S2-A1  D = L / 11.165, so freeboard D - T and the steel numeral follow L and T.
  S2-A2  required freeboard 5.00 m (the reference ILLC result) is used for all candidates.
  S2-A3  KG = 10.70 m x D / 19.75 (Table 7.2 full-load KG scaled with depth).
  S2-A4  hold volume = 74 177 m3 x (moulded volume to D) / (reference moulded volume to D).
  S2-A5  stores 899.91 t (p.94) for every candidate, so cargo = DWT - 899.91 t.
  S2-A6  transom area AT = 10.0 m2 x (B/B_ref)(T/T_ref); iE from the Holtrop regression.
"""
from __future__ import annotations

import math
from functools import lru_cache

import numpy as np

from .constraints import check_design, summarise
from .geometry import build_candidate_hull
from .hydrostatics import compute_hydrostatics, section_properties
from .propulsion import PoweringAssumptions, power_chain
from .reference import LPP, T_DESIGN, appendage_estimate, reference_hull
from .resistance import HoltropInput, holtrop_mennen, holtrop_validity
from .weights import WEIGHT_SCENARIOS, lightship_watson_gilfillan

D_REF = 19.75
L_OVER_D = LPP / D_REF                 # 11.165
KG_REF, KG_SOURCE = 10.70, "REPORT Table 7.2 full-load departure"
HOLD_VOLUME_REF_M3 = 74177.11          # sum of Table 6.2 (DISC-10)
STORES_T = 899.91                      # REPORT p.94
DWT_REQUIRED_T = 75000.0
AT_REF_M2 = 10.0                       # inverted from NavCad RTR (Sprint 1, MISS-08)
SPEED_KN = 13.0
GEOMETRY_SCENARIOS = ("pchip", "linear")
ETA_D = {"historical": 0.60, "sensitivity": 0.781}
SEA_MARGINS = (0.0, 0.10, 0.15, 0.20, 0.25)


@lru_cache(maxsize=1)
def _reference_underdeck_volume():
    return compute_hydrostatics(reference_hull(), D_REF).volume_m3


@lru_cache(maxsize=1)
def reference_beam():
    return 2.0 * reference_hull().max_half_breadth


def depth_for(L: float) -> float:
    return L / L_OVER_D


def evaluate_candidate(L: float, B: float, T: float, cb_target: float, *, holtrop: bool = True) -> dict:
    D = depth_for(L)
    row = {"lpp_m": L, "breadth_m": B, "draught_m": T, "cb_target": cb_target, "depth_m": D}
    ch = build_candidate_hull(reference_hull(), L, B, D, T, cb_target, D_REF)
    row.update(lackenby_k=ch.k, geometry_ok=ch.converged, geometry_note=ch.note)

    hyd = {g: compute_hydrostatics(ch.hull, T, interp=g) for g in GEOMETRY_SCENARIOS}
    h = hyd["pchip"]
    row.update(cb=h.cb, cb_length_basis=h.length_basis, cm=h.cm, cp=h.cp, cwp=h.cwp,
               lcb_pct=(h.lcb_m_from_ap - L / 2) / L * 100, kmt_m=h.kmt_m,
               wetted_surface_m2=h.wetted_surface_m2, tpc=h.tpc_t_per_cm)

    dwt = {}
    for g, hg in hyd.items():
        row[f"disp_{g}_t"] = hg.displacement_shell_t
        for w in WEIGHT_SCENARIOS:
            ls = lightship_watson_gilfillan(L, B, D, T, h.cb, hg.displacement_shell_t, w)
            if g == "pchip":
                row[f"lightship_{w}_t"] = ls.lightship_t
            dwt[(g, w)] = hg.displacement_shell_t - ls.lightship_t
            row[f"dwt_{g}_{w}_t"] = dwt[(g, w)]
    nominal = dwt[("pchip", "nominal")]
    worst, best = min(dwt.values()), max(dwt.values())
    row.update(dwt_nominal_t=nominal, dwt_worst_t=worst, dwt_best_t=best,
               dwt_margin_nominal_t=nominal - DWT_REQUIRED_T,
               dwt_margin_worst_t=worst - DWT_REQUIRED_T,
               dwt_margin_best_t=best - DWT_REQUIRED_T)
    row["dwt_verdict"] = ("robust" if worst >= DWT_REQUIRED_T else
                          "nominal_only" if nominal >= DWT_REQUIRED_T else
                          "best_case_only" if best >= DWT_REQUIRED_T else "short")

    hold = HOLD_VOLUME_REF_M3 * compute_hydrostatics(ch.hull, D).volume_m3 / _reference_underdeck_volume()
    kg = KG_REF * D / D_REF
    checks = check_design(dict(
        draught_m=T, breadth_m=B, depth_m=D, loa_m=None,
        displacement_t=h.displacement_shell_t, lightship_t=row["lightship_nominal_t"],
        km_m=h.kmt_m, kg_m=kg, kg_note=f"S2-A3: KG {kg:.2f} m scaled from {KG_SOURCE}",
        hold_volume_m3=hold, cargo_mass_t=nominal - STORES_T))
    summ = summarise(checks)
    row.update(hold_volume_m3=hold, kg_m=kg, gm_m=h.kmt_m - kg, freeboard_m=D - T,
               status=summ["status"] if ch.converged else "geometry_not_realisable",
               n_failed=summ["n_failed"], failed="; ".join(summ["failed"]),
               unknown="; ".join(summ["unknown"]))
    for c in checks:
        row[f"margin::{c.name}"] = c.margin
    other_fails = [n for n in summ["failed"] if not n.startswith("deadweight")]
    row["fails_other_than_dwt"] = "; ".join(other_fails)

    if holtrop:
        row.update(_holtrop_indicator(ch.hull, L, B, T, h))
    return row


def _holtrop_indicator(hull, L, B, T, h) -> dict:
    abt, hb = section_properties(hull, hull.x[-1], T)
    at = AT_REF_M2 * (B / reference_beam()) * (T / T_DESIGN)
    s_app, k2, _ = appendage_estimate(L, T, B)
    p = HoltropInput(L=L, B=h.beam_wl_m, T=T, volume=h.volume_m3, lcb_pct=(h.lcb_m_from_ap - L / 2) / L * 100,
                     cm=h.cm, cwp=h.cwp, S=h.wetted_surface_m2, abt=abt, hb=hb, at=at, ie_deg=None,
                     s_app=s_app, k2_app=k2)
    out = {"holtrop_out_of_range": "; ".join(k for k, v in holtrop_validity(p, SPEED_KN).items()
                                             if not v["inside"])}
    for ver in ("1982", "1984"):
        r = holtrop_mennen(p, SPEED_KN, version=ver)
        out[f"pe_indicator_{ver}_kw"] = r.pe_w / 1000
    return out


def power_grid(pe_kw: float) -> list[dict]:
    """MCR for each eta_D scenario x sea margin, with REPORT eta_S 0.97 and 85 % MCR."""
    rows = []
    for label, eta in ETA_D.items():
        for sm in SEA_MARGINS:
            pc = power_chain(pe_kw, PoweringAssumptions(eta_d=eta, sea_margin=sm))
            rows.append({"eta_d_scenario": label, "eta_d": eta, "sea_margin": sm, "mcr_kw": pc.mcr_kw})
    return rows
