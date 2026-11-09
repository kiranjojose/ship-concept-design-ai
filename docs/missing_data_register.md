# D1.3 Assumptions and missing-data register (draft v0.1, 2026-11-07)

Source checked: `kiran.pdf`, the B.Tech report "Design of 75,000 Deadweight Bulk Carrier of 13 Knots Service Speed" (May 2019, 167 pages). Page numbers below are the report's printed numbers.

This register has three parts:

1. **Missing material**: things the workflow needs that are not in the shared folder.
2. **Discrepancies**: places where the report contradicts itself, or a printed result could not be reproduced from its own inputs.
3. **Assumptions** made while transcribing.

Severity levels:

- **High**: affects a value that WP2 will validate against.
- **Medium**: affects secondary quantities.
- **Low**: affects text only.

## 1. Missing material

| ID | Item | Needed for | Status | Action |
|---|---|---|---|---|
| MISS-01 | Spreadsheets (dimension sweep, mass, capacity, freeboard) | Checking Tables 2.3, 2.4, 6.1 and 6.2 cell by cell | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-02 | Rhino hull model | WP4 geometry, wetted surface, reproducing the hydrostatics | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-03 | MAXSURF model (.msd) and Hydromax/Resistance runs | Explaining Table 3.4 and Table 4.1, and the 4% displacement gap (DISC-06) | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-04 | NavCad project file | The Holtrop inputs that were not printed (LCB, iE, transom area, bulb, form factor, appendages) | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-05 | Autohydro model and loading reports | Loading conditions and the KN curves (Fig 7.5) | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-06 | Drawings: lines plan, GA, midship section | The report lists them (p. xi) but they are not in the PDF | **Confirmed unavailable** (Kiran, 7 Nov) | Ask Kiran |
| MISS-07 | Ballast departure and arrival conditions | Stability baseline | The report says they were studied (p.100, p.151) but does not show them | Ask Kiran, or treat as missing |
| MISS-08 | Holtrop input details: LCB position, half-angle of entrance as used, bulb area and centre, transom area, appendage list | Reproducing Rt with our own Holtrop-Mennen code (WP2) | **Partly resolved (Sprint 1).** Transom area AT = 10.0 m², recovered by inverting Table 4.2 RTR at 13 kn; it then reproduces RTR at all 8 speeds to within 0.1%. LCB, ABT and hB are taken from the rebuilt hull. The appendage list is still unknown (A9) | See docs/validation_sprint1.md §3 |
| MISS-09 | Length overall, LWL of the design waterline used in the rules | Port LOA check, freeboard and equipment number | LOA is unstated. Table 3.1 (p. 48) gives profile offsets, including the LWL stern offset of −7.4 relative to AP. Software hydrostatics give LWL = 228.149 m (p. 57). | Recover full longitudinal extent from drawings or candidate geometry |
| MISS-10 | Engine MCR and NCR, and the propeller diameter actually selected | Brake-power reference | Garbled or ambiguous (DISC-08, DISC-09) | Ask Kiran or recompute |
| MISS-11 | Guldhammer–Harvald and BSRA resistance results | Ch.10 says these were computed, and that the BSRA result was adopted | Not shown | Ask Kiran |
| MISS-12 | Datum of the "zero pt." in the hydrostatics output | LCB and LCF relative to AP or midship | Not stated | Recover from the MAXSURF model |

## 2. Discrepancies

| ID | Quantity | Conflicting values (source) | Adopted in YAML | Severity |
|---|---|---|---|---|
| DISC-01 | Operating range | 6323 nm (p.8), 6023 nm (p.10, 5475 nm + 10%), 6223 nm (p.32, used in the fuel calculation), 5840 nm (Table 9.1) | 6323 (mission statement). Fuel mass uses 6223 | Medium |
| DISC-02 | Speed | 13 kn throughout. p.14 says "service speed of 16.5 knots and trial speed 17.325"; p.15 uses Vs = 12.6 and Vt = 16.8 in the Dankwardt formula | 13 kn service. 13.65 kn trial reproduces the printed Vokes PD = 7782.89 kW exactly | Medium |
| DISC-03 | Block coefficient | 0.82 (Tables 2.4, 2.12, 9.1); 0.83 (NavCad input). The displacement 88 409 t back-calculates to CB = 0.8301. Modelled hull: 0.774 on LWL, about 0.80 on LBP. Dankwardt as written on p.16 gives 0.846 at Fn = 0.1438 | **0.83**, because it is consistent with the printed displacement | High |
| DISC-04 | Depth and draught | Table 2.12 "Final main dimensions" prints D = 18.23 and T = 19.79, which is impossible since T > D. Everywhere else: D = 19.75, T = 14.29. The freeboard depth correction uses D = 18.23 | D = 19.75, T = 14.29 | High (typo, but it propagates into the freeboard) |
| DISC-05 | Length used in rule calculations | Bulkheads, frame spacing and the freeboard depth correction use L = 198.80 m (p.26–27, 43). The design LBP is 220.5 m. Hold lengths also disagree: 23.877 m calculated, 21.44 m in Table 2.9, and "150.094/7" vs a cargo length of 167.139 m | LBP = 220.5. Rule calculations to be redone in WP2 if needed | Medium |
| DISC-06 | Displacement at design draught | 88 409 t from the design equation vs 84 755 t from the modelled hull (p.57). Gap: 3 654 t (−4.1%) | Both kept, as separate fields | **High**. The faired hull does not reach the design displacement at T = 14.29. This is the main validation case for hydrostatics |
| DISC-07 | Resistance at 13 kn | 635.9 kN (Holtrop/NavCad, Table 4.2) vs 584.6 kN ("MAXSURF", Table 4.1), an 8.8% difference. The text says the BSRA method was adopted, but no BSRA numbers are shown. Table 4.2 components sum to 516 kN, so a form factor of about 1.30 is implied but not printed | 635.9 kN as primary, 584.6 kN as alternative | High |
| DISC-08 | Delivered and brake power | PD = 6817.83 kW (p.37) cannot be reproduced from PE/(QPC·ηs): Table 4.2 gives 7301 kW and Table 4.1 gives 6718 kW. PB values in the report: 8020.98 kW (p.37), 7938.55 kW (p.19), 6818.00 kW (p.70, "after 10% allowance", which equals PD). Engine power is printed as "7360-100400 kW" | PB = null. To be recomputed in WP2 with documented efficiencies | High |
| DISC-09 | Propeller | The text says 3 blades were selected; the sizing table is for 4 blades. Sizing gives D = 10.27–10.48 m, larger than Dmax = 9.4 m (= 2/3 T). The final table lists "Depth 8.50 m" (probably the diameter) and V optimum = 6.68 kn. ηH is printed as 0.98, but (1−t)/(1−w) = 1.19 | Diameter null. Factors kept as printed | Medium |
| DISC-10 | Cargo hold volume | The sum of Table 6.2 is 74 177 m³, but the printed total is 68 430 m³. The preliminary estimate is 82 861 m³ (p.40, Table 9.2). The stowage factor of 1.116 on p.98 is 82 861 / 74 248, from the preliminary volume | Total 74 177 m³ (derived sum) | High for the capacity check. 74 177 m³ / 74 260 t = 0.999 m³/t, which is above the rice (0.95) and oats (0.98) requirements, but with a thin margin |
| DISC-11 | Lightship | 13 248.99 t (Table 6.1) vs 10 926.83 t (all loading-condition tables, p.101–105). Half the outfit mass is 669.43 t in the text and 696.43 t in the table | 13 248.99 t. The loading conditions are therefore about 2 300 t light, and their GM and draughts are suspect | High for stability |
| DISC-12 | Cargo loads in the loading conditions | Rice loads (t) equal the hold volumes (m³) numerically, which implies SF = 1.0, not 0.95. Oats loads differ by hold | As printed | Medium |
| DISC-13 | Trim in Tables 7.4, 7.6, 7.8 | "TRIM" is printed as 16.98–21.05 m while the aft and forward draughts differ by 0.09 m | Null | Low |
| DISC-14 | Route, cargo and narrative text | Ch.2 says rice/oats on Bhorsagar ↔ Hay Point. p.10 and Ch.9 say iron ore/coal on Mumbai ↔ Adelaide ("Adelaide (china)"). Port text mixes in Mumbai details. Ch.10 mentions an 8-cylinder engine and a "high speed" vessel, but Ch.4 selects 6 cylinders at 13 kn | Ch.2 mission (rice/oats, Bhorsagar ↔ Hay Point) | Low (text), but must not be quoted in the NTNU proposal |
| DISC-15 | Main engine mass | 46 t for an MAN B&W 6S80MC in Table 6.1. Real engines of this class weigh several hundred tonnes, but the rest of the engine plant (695 t) may absorb this | As printed, flagged | Low |
| DISC-16 | Waterplane coefficient | 0.8947 (p.19), 0.901 (p.41), 0.871 (modelled hull) | 0.8947 | Low |
| DISC-18 | Quasi-propulsive coefficient | QPC 0.60 is used for PD (p.36–37). The report's own factors w 0.38, t 0.26, ηR 1.05 and ηO 0.623 give ηD = 1.194 × 0.623 × 1.05 = 0.781 | Kiran (9 Nov): 0.60 = historical scenario, 0.781 = sensitivity; reference PB stays null | High for brake power |
| DISC-17 | Hydrostatics output KG | KG = 11.257 (0.57D) in Table 3.4 and KG = T in the p.57 summary. These are software placeholders, so GMt = −0.437 on p.57 is meaningless | Recorded as `kg_m_assumed` | Low |

## 3. Assumptions made during transcription

- A1: Seawater density is 1.025 t/m³ and the shell (appendage) factor is 1.006, as used in the report.
- A2: Where values conflict, the adopted value is the one most consistent with downstream calculations. All others are kept under `conflicts:` in the YAML.
- A3: "Trial speed" is taken as 13.65 kn (1.05 × 13), inferred from the printed Vokes result. The report does not state it.
- A4: The hydrostatics in Table 3.4 and on p.57 look like MAXSURF Stability (Hydromax) output, but the report does not name the software ("GHS or manually" on p.53). This is an inference.
- A5: Table 4.1 is labelled "MAXSURF". The method inside MAXSURF Resistance is not stated.
- A6: Table 3.4 is an image. It was transcribed manually from a page render and should be spot-checked.
- A7: Waterline heights for Table 3.2 are WL_n = 2.6·n m (spacing from p.48), LWL = 14.29 m and MDK = 19.75 m. The report does not tabulate them. Accepted by Kiran (9 Nov 2026) as a documented reconstruction assumption.
- A8: The sea margin is 15% in the power chain. The report states no sea margin. Kiran (9 Nov): keep 15% as one explicit scenario and vary it separately (0–25%).
- A9: Appendages in Holtrop are a rudder only. The area comes from the DNV guideline T·L/100·(1+25(B/L)²), wetted area 2A, (1+k2) = 1.5. NavCad's Rapp of 20.8 kN implies more appendage area, but its list is not printed.
- A10: Holtrop stern-shape parameter Cstern = 0 (normal section). Not stated in the report.

## 4. What this means for WP2 validation targets

Reference values that are usable now (stated once, internally consistent):

- L = 220.5 m, B = 32.78 m, T = 14.29 m, D = 19.75 m, CB = 0.83, V = 13 kn
- Displacement from the design equation: 88 409 t
- Holtrop Rt and PE vs speed: Table 4.2, 8–15 kn
- Lightship from Watson–Gilfillan: 13 249 t
- Hydrostatic curves of the modelled hull: Table 3.4

Reference values that need recovery or recomputation before we can validate against them: brake power, propeller, loading-condition stability, rule-based freeboard.

Tolerances still to be decided. A proposal for WP2:

- ±0.5% on displacement from the same formula
- ±5% on Holtrop Rt, because the NavCad inputs are incomplete

## 5. Update 2026-11-07: no source files beyond the report

Kiran confirmed that no spreadsheets, CAD or software files survive, so the report is the only source. The replacement strategy:

- **Hull geometry and hydrostatics.** These are rebuilt from the faired offsets (Table 3.2), not from Rhino or MAXSURF.
- **Quick check.** I integrated the offsets with the trapezoidal rule. Waterline heights were inferred from the 2.6 m spacing given on p.48, which is assumption A7. The results against Table 3.4:

  | Draught | Displacement from offsets | Table 3.4 | Difference |
  |---|---|---|---|
  | 14.29 m | 85 979 t | 84 755 t | +1.4% |
  | 13.366 m | 79 905 t | 78 586 t | +1.7% |
  | 10.335 m | 60 292 t | 58 939 t | +2.3% |

  At 14.29 m the waterplane area is 6 430 m² against 6 511 m² (−1.2%). The LCB is 112.1 m against 111.9 m. Block coefficient on LBP is 0.81.

- **What the check shows about DISC-06.** The offsets themselves only reach about 86 000 t at the design draught. The 4% shortfall against the design equation (88 409 t) is therefore in the lines, not in the software.
- **Holtrop inputs (MISS-08).** The missing inputs (LCB, waterplane coefficient, wetted surface, transom area, bulb) will be derived from the rebuilt hull, and each will be recorded as an assumption.

## 6. Update 2026-11-07 (Sprint 1 engine)

The Sprint 1 engine finds the following (details in `docs/validation_sprint1.md`):

- **DISC-06 explained.** The offsets and the 2019 software hull agree to within ±0.3% in each displacement slice from 3.985 to 13.366 m. The whole difference is below 2.3 m: the software hull starts from a keel line (beam 0.001 m at T = 0), while the offsets have a 27.5 m flat of bottom. The stern overhang aft of AP accounts for a small further difference.
- **Deadweight balance fails on the rebuilt hull.** 86 974 t (with shell factor) − 13 249 t lightship = 73 725 t, which is 1 275 t short of 75 000 t. With the design-equation displacement it passes by 160 t.
- **Resistance at 13 kn.** ~~Holtrop 1984 gives +1.7%~~ Corrected 9 Nov: v0.1's version labels were swapped. The 1982 version gives +1.7% and the 1984 version −0.6% against Table 4.2. The fit cannot tell which version NavCad used. NavCad's Rw ≈ 0 cannot be reproduced, and it causes the excess at 14–15 kn.
- New entries: A7–A10 and DISC-18. MISS-08 is partly resolved.

## 7. Update 2026-11-09 (Kiran's review)

- Decisions recorded in `docs/validation_sprint1.md` §7.
- **NEW-01. The Holtrop benchmark does not reconcile.** At the paper's lcb of −2.02% (p.170), the engine gives 1+k1 = 1.1625 and iE = 11.84°. The values used in v0.1 (1.156 and 12.08°) are reproduced only at −0.75%. Rw (557.11 kN, confirmed) is reproduced to 0.05%. Status per value is in `data/literature/holtrop_mennen_1982_example.yaml`.
- **NEW-01 update (v0.3).** Kiran confirmed every p.170 value from the published scan. The printed LCB of −2.02% is inconsistent with the printed 1+k1 and iE in the example itself; −0.75% is kept as *inferred*. A second gap: RA is 220.57 kN in the engine vs 221.98 kN printed (−0.64%). Both stay open, tracked as strict xfail tests.
