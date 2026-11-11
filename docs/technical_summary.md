# Technical summary: automated preliminary design of a 75,000 DWT bulk carrier

Draft v0.1, 10 Nov 2026. This summary brings together the Sprint 1 validation note, the Sprint 2 design-space note and the follow-up search and surrogate benchmarks. It is the reference for the numbers quoted in the README and the NTNU application. Section 10 lists the files each result comes from.

## 1. Purpose and scope

The study asks whether a 2019 manual preliminary design can be rebuilt as a reproducible calculation chain, checked against its own source, and then used to explore the design space around it. The case is a 75,000 t deadweight bulk carrier at 13 kn on the Bhorsagar to Hay Point route, designed in the author's B.Tech report (2019).

The only design source is that report. The original spreadsheets, CAD, MAXSURF, NavCad and Autohydro files are not available. Every reference value is therefore taken from the printed tables, and each transcribed table in `data/reference/` names its page. The one external benchmark is the worked example on p. 170 of Holtrop and Mennen (1982), checked against a scan of the published page.

In scope: hull reconstruction from offsets, upright hydrostatics, Holtrop–Mennen resistance as an indicator, a Watson–Gilfillan weight model, deadweight feasibility under uncertainty, concept screens, sampling, a comparison of two search methods and a surrogate benchmark. Out of scope: lines design, general arrangement, intact and damage stability, structure, seakeeping and cost.

## 2. Reference design

| Quantity | Value | Source |
|---|---|---|
| LPP | 220.5 m | Table 2.4 |
| Breadth, depth, design draught | 32.78 m, 19.75 m, 14.29 m | Table 2.4 |
| Block coefficient | 0.83 for the historical sizing equation (the report prints 0.82, but 0.83 reproduces its displacement) | Table 2.4, p. 60 |
| Service speed | 13 kn | Owner requirements |
| Displacement, sizing equation | 88,409 t | L·B·T·CB·1.025·1.006 |
| Lightship | 13,249 t | Table 6.1 |
| Calm-water resistance and effective power at 13 kn | 635.9 kN, 4,249 kW | Table 4.2 (NavCad) |
| Brake power | Not used. The report's value cannot be reproduced from its own inputs | `reference_bulk_carrier.yaml` (null) |

The report's inconsistencies are recorded in `docs/missing_data_register.md` and are not used as inputs. Examples are the lightship in the loading tables (DISC-11) and the printed CB.

## 3. Engineering models

| Module | Method | Main assumption |
|---|---|---|
| Geometry | Table 3.2 offsets interpolated with PCHIP (linear as a sensitivity). Candidate hulls are scaled by L, B and D, and then a Lackenby 1 − CP station shift is applied, solved so that the integrated CB equals the target | Waterline heights WL_n = 2.6·n m (A7). The offsets stop at AP and FP |
| Hydrostatics | Trapezoidal integration on an 801 × 241 grid. Gives displacement, centres, KM, TPC, MCT, form coefficients and wetted surface | Upright, even keel. Shell factor 1.006 |
| Weights | Watson–Gilfillan steel (E-numeral, K = 0.0305), outfit (0.325 − 0.0006 L)·L·B and machinery 0.102·PB, with PD = 12.2033·Δ^0.567 kW as in Table 2.3 | The report's own method (pp. 17–18) |
| Deadweight | Displacement × 1.006 minus lightship, in 2 geometry × 4 weight scenarios | Scenario bounds from the report (§6.2) |
| Resistance | Holtrop–Mennen 1982 or 1984, chosen explicitly (no default), with validity warnings | Indicator only, not used for ranking (§4.3) |
| Powering | PE → PD → PB → MCR, with each factor named. ηD 0.60 (historical) and 0.781 (sensitivity) against sea margins from 0 to 25% | Sea margin 15% is one scenario (A8) |
| Constraints | Draught against Bhorsagar and Hay Point, beam, LOA, freeboard, deadweight, GM₀ and hold volume per tonne. Each check is pass, fail or unknown | A check that cannot be made is unknown, never a pass |

The engine is a Python package (`src/marine_concept_ai`) with 81 tests. Two further tests are strict expected failures, which track the open benchmark items in §4.3.

## 4. Validation against the source

### 4.1 Sizing equation

The engine reproduces the 88,409 t design-equation displacement with CB 0.83, inside the ±0.5% tolerance. The automated replay of the report's length sweep gives 75,160.47 t nominal deadweight for the selected 220.5 m ship, 1.93 t from the 75,158.54 t in Table 2.4. The weight model reproduces every row of Table 2.3 (steel within 0.3%, outfit within 0.1%, delivered power within 0.001%).

### 4.2 Hydrostatics from the offsets

At T = 14.29 m, the hull rebuilt from the offsets displaces 86,455 t without the shell factor. That is 2.0% above the 84,755 t from the 2019 software hydrostatics (Table 3.4). Comparing slice by slice locates the difference: between 3.985 and 13.366 m every slice agrees within ±0.3%, and 1,636 t of the 1,700 t gap lies below 2.3 m. The 2019 software hull starts from a keel line, while the offsets have a 27.5 m flat of bottom. The integration is converged to better than 0.001%. Linear interpolation of the same offsets gives 0.55% less displacement than PCHIP, and that difference is carried as an uncertainty scenario.

### 4.3 Resistance

**Published benchmark.** On the Holtrop and Mennen (1982) worked example, the engine reproduces S, RF, Rapp, Rw, RB and RTR. Two items remain open:

1. With the printed LCB of −2.02%, the printed formulas do not give the printed 1 + k1 (1.156) or iE (12.08°). Both are reproduced with LCB = −0.75%, which suggests an inconsistency in the published example itself.
2. The correlation allowance RA is 220.57 kN against 221.98 kN printed (−0.64%). The cause has not been identified.

Until both are reconciled, Holtrop results are shown as indicators and never used to rank or filter candidates.

**Comparison with NavCad (Table 4.2).** At 13 kn, Rt on the rebuilt hull is +1.7% (1982 version) and −0.6% (1984 version) from Table 4.2. Both are inside the legacy ±5% threshold. The two versions bracket the NavCad result, and the fit cannot show which version NavCad used. Above 14 kn the engine overpredicts by up to 7.9%, because NavCad prints almost zero wave resistance. B/T = 2.29 is below Holtrop's range for bulk carriers and is flagged.

## 5. Finding: the reference ship's deadweight depends on the hull representation

With the same 13,249 t lightship, the deadweight at the 14.29 m design draught is:

| Displacement basis | Deadweight | Margin to 75,000 t |
|---|---|---|
| Preliminary sizing equation | 75,160 t | +160 t |
| Hull rebuilt from the published offsets, with shell factor | 73,725 t | −1,275 t |
| 2019 software hydrostatics | 71,506 t | −3,494 t |

The feasibility verdict changes with the hull representation. The report records one design iteration, the length sweep, and its conclusion notes that further iterations on the design spiral are needed (Ch. 10). This motivated the design-space study: use one geometry and weight model for every candidate, the reference included, and measure how much margin remains under uncertainty.

## 6. Design-space exploration

### 6.1 Design variables and bounds

Four variables are sampled, with bounds from the report's own data (agreed 9 Nov 2026, `configs/design_space.yaml`): L 200–240 m, B 29.7–36.5 m, T 12.6–15.6 m and CB 0.80–0.87. Depth follows from D = L/11.165, the reference ratio (S2-A1). The study uses 300 Latin-hypercube candidates with seed 20261109.

### 6.2 Uncertainty scenarios

Deadweight is evaluated with two geometry bases (PCHIP and linear interpolation of the offsets) and four weight bases (K = 0.029, K = 0.0305 nominal, nominal plus average reserves, K = 0.032 plus top reserves; all from p. 17). A candidate is **robust** if it reaches 75,000 t in the worst case (linear geometry, high weight). The band between nominal and worst case is about 1,400 t.

### 6.3 Results

- **80** of 300 candidates reach 75,000 t in every scenario and pass every check that can be made.
- **14** reach it only at nominal, and **102** fall short.
- **104** fail the freeboard or hold-volume screen regardless of deadweight (95 freeboard, 91 hold volume, with overlap).
- LOA cannot be checked for any candidate (MISS-09), so the best status available is *unknown, with LOA as the only open check*.

On the common model, the reference ship is **1,195 t short** at nominal (from −2,550 t in the worst case to −655 t in the best). Changed one variable at a time, it reaches 75,000 t at nominal with +3.98 m of length, +0.52 m of beam, +0.20 m of draught or +0.012 of CB. The robust (worst-case) changes are roughly twice as large. Draught and CB are the cheapest changes on paper, but they use up the freeboard and hold-volume margins, which on the reference are only 0.46 m and 0.04 m³/t. Length and beam recover deadweight without touching either margin.

### 6.4 Comparison with the 2019 workflow

The report's length sweep has nine grid lengths plus the selected case, computed by hand or spreadsheet with no recorded time. The automated replay reproduces it in about 0.05 ms per ten-case run and places the 75,000 t crossing at 220.737 m by linear interpolation between the 220 m and 225 m rows. The selected 220.5 m row clears the target because of its CB, 0.8301, against 0.8264 on the grid trend. On the trend it would be about 270 t short.

The 300-case geometry-based sweep took 78.6 s. It evaluates four variables, eight uncertainty scenarios and eight checks per candidate, where the 2019 sweep used one variable and one deterministic scenario.

## 7. Displacement search: random search and differential evolution

**Objective.** Minimise nominal displacement, subject to at least 75,000 t deadweight in the worst scenario and the Sprint 2 concept screens. Holtrop is disabled. This stands in for the brake-power objective of the original plan (D3.3), which was deferred because it depends on the unreconciled resistance benchmark. Minimum displacement is a proxy for a smaller, cheaper hull, not a powering result.

**Protocol.** Both methods get 96 physics evaluations per seed, the same bounds and the same first 16 points. Differential evolution runs a population of 16 for five generations, with no polishing step. There are three seeds.

| Seed | Random: best displacement | DE: best displacement | Lower | Worst-case DWT margin (random / DE) | Candidates passing the screen (random / DE) |
|---|---|---|---|---|---|
| 20261109 | 90,532 t | 89,815 t | DE | +569 t / +52 t | 26 / 38 |
| 20261110 | 91,482 t | 89,319 t | DE | +1,279 t / +132 t | 18 / 32 |
| 20261111 | 90,335 t | 90,364 t | Random (by 28 t) | +546 t / +38 t | 21 / 38 |

**Reading.** At this budget, differential evolution found the lower displacement in two of three seeds, and it found more screen-passing candidates in all three. Three seeds are not enough to claim that one method is better in general. DE's lower displacements come with worst-case deadweight margins of only 38 to 132 t and hold-volume margins as small as 0.004 m³/t. This is expected, because an optimiser drives to the constraint boundary. It also means those candidates are only as good as the scenario bounds and the screening assumptions (S2-A2, S2-A4). Every selected candidate still has LOA unknown.

## 8. Surrogate benchmark

**Set-up.** Two regressors predict nominal displacement and worst-case deadweight from (L, B, T, CB). They are trained on 240 of the 300 archived sweep candidates and tested on the other 60 (fixed split, seed 20261109).

| Model | Worst-case DWT MAE | RMSE | Max error | Wrong 75,000 t decisions | Time for 60 predictions |
|---|---|---|---|---|---|
| Linear regression | 349.3 t | 467.0 t | 1,881.7 t | 0 | 0.02 ms |
| Quadratic ridge | 13.1 t | 19.2 t | 75.0 t | 0 | 0.12 ms |
| Physics evaluator | — | — | — | — | 3.55 s |

**Reading.** Within the sampled bounds, a quadratic model reproduces the engine's worst-case deadweight with a 13 t mean error, about 1% of the 1,400 t uncertainty band. It predicts about 30,000 times faster than the physics evaluator. Neither model made a wrong threshold decision on the test set. However, the nearest test case was 536 t from 75,000 t, so the test says almost nothing about decisions near the threshold, which are the ones that matter for screening. The surrogate approximates this engine, not the ship. Its error is measured against the engine's output, and any candidate it proposes must be confirmed with the physics evaluator.

## 9. Assumptions and limitations

**Assumptions** (full list in `docs/missing_data_register.md` and the Sprint 2 note):

- A7: waterline heights for the offset table, inferred from the 2.6 m spacing.
- A8: a 15% sea margin as one scenario, varied from 0 to 25%.
- A9: appendages limited to a rudder in Holtrop.
- S2-A1: D = L/11.165 for all candidates.
- S2-A2: a fixed 5.00 m freeboard requirement for all candidates. This drives most freeboard failures.
- S2-A3: KG scaled with D from the full-load condition.
- S2-A4: hold volume scaled with moulded volume. This drives the stowage failures.
- S2-A5: fixed stores of 899.91 t.

**Limitations:**

- **Resistance benchmark open.** Two discrepancies on the published example (LCB and RA) remain, so brake-power ranking (D3.3) is deferred.
- **Freeboard.** Screened against a fixed 5.00 m value, not a candidate-specific ILLC calculation.
- **LOA.** Unknown for every candidate, because the report gives no full longitudinal profile.
- **Geometry.** Every candidate is a transformation of one parent hull. The offsets stop at AP and FP, so the stern overhang and bulb nose are missing. Hydrostatics are upright and even keel only.
- **Search evidence.** Three seeds at one budget.
- **Surrogate evidence.** One split, with no test points near the threshold.
- **Single source.** The validation is against the report's printed values and one published example, not against an independent ship.

## 10. Reproducibility and traceability

The code, transcribed data and results are in the public repository `kiranjojose/ship-concept-design-ai`. All random elements are seeded. The README lists the commands. A full run consists of the test suite, the length-sweep replay, the displacement search and the surrogate benchmark. The 300-case sweep and figures can be regenerated separately.

| Section | Result file |
|---|---|
| §4.2, §4.3, §5 | `results/tables/s1_summary.json`, `s1_hydrostatics_vs_table_3_4.csv`, `s1_resistance_vs_table_4_2.csv`, `s1_deadweight_margin_scenarios.csv` |
| §4.3 benchmark | `data/literature/holtrop_mennen_1982_example.yaml`, `tests/unit/test_holtrop_mennen.py` |
| §4.1, §6.4 | `experiments/03_design_space/rerun_report_sweep.py`, `tests/reference/test_report_sweep_replay.py` |
| §6.3 | `results/tables/s2_summary.json`, `s2_sweep_candidates.csv`, `s2_recovery_one_at_a_time.csv` |
| §7 | `results/tables/displacement_search.json` |
| §8 | `results/tables/surrogate_benchmark.json` |

Timings were measured on the author's Mac and will differ on other machines.

## 11. What comes next

The planned Phase B work builds on the limitations above:

- a parametric hull with its own LOA and overhangs;
- candidate-specific freeboard;
- reconciling the Holtrop benchmark, so that brake power can become the objective;
- surrogate tests concentrated near the constraint boundary, with active sampling there;
- a controlled comparison of the manual and automated workflows.
