"""Preliminary-design feasibility checks.

Each check returns value, limit, margin (positive = satisfied) and the source of the
limit. Limits come from the REPORT's owner requirements and rule checks; none are
invented. Where the report gives no limit, the check is not made.

These are concept-stage screens, not class approval:
  * port limits are compared with draught/beam directly (no under-keel clearance is
    given in the report, so none is applied);
  * freeboard uses the report's own ILLC Type B-60 result, not a new ILLC calculation;
  * GM uses KM from hydrostatics and a KG supplied by the caller.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

REFERENCE_LIMITS = {
    "bhorsagar_depth_m": (16.41, "REPORT p.9"),
    "hay_point_max_draught_m": (17.6, "REPORT p.9"),
    "hay_point_max_beam_m": (53.0, "REPORT p.9"),
    "hay_point_max_loa_m": (300.0, "REPORT p.9"),
    "required_freeboard_m": (5.00001, "REPORT p.43-44, ILLC Type B-60 (depth correction used D=18.23, DISC-04)"),
    "deadweight_t": (75000.0, "REPORT p.8 owner requirement"),
    "gm_min_m": (0.15, "IMO IS Code 2008, Part A 2.2.4 (criterion listed REPORT p.106)"),
    "stowage_factor_m3_per_t": (0.98, "REPORT p.8, oats (rice 0.95)"),
}


@dataclass
class ConstraintResult:
    name: str
    value: float | None
    limit: float
    sense: str          # "<=" or ">="
    margin: float | None
    satisfied: bool | None
    source: str
    note: str = ""

    def as_dict(self):
        return asdict(self)


def _c(name, value, limit, sense, source, note=""):
    if value is None:
        return ConstraintResult(name, None, limit, sense, None, None, source, note or "input missing")
    margin = (limit - value) if sense == "<=" else (value - limit)
    return ConstraintResult(name, value, limit, sense, margin, margin >= 0, source, note)


def check_design(d: dict, limits: dict | None = None) -> list[ConstraintResult]:
    """d keys (SI, t, m): draught_m, breadth_m, depth_m, loa_m (may be None),
    displacement_t, lightship_t, km_m, kg_m (may be None), hold_volume_m3, cargo_mass_t."""
    lim = {**REFERENCE_LIMITS, **(limits or {})}
    v = lambda k: lim[k][0]
    s = lambda k: lim[k][1]
    for k in ("draught_m", "breadth_m", "depth_m"):
        if d.get(k) is None:
            raise ValueError(f"{k} is required")
    out = [
        _c("draught vs Bhorsagar depth", d["draught_m"], v("bhorsagar_depth_m"), "<=", s("bhorsagar_depth_m"),
           "no under-keel clearance applied"),
        _c("draught vs Hay Point", d["draught_m"], v("hay_point_max_draught_m"), "<=", s("hay_point_max_draught_m")),
        _c("beam vs Hay Point", d["breadth_m"], v("hay_point_max_beam_m"), "<=", s("hay_point_max_beam_m")),
        _c("LOA vs Hay Point", d.get("loa_m"), v("hay_point_max_loa_m"), "<=", s("hay_point_max_loa_m"),
           "" if d.get("loa_m") is not None else "LOA not in report (MISS-09)"),
        _c("freeboard D-T", d["depth_m"] - d["draught_m"], v("required_freeboard_m"), ">=", s("required_freeboard_m")),
        _c("deadweight = displacement - lightship",
           None if d.get("displacement_t") is None or d.get("lightship_t") is None
           else d["displacement_t"] - d["lightship_t"], v("deadweight_t"), ">=", s("deadweight_t")),
    ]
    gm = None if d.get("kg_m") is None else d["km_m"] - d["kg_m"]
    out.append(_c("GM0 (KM - KG)", gm, v("gm_min_m"), ">=", s("gm_min_m"), d.get("kg_note", "")))
    sf = None
    if d.get("hold_volume_m3") is not None and d.get("cargo_mass_t"):
        sf = d["hold_volume_m3"] / d["cargo_mass_t"]
    out.append(_c("hold volume / cargo mass", sf, v("stowage_factor_m3_per_t"), ">=", s("stowage_factor_m3_per_t")))
    return out


def summarise(results: list[ConstraintResult]) -> dict:
    """Tri-state feasibility. A check that could not be evaluated (missing input) is
    UNKNOWN, never a pass:
      status "fail"    if any evaluated check fails (feasible = False)
      status "unknown" if none fails but at least one is unknown (feasible = None)
      status "pass"    only if every check was evaluated and passed (feasible = True)
    """
    failed = [r.name for r in results if r.satisfied is False]
    unknown = [r.name for r in results if r.satisfied is None]
    status = "fail" if failed else ("unknown" if unknown else "pass")
    return {"n_checks": len(results), "n_evaluated": len(results) - len(unknown),
            "n_failed": len(failed), "failed": failed, "unknown": unknown, "status": status,
            "feasible": {"pass": True, "fail": False, "unknown": None}[status]}
