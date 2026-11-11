"""Sprint 1: rebuild the reference bulk carrier with the engine and compare with REPORT.

Run from the repo root:  python experiments/01_reference_reconstruction/run_reference.py
Writes CSV tables and a JSON summary to results/tables/.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd

from marine_concept_ai.constraints import check_design, summarise
from marine_concept_ai.hydrostatics import compute_hydrostatics, convergence_study
from marine_concept_ai.propulsion import PoweringAssumptions, holtrop_propulsion_factors, power_chain
from marine_concept_ai.reference import (D_PROP_MAX_M, LPP, T_DESIGN, navcad_inputs, rebuilt_hull_inputs,
                                         reference_hull, reference_yaml)
from marine_concept_ai.resistance import holtrop_mennen, holtrop_validity

ROOT = Path(__file__).resolve().parents[2]
TAB = ROOT / "results" / "tables"
REF = ROOT / "data" / "reference"


def hydrostatics_comparison() -> pd.DataFrame:
    t34 = pd.read_csv(REF / "hydrostatics_table_3_4.csv", comment="#")
    t34 = t34[t34.draught_m > 0].reset_index(drop=True)
    hull = reference_hull()
    rows = []
    prev = None
    for _, r in t34.iterrows():
        h = compute_hydrostatics(hull, float(r.draught_m))
        row = {
            "draught_m": r.draught_m,
            "disp_t_engine": h.displacement_t, "disp_t_report": r.displacement_t,
            "disp_err_pct": 100 * (h.displacement_t / r.displacement_t - 1),
            "awp_m2_engine": h.waterplane_area_m2, "awp_m2_report": r.waterplane_area_m2,
            "awp_err_pct": 100 * (h.waterplane_area_m2 / r.waterplane_area_m2 - 1),
            "kb_m_engine": h.kb_m, "kb_m_report": r.kb_m,
            "bmt_m_engine": h.bmt_m, "bmt_m_report": r.bmt_m,
            "kmt_m_engine": h.kmt_m, "kmt_m_report": r.kmt_m,
            "lcb_m_engine": h.lcb_m_from_ap, "lcb_m_report": r.lcb_m_from_zero_fwd_pos,
            "lcf_m_engine": h.lcf_m_from_ap, "lcf_m_report": r.lcf_m_from_zero_fwd_pos,
            "tpc_engine": h.tpc_t_per_cm, "tpc_report": r.tpc_t_per_cm,
            "wsa_m2_engine": h.wetted_surface_m2, "wsa_m2_report": r.wetted_area_m2,
            "wsa_err_pct": 100 * (h.wetted_surface_m2 / r.wetted_area_m2 - 1),
            "cm_engine": h.cm, "cm_report": r.cm,
        }
        # displacement of the slice between this draught and the previous one
        if prev is not None:
            de, dr = h.displacement_t - prev[0], r.displacement_t - prev[1]
            row["slice_disp_err_pct"] = 100 * (de / dr - 1)
        prev = (h.displacement_t, r.displacement_t)
        rows.append(row)
    return pd.DataFrame(rows)


def resistance_comparison() -> pd.DataFrame:
    t42 = pd.read_csv(REF / "resistance_holtrop_navcad_table_4_2.csv", comment="#")
    cases = {"navcad_inputs": navcad_inputs(), "rebuilt_hull": rebuilt_hull_inputs()}
    rows = []
    for name, p in cases.items():
        for ver in ("1984", "1982"):
            for _, r in t42.iterrows():
                res = holtrop_mennen(p, float(r.speed_kn), version=ver)
                rows.append({
                    "case": name, "hm_version": ver, "speed_kn": r.speed_kn,
                    "rt_kn_engine": res.rt_n / 1e3, "rt_kn_report": r.rt_kn,
                    "rt_err_pct": 100 * (res.rt_n / 1e3 / r.rt_kn - 1),
                    "pe_kw_engine": res.pe_w / 1e3, "pe_kw_report": r.pe_kw,
                    "one_plus_k1": 1 + res.k1,
                    "rf_kn": res.rf_n / 1e3, "rf_kn_report": r.rf_kn,
                    "rw_kn": res.rw_n / 1e3, "rw_kn_report": r.rw_kn,
                    "rb_kn": res.rb_n / 1e3, "rtr_kn": res.rtr_n / 1e3, "rtr_kn_report": r.rtr_kn,
                    "ra_kn": res.ra_n / 1e3, "ra_kn_report": r.ra_kn,
                    "rapp_kn": res.rapp_n / 1e3, "rapp_kn_report": r.rapp_kn,
                })
    return pd.DataFrame(rows)


def transom_sensitivity() -> pd.DataFrame:
    rows = []
    for src in ("zero", "navcad_rtr", "station0"):
        for name, f in (("navcad_inputs", navcad_inputs), ("rebuilt_hull", rebuilt_hull_inputs)):
            p = f(src)
            for ver in ("1982", "1984"):
                r = holtrop_mennen(p, 13.0, version=ver)
                rows.append({"at_source": src, "case": name, "hm_version": ver, "at_m2": p.at,
                             "rtr_kn": r.rtr_n / 1e3, "rt_kn": r.rt_n / 1e3,
                             "rt_err_pct": 100 * (r.rt_n / 1e3 / 635.9 - 1)})
    return pd.DataFrame(rows)


ETA_D_SCENARIOS = {
    "historical_QPC_0.60": (0.60, "REPORT p.36-37"),
    "sensitivity_0.781": (None, "REPORT's own w 0.38, t 0.26, eta_R 1.05, eta_O 0.623 (p.66-71), DISC-18"),
}
SEA_MARGINS = (0.0, 0.10, 0.15, 0.20, 0.25)


def powering_scenarios():
    """Indicative installed power at 13 kn. Calm-water PE is the primary hull metric;
    MCR is shown for two eta_D scenarios crossed with sea margins, varied separately.
    Reference brake power stays unknown (null in the YAML)."""
    pf_rep = reference_yaml()["reference_results"]["propulsive_factors"]
    w, t, eta_r, eta_o = (pf_rep[k]["value"] for k in
                          ("wake_fraction", "thrust_deduction", "relative_rotative_efficiency", "open_water_efficiency"))
    eta_d_rep_factors = (1 - t) / (1 - w) * eta_o * eta_r
    rows = []
    for case, f in (("rebuilt_hull", rebuilt_hull_inputs), ("navcad_inputs", navcad_inputs)):
        p = f()
        for ver in ("1982", "1984"):
            pe = holtrop_mennen(p, 13.0, version=ver).pe_w / 1e3
            for scen, (eta_d, src) in ETA_D_SCENARIOS.items():
                eta_d = eta_d if eta_d is not None else eta_d_rep_factors
                for sm in SEA_MARGINS:
                    pc = power_chain(pe, PoweringAssumptions(eta_d=eta_d, sea_margin=sm))
                    rows.append({"case": case, "hm_version": ver, "eta_d_scenario": scen, "eta_d": eta_d,
                                 "sea_margin": sm, "pe_kw": pe, "pd_kw": pc.pd_kw,
                                 "pb_service_kw": pc.pb_service_kw, "mcr_kw": pc.mcr_kw, "eta_d_source": src})
    # Holtrop w, t, eta_R are reported for information only: EXCLUDED from engine sizing
    # until a propeller operating point (diameter, rpm) is supported (DISC-09).
    p = rebuilt_hull_inputs()
    res = holtrop_mennen(p, 13.0, version="1984")
    hp = holtrop_propulsion_factors(p.L, p.B, p.T, p.cb, p.cp, p.cm, p.lcb_pct, p.S, res.cf, res.ca, res.k1,
                                    D_prop=D_PROP_MAX_M)
    hp["eta_d_with_report_eta_o"] = hp["eta_h"] * eta_o * hp["eta_r"]
    hp["status"] = "excluded from engine sizing (no supported propeller operating point)"
    return pd.DataFrame(rows), hp


def deadweight_margin_scenarios():
    """Margin to the 75,000 t DWT requirement under displacement (geometry) and lightship
    (weight) uncertainty. Every input is a reported value or an engine output."""
    y = reference_yaml()
    rr = y["reference_results"]
    hull = reference_hull()
    disp = {
        "design equation (REPORT p.19)": rr["displacement"]["design_equation_t"]["value"],
        "offsets, PCHIP, x1.006": compute_hydrostatics(hull, T_DESIGN).displacement_shell_t,
        "offsets, linear, x1.006": compute_hydrostatics(hull, T_DESIGN, interp="linear").displacement_shell_t,
        "offsets, PCHIP, no shell factor": compute_hydrostatics(hull, T_DESIGN).displacement_t,
        "2019 software hull, Table 3.4 / p.57": rr["displacement"]["modelled_hull_at_design_draught_t"]["value"],
    }
    ls = {
        "detailed, Table 6.1": rr["lightship_mass_t"]["value"],
        "preliminary, Table 2.4": 13250.49,
        "loading-condition tables p.101-105 (DISC-11)": rr["lightship_mass_t"]["conflicts"][0]["value"],
    }
    rows = []
    for dk, dv in disp.items():
        for lk, lv in ls.items():
            dwt = dv - lv
            rows.append({"displacement_basis": dk, "lightship_basis": lk, "displacement_t": dv, "lightship_t": lv,
                         "deadweight_t": dwt, "margin_to_75000_t": dwt - 75000.0, "meets_requirement": dwt >= 75000.0})
    return pd.DataFrame(rows)


def constraints_reference():
    y = reference_yaml()
    pdim, rr = y["principal_dimensions"], y["reference_results"]
    h = compute_hydrostatics(reference_hull(), T_DESIGN)
    cargo = rr["cargo_mass_t"]["value"]
    hold = rr["capacities_m3"]["cargo_holds_total"]["value"]
    base = dict(draught_m=pdim["draught_m"]["value"], breadth_m=pdim["breadth_m"]["value"],
                depth_m=pdim["depth_m"]["value"], loa_m=None, lightship_t=rr["lightship_mass_t"]["value"],
                km_m=h.kmt_m, kg_m=10.70, kg_note="KG 10.70 m, full-load departure (rice), REPORT Table 7.2",
                hold_volume_m3=hold, cargo_mass_t=cargo)
    out = []
    for label, disp in (("design equation (88,409 t)", rr["displacement"]["design_equation_t"]["value"]),
                        ("rebuilt hull, with shell 1.006", h.displacement_shell_t)):
        checks = check_design({**base, "displacement_t": disp})
        summ = summarise(checks)
        for c in checks:
            out.append({"displacement_basis": label, **c.as_dict(), "overall_status": summ["status"]})
    return pd.DataFrame(out)


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    hyd = hydrostatics_comparison()
    res = resistance_comparison()
    tr = transom_sensitivity()
    pw, hp = powering_scenarios()
    dwt = deadweight_margin_scenarios()
    conv = convergence_study(reference_hull(), T_DESIGN)
    con = constraints_reference()
    hyd.to_csv(TAB / "s1_hydrostatics_vs_table_3_4.csv", index=False, float_format="%.4f")
    res.to_csv(TAB / "s1_resistance_vs_table_4_2.csv", index=False, float_format="%.4f")
    tr.to_csv(TAB / "s1_transom_sensitivity_13kn.csv", index=False, float_format="%.4f")
    pw.to_csv(TAB / "s1_power_chain_13kn.csv", index=False, float_format="%.4f")
    dwt.to_csv(TAB / "s1_deadweight_margin_scenarios.csv", index=False, float_format="%.2f")
    conv.to_csv(TAB / "s1_hydrostatics_convergence.csv", index=False, float_format="%.8g")
    con.to_csv(TAB / "s1_constraints_reference.csv", index=False, float_format="%.4f")

    h = compute_hydrostatics(reference_hull(), T_DESIGN)
    nc, rb = navcad_inputs(), rebuilt_hull_inputs()
    summary = {
        "design_draught_hydrostatics": h.as_dict(),
        "holtrop_inputs": {"navcad_inputs": nc.as_dict(), "rebuilt_hull": rb.as_dict()},
        "validity_13kn": {"navcad_inputs": holtrop_validity(nc, 13.0), "rebuilt_hull": holtrop_validity(rb, 13.0)},
        "holtrop_propulsion_factors_D9.4_not_for_sizing": hp,
    }
    (TAB / "s1_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 40)
    print(hyd[["draught_m", "disp_t_engine", "disp_t_report", "disp_err_pct", "slice_disp_err_pct",
               "awp_err_pct", "kb_m_engine", "kb_m_report", "kmt_m_engine", "kmt_m_report", "wsa_err_pct"]])
    print(res[res.speed_kn == 13][["case", "hm_version", "rt_kn_engine", "rt_err_pct", "one_plus_k1",
                                   "rf_kn", "rw_kn", "rtr_kn", "ra_kn", "rapp_kn"]])
    print(res.groupby(["case", "hm_version"]).rt_err_pct.agg(["min", "max"]))
    print(tr)
    print(pw[(pw.case == "rebuilt_hull")][["hm_version", "eta_d_scenario", "eta_d", "sea_margin", "pe_kw", "mcr_kw"]])
    print(dwt[["displacement_basis", "lightship_basis", "deadweight_t", "margin_to_75000_t"]])
    print(conv)
    print(con[["displacement_basis", "name", "value", "limit", "margin", "satisfied", "overall_status"]])


if __name__ == "__main__":
    main()
