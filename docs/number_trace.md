# Number trace: README and technical summary

Checked 10 Nov 2026 against the files at the working tree that follows ecf42e7, after a clean `./reproduce.sh` run in a fresh Linux environment (81 passed, 2 xfailed; search and surrogate values identical to the committed JSON, timings differ by machine). Each number quoted in `README.md` and `docs/technical_summary.md` is listed with the file and field it comes from. "Report" means a printed value in the 2019 report; those are transcribed in `data/reference/` or `configs/reference_bulk_carrier.yaml`.

Rule for the application text: quote only numbers from this table. None of them comes from the passages flagged as inconsistent in `docs/missing_data_register.md` (printed CB 0.82, loading-condition lightship DISC-11, report brake power).

## Reference and validation

| Number | Meaning | Source | Check |
|---|---|---|---|
| 220.5 m, 32.78 m, 19.75 m, 14.29 m | LPP, B, D, T | Report Table 2.4; `dimension_sweep_table_2_3.csv` last row | ✓ |
| CB 0.83 | Sizing-equation CB (printed 0.82; 88,409.03 t implies 0.8301) | `reference_bulk_carrier.yaml`, p. 60 note | ✓ |
| 88,409 t | Design-equation displacement | `s1_deadweight_margin_scenarios.csv` (88,409.03) | ✓ |
| 13,249 t | Lightship, Table 6.1 | same file (13,248.99) | ✓ |
| 75,160 t / +160 t | DWT, sizing equation with Table 6.1 lightship | same file (75,160.04 / 160.04) | ✓ |
| 73,725 t / −1,275 t | DWT, offsets PCHIP ×1.006 | same file (73,724.89 / −1,275.11) | ✓ |
| 71,506 t / −3,494 t | DWT, 2019 software hull | same file (71,506.01 / −3,493.99) | ✓ |
| 75,160.47 t | Replay DWT at 220.5 m (Table 2.4 lightship basis) | `rerun_report_sweep.py` output | ✓ |
| 75,158.54 t, 1.93 t | Table 2.4 DWT and replay difference | `s1_deadweight_margin_scenarios.csv` row 2; 75,160.47 − 75,158.54 | ✓ |
| 220.737 m | 75,000 t grid crossing | `rerun_report_sweep.py` output | ✓ |
| 0.048 ms (≈ 0.05 ms) | Ten-row replay time | `rerun_report_sweep.py` output, machine-dependent | ✓ |
| 86,455 t | Offsets displacement, no shell factor | `s1_summary.json` design_draught_hydrostatics.displacement_t | ✓ |
| 84,755 t, +2.0% | Table 3.4 displacement and difference | `s1_hydrostatics_vs_table_3_4.csv` (2.006%) | ✓ |
| 1,636 t of 1,700 t | Gap below 2.289 m | same file: 11,458.65 − 9,823; 86,455 − 84,755 | ✓ |
| ±0.3% (3.985–13.366 m slices) | Slice agreement | same file, slice_disp_err_pct (max 0.29%) | ✓ |
| < 0.001% | Convergence at 801 × 241 | `s1_hydrostatics_convergence.csv` (−6.1e-6 relative) | ✓ |
| 0.55% | Linear vs PCHIP | 86,494.12 vs 86,973.88 in `s1_deadweight_margin_scenarios.csv` | ✓ |
| +1.7% / −0.6% | Rt at 13 kn, rebuilt hull, 1982 / 1984 | `s1_resistance_vs_table_4_2.csv` (1.694 / −0.553) | ✓ |
| up to 7.9% | Rt at 15 kn, 1982 | same file (7.950) | ✓ |
| 635.9 kN, 4,249 kW | Table 4.2 at 13 kn | same file, report columns | ✓ |
| B/T 2.29 | Outside 2.4–3.2 | `s1_summary.json` validity_13kn | ✓ |
| 1.156, 12.08°, −2.02%, −0.75% | Holtrop 1982 example LCB issue | `holtrop_mennen_1982_example.yaml` | ✓ |
| 220.57 vs 221.98 kN, −0.64% | RA discrepancy | same file; `test_holtrop_mennen.py` | ✓ |

## Design space

| Number | Meaning | Source | Check |
|---|---|---|---|
| 300, seed 20261109 | LHS candidates | `s2_summary.json` | ✓ |
| 80 / 14 / 102 / 104 | Robust / nominal only / short (100 + 2 best-case-only) / failing other screens | `s2_summary.json` dwt_verdict_counts_passing_other_checks; 300 − 196 | ✓ |
| 95 / 91 | Freeboard / hold-volume failures (overlapping) | `s2_summary.json` fails_other_than_dwt_counts | ✓ |
| −1,195 t (−2,550 to −655 t) | Reference margin on the common model | `s2_summary.json` reference | ✓ |
| +3.98 m, +0.52 m, +0.20 m, +0.012 | One-at-a-time recovery, nominal | `s2_recovery_one_at_a_time.csv` | ✓ |
| 0.46 m, 0.04 m³/t | Reference freeboard and stowage margins | same file (0.45999, 0.0369) | ✓ |
| about 1,400 t | Nominal − worst band | `s2_sweep_candidates.csv`: 1,203–1,661 t over the 132 robust candidates, 1,355 t for the reference | ✓ |
| 78.6 s | Sweep runtime | `s2_summary.json` runtime_s, machine-dependent | ✓ |

## Search and surrogate

| Number | Meaning | Source | Check |
|---|---|---|---|
| 96 evaluations, population 16, 5 generations, 3 seeds | Protocol | `compare_search.py`; `displacement_search.json` | ✓ |
| 89,815 / 89,319 / 90,364 t | DE best per seed | `displacement_search.json` best.disp_pchip_t | ✓ |
| 90,532 / 91,482 / 90,335 t | Random best per seed | same | ✓ |
| 75,132 t | Worst-case DWT of the overall DE best | same, seed 20261110 best.dwt_worst_t (75,131.96) | ✓ |
| +52 / +132 / +38 t and +569 / +1,279 / +546 t | Worst-case margins, DE / random | same, dwt_margin_worst_t | ✓ |
| 38 / 32 / 38 and 26 / 18 / 21 | Candidates passing the screen, DE / random | same, passing_screen | ✓ |
| 0.004 m³/t | Smallest DE stowage margin | same, seed 20261110 | ✓ |
| 240 / 60 | Train / test split | `surrogate_benchmark.json` | ✓ |
| 13.1 t, 19.2 t, 75.0 t | Quadratic ridge MAE, RMSE, max | same, dwt_worst_t | ✓ |
| 349.3 t, 467.0 t, 1,881.7 t | Linear MAE, RMSE, max | same | ✓ |
| 0 | Wrong threshold decisions, both models | same, dwt_false_passes / dwt_false_fails | ✓ |
| 0.12 ms, 0.02 ms, 3.55 s, ≈ 30,000× | Prediction and physics time, Mac run | same, machine-dependent (Linux rerun: 0.31 ms, ≈ 43,000×) | ✓ |
| 536 t | Nearest test case to 75,000 t | Derived: test IDs in `surrogate_benchmark.json` joined to `s2_sweep_candidates.csv` dwt_worst_t (535.7 t). The nearest of all 300 sweep candidates is 70 t | ✓ derived, not stored |

## Follow-ups

- **536 t** is reproducible from the stored test IDs but is not a field in `surrogate_benchmark.json`. Optional: add `min_test_distance_to_threshold_t` to the benchmark script before the freeze.
- Timings are the Mac run. State "on the author's laptop" wherever they are quoted.
