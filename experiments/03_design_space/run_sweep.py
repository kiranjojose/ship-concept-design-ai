"""Sprint 2, first design-space sweep.

    python experiments/03_design_space/run_sweep.py          # writes results/tables/s2_*

Outputs
  s2_sweep_candidates.csv     one row per candidate: geometry, DWT under every scenario, checks
  s2_power_grid.csv           MCR per candidate x Holtrop version x eta_D x sea margin (indicator)
  s2_recovery_one_at_a_time.csv  change in each variable alone that recovers 75 000 t
  s2_summary.json             counts and the headline numbers

Holtrop PE is reported as an indicator and is NOT used to rank or filter candidates.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
from scipy.optimize import brentq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from marine_concept_ai.design_space import (DWT_REQUIRED_T, depth_for, evaluate_candidate,  # noqa: E402
                                            power_grid, reference_beam)
from marine_concept_ai.hydrostatics import compute_hydrostatics  # noqa: E402
from marine_concept_ai.reference import LPP, T_DESIGN, reference_hull  # noqa: E402
from marine_concept_ai.sampling import load_design_space, latin_hypercube  # noqa: E402

TAB = ROOT / "results" / "tables"


def reference_point() -> dict:
    cb_ref = compute_hydrostatics(reference_hull(), T_DESIGN).cb
    return {"lpp_m": LPP, "breadth_m": reference_beam(), "draught_m": T_DESIGN, "block_coefficient": cb_ref}


def run_lhs(cfg) -> pd.DataFrame:
    s = cfg["sampling"]
    pts = latin_hypercube(cfg["design_space"], s["n_samples"], s["seed"])
    if s.get("include_reference", True):
        pts = pd.concat([pd.DataFrame([reference_point()]), pts], ignore_index=True)
    rows = []
    for i, p in pts.iterrows():
        r = evaluate_candidate(p.lpp_m, p.breadth_m, p.draught_m, p.block_coefficient)
        r["candidate_id"] = "REF" if (i == 0 and s.get("include_reference", True)) else f"C{i:03d}"
        rows.append(r)
    df = pd.DataFrame(rows)
    return df[["candidate_id"] + [c for c in df.columns if c != "candidate_id"]]


def run_power_grid(df) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        for ver in ("1982", "1984"):
            for g in power_grid(r[f"pe_indicator_{ver}_kw"]):
                rows.append({"candidate_id": r.candidate_id, "holtrop_version": ver,
                             "pe_indicator_kw": r[f"pe_indicator_{ver}_kw"], **g})
    return pd.DataFrame(rows)


def recovery_one_at_a_time(cfg) -> pd.DataFrame:
    """Vary one variable from the reference, others fixed, until the DWT margin is zero."""
    ref = reference_point()
    ds = cfg["design_space"]
    names = {"lpp_m": "L", "breadth_m": "B", "draught_m": "T", "block_coefficient": "CB"}
    rows = []
    for var in names:
        def margin(x, which):
            p = {**ref, var: x}
            r = evaluate_candidate(p["lpp_m"], p["breadth_m"], p["draught_m"], p["block_coefficient"], holtrop=False)
            return r[f"dwt_margin_{which}_t"], r
        for which in ("nominal", "worst"):
            lo, hi = ref[var], ds[var]["max"]
            m_hi, _ = margin(hi, which)
            if m_hi < 0:
                rows.append({"variable": names[var], "dwt_basis": which, "reference": lo, "required": None,
                             "change": None, "change_pct": None,
                             "note": f"not recovered within the bound {hi}"})
                continue
            x = brentq(lambda v: margin(v, which)[0], lo, hi, xtol=1e-5)
            x += 1e-4 * (hi - lo)   # report the state just on the feasible side of the root
            _, r = margin(x, which)
            rows.append({"variable": names[var], "dwt_basis": which, "reference": lo, "required": x,
                         "change": x - lo, "change_pct": (x / lo - 1) * 100,
                         "depth_m": r["depth_m"], "freeboard_m": r["freeboard_m"],
                         "status": r["status"], "fails_other_than_dwt": r["fails_other_than_dwt"],
                         "unknown": r["unknown"],
                         "margin_freeboard_m": r["margin::freeboard D-T"],
                         "margin_stowage_m3_per_t": r["margin::hold volume / cargo mass"],
                         "note": ""})
    return pd.DataFrame(rows)


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    cfg = load_design_space()
    t0 = time.time()
    df = run_lhs(cfg)
    df.to_csv(TAB / "s2_sweep_candidates.csv", index=False, float_format="%.6g")
    run_power_grid(df).to_csv(TAB / "s2_power_grid.csv", index=False, float_format="%.6g")
    rec = recovery_one_at_a_time(cfg)
    rec.to_csv(TAB / "s2_recovery_one_at_a_time.csv", index=False, float_format="%.6g")

    c = df[df.candidate_id != "REF"]
    ok = c[c.geometry_ok]
    no_other_fail = ok[ok.fails_other_than_dwt == ""]
    summary = {
        "design_space_status": cfg.get("status"),
        "n_candidates": int(len(c)),
        "seed": cfg["sampling"]["seed"],
        "geometry_not_realisable": int((~c.geometry_ok).sum()),
        "status_counts": ok.status.value_counts().to_dict(),
        "dwt_verdict_counts": ok.dwt_verdict.value_counts().to_dict(),
        "dwt_verdict_counts_passing_other_checks": no_other_fail.dwt_verdict.value_counts().to_dict(),
        "fails_other_than_dwt_counts": ok.fails_other_than_dwt[ok.fails_other_than_dwt != ""]
            .str.split("; ").explode().value_counts().to_dict(),
        "unknown_checks": ok.unknown.value_counts().to_dict(),
        "reference": df[df.candidate_id == "REF"].iloc[0][
            ["cb", "disp_pchip_t", "lightship_nominal_t", "dwt_margin_nominal_t", "dwt_margin_worst_t",
             "dwt_margin_best_t", "pe_indicator_1982_kw", "pe_indicator_1984_kw", "status"]].to_dict(),
        "runtime_s": round(time.time() - t0, 1),
        "note": "Holtrop PE is an indicator only; no ranking is made on it.",
    }
    (TAB / "s2_summary.json").write_text(json.dumps(summary, indent=2, default=float))
    print(json.dumps(summary, indent=2, default=float))
    print(rec.to_string())


if __name__ == "__main__":
    main()
