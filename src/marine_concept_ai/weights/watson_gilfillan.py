"""Lightship mass by the method the REPORT used for its dimension sweep (p.17-18, Table 2.3).

    E    = L (B + T) + 0.85 L (D - T) + 250                     Lloyd's equipment numeral
    SE7  = K E^1.36                                             steel mass at CB = 0.70
    CB8  = CB + (1 - CB)(0.8 D - T) / (3 T)                     CB at 0.8 D
    SE   = SE7 [1 + 0.5 (CB8 - 0.70)]                           steel mass
    OU   = (0.325 - 0.0006 L) L B                               outfit mass
    PD   = 12.2033 * Displacement^0.567  (kW, at 13 kn)         delivered power, Table 2.3
    PB   = 1.02 PD                                              Table 2.4 (7938.55 / 7782.89)
    EP   = 0.102 PB                                             engine-plant mass

K = 0.0305 is the mid value the report took from the bulk-carrier range 0.029-0.032
(p.17). The PD relation is the one behind Table 2.3's power row: PD / Displacement^0.567
is 12.2033 in all ten rows (to 6 significant figures), so the constant is read from the
table, not fitted to a model. It keeps the weight model independent of Holtrop.

Design reserves. The report lists reserve ranges (steel 1-2 %, engine plant 2-3 %,
outfit 4-6 %, p.17) and says the averages are applied, but Table 2.3 and Table 2.4 match
the formulas *without* them (DISC-S2-01 in docs/design_space_sprint2.md). The nominal
scenario therefore has no reserve, and the reserves are used as the weight-uncertainty
scenarios together with the K range.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

PD_CONST_13KN = 12.2033      # kW / t^0.567, REPORT Table 2.3 (all rows)
PB_OVER_PD = 7938.55 / 7782.89   # REPORT Table 2.4
EP_PER_PB = 0.102            # t/kW, REPORT p.17


@dataclass(frozen=True)
class WeightScenario:
    name: str
    k_steel: float
    reserve_steel: float
    reserve_outfit: float
    reserve_ep: float
    source: str


WEIGHT_SCENARIOS = {
    "low": WeightScenario("low", 0.029, 0.0, 0.0, 0.0, "K at bottom of bulk-carrier range, no reserve (p.17)"),
    "nominal": WeightScenario("nominal", 0.0305, 0.0, 0.0, 0.0, "as Table 2.3 / 2.4 (K mid-range, no reserve)"),
    "reserve_avg": WeightScenario("reserve_avg", 0.0305, 0.015, 0.05, 0.025, "K mid-range + average reserves (p.17)"),
    "high": WeightScenario("high", 0.032, 0.02, 0.06, 0.03, "K at top of range + top reserves (p.17)"),
}


@dataclass
class LightshipEstimate:
    e_numeral: float
    se7_t: float
    cb8: float
    steel_t: float
    outfit_t: float
    pd_kw: float
    pb_kw: float
    engine_plant_t: float
    lightship_t: float
    scenario: str

    def as_dict(self):
        return asdict(self)


def lightship_watson_gilfillan(L: float, B: float, D: float, T: float, cb: float,
                               displacement_t: float, scenario: str | WeightScenario = "nominal") -> LightshipEstimate:
    s = WEIGHT_SCENARIOS[scenario] if isinstance(scenario, str) else scenario
    if not (0 < T < D and 0 < cb < 1):
        raise ValueError("need 0 < T < D and 0 < CB < 1")
    e = L * (B + T) + 0.85 * L * (D - T) + 250.0
    se7 = s.k_steel * e ** 1.36
    cb8 = cb + (1 - cb) * (0.8 * D - T) / (3 * T)
    steel = se7 * (1 + 0.5 * (cb8 - 0.70)) * (1 + s.reserve_steel)
    outfit = (0.325 - 0.0006 * L) * L * B * (1 + s.reserve_outfit)
    pd = PD_CONST_13KN * displacement_t ** 0.567
    pb = PB_OVER_PD * pd
    ep = EP_PER_PB * pb * (1 + s.reserve_ep)
    return LightshipEstimate(e, se7, cb8, steel, outfit, pd, pb, ep, steel + outfit + ep, s.name)
