# Reference design inventory (WP1, 2026-11-07)

| # | Source (plan §6.1) | Found? | Where | Usable content |
|---|---|---|---|---|
| 1 | Bachelor's project report | **Yes** | `kiran.pdf` in the shared folder (167 pp., May 2019) | Requirements, methods, all tables below |
| 2 | Principal dimension calculations | Yes, in the report | Ch.2, Tables 2.1–2.4, p.10–19 | Parent ships, sweep L = 200–240 m, selected design |
| 3 | Hydrostatic calculations | Yes, partly | Ch.3, Table 3.4 (image), p.57 | Curves at 9 draughts, plus the design draught |
| 4 | Resistance calculations | Yes, partly | Ch.4, Tables 4.1 and 4.2 | Holtrop–Mennen (NavCad) at 8–15 kn; "MAXSURF" curve at 10–15 kn |
| 5 | Propulsion calculations | Yes, inconsistent | Ch.2.29, Ch.4.3–4.6 | w, t, QPC, engine choice. Power figures conflict (DISC-08) |
| 6 | General arrangement | Text only | Ch.5 | Bulkheads, frames, holds, crew. **Drawing missing** |
| 7 | Lines plan | Offsets only | Table 3.2 (faired offsets) | Half-breadths, 25 stations × 12 WLs. **Drawing missing** |
| 8 | Rhino files | **No** | None | None |
| 9 | MAXSURF files | **No** | None | None |
| 10 | Spreadsheets | **No** | None | None |
| 11 | Other software files (NavCad, Autohydro) | **No** | None | None |
| 12 | Mass and capacity | Yes | Ch.6, Tables 6.1–6.6 | Lightship breakdown with LCG/VCG, tank capacities |
| 13 | Trim and stability | Yes, full-load only | Ch.7 | 4 full-load conditions, GZ, IMO criteria |
| 14 | Midship section | Yes | Ch.8 | Out of Phase A scope; not transcribed |

Transcribed into `data/reference/`:

- `parent_ships_table_2_1.csv`
- `dimension_sweep_table_2_3.csv`
- `faired_offsets_table_3_2.csv`
- `hydrostatics_table_3_4.csv`
- `resistance_holtrop_navcad_table_4_2.csv`
- `resistance_maxsurf_table_4_1.csv`
- `lightship_table_6_1.csv`
- `cargo_holds_table_6_2.csv`
- `stability_summary.csv`

The structured design record is `configs/reference_bulk_carrier.yaml`. Gaps and conflicts are listed in `docs/missing_data_register.md`.

Ownership note: the report is the author's own B.Tech work. The parent-ship particulars are from the Register ship book. Keep `data/raw/` (the PDF itself) out of any public repository until redistribution has been decided.
