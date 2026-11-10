# Sprint 2 note: first design-space sweep

Draft v0.1, 9 Nov 2026. To reproduce:

```
python experiments/03_design_space/run_sweep.py      # results/tables/s2_*  (about 80 s)
python experiments/03_design_space/make_figures.py   # results/figures/s2_*
pytest -rxs                                          # 81 passed, 2 xfailed (the two open Holtrop items)
```

Rules from Kiran (9 Nov) that this sweep follows:

- Holtrop is **not** used for ranking. Calm-water PE is shown as an indicator only.
- The deadweight requirement is 75 000 t, and the margin is shown under geometry and weight uncertainty.
- A check that cannot be made is **unknown**, never a pass.
- CB is derived from each candidate's own geometry.
- Power is reported as a grid of ηD (0.60 or 0.781) against sea margin.

The only source is the 2019 report. Page numbers are the report's printed numbers.

## 1. Headline

Of 300 Latin-hypercube candidates:

- **80** reach 75 000 t in every uncertainty scenario and pass every check that can be made.
- **14** reach 75 000 t only at nominal.
- **102** fall short.
- **104** fail freeboard or stowage, whatever their deadweight.

No candidate is "feasible" outright. LOA is not in the report (MISS-09), so the Hay Point LOA check is unknown for every candidate. The best status available is therefore *unknown, with LOA as the only open check*.

On the same model, the rebuilt reference ship is **1 195 t short** at nominal. The scenario range is −2 550 t to −655 t. Recovering 75 000 t from the reference by changing one variable alone needs:

| Variable | Nominal | Worst case | What limits it |
|---|---|---|---|
| L | +3.98 m (+1.8%) | +8.79 m (+4.0%) | nothing within bounds. D grows with L, so freeboard improves |
| B | +0.52 m (+1.6%) | +1.12 m (+3.4%) | nothing within bounds |
| T | +0.20 m (+1.4%) | +0.42 m (+3.0%) | **freeboard 0.04 m and stowage 0.001 m³/t from failing** in the worst case |
| CB | +0.012 (+1.4%) | +0.025 (+3.0%) | stowage margin shrinks (0.029 m³/t) |

`s2_recovery_one_at_a_time.csv`, figure `s2_recovery_one_at_a_time.png`.

**Reading for the write-up.** The uncertainty band is about 1 400 t wide (nominal minus worst case, 1 200 to 1 660 t across the robust candidates). The robust change is therefore roughly twice the nominal one. Draught and CB are the cheapest levers on paper, but they eat the freeboard and hold-volume margins the reference already runs thin on: 0.46 m and 0.04 m³/t. Beam and length recover deadweight without touching those margins.

Fitted over the sweep (R² 0.996), deadweight at nominal rises by about 304 t per metre of L, 2 305 t per metre of B, 6 179 t per metre of T and 987 t per 0.01 of CB. This is a linear summary over the bounds, not a model.

## 2. How a candidate is evaluated (`design_space.evaluate_candidate`)

Every candidate, including the reference, goes through the same chain. This is the "common geometry and weight model" from the Sprint 1 framing.

**Geometry** (`geometry.transform`). The hull is built from the Table 3.2 offsets in two steps:

1. The offsets are scaled by L/220.5, B/32.78 and D/19.75.
2. A Lackenby "1 − CP" station shift moves the stations by (1 − x′)·k, with the same k for the fore and aft halves.

k is solved so that the CB *integrated from the candidate's hull* at its draught equals the sampled target. The reported CB, CM, CWP, LCB, KM and S are all integrated, and CB is on LPP (`cb_length_basis`). Tests confirm the following:

- k > 0 changes CP by exactly k(1 − CP), with CM unchanged.
- CB is monotonic in k.
- The identity transform reproduces the Sprint 1 hull.
- An unreachable CB is flagged, never substituted.

Across the sweep, k ranges from −0.16 to +0.35. Negative k removes parallel middle body; CM then drops slightly, to 0.989 at the minimum.

**Weight** (`weights.watson_gilfillan`). This is the report's own method (p.17–18): Watson–Gilfillan steel from the E-numeral with K = 0.0305, outfit from (0.325 − 0.0006 L)·L·B, and engine plant from 0.102·PB. PD = 12.2033·Δ^0.567 kW is the relation behind Table 2.3's power row: the ratio is 12.2033 in all ten rows. The weight model therefore uses neither Holtrop nor the candidate's resistance. It reproduces every row of Table 2.3 (steel within 0.3%, outfit within 0.1%, PD within 0.001%) and the Table 2.4 lightship of 13 250 t (`tests/reference/test_weights_vs_table_2_3.py`).

**Deadweight uncertainty.** Deadweight is displacement × 1.006 minus lightship, evaluated for 2 geometry × 4 weight scenarios. Every scenario bound is from the report or from Sprint 1.

| Scenario | Basis | Reference lightship |
|---|---|---|
| geometry `pchip` (nominal) | offsets, PCHIP, ×1.006 | — |
| geometry `linear` | offsets, linear interpolation, ×1.006 (−0.55%, Sprint 1 §2) | — |
| weight `low` | K = 0.029, bottom of the bulk-carrier range (p.17) | 12 634 t |
| weight `nominal` | K = 0.0305, no reserve, as Tables 2.3/2.4 | 13 174 t |
| weight `reserve_avg` | + average reserves: steel 1.5%, engine plant 2.5%, outfit 5% (p.17) | 13 428 t |
| weight `high` | K = 0.032 + top reserves 2 / 3 / 6% | 14 052 t |

The verdict compares deadweight with 75 000 t. It is *robust* if the worst case (linear geometry, high weight) clears 75 000 t, *nominal_only* if only the nominal case does, *best_case_only* if only the best case does, and *short* otherwise.

The reference lightship here (13 174 t) is 75 t below Table 6.1, because the candidate's integrated CB is 0.817, not the 0.83 of the sizing equation.

**Checks.** `constraints.check_design` runs unchanged, with the nominal deadweight. It covers draught against Bhorsagar and Hay Point, beam, LOA (unknown), freeboard, deadweight, GM₀ and hold volume per tonne of cargo.

**Power indicator.** Holtrop–Mennen PE at 13 kn is computed with both versions and the MCR grid is built from it (ηD 0.60 / 0.781 × sea margin 0–25%, ηS 0.97, 85% MCR; `s2_power_grid.csv`). Nothing is ranked or filtered on it. 231 of the 300 candidates are outside Holtrop's tanker/bulk-carrier range on at least one ratio (B/T, CP or L/B), which is a second reason to keep it as an indicator. For the reference on this pipeline, PE is 4 339 kW (1982) and 4 244 kW (1984). The MCR at a 15% sea margin is 10 087 / 7 750 kW (1982) and 9 865 / 7 579 kW (1984) for ηD 0.60 / 0.781.

## 3. Assumptions added in Sprint 2

| ID | Assumption | Why | Effect |
|---|---|---|---|
| S2-A1 | D = L / 11.165 (reference L/D; report's parent mean 11.16, p.16) | Kiran's brief samples L/B/T/CB only; this is the report's own D rule | Freeboard D − T is tied to L and T |
| S2-A2 | Required freeboard 5.00 m (reference ILLC Type B-60) for every candidate | No ILLC recomputation yet | **Drives most of the 95 freeboard failures.** A real ILLC calculation varies with L, CB and D |
| S2-A3 | KG = 10.70 m × D/19.75 (Table 7.2 full load) | No loading condition per candidate | GM₀ margin is large (≥ 2 m), so this check never binds |
| S2-A4 | Hold volume = 74 177 m³ × (moulded volume to D) / (reference value) | No hold arrangement per candidate | Drives the 91 stowage failures (≥ 0.98 m³/t, oats) |
| S2-A5 | Stores 899.91 t (p.94) for all; cargo = DWT − stores | Same route and endurance | Small |
| S2-A6 | Transom AT = 10.0 m² × (B/B_ref)(T/T_ref); iE from the Holtrop regression | Holtrop indicator only | No effect on feasibility |

**DISC-S2-01.** The report says the average design reserves are added (p.17), but Tables 2.3 and 2.4 match the formulas *without* them. Nominal follows the tables, and the reserves become uncertainty scenarios.

## 4. Design-space bounds (agreed by Kiran, 9 Nov 2026)

`configs/design_space.yaml` is marked `status: agreed`. Every bound comes from the report:

| Variable | Bounds | Source |
|---|---|---|
| L | 200–240 m | Table 2.3 sweep |
| B | 29.7–36.5 m | Table 2.3 lowest to Table 2.1 highest |
| T | 12.6–15.6 m | Table 2.1 lowest to Table 2.3 highest |
| CB | 0.80–0.87 | Table 2.3 lower end less 0.01, to the Dankwardt upper band |

The seed is 20261109.

## 5. Fixed on the way

`constraints.checks._c` now casts each value and the pass flag to plain Python types. With numpy inputs, `satisfied` was a numpy bool, so `satisfied is False` was never true and **failed checks were summarised as unknown**. Sprint 1 used Python floats, so its results are unaffected. The regression test is `test_numpy_inputs_do_not_hide_failures`.

## 6. Comparison with the 2019 length sweep

Run `PYTHONPATH=src python experiments/03_design_space/rerun_report_sweep.py` from the repository root. The replay takes the dimensions and displacement from Table 2.3, derives the block coefficient implied by that displacement, and recomputes nominal lightship and deadweight with the same weight function used in Sprint 2.

| Measure | 2019 report, pp. 18–19 | Automated replay |
|---|---|---|
| Cases | Nine distinct grid lengths from 200 to 240 m in 5 m steps, plus the selected 220.5 m case. The last 205 m column repeats an earlier case. | The same nine grid cases and one selected case |
| Time | The report gives no elapsed time. | About 0.05 ms median per ten-case replay on the Mac, including reading the CSV. Five batches of 1,000 replays, excluding interpreter startup, transcription and output. |
| Selected case | 220.5 m LPP and 75,158.54 t nominal deadweight in Table 2.4 | 220.5 m LPP and 75,160.47 t nominal deadweight, a difference of 1.93 t |

The replay brackets 75,000 t between 220 m (74,189.68 t) and 225 m (79,689.80 t). Linear interpolation between those two cases gives 220.737 m. Figure 2.6 plots points around 216–218 m, consistent with the parent-ship data, so it does not establish how the report selected 220.5 m. The selected row clears the target because of its block coefficient, not its length: it uses CB 0.8301 (implied by its displacement), while the grid trend at 220.5 m gives 0.8264. On the grid trend a 220.5 m ship gives about 74,730 t, roughly 270 t short; the higher CB alone adds about 375 t. The separately published 220.5 m row clears the nominal target on the report's sizing basis.

The geometry-based Sprint 2 evaluation of the same 220.5 m reference falls 1,195 t short at nominal and 2,550 t short in the worst scenario. That change in verdict is the engineering comparison for the exit gate. The 300-case geometry sweep took 78.6 s in the recorded run and evaluates a broader set of inputs and constraints than the sizing replay.

## 7. Sprint scope and open checks

- **Optimisation (D3.3).** Brake-power optimisation was deferred at the Sprint 2 exit gate. The follow-up [displacement search](../experiments/04_optimization/compare_search.py) compares random search and differential evolution on a separate objective, minimum nominal displacement subject to at least 75,000 t DWT in every modelled scenario and the existing concept screens.
- **Freeboard (S2-A2).** The sprint applies the reference 5.00 m minimum as a screening assumption for all candidates. The 95 freeboard failures are conditional on this assumption. Candidate-specific ILLC calculations are outside this sprint.
- **LOA (MISS-09).** The report gives the Hay Point limit of 300 m on p. 9. Table 3.1 on p. 48 gives profile offsets relative to FP and AP, including an LWL stern offset of −7.4 (forward positive). Tables 2.5 and 2.6 on pp. 21–22 show the earlier stem and stern profiles. The software gives a waterline length of 228.149 m on p. 57. These are partial profile and waterline data. The report does not give the full longitudinal extent or a rule for candidate overhangs, so LOA remains unknown for every candidate.
