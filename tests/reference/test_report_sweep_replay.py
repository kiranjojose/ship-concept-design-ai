"""The automated replay of the report's length sweep (Table 2.3 / 2.4), used for the Sprint 2 exit gate."""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "rerun_report_sweep", ROOT / "experiments" / "03_design_space" / "rerun_report_sweep.py")
rerun = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rerun)


@pytest.fixture(scope="module")
def cases():
    return rerun.replay()


def test_selected_case_reproduces_table_2_4(cases):
    length, dwt = cases[-1]
    assert length == 220.5
    assert dwt == pytest.approx(75158.54, abs=2.0)


def test_grid_crosses_75000_between_220_and_225(cases):
    grid = cases[:-1]
    (l0, d0), (l1, d1) = next((a, b) for a, b in zip(grid, grid[1:]) if a[1] < 75000 <= b[1])
    assert (l0, l1) == (220.0, 225.0)
    assert l0 + (l1 - l0) * (75000 - d0) / (d1 - d0) == pytest.approx(220.737, abs=1e-3)
