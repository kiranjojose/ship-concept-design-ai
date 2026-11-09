"""Sanity checks on the transcribed reference dataset (D1.1).

These check internal consistency of the transcription, not engineering correctness.
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REF = yaml.safe_load((ROOT / "configs" / "reference_bulk_carrier.yaml").read_text())


def test_design_equation_reproduces_reported_displacement():
    pd = REF["principal_dimensions"]
    L, B, T, cb = (pd[k]["value"] for k in ("lpp_m", "breadth_m", "draught_m", "block_coefficient"))
    disp = L * B * T * cb * 1.025 * 1.006
    reported = REF["reference_results"]["displacement"]["design_equation_t"]["value"]
    assert abs(disp - reported) / reported < 0.001


def test_effective_power_consistent_with_resistance():
    rr = REF["reference_results"]
    v = rr["resistance_kn"]["at_speed_kn"] * 1852 / 3600
    assert abs(rr["resistance_kn"]["value"] * v - rr["effective_power_kw"]["value"]) / rr["effective_power_kw"]["value"] < 0.005


def test_no_value_without_source_or_status():
    for key, item in REF["principal_dimensions"].items():
        if isinstance(item, dict) and "value" in item:
            assert "source" in item or item.get("status") in ("derived", "missing"), key
