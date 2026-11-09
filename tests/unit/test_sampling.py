import numpy as np
import pytest

from marine_concept_ai.sampling import DESIGN_VARIABLES, full_grid, latin_hypercube, load_design_space, random_uniform

B = {"lpp_m": {"min": 200, "max": 240}, "breadth_m": {"min": 30, "max": 36},
     "draught_m": {"min": 12.6, "max": 15.6}, "block_coefficient": {"min": 0.80, "max": 0.87}}


def test_lhs_is_seeded_bounded_and_stratified():
    a, b = latin_hypercube(B, 50, 7), latin_hypercube(B, 50, 7)
    assert a.equals(b)
    assert not a.equals(latin_hypercube(B, 50, 8))
    for v in DESIGN_VARIABLES:
        lo, hi = B[v]["min"], B[v]["max"]
        assert a[v].between(lo, hi).all()
        # one point in each of the 50 equal strata
        strata = np.floor((a[v] - lo) / (hi - lo) * 50).clip(0, 49)
        assert len(set(strata)) == 50


def test_random_and_grid():
    r = random_uniform(B, 20, 1)
    assert r.shape == (20, 4) and r.equals(random_uniform(B, 20, 1))
    g = full_grid(B, 3)
    assert len(g) == 81 and g.lpp_m.nunique() == 3
    with pytest.raises(ValueError):
        full_grid(B, 1)


def test_config_bounds_load():
    cfg = load_design_space()
    assert cfg["sampling"]["seed"] == 20261109
    for v in DESIGN_VARIABLES:
        assert cfg["design_space"][v]["min"] < cfg["design_space"][v]["max"]


def test_null_bounds_are_refused(tmp_path):
    p = tmp_path / "ds.yaml"
    p.write_text("design_space:\n" + "".join(f"  {v}: {{min: null, max: null}}\n" for v in DESIGN_VARIABLES))
    with pytest.raises(ValueError, match="not set"):
        load_design_space(p)
