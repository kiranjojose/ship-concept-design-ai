"""Candidate hull generation: scaling and Lackenby 1-CP shift."""
import numpy as np
import pytest

from marine_concept_ai.geometry import build_candidate_hull, lackenby_shift, scale_hull
from marine_concept_ai.hydrostatics import compute_hydrostatics
from marine_concept_ai.reference import reference_hull

T = 14.29


@pytest.fixture(scope="module")
def ref():
    return reference_hull(), compute_hydrostatics(reference_hull(), T)


def test_identity_transform_reproduces_reference(ref):
    hull, h0 = ref
    s = scale_hull(hull, 220.5, 2 * hull.max_half_breadth, 19.75, 19.75)
    h = compute_hydrostatics(lackenby_shift(s, 0.0), T)
    assert h.volume_m3 == pytest.approx(h0.volume_m3, rel=1e-12)


def test_affine_scaling_scales_volume_and_keeps_cb(ref):
    hull, h0 = ref
    sx, sy, sz = 1.05, 0.97, 1.02
    s = scale_hull(hull, 220.5 * sx, 2 * hull.max_half_breadth * sy, 19.75 * sz, 19.75)
    h = compute_hydrostatics(s, T * sz)
    assert h.volume_m3 == pytest.approx(h0.volume_m3 * sx * sy * sz, rel=1e-6)
    assert h.cb == pytest.approx(h0.cb, rel=1e-6)


@pytest.mark.parametrize("k", [0.05, 0.1, 0.2])
def test_lackenby_positive_k_changes_cp_by_k_times_1_minus_cp(ref, k):
    hull, h0 = ref
    h = compute_hydrostatics(lackenby_shift(hull, k), T)
    assert h.cp - h0.cp == pytest.approx(k * (1 - h0.cp), rel=0.01)
    assert h.cm == pytest.approx(h0.cm, rel=1e-9)        # midship section untouched
    assert h.beam_wl_m == pytest.approx(h0.beam_wl_m, rel=1e-9)


def test_lackenby_monotone_in_k(ref):
    hull, _ = ref
    cbs = [compute_hydrostatics(lackenby_shift(hull, k), T, nx=401, nz=81).cb for k in np.linspace(-0.3, 0.4, 8)]
    assert np.all(np.diff(cbs) > 0)


@pytest.mark.parametrize("cb", [0.80, 0.83, 0.87])
def test_candidate_reaches_cb_target_from_geometry(ref, cb):
    hull, _ = ref
    c = build_candidate_hull(hull, 230.0, 34.0, 230 / 11.165, 15.0, cb, 19.75)
    assert c.converged
    assert c.cb_achieved == pytest.approx(cb, abs=5e-4)
    assert compute_hydrostatics(c.hull, 15.0).cb == pytest.approx(c.cb_achieved, rel=1e-12)


def test_unreachable_cb_is_flagged_not_hidden(ref):
    hull, _ = ref
    c = build_candidate_hull(hull, 220.5, 32.78, 19.75, 14.29, 0.97, 19.75)
    assert not c.converged and "outside" in c.note


def test_draught_must_be_below_depth(ref):
    with pytest.raises(ValueError):
        build_candidate_hull(ref[0], 220.5, 32.78, 19.75, 20.0, 0.82, 19.75)
