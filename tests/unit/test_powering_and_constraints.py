import pytest

from marine_concept_ai.constraints import check_design, summarise
from marine_concept_ai.propulsion import PoweringAssumptions, power_chain


def test_power_chain_arithmetic():
    pc = power_chain(1000.0, PoweringAssumptions(eta_d=0.5, eta_s=1.0, sea_margin=0.2, engine_load=0.8))
    assert pc.pd_kw == pytest.approx(2000)
    assert pc.ps_kw == pytest.approx(2000)
    assert pc.pb_service_kw == pytest.approx(2400)
    assert pc.mcr_kw == pytest.approx(3000)


def test_power_chain_rejects_bad_efficiency():
    with pytest.raises(ValueError):
        power_chain(1000.0, PoweringAssumptions(eta_d=1.2))
    with pytest.raises(ValueError):
        power_chain(1000.0, PoweringAssumptions(sea_margin=-0.1))


def test_default_assumptions_are_sourced():
    a = PoweringAssumptions()
    assert set(a.sources) == {"eta_d", "eta_s", "sea_margin", "engine_load"}
    assert "assumption" in a.sources["sea_margin"]


BASE = dict(draught_m=14.29, breadth_m=32.78, depth_m=19.75, loa_m=None, displacement_t=88409.03,
            lightship_t=13248.99, km_m=13.6, kg_m=10.7, hold_volume_m3=74177.11, cargo_mass_t=74260.13)


def test_skipped_check_is_unknown_not_pass():
    s = summarise(check_design(BASE))               # LOA unknown
    assert s["status"] == "unknown" and s["feasible"] is None
    assert s["unknown"] == ["LOA vs Hay Point"] and s["n_evaluated"] == 7


def test_all_checks_evaluated_and_passing():
    s = summarise(check_design({**BASE, "loa_m": 228.0}))
    assert s["status"] == "pass" and s["feasible"] is True


def test_any_failure_dominates_unknown():
    s = summarise(check_design({**BASE, "displacement_t": 86000.0}))
    assert s["status"] == "fail" and s["feasible"] is False


def test_missing_displacement_is_unknown():
    res = {r.name: r for r in check_design({**BASE, "displacement_t": None})}
    assert res["deadweight = displacement - lightship"].satisfied is None


def test_constraint_failures_detected():
    res = {r.name: r for r in check_design({**BASE, "draught_m": 17.0, "displacement_t": 86000.0})}
    assert not res["draught vs Bhorsagar depth"].satisfied
    assert res["draught vs Hay Point"].satisfied
    assert not res["deadweight = displacement - lightship"].satisfied
    assert res["deadweight = displacement - lightship"].margin == pytest.approx(86000 - 13248.99 - 75000)
    assert not res["freeboard D-T"].satisfied


def test_missing_input_is_not_a_pass():
    res = {r.name: r for r in check_design({**BASE, "kg_m": None})}
    assert res["GM0 (KM - KG)"].satisfied is None
    assert res["LOA vs Hay Point"].satisfied is None
