"""Watson-Gilfillan lightship model reproduces REPORT Table 2.3 / 2.4."""
from pathlib import Path

import pandas as pd
import pytest

from marine_concept_ai.weights import WEIGHT_SCENARIOS, lightship_watson_gilfillan

ROOT = Path(__file__).resolve().parents[2]
TAB23 = pd.read_csv(ROOT / "data" / "reference" / "dimension_sweep_table_2_3.csv", comment="#")


@pytest.mark.parametrize("i", range(len(TAB23)))
def test_table_2_3_rows(i):
    r = TAB23.iloc[i]
    # Table 2.3 prints CB to 2 d.p.; the unrounded CB is implied by its displacement
    cb = r.displacement_t / (r.lbp_m * r.breadth_m * r.draught_m * 1.025 * 1.006)
    w = lightship_watson_gilfillan(r.lbp_m, r.breadth_m, r.depth_m, r.draught_m, cb, r.displacement_t)
    assert w.e_numeral == pytest.approx(r.E_numeral, rel=5e-4)
    assert w.se7_t == pytest.approx(r.steel_7_t, rel=1.5e-3)
    assert w.steel_t == pytest.approx(r.steel_mass_t, rel=3e-3)
    assert w.outfit_t == pytest.approx(r.outfit_mass_t, rel=1e-3)
    assert w.pd_kw == pytest.approx(r.delivered_power_kw, rel=1e-5)


def test_table_2_4_lightship_and_deadweight():
    w = lightship_watson_gilfillan(220.5, 32.78, 19.75, 14.29, 0.83009, 88409.03)
    assert w.engine_plant_t == pytest.approx(809.73, abs=0.5)
    assert w.lightship_t == pytest.approx(13250.49, rel=5e-4)
    assert 88409.03 - w.lightship_t == pytest.approx(75158.54, abs=10)


def test_scenarios_are_ordered():
    ls = [lightship_watson_gilfillan(220.5, 32.78, 19.75, 14.29, 0.8166, 86974, s).lightship_t
          for s in ("low", "nominal", "reserve_avg", "high")]
    assert ls == sorted(ls)
    assert set(WEIGHT_SCENARIOS) == {"low", "nominal", "reserve_avg", "high"}
