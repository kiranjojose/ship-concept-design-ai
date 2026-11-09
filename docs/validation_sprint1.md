# Sprint 1 validation note: calculation engine vs the 2019 report

Draft v0.3, 9 Nov 2026. v0.2 applied Kiran's review; v0.3 adds the printed p.170 benchmark values (from Kiran's scan) and the deadweight framing. Changes are listed in §9. To reproduce:

```
python experiments/01_reference_reconstruction/run_reference.py   # writes results/tables/s1_*
pytest -rxs                                                        # 46 pass, 2 xfail (the two open benchmark discrepancies)
```

Source of every reference value: the B.Tech report (`data/raw/kiran_btech_report_2019.pdf`). Page numbers are the report's printed numbers. IDs such as DISC-06 and A7 refer to `docs/missing_data_register.md`.

## 1. What the engine does

| Module | Method | Inputs |
|---|---|---|
| `geometry.offsets` | Offset table, interpolated with PCHIP (default) or piecewise-linear, first vertically then longitudinally | Table 3.2, plus waterline heights from assumption A7 |
| `hydrostatics` | Trapezoidal integration on an 801 × 241 grid. Gives volume, displacement, LCB, KB, Awp, LCF, BMT, BML, KM, TPC, MCT, the form coefficients and wetted surface (triangulated hull surface). Coefficients are derived from the geometry of each hull, and each result records its length basis (`length_basis = "LPP"`) | Offsets, draught |
| `resistance.holtrop_mennen` | Holtrop–Mennen with `version="1982"` or `"1984"`, chosen by the caller (there is **no default**, see §3). Also the S and iE regressions and the validity ranges | Hull particulars |
| `propulsion.powering` | PE to PD to PS to PB (service) to MCR, with each factor named and sourced. Holtrop's single-screw w, t and ηR are computed for information only | PE, efficiencies, margins |
| `constraints` | Port limits, freeboard, deadweight balance, GM₀ and hold volume. Overall status is pass, fail or **unknown**: a check that could not be evaluated is never counted as a pass | Design particulars |
| `reference` | Builds the reference ship's inputs as two cases: the NavCad inputs printed on p.60, and a hull fully rebuilt from the offsets | YAML and offsets |

## 2. Hydrostatics: rebuilt hull vs Table 3.4

**Reconstruction assumption A7.** The report gives a 2.6 m waterline spacing (p.48) but does not map the labels to heights. The engine uses WL_n = 2.6·n m, LWL = 14.29 m and MDK = 19.75 m.

**Numerical convergence** (`results/tables/s1_hydrostatics_convergence.csv`) is checked separately from agreement with the report. At T = 14.29 m, the default 801 × 241 grid differs from a 1601 × 481 grid by less than 0.001% in volume, KB, BMT and wetted surface. The test `test_hydrostatics_numerically_converged` enforces 0.01%.

At the design draught, T = 14.29 m:

| Quantity | Engine (offsets) | Table 3.4 / p.57 | Difference |
|---|---|---|---|
| Displacement, ρ = 1.025, no shell factor | 86 455 t | 84 755 t | +2.0% |
| Waterplane area | 6 446 m² | 6 511 m² | −1.0% |
| KB | 7.47 m | 7.61 m | −0.14 m |
| KMt | 13.61 m | 13.85 m | −0.25 m |
| LCB from AP | 112.16 m | 111.86 m (datum not stated, MISS-12) | +0.29 m |
| TPC | 66.07 | 66.74 | −1.0% |
| Wetted surface | 11 481 m² | 11 279 m² (NavCad input: 11 356 m²) | +1.8% (+1.1%) |
| CM | 0.991 | 0.971 (design value 0.992, p.20) | |
| CB on LBP | 0.817 | 0.774 on LWL = 228.1 m | |

**Where the gap comes from.** Table 3.4's draughts are steps of 9 823 t, so its rows can be compared slice by slice:

| Slice | Engine vs Table 3.4 |
|---|---|
| 0 → 2.289 m | +16.7% (1 636 t of the 1 700 t total gap) |
| 2.289 → 3.985 m | +1.0% |
| 3.985 → 13.366 m, each slice | within ±0.3% |
| 13.366 → 14.29 m | −1.3% |

The whole 2% gap is in the bottom 2.3 m. In Table 3.4 the beam at T = 0 is 0.001 m, so the 2019 software hull started from a keel line. The offsets have a 27.5 m flat of bottom at the baseline. The deficit in the top slice is the stern overhang aft of AP, which is in the software's 228.1 m waterline but not in the offsets.

**Interpolation sensitivity.** Linear interpolation of the same offsets gives 85 978 t, 0.55% below PCHIP. This modelling uncertainty is much larger than the numerical error, and it is carried into the deadweight margin in §5.

## 3. Resistance: Holtrop–Mennen vs Table 4.2 (NavCad)

### 3.1 Version labels corrected, and no default until the benchmark is reconciled

v0.1 had the two form-factor equations under each other's labels. As Kiran pointed out, the equation with c12, c13 and (B/LR) is from the **1982** paper, and the one with 0.487118·c14 is from **1984**. The labels are now corrected. The version also controls the wave-resistance interference term: m2 = c15·CP²·exp(−0.1 Fn⁻²) in 1982, and m4 = 0.4·c15·exp(−0.034 Fn⁻³·²⁹) in 1984. RF, RA, RTR, RB and Rapp use the same formulas in both versions as implemented. `holtrop_mennen()` now requires `version=`, so no result is computed with a version that was not explicitly chosen.

**Benchmark: Holtrop & Mennen (1982) worked example, printed p.170.** Kiran confirmed every printed value from a scan of the published page. The values are in `data/literature/holtrop_mennen_1982_example.yaml`.

Printed inputs: LWL = 205 m (used as L), LPP = 200 m, B = 32 m, TF = TA = 10 m, ∇ = 37 500 m³, LCB 2.02% aft of ½LWL, CM 0.980, CWP 0.750, ABT 20 m² at hB = 4 m, AT 16 m², Sapp 50 m² with (1+k2) = 1.50, Cstern = +10, V = 25 kn.

| Quantity | Printed | Engine (1982), printed LCB −2.02% | Engine (1982), inferred LCB −0.75% | Check |
|---|---|---|---|---|
| LR | — | 74.551 m | 81.385 m | — |
| 1+k1 | 1.156 | 1.16247 | 1.15644 | **open**: reproduces only at the inferred LCB |
| iE (regression) | 12.08° | 11.841° | 12.077° | **open**: reproduces only at the inferred LCB |
| S (regression) | 7 381.45 m² | 7 381.45 | 7 381.45 | pass (independent of LCB) |
| RF | 869.63 kN | 869.64 | 869.64 | pass |
| Rapp | 8.83 kN | 8.84 | 8.84 | pass (within print rounding) |
| Rw | 557.11 kN | 556.86 | 556.86 | pass, −0.05% |
| RB | 0.049 kN | 0.049 | 0.049 | pass |
| RTR | 0.00 kN | 0.00 | 0.00 | pass (FnT > 5) |
| RA | 221.98 kN | 220.57 | 220.57 | **open**: −0.64%, cause not identified |
| Rt | 1 793.26 kN | 1 797.25 (+0.22%) | 1 792.01 (−0.07%) | follows from the two open items |

**Discrepancy 1, LCB (in the worked example itself).** With the printed formulas, the printed LCB of −2.02% gives 1+k1 = 1.16247 and iE = 11.841°. The printed intermediate results, 1.156 and 12.08°, are reproduced to their printed precision only with LCB = −0.75%. The fixture keeps −2.02% as the printed input and records −0.75% separately, labelled as *inferred from the worked outputs*. The inconsistency appears to be in the published example, not in the code: both Kiran's run and this engine get the same numbers.

**Discrepancy 2, correlation allowance.** The engine's RA is 220.57 kN against 221.98 kN printed. It does not depend on LCB, and using LPP = 200 m instead of LWL makes it worse (224.6 kN). The cause is not identified. With the inferred LCB, the Rt residual (−1.25 kN) is almost exactly this RA gap (−1.41 kN).

**How the tests treat this.** Every quantity that does not depend on LCB is asserted against the printed value: S, RF, Rapp, Rw, RB and RTR. The LCB-dependent outputs are asserted at the inferred LCB. The two discrepancies are strict xfails, at the printed LCB and on exact RA. They show up in every test run, and they fail loudly if the code changes so that they unexpectedly pass. A further test bounds the RA gap at 1%. **The benchmark stays open** until both discrepancies are reconciled, or explained by a second source such as the 1984 paper or a published re-implementation.

**Holtrop stays out of candidate ranking until the benchmark is closed** (Kiran, 9 Nov). Both versions are reported below.

### 3.2 Comparison with Table 4.2

Rt from the engine, with the deviation from Table 4.2:

| Speed (kn) | 8 | 9 | 10 | 11 | 12 | **13** | 14 | 15 |
|---|---|---|---|---|---|---|---|---|
| Table 4.2 (kN) | 258.4 | 321.8 | 391.4 | 467.0 | 548.6 | **635.9** | 728.8 | 827.3 |
| Rebuilt hull, 1982 | −1.3% | −1.3% | −1.1% | −0.7% | +0.1% | **+1.7%** | +4.3% | +7.9% |
| Rebuilt hull, 1984 | −3.5% | −3.5% | −3.3% | −2.9% | −2.1% | **−0.6%** | +1.9% | +5.7% |
| NavCad inputs, 1982 | −0.5% | −0.4% | −0.2% | +0.2% | +1.1% | **+2.7%** | +5.4% | +9.1% |
| NavCad inputs, 1984 | −3.4% | −3.4% | −3.2% | −2.8% | −1.9% | **−0.3%** | +2.3% | +6.3% |

Calm-water PE at 13 kn (rebuilt hull) is 4 325 kW with the 1982 version and 4 229 kW with 1984; the report gives 4 249 kW.

**The legacy comparison threshold (±5% at 13 kn) is met by all four combinations.** This is a comparison with a historical software output, not a validation of either version. As Kiran noted, the fit alone cannot tell which version NavCad used: the 1982 and 1984 results bracket Table 4.2, and both depend on unprinted inputs.

Components:

- **RF and RA** match NavCad within 1.8% and 1.2% at every speed.
- **Transom.** AT = 10.0 m², recovered by inverting NavCad's RTR at 13 kn. With that one number, the engine reproduces NavCad's RTR at the other seven speeds to within 0.1%. Rt at 13 kn with AT = 0, 10 and 22.4 m² (section at AP, an upper bound): −0.0%, +1.7% and +7.9% (1982), and −2.3%, −0.6% and +5.6% (1984).
- **Form factor.** Table 4.2's components imply (1+k1) ≈ 1.304. The engine gives 1.333 (1982) and 1.297 (1984) on the rebuilt hull. These are not decisive, because LCB and Cstern were not printed.
- **Wave resistance.** NavCad prints Rw ≈ 10⁻⁷ kN at every speed. Both versions give about 19 kN at 13 kn and 75–77 kN at 15 kn. This is the source of the high-speed excess.
- **Appendages.** NavCad gives 20.8 kN. The engine models only a rudder (A9), which gives 5.0 kN.
- **Validity.** B/T = 2.29 is below Holtrop's tanker and bulk-carrier range (2.4–3.2) and is flagged.

## 4. Power at 13 kn

**The primary hull metric is calm-water PE at 13 kn** (§3.2). Installed power is indicative only, and **reference brake power stays unknown** (`null` in the YAML).

MCR from the rebuilt hull's PE, with ηS = 0.97 and engine load 85% MCR (p.37). The ηD scenario and the sea margin are varied separately:

| Version | ηD scenario | SM 0% | SM 10% | **SM 15%** | SM 20% | SM 25% |
|---|---|---|---|---|---|---|
| 1982 | historical 0.60 (p.36–37) | 8 742 | 9 616 | **10 054** | 10 491 | 10 928 |
| 1982 | sensitivity 0.781 (report's own w, t, ηR, ηO; DISC-18) | 6 718 | 7 390 | **7 726** | 8 062 | 8 398 |
| 1984 | historical 0.60 | 8 549 | 9 404 | **9 831** | 10 259 | 10 686 |
| 1984 | sensitivity 0.781 | 6 570 | 7 227 | **7 555** | 7 884 | 8 212 |

All values are kW. The 15% sea margin (A8) is an explicit scenario: the report states no sea margin. The ηD of 0.927 from Holtrop's w, t and ηR at D = 9.4 m is **excluded from engine sizing** until the propeller operating point (diameter and rpm, DISC-09) is supported. It is kept in `s1_summary.json` for information only. Full grid: `results/tables/s1_power_chain_13kn.csv`.

## 5. Constraints and the deadweight requirement

**The design requirement is 75 000 t DWT.** The margin under displacement (geometry) and lightship (weight) uncertainty, where every input is a reported value or an engine output (`s1_deadweight_margin_scenarios.csv`):

| Displacement basis \ Lightship | 13 249 t (Table 6.1) | 13 250 t (Table 2.4) | 10 927 t (loading tables, DISC-11) |
|---|---|---|---|
| Design equation, 88 409 t | **+160 t** | +159 t | +2 482 t |
| Offsets, PCHIP, ×1.006 (86 974 t) | **−1 275 t** | −1 277 t | +1 047 t |
| Offsets, linear, ×1.006 (86 494 t) | −1 755 t | −1 756 t | +567 t |
| Offsets, PCHIP, no shell factor (86 455 t) | −1 794 t | −1 795 t | +528 t |
| 2019 software hull, 84 755 t | −3 494 t | −3 495 t | −1 172 t |

The requirement is met only with the design-equation displacement, or with the low lightship from the loading tables, which DISC-11 shows is inconsistent with Table 6.1. With the lightship from Table 6.1, every geometry-based displacement falls short, by 1 275 to 3 494 t depending on the basis.

**Framing for the NTNU write-up** (Kiran's wording, 9 Nov). The two shortfalls come from different hull representations. The 1 275 t comes from the reconstruction from the published offsets, with the shell factor. The 3 494 t comes from the original 2019 software hydrostatics. Both use the detailed 13 249 t lightship.

> At the 14.29 m design draught, the preliminary sizing equation gives 75,160 t deadweight. Using the same lightship estimate, reconstruction from the published offsets gives 73,725 t, and the original software hydrostatics imply 71,506 t. This changes the feasibility verdict. The next stage will use a common geometry and weight model to determine which design changes recover the 75,000 t requirement and how much margin remains under uncertainty.

Other checks on the reference design:

| Check | Value | Limit | Result |
|---|---|---|---|
| Draught vs Bhorsagar depth (p.9) | 14.29 m | ≤ 16.41 m | pass (no under-keel clearance applied) |
| Draught vs Hay Point (p.9) | 14.29 m | ≤ 17.6 m | pass |
| Beam vs Hay Point | 32.78 m | ≤ 53 m | pass |
| LOA vs Hay Point | not in report | ≤ 300 m | **unknown** (MISS-09) |
| Freeboard D − T | 5.46 m | ≥ 5.00 m (p.43–44) | pass |
| GM₀ = KM(offsets) − KG 10.70 (Table 7.2) | 2.91 m | ≥ 0.15 m | pass |
| Hold volume / cargo | 0.999 m³/t | ≥ 0.98 (oats) | pass, with a thin margin |

**Overall status:** *unknown* with the design-equation displacement, because LOA is missing. *Fail* with the rebuilt-hull displacement. v0.1 reported the design-equation case as feasible even though the LOA check was skipped; that is now fixed.

## 6. Gate status

| Gate | Status |
|---|---|
| Design-equation displacement within ±0.5% of 88 409 t | **Pass**: reproduced from L·B·T·CB·1.025·1.006 with CB 0.83 (historical sizing basis; candidates use geometry-derived CB) |
| Rt within ±5% at 13 kn (legacy comparison) | **Met by both versions**, but it is not a validation. The benchmark reconciliation (§3.1) is open |
| Hydrostatic integration converged | **Pass**: < 0.001% at the default grid |
| Rebuilt hull vs Table 3.4 | +2.0% overall; slices from 3.985 to 13.366 m within ±0.3%; gap explained |

## 7. Decisions recorded (Kiran, 9 Nov 2026)

1. **CB 0.83** reproduces the historical sizing equation and the NavCad input. Each candidate derives CB from its own geometry, with the length basis recorded.
2. **2.6 m waterline spacing** (p.48). The label-to-height mapping is a documented reconstruction assumption (A7).
3. **Power.** Calm-water PE is primary. ηD 0.60 is the historical scenario and 0.781 the sensitivity. A 15% sea margin is one explicit scenario, varied separately. Reference PB stays unknown. The 0.927 case is excluded from sizing.
4. **Holtrop version.** No default until the 1982 benchmark is reconciled.
5. **Tolerances.** ±0.5% on the historical sizing equation, ±5% at 13 kn as a legacy threshold, a separate numerical convergence check, and 75 000 t DWT as the design requirement with its margin shown. Missing required checks are unknown.

## 8. Open items

- **Holtrop benchmark** (§3.1): discrepancy 1 (LCB) and discrepancy 2 (RA) are open. Next step: compare against a second source, such as the 1984 paper's example or a published re-implementation.
- **Mac test run:** confirmed by Kiran, 9 Nov (v0.2: 41 passed, 3 skipped). Please re-run after this update: expect 46 passed, 2 xfailed.

## 9. Changes

v0.3 (9 Nov):

- p.170 values confirmed from Kiran's scan.
- Benchmark checks turned on for the quantities that don't depend on LCB.
- LCB −0.75% labelled as inferred.
- LCB and RA discrepancies documented, and tracked as strict xfails.
- Deadweight framing added.

v0.2 (9 Nov), changes from v0.1:

- Form-factor labels 1982 and 1984 corrected. The Rw interference term is now version-specific. `version` is required.
- Benchmark moved to a status-tracked file. v0.1's unverified recollections are no longer asserted, and the LCB input corrected to −2.02%.
- Constraint summary is tri-state; a skipped check is no longer counted as a pass.
- Added a numerical convergence study and an interpolation sensitivity test.
- Added the deadweight-margin scenario table.
- Power is reported as an ηD × sea-margin grid. The Holtrop ηD is excluded from sizing.
- Hydrostatics results now record their length basis.
- Removed v0.1's claim that NavCad "probably used the 1982 form factor"; the fit cannot establish that.

## 10. Known limitations

- The offsets stop at AP and FP. The stern overhang and the bulb nose are not modelled.
- Hydrostatics are upright and even keel only.
- Wetted surface excludes the transom face.
- Only the Fn ≤ 0.40 wave-resistance branch is implemented.
- SI floats internally; Pint is not used in the numerical core.
