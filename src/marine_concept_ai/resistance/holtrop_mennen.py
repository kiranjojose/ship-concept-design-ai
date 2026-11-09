"""Holtrop-Mennen resistance prediction, 1984 revision.

References
  [H82] J. Holtrop, G.G.J. Mennen, "An approximate power prediction method",
        International Shipbuilding Progress 29(335), 1982, 166-170.
  [H84] J. Holtrop, "A statistical re-analysis of resistance and propulsion data",
        International Shipbuilding Progress 31(363), 1984, 272-276.

Rtotal = RF (1+k1) + Rapp + Rw + RB + RTR + RA     (all in N)

Two versions are selectable and the caller must choose one (no default) until the
benchmark against the published [H82] example is reconciled (docs/validation_sprint1.md).
Wave resistance uses the low-speed formula (Fn <= 0.40) of the chosen version. Higher-speed
branches are not implemented because the bulk-carrier design space never reaches them.

Conventions: L is the waterline length used by the method; lcb_pct is LCB forward of
0.5 L as a percentage of L (positive forward), as in [H82].
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

from ..units import G, NU_SW_15C, RHO_SW


@dataclass
class HoltropInput:
    L: float                 # m, waterline length
    B: float                 # m
    T: float                 # m, mean draught
    volume: float            # m3, moulded displaced volume
    lcb_pct: float           # % L forward of 0.5L
    cm: float
    cwp: float
    S: float                 # m2, bare-hull wetted surface
    TF: float | None = None  # m, forward draught (default T)
    TA: float | None = None  # m, aft draught (default T)
    abt: float = 0.0         # m2, transverse bulb area at FP
    hb: float = 0.0          # m, height of bulb-area centroid above keel
    at: float = 0.0          # m2, immersed transom area at rest
    ie_deg: float | None = None   # half angle of entrance; None -> [H84] estimate
    c_stern: float = 0.0     # afterbody form: -25 pram/gondola, -10 V, 0 normal, +10 U/Hogner
    s_app: float = 0.0       # m2, appendage wetted area
    k2_app: float = 1.5      # (1+k2) equivalent for the appendages
    rho: float = RHO_SW
    nu: float = NU_SW_15C
    notes: dict = field(default_factory=dict)

    def __post_init__(self):
        self.TF = self.T if self.TF is None else self.TF
        self.TA = self.T if self.TA is None else self.TA

    @property
    def cb(self):
        return self.volume / (self.L * self.B * self.T)

    @property
    def cp(self):
        return self.cb / self.cm

    def as_dict(self):
        return asdict(self)


@dataclass
class ResistanceResult:
    speed_kn: float
    fn: float
    re: float
    cf: float
    ca: float
    k1: float                # form factor (1+k1) - 1
    rf_n: float
    rapp_n: float
    rw_n: float
    rb_n: float
    rtr_n: float
    ra_n: float
    rt_n: float
    pe_w: float

    def as_dict(self):
        return asdict(self)


def ittc57_cf(re: float) -> float:
    return 0.075 / (math.log10(re) - 2.0) ** 2


def _lr(p: HoltropInput) -> float:
    cp = p.cp
    return p.L * (1.0 - cp + 0.06 * cp * p.lcb_pct / (4.0 * cp - 1.0))


def estimate_half_angle_of_entrance(p: HoltropInput) -> float:
    """Regression for iE in degrees (reproduces iE = 12.08 deg of the [H82] p.170 example at lcb = -0.75 %; see validation note)."""
    cp, L, B = p.cp, p.L, p.B
    expo = -((L / B) ** 0.80856 * (1 - p.cwp) ** 0.30484 * (1 - cp - 0.0225 * p.lcb_pct) ** 0.6367
             * (_lr(p) / B) ** 0.34574 * (100 * p.volume / L ** 3) ** 0.16302)
    return 1.0 + 89.0 * math.exp(expo)


def estimate_wetted_surface(L, B, T, cb, cm, cwp, abt=0.0) -> float:
    """[H82] regression for bare-hull wetted surface, m2."""
    return (L * (2 * T + B) * math.sqrt(cm)
            * (0.453 + 0.4425 * cb - 0.2862 * cm - 0.003467 * B / T + 0.3696 * cwp)
            + 2.38 * abt / cb)


VERSIONS = ("1982", "1984")


def _check_version(version):
    if version not in VERSIONS:
        raise ValueError(f"version must be one of {VERSIONS}, got {version!r}")


def form_factor(p: HoltropInput, version: str) -> float:
    """(1+k1).

    "1982": [H82] p.168, 1+k1 = c13 {0.93 + c12 (B/LR)^0.92497 (0.95-CP)^-0.521448
            (1-CP+0.0225 lcb)^0.6906}
    "1984": [H84], 1+k1 = 0.93 + 0.487118 c14 (B/L)^1.06806 (T/L)^0.46106 (L/LR)^0.121563
            (L^3/vol)^0.36486 (1-CP)^-0.604247
    (Labels corrected 2026-11-09 after Kiran's review: v0.1 had them swapped.)
    """
    _check_version(version)
    L, B, T, cp = p.L, p.B, p.T, p.cp
    lr = _lr(p)
    if version == "1984":
        c14 = 1.0 + 0.011 * p.c_stern
        return 0.93 + 0.487118 * c14 * (B / L) ** 1.06806 * (T / L) ** 0.46106 \
            * (L / lr) ** 0.121563 * (L ** 3 / p.volume) ** 0.36486 * (1 - cp) ** -0.604247
    tl = T / L
    if tl > 0.05:
        c12 = tl ** 0.2228446
    elif tl > 0.02:
        c12 = 48.20 * (tl - 0.02) ** 2.078 + 0.479948
    else:
        c12 = 0.479948
    c13 = 1.0 + 0.003 * p.c_stern
    return c13 * (0.93 + c12 * (B / lr) ** 0.92497 * (0.95 - cp) ** -0.521448
                  * (1 - cp + 0.0225 * p.lcb_pct) ** 0.6906)


def holtrop_mennen(p: HoltropInput, speed_kn: float, *, version: str) -> ResistanceResult:
    """`version` ("1982" or "1984") is required: it selects the form factor and the
    wave-resistance interference term (m2 in [H82], m4 in [H84]). The other
    components use the same formulas in both versions as implemented here."""
    _check_version(version)
    L, B, T, TF = p.L, p.B, p.T, p.TF
    rho, vol = p.rho, p.volume
    cb, cp, cm, cwp = p.cb, p.cp, p.cm, p.cwp
    V = speed_kn * 1852.0 / 3600.0
    q = 0.5 * rho * V ** 2
    fn = V / math.sqrt(G * L)
    re = V * L / p.nu
    cf = ittc57_cf(re)
    ie = p.ie_deg if p.ie_deg is not None else estimate_half_angle_of_entrance(p)

    # friction and form
    k1p = form_factor(p, version)
    rf = q * p.S * cf

    # appendages
    rapp = q * p.s_app * p.k2_app * cf

    # wave resistance, Fn <= 0.4 branch
    bl = B / L
    c7 = 0.229577 * bl ** 0.33333 if bl < 0.11 else (bl if bl < 0.25 else 0.5 - 0.0625 / bl)
    c1 = 2223105.0 * c7 ** 3.78613 * (T / B) ** 1.07961 * (90.0 - ie) ** -1.37565
    if p.abt > 0:
        c3 = 0.56 * p.abt ** 1.5 / (B * T * (0.31 * math.sqrt(p.abt) + TF - p.hb))
    else:
        c3 = 0.0
    c2 = math.exp(-1.89 * math.sqrt(c3))
    c5 = 1.0 - 0.8 * p.at / (B * T * cm)
    lam = 1.446 * cp - 0.03 * L / B if L / B < 12 else 1.446 * cp - 0.36
    if cp < 0.8:
        c16 = 8.07981 * cp - 13.8673 * cp ** 2 + 6.984388 * cp ** 3
    else:
        c16 = 1.73014 - 0.7067 * cp
    m1 = 0.0140407 * L / T - 1.75254 * vol ** (1 / 3) / L - 4.79323 * B / L - c16
    l3v = L ** 3 / vol
    if l3v < 512:
        c15 = -1.69385
    elif l3v > 1726.91:
        c15 = 0.0
    else:
        c15 = -1.69385 + (L / vol ** (1 / 3) - 8.0) / 2.36
    if version == "1982":
        m_int = c15 * cp ** 2 * math.exp(-0.1 * fn ** -2)          # [H82] m2
    else:
        m_int = c15 * 0.4 * math.exp(-0.034 * fn ** -3.29)          # [H84] m4
    rw = c1 * c2 * c5 * vol * rho * G * math.exp(m1 * fn ** -0.9 + m_int * math.cos(lam * fn ** -2))

    # bulbous bow
    rb = 0.0
    if p.abt > 0:
        pb = 0.56 * math.sqrt(p.abt) / (TF - 1.5 * p.hb)
        fni = V / math.sqrt(G * (TF - p.hb - 0.25 * math.sqrt(p.abt)) + 0.15 * V ** 2)
        rb = 0.11 * math.exp(-3.0 * pb ** -2) * fni ** 3 * p.abt ** 1.5 * rho * G / (1 + fni ** 2)

    # immersed transom
    rtr = 0.0
    if p.at > 0:
        fnt = V / math.sqrt(2 * G * p.at / (B + B * cwp))
        c6 = 0.2 * (1 - 0.2 * fnt) if fnt < 5 else 0.0
        rtr = q * p.at * c6

    # model-ship correlation
    c4 = min(TF / L, 0.04)
    ca = (0.006 * (L + 100) ** -0.16 - 0.00205
          + 0.003 * math.sqrt(L / 7.5) * cb ** 4 * c2 * (0.04 - c4))
    ra = q * p.S * ca

    rt = rf * k1p + rapp + rw + rb + rtr + ra
    return ResistanceResult(speed_kn, fn, re, cf, ca, k1p - 1.0, rf, rapp, rw, rb, rtr, ra, rt, rt * V)


# [H82] Table 1, "tankers, bulk carriers"
VALIDITY_TANKER_BULK = {"fn": (0.0, 0.24), "cp": (0.73, 0.85), "L/B": (5.1, 7.1), "B/T": (2.4, 3.2)}


def holtrop_validity(p: HoltropInput, speed_kn: float) -> dict[str, dict]:
    """Return each parameter, its range, and whether it lies inside [H82] Table 1."""
    fn = speed_kn * 1852 / 3600 / math.sqrt(G * p.L)
    vals = {"fn": fn, "cp": p.cp, "L/B": p.L / p.B, "B/T": p.B / p.T}
    return {k: {"value": v, "range": VALIDITY_TANKER_BULK[k],
                "inside": VALIDITY_TANKER_BULK[k][0] <= v <= VALIDITY_TANKER_BULK[k][1]}
            for k, v in vals.items()}
