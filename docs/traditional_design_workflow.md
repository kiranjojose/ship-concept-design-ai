# D1.2 Traditional design workflow (draft, reconstructed from the 2019 report)

The report's own flow chart (p.45) covers the steps from owner requirements to length selection. The rest of the sequence below comes from the chapter order and the methods used in each chapter.

```
Owner requirements (DWT 75 000 t, 13 kn, rice/oats, Bhorsagar <-> Hay Point)      [manual]
        |
Mission analysis: route, ports, range, draught limits                              [manual, literature]
        |
Parent-ship study: 16 ships ~75k DWT, log fits of L/B, L/D, B/D, B/T, D/T vs DWT    [spreadsheet]
        |
First displacement estimate: CD = 0.8 -> 93 750 t                                  [manual]
        |
Length estimates: Schneekluth, Dankwardt, Ashik, parent range -> 190-240 m          [manual]
        |
Dimension sweep L = 200..240 m: B, D, T from ratios; CB from Dankwardt;            [spreadsheet]  <- automatable (WP2/3)
lightship from Watson-Gilfillan; DWT = Disp - LS
        |
Select L = 220.5 m (Table 2.4, selection rationale unclear)                        [spreadsheet + judgement]
        |
Form coefficients CW, CM, CP (empirical)                                            [manual]
        |
Preliminary checks: capacity (empirical), Prohaska stability, ILLC freeboard,      [manual]
bow height, displacement balance
        |
Lines: BSRA series charts -> offsets -> transom stern -> manual fairing             [manual + CAD (Rhino)]
        |
Bonjean curves and hydrostatics                                                     [manual Simpson + software]
        |
Resistance: Holtrop-Mennen (NavCad); "MAXSURF" table                              [software]
        |
Propulsion: empirical w, t, eta_R; Wageningen B-series Bp-delta charts;             [manual, chart reading]
engine selection (MAN B&W 6S80MC)
        |
General arrangement, equipment, rudder, LSA                                         [manual + CAD]
        |
Detailed mass (LCG/VCG) and capacity                                                [manual Simpson / Autohydro]
        |
Trim and intact stability, 4 full-load conditions, IMO criteria                     [software (Autohydro)]
        |
Midship section scantlings (LR rules)                                               [manual, rule-based]
```

## Classification of steps

| Step | Mode | Judgement-heavy? | Candidate for automation in Phase A |
|---|---|---|---|
| Parent-ship regression | Spreadsheet | Low | Yes (data in `data/reference/parent_ships_table_2_1.csv`) |
| Dimension sweep and length selection | Spreadsheet | Medium | **Yes, core of WP2/WP3** |
| Form coefficients | Empirical formulas | Low | Yes |
| Lines and fairing | CAD + manual | High | No (WP4) |
| Hydrostatics | Software | Low | Partially: displacement only. Full curves need geometry |
| Resistance (Holtrop-Mennen) | Software | Low | **Yes, core of WP2** |
| Propulsion and powering | Manual charts | Medium | Yes, with documented efficiencies |
| Capacity, GA | Manual + CAD | High | No (out of scope) |
| Stability | Software | Medium | No for Phase A (needs geometry and KG) |
| Structure | Rules | Medium | No (excluded) |

The report shows only one real design iteration: the length sweep. Ch.10 itself says that "further iterations on the design spiral are necessary". This is the gap the automated workflow targets.
