"""End-to-end candidate evaluation."""
import numpy as np
import pytest

from marine_concept_ai.constraints import check_design, summarise
from marine_concept_ai.design_space import evaluate_candidate, reference_beam


@pytest.fixture(scope="module")
def ref_row():
    return evaluate_candidate(220.5, reference_beam(), 14.29, 0.81661)


def test_reference_candidate_matches_sprint1_geometry(ref_row):
    assert ref_row["disp_pchip_t"] == pytest.approx(86974, rel=2e-4)       # Sprint 1, offsets x 1.006
    assert ref_row["kmt_m"] == pytest.approx(13.61, abs=0.01)
    assert ref_row["cb_length_basis"] == "LPP"


def test_reference_candidate_is_short_of_75000(ref_row):
    assert ref_row["dwt_margin_worst_t"] < ref_row["dwt_margin_nominal_t"] < ref_row["dwt_margin_best_t"] < 0
    assert ref_row["status"] == "fail" and ref_row["dwt_verdict"] == "short"
    assert "LOA vs Hay Point" in ref_row["unknown"]


def test_missing_loa_keeps_status_unknown_never_pass():
    r = evaluate_candidate(232.0, 34.5, 14.4, 0.83, holtrop=False)
    assert r["dwt_verdict"] == "robust"
    assert r["fails_other_than_dwt"] == ""
    assert r["status"] == "unknown"


def test_deadweight_rises_with_each_main_dimension():
    base = evaluate_candidate(220.0, 32.5, 14.0, 0.82, holtrop=False)["dwt_nominal_t"]
    for args in ((225.0, 32.5, 14.0, 0.82), (220.0, 33.5, 14.0, 0.82),
                 (220.0, 32.5, 14.3, 0.82), (220.0, 32.5, 14.0, 0.84)):
        assert evaluate_candidate(*args, holtrop=False)["dwt_nominal_t"] > base


def test_deep_draught_fails_freeboard():
    r = evaluate_candidate(205.0, 33.0, 15.5, 0.84, holtrop=False)
    assert "freeboard D-T" in r["fails_other_than_dwt"] and r["status"] == "fail"


def test_numpy_inputs_do_not_hide_failures():
    """Regression: numpy bools made `satisfied is False` untrue, so failures were reported as unknown."""
    d = dict(draught_m=np.float64(14.29), breadth_m=np.float64(32.78), depth_m=np.float64(19.75), loa_m=None,
             displacement_t=np.float64(80000.0), lightship_t=np.float64(13249.0), km_m=np.float64(13.6),
             kg_m=np.float64(10.7), hold_volume_m3=np.float64(74177.0), cargo_mass_t=np.float64(66000.0))
    s = summarise(check_design(d))
    assert s["status"] == "fail" and any(n.startswith("deadweight") for n in s["failed"])
