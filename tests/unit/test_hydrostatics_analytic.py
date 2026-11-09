"""Hydrostatics on shapes with exact answers."""
import numpy as np
import pytest

from marine_concept_ai.geometry import OffsetTable
from marine_concept_ai.hydrostatics import compute_hydrostatics, section_properties

L, B, T = 100.0, 20.0, 8.0


def box(nx=11, nz=6, depth=12.0):
    x = np.linspace(0, L, nx)
    z = np.linspace(0, depth, nz)
    return OffsetTable(x=x, z=z, y=np.full((nx, nz), B / 2), lpp=L)


def test_box_barge_exact():
    h = compute_hydrostatics(box(), T, rho=1000.0)
    assert h.volume_m3 == pytest.approx(L * B * T, rel=1e-9)
    assert h.displacement_t == pytest.approx(L * B * T, rel=1e-9)
    assert h.lcb_m_from_ap == pytest.approx(L / 2, rel=1e-9)
    assert h.kb_m == pytest.approx(T / 2, rel=1e-9)
    assert h.waterplane_area_m2 == pytest.approx(L * B, rel=1e-9)
    assert h.bmt_m == pytest.approx(B ** 2 / (12 * T), rel=1e-9)
    assert h.bml_m == pytest.approx(L ** 2 / (12 * T), rel=1e-3)
    assert (h.cb, h.cm, h.cp, h.cwp) == pytest.approx((1, 1, 1, 1), rel=1e-9)
    assert h.tpc_t_per_cm == pytest.approx(L * B / 100, rel=1e-9)
    # sides + bottom, ends are open
    assert h.wetted_surface_m2 == pytest.approx(L * (B + 2 * T), rel=1e-6)


def test_shell_factor_applied():
    h = compute_hydrostatics(box(), T)
    assert h.displacement_shell_t == pytest.approx(h.displacement_t * 1.006)


def test_parabolic_waterplane():
    x = np.linspace(0, L, 41)
    z = np.array([0.0, 4.0, 12.0])
    y = (B / 2) * (1 - (2 * x / L - 1) ** 2)
    hull = OffsetTable(x=x, z=z, y=np.repeat(y[:, None], 3, axis=1), lpp=L)
    h = compute_hydrostatics(hull, T)
    assert h.cwp == pytest.approx(2 / 3, rel=1e-3)
    assert h.cb == pytest.approx(2 / 3, rel=1e-3)
    assert h.lcf_m_from_ap == pytest.approx(L / 2, rel=1e-6)
    assert h.cm == pytest.approx(1.0, rel=1e-6)


def test_triangular_section_kb():
    # V-section y = (B/2) z/T: KB = 2T/3, area = B T / 2
    x = np.linspace(0, L, 5)
    z = np.linspace(0, T, 9)
    y = np.tile(B / 2 * z / T, (5, 1))
    h = compute_hydrostatics(OffsetTable(x=x, z=z, y=y, lpp=L), T)
    assert h.kb_m == pytest.approx(2 * T / 3, rel=1e-3)
    assert h.volume_m3 == pytest.approx(L * B * T / 2, rel=1e-3)
    area, zc = section_properties(OffsetTable(x=x, z=z, y=y, lpp=L), L / 2, T)
    assert area == pytest.approx(B * T / 2, rel=1e-3)
    assert zc == pytest.approx(2 * T / 3, rel=1e-3)


def test_offsets_validation():
    with pytest.raises(ValueError):
        OffsetTable(x=[0, 1], z=[0, 1], y=[[1, -1], [1, 1]], lpp=1)
    with pytest.raises(ValueError):
        compute_hydrostatics(box(), 50.0)
