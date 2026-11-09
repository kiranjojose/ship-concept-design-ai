"""Holtrop-Mennen implementation checks.

Literature benchmark: numerical example of Holtrop & Mennen (1982), printed p.170, stored
with per-value status in data/literature/holtrop_mennen_1982_example.yaml (all printed
values confirmed against the published scan by Kiran, 2026-11-09).

Quantities that do not depend on LCB are asserted against the printed values. Two known
discrepancies are kept visible as strict xfails, so the benchmark stays open until they are
documented away or reconciled:
  * LCB: printed -2.02 % does not reproduce the printed 1+k1 and iE; the inferred -0.75 % does.
  * RA: 220.57 kN (engine) vs 221.98 kN (printed).
"""
import math
from pathlib import Path

import pytest
import yaml

from marine_concept_ai.resistance import (HoltropInput, estimate_half_angle_of_entrance,
                                          estimate_wetted_surface, holtrop_mennen, holtrop_validity,
                                          ittc57_cf)
from marine_concept_ai.resistance.holtrop_mennen import _lr, form_factor

BENCH = yaml.safe_load((Path(__file__).resolve().parents[2] / "data" / "literature"
                        / "holtrop_mennen_1982_example.yaml").read_text())
I, R = BENCH["inputs"], BENCH["results"]


def iv(k):
    return I[k]["value"]


def rv(k):
    assert R[k]["status"] == "confirmed", k
    return R[k]["value"]


def example(lcb_key="lcb_pct"):
    return HoltropInput(L=iv("L_m"), B=iv("B_m"), T=iv("TF_m"), TF=iv("TF_m"), TA=iv("TA_m"),
                        volume=iv("volume_m3"), lcb_pct=iv(lcb_key), cm=iv("cm"), cwp=iv("cwp"),
                        S=rv("S_m2"), abt=iv("abt_m2"), hb=iv("hb_m"), at=iv("at_m2"),
                        ie_deg=rv("ie_deg"), c_stern=iv("c_stern"), s_app=iv("s_app_m2"),
                        k2_app=iv("k2_app"))


def run(lcb_key="lcb_pct"):
    return holtrop_mennen(example(lcb_key), iv("speed_kn"), version="1982")


def test_version_is_required():
    with pytest.raises(TypeError):
        holtrop_mennen(example(), 25.0)
    with pytest.raises(ValueError):
        holtrop_mennen(example(), 25.0, version="1990")


def test_ittc57():
    assert ittc57_cf(1e9) == pytest.approx(0.075 / 49)
    assert ittc57_cf(1e7) == pytest.approx(0.075 / 25)


# --- confirmed quantities independent of LCB -------------------------------------------

def test_benchmark_wetted_surface_regression():
    p = example()
    assert estimate_wetted_surface(p.L, p.B, p.T, p.cb, p.cm, p.cwp, p.abt) == pytest.approx(rv("S_m2"), abs=0.05)


def test_benchmark_friction_appendages_bulb_transom():
    r = run()
    assert r.rf_n / 1e3 == pytest.approx(rv("rf_kn"), rel=5e-4)
    assert r.rapp_n / 1e3 == pytest.approx(rv("rapp_kn"), abs=0.01)
    assert r.rb_n / 1e3 == pytest.approx(rv("rb_kn"), abs=5e-4)
    assert r.rtr_n / 1e3 == pytest.approx(rv("rtr_kn"), abs=5e-3)


def test_benchmark_wave_resistance():
    assert run().rw_n / 1e3 == pytest.approx(rv("rw_kn"), rel=1e-3)


def test_1984_wave_term_differs_from_1982():
    p = example()
    r82 = holtrop_mennen(p, 25.0, version="1982")
    r84 = holtrop_mennen(p, 25.0, version="1984")
    assert r82.rw_n != r84.rw_n and abs(r84.rw_n / r82.rw_n - 1) < 0.02


# --- LCB-dependent quantities: reproduced only with the inferred LCB --------------------

def test_benchmark_lcb_dependent_outputs_with_inferred_lcb():
    """With lcb = -0.75 % (inferred, not printed) the printed 1+k1 and iE are reproduced."""
    p = example("lcb_pct_inferred")
    assert form_factor(p, "1982") == pytest.approx(rv("one_plus_k1"), abs=5e-4)
    assert estimate_half_angle_of_entrance(p) == pytest.approx(rv("ie_deg"), abs=0.005)
    assert _lr(p) == pytest.approx(81.385, abs=0.005)


@pytest.mark.xfail(strict=True, reason="OPEN: printed LCB -2.02 % gives 1+k1 1.16247, iE 11.841 deg "
                                       "vs printed 1.156, 12.08 deg (inconsistency in the worked example)")
def test_benchmark_lcb_dependent_outputs_with_printed_lcb():
    p = example("lcb_pct")
    assert form_factor(p, "1982") == pytest.approx(rv("one_plus_k1"), abs=5e-4)
    assert estimate_half_angle_of_entrance(p) == pytest.approx(rv("ie_deg"), abs=0.005)


# --- correlation allowance and total -----------------------------------------------------

def test_benchmark_correlation_allowance_gap_is_bounded():
    """Documents the size of the open RA gap so it cannot grow unnoticed."""
    assert run().ra_n / 1e3 == pytest.approx(rv("ra_kn"), rel=0.01)


@pytest.mark.xfail(strict=True, reason="OPEN: RA 220.57 kN (engine) vs 221.98 kN printed, cause not identified")
def test_benchmark_correlation_allowance_exact():
    assert run().ra_n / 1e3 == pytest.approx(rv("ra_kn"), abs=0.01)


def test_benchmark_total_with_inferred_lcb():
    """Rt with the inferred LCB is within 0.1 % of print; the residual equals the RA gap."""
    r = run("lcb_pct_inferred")
    assert r.rt_n / 1e3 == pytest.approx(rv("rt_kn"), rel=1e-3)


@pytest.mark.parametrize("version", ["1982", "1984"])
def test_components_switch_off(version):
    p = example()
    p.abt = p.hb = p.at = p.s_app = 0.0
    r = holtrop_mennen(p, 15.0, version=version)
    assert r.rb_n == r.rtr_n == r.rapp_n == 0.0
    assert r.rt_n == pytest.approx(r.rf_n * (1 + r.k1) + r.rw_n + r.ra_n)


@pytest.mark.parametrize("version", ["1982", "1984"])
def test_resistance_increases_with_speed_and_pe_consistent(version):
    p = example()
    rs = [holtrop_mennen(p, v, version=version) for v in (10, 12, 14, 16, 18)]
    assert all(b.rt_n > a.rt_n for a, b in zip(rs, rs[1:]))
    for r in rs:
        assert r.pe_w == pytest.approx(r.rt_n * r.speed_kn * 1852 / 3600)


def test_transom_term_vanishes_above_fnt_5():
    p = example()
    p.at = 1.0
    assert holtrop_mennen(p, 25, version="1982").rtr_n == 0.0


def test_validity_flags():
    p = HoltropInput(L=220.5, B=32.78, T=14.29, volume=0.83 * 220.5 * 32.78 * 14.29, lcb_pct=0.9,
                     cm=0.992, cwp=0.894, S=11356.0)
    v = holtrop_validity(p, 13.0)
    assert v["fn"]["inside"] and v["cp"]["inside"] and v["L/B"]["inside"]
    assert not v["B/T"]["inside"]
    assert math.isclose(v["B/T"]["value"], 32.78 / 14.29)
