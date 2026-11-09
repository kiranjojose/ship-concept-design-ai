"""Engine vs REPORT values. Tolerances are the Sprint 1 gates proposed in
docs/missing_data_register.md section 4 (pending Kiran's confirmation):
  displacement from the design equation  +-0.5 %
  Holtrop Rt at 13 kn vs Table 4.2        +-5 % (legacy comparison threshold)
Rebuilt-hull hydrostatics are compared with Table 3.4 using the tolerances justified
in docs/validation_sprint1.md (the offsets and the 2019 software hull differ below
2.3 m and aft of AP, so a whole-hull 0.5 % match is not expected).
"""
import pandas as pd
import pytest

from marine_concept_ai.hydrostatics import compute_hydrostatics
from marine_concept_ai.reference import (ROOT, navcad_inputs, rebuilt_hull_inputs, reference_hull,
                                         reference_yaml)
from marine_concept_ai.resistance import holtrop_mennen

REF = ROOT / "data" / "reference"
T42 = pd.read_csv(REF / "resistance_holtrop_navcad_table_4_2.csv", comment="#").set_index("speed_kn")
T34 = pd.read_csv(REF / "hydrostatics_table_3_4.csv", comment="#")


def test_design_equation_displacement():
    y = reference_yaml()
    L, B, T, cb = (y["principal_dimensions"][k]["value"] for k in ("lpp_m", "breadth_m", "draught_m", "block_coefficient"))
    disp = L * B * T * cb * 1.025 * 1.006
    assert disp == pytest.approx(88409.03, rel=0.005)


VERSIONS = ["1982", "1984"]


@pytest.mark.parametrize("version", VERSIONS)
@pytest.mark.parametrize("make", [navcad_inputs, rebuilt_hull_inputs])
def test_rt_13kn_within_5pct(make, version):
    """Legacy comparison threshold, +-5 % at 13 kn (Kiran, 2026-11-09)."""
    r = holtrop_mennen(make(), 13.0, version=version)
    assert r.rt_n / 1e3 == pytest.approx(T42.loc[13, "rt_kn"], rel=0.05)


def test_rt_15kn_gap_is_wave_resistance():
    """At 15 kn the engine is above Table 4.2; the excess is less than Rw, which NavCad reports as ~0."""
    r = holtrop_mennen(rebuilt_hull_inputs(), 15.0, version="1982")
    excess = r.rt_n / 1e3 - T42.loc[15, "rt_kn"]
    assert excess > 0
    assert r.rw_n / 1e3 > excess


@pytest.mark.parametrize("v", [8, 10, 12, 13, 15])
def test_components_that_navcad_prints(v):
    r = holtrop_mennen(navcad_inputs(), float(v), version="1982")  # RF, RA, RTR identical in both versions
    assert r.ra_n / 1e3 == pytest.approx(T42.loc[v, "ra_kn"], rel=0.03)
    assert r.rf_n / 1e3 == pytest.approx(T42.loc[v, "rf_kn"], rel=0.03)
    # AT is recovered from RTR at 13 kn only; the other speeds are an independent check
    assert r.rtr_n / 1e3 == pytest.approx(T42.loc[v, "rtr_kn"], rel=0.01)


def test_hydrostatics_numerically_converged():
    """Numerical convergence of the integration, separate from agreement with the report."""
    from marine_concept_ai.hydrostatics import convergence_study
    df = convergence_study(reference_hull(), 14.29)
    default = df[(df.nx == 801) & (df.nz == 241)].iloc[0]
    for c in ("volume_m3", "kb_m", "bmt_m", "wetted_surface_m2"):
        assert abs(default[c + "_rel_to_finest"]) < 1e-4


def test_rebuilt_hull_design_draught():
    h = compute_hydrostatics(reference_hull(), 14.29)
    assert h.displacement_t == pytest.approx(84755, rel=0.025)       # Table 3.4 / p.57
    assert h.waterplane_area_m2 == pytest.approx(6511.062, rel=0.015)
    assert h.kmt_m == pytest.approx(13.853, rel=0.025)
    assert h.wetted_surface_m2 == pytest.approx(11356.43, rel=0.02)  # NavCad input, p.60
    assert h.cm == pytest.approx(0.992, abs=0.002)                    # REPORT p.20


def test_rebuilt_hull_slices_match_between_2_3_and_13_4_m():
    """Displacement between draughts 2.289 and 13.366 m agrees with Table 3.4 to 0.5 %:
    the hull differences are confined to the bottom and the stern overhang."""
    hull = reference_hull()
    t = T34.set_index("draught_m")["displacement_t"]
    lo = compute_hydrostatics(hull, 2.289).displacement_t
    hi = compute_hydrostatics(hull, 13.366).displacement_t
    assert hi - lo == pytest.approx(t[13.366] - t[2.289], rel=0.005)
