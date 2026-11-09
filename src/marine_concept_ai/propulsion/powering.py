"""Effective -> delivered -> brake power, with every factor named and sourced.

    PD  = PE / eta_D                         eta_D = quasi-propulsive coefficient (QPC)
    PS  = PD / eta_S                         shaft/stern-tube efficiency
    PB_service = PS * (1 + sea_margin)       power needed in service conditions
    MCR = PB_service / engine_load           engine operated at `engine_load` x MCR

Defaults are the values the REPORT used where it states one (QPC 0.60, eta_S 0.97,
engine load 0.85, p.36-37). The sea margin is not stated in the report: the default
of 15 % is a common preliminary-design allowance and is an ASSUMPTION (A8).
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field


@dataclass
class PoweringAssumptions:
    eta_d: float = 0.60          # REPORT p.36-37 (QPC)
    eta_s: float = 0.97          # REPORT p.37
    sea_margin: float = 0.15     # ASSUMPTION A8, not in REPORT
    engine_load: float = 0.85    # REPORT p.37 ("PD/0.85 MCR")
    sources: dict = field(default_factory=lambda: {
        "eta_d": "REPORT p.36-37",
        "eta_s": "REPORT p.37",
        "sea_margin": "assumption A8 (not stated in REPORT)",
        "engine_load": "REPORT p.37",
    })


@dataclass
class PowerChain:
    pe_kw: float
    pd_kw: float
    ps_kw: float
    pb_service_kw: float
    mcr_kw: float
    assumptions: PoweringAssumptions

    def as_dict(self):
        d = asdict(self)
        d.pop("assumptions")
        d.update({f"a_{k}": v for k, v in asdict(self.assumptions).items() if k != "sources"})
        return d


def power_chain(pe_kw: float, a: PoweringAssumptions | None = None) -> PowerChain:
    a = a or PoweringAssumptions()
    for name in ("eta_d", "eta_s", "engine_load"):
        v = getattr(a, name)
        if not 0 < v <= 1:
            raise ValueError(f"{name}={v} must be in (0, 1]")
    if a.sea_margin < 0:
        raise ValueError("sea_margin must be >= 0")
    pd = pe_kw / a.eta_d
    ps = pd / a.eta_s
    pbs = ps * (1 + a.sea_margin)
    return PowerChain(pe_kw, pd, ps, pbs, pbs / a.engine_load, a)


def holtrop_propulsion_factors(L, B, T, cb, cp, cm, lcb_pct, S, cf, ca, k1, D_prop,
                               ae_a0=0.35, c_stern=0.0):
    """Single-screw wake fraction, thrust deduction and eta_R from [H84].

    D_prop is the propeller diameter in m. The REPORT does not fix it (DISC-09), so the
    caller must state which value it uses.
    """
    TA = T
    bta = B / TA
    c8 = B * S / (L * D_prop * TA) if bta < 5 else S * (7 * bta - 25) / (L * D_prop * (bta - 3))
    c9 = c8 if c8 < 28 else 32 - 16 / (c8 - 24)
    c11 = TA / D_prop if TA / D_prop < 2 else 0.0833333 * (TA / D_prop) ** 3 + 1.33333
    if cp < 0.7:
        c19 = 0.12997 / (0.95 - cb) - 0.11056 / (0.95 - cp)
    else:
        c19 = 0.18567 / (1.3571 - cm) - 0.71276 + 0.38648 * cp
    c20 = 1 + 0.015 * c_stern
    cp1 = 1.45 * cp - 0.315 - 0.0225 * lcb_pct
    cv = (1 + k1) * cf + ca
    w = (c9 * c20 * cv * L / TA * (0.050776 + 0.93405 * c11 * cv / (1 - cp1))
         + 0.27915 * c20 * math.sqrt(B / (L * (1 - cp1))) + c19 * c20)
    t = (0.25014 * (B / L) ** 0.28956 * (math.sqrt(B * T) / D_prop) ** 0.2624
         / (1 - cp + 0.0225 * lcb_pct) ** 0.01762 + 0.0015 * c_stern)
    eta_r = 0.9922 - 0.05908 * ae_a0 + 0.07424 * (cp - 0.0225 * lcb_pct)
    return {"w": w, "t": t, "eta_r": eta_r, "eta_h": (1 - t) / (1 - w)}
