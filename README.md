# Ship Concept Design AI

A reproducible preliminary-design study of a **75,000 DWT bulk carrier at 13 kn**. The case reconstructs Kiran Jose Puthussery's 2019 B.Tech design from the report's offset and sizing tables, then uses a common geometry and weight model to screen hull variants.

The historical sizing calculation gives **75,160.47 t DWT** for the selected 220.5 m ship. The same reference falls **1,195 t short** at nominal in the geometry-based sweep. Across 300 sampled variants, **80** meet the deadweight requirement in all modelled scenarios and pass the other evaluated screens. LOA remains unknown for those candidates. See the [Sprint 2 report](docs/design_space_sprint2.md) for the assumptions, scenario definitions and comparison with the original workflow.

## Reproduce the results

Run from a checkout with Python 3.10 or later.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,ml]'
./reproduce.sh
```

`reproduce.sh` runs the test suite (81 pass, 2 expected failures), the length-sweep replay, the displacement search and the surrogate benchmark, in about 3 minutes. Add `--full` to regenerate the 300-case sweep and its figures as well. Every result is seeded; only the recorded timings depend on the machine.

| Experiment | What to look for |
|---|---|
| Historical length sweep | Nine grid lengths and the selected case from Tables 2.3–2.4. The 75,000 t grid crossing is 220.737 m. |
| Displacement optimisation | Uniform random search and differential evolution on the same bounds, initial points and physics evaluation budget. The objective is nominal displacement, with at least 75,000 t DWT in all modelled scenarios and the existing concept screens. |
| Surrogate benchmark | Linear and quadratic regression trained on the archived sweep. Compare held-out errors, threshold mistakes and prediction time against physics evaluation. |

The archived sweep is included, and `./reproduce.sh --full` regenerates it. The [experiment results](results/tables) include the sampled designs and benchmark summaries.

## Benchmark results

With 96 physics evaluations per method and seed, differential evolution found lower displacement in two of three runs. Its best candidate displaced **89,319 t** and had **75,132 t** deadweight in the worst modelled scenario. The best random-search candidate displaced **90,335 t**. These are the best candidates observed at this budget. The [search results](results/tables/displacement_search.json) record each seed, the number of candidates passing the screen and the margins of each selected candidate.

On a fixed 240/60 train/test split, the quadratic ridge surrogate gave a worst-scenario deadweight MAE of **13.1 t**, versus **349.3 t** for the linear model. On the Mac, it predicted the 60 rows in about **0.12 ms**, versus **3.55 s** through the physics evaluator. Neither model crossed the 75,000 t threshold incorrectly in this split. The nearest test case was **536 t** from the threshold, so the split gives little evidence about near-boundary decisions. See the [held-out metrics and test IDs](results/tables/surrogate_benchmark.json).

## Model scope

- Geometry comes from the reference offset table and a Lackenby station shift. Hydrostatics are upright and even keel. Lightship is estimated with Watson–Gilfillan.
- The displacement search uses the fixed freeboard and scaled cargo volume and KG screens from Sprint 2. Candidate LOA remains unknown. Scenario coverage describes the specific geometry and weight variants implemented here.
- Holtrop resistance and installed power are indicators. The two expected test failures track the unresolved LCB and correlation allowance discrepancies in the [published worked-example benchmark](docs/validation_sprint1.md). Displacement optimisation uses the physics evaluator with Holtrop disabled.
- The surrogate approximates outputs from this engine within the sampled design space. Its held-out errors quantify agreement with the engine. Confirm proposed candidates with the physics evaluator.

## Deferred work and known limitations

- **Brake-power ranking (D3.3) is deferred.** Ranking candidates by brake power needs the Holtrop benchmark to be reconciled first: the LCB (−2.02 % printed vs −0.75 % inferred) and correlation allowance discrepancies are still open and are tracked as the two expected test failures. Minimum displacement is used as the search objective instead; it is a proxy for a smaller hull, not a powering result.
- **Brake power from the 2019 report is not used.** It cannot be reproduced from the report's own inputs, so it is recorded as null in `configs/reference_bulk_carrier.yaml`.
- **Freeboard** is screened against a fixed 5.00 m value, not a candidate-specific ILLC calculation.
- **LOA** is unknown for every candidate, because the report gives no full longitudinal profile.
- **Geometry** is always a transformation of one parent hull, and the search evidence is three seeds at one budget.
- **Surrogate accuracy near 75,000 t is untested**, because no held-out case lies within 536 t of the threshold.

## Repository layout

| Path | Contents |
|---|---|
| `src/marine_concept_ai/` | The engine: hull geometry and transformation, hydrostatics, Holtrop–Mennen resistance, powering, Watson–Gilfillan weights, constraint checks, sampling and the design-space evaluator |
| `configs/` | Reference ship, design-space bounds and experiment settings |
| `data/reference/`, `data/literature/` | Tables transcribed from the 2019 report and the Holtrop & Mennen (1982) worked example (not MIT, see [data/README.md](data/README.md)) |
| `experiments/01_reference_reconstruction/` | Sprint 1 rebuild of the reference ship and comparison with the report |
| `experiments/03_design_space/` | 300-case sweep, figures and the replay of the report's length sweep |
| `experiments/04_optimization/` | Random search vs differential evolution |
| `experiments/05_surrogate_models/` | Linear and quadratic surrogate benchmark |
| `results/tables/`, `results/figures/` | Archived outputs of the experiments above |
| `tests/` | Unit, reference and integration tests (81 pass, 2 expected failures) |
| `reproduce.sh` | One-command reproduction |

## Documentation

- [Technical summary](docs/technical_summary.md): the study end to end, with assumptions and results
- [Number trace](docs/number_trace.md): where each headline number comes from
- [Sprint 1 validation](docs/validation_sprint1.md): engine vs the report and the published Holtrop example
- [Sprint 2 design space](docs/design_space_sprint2.md): sweep, scenarios and feasible region
- [Missing data register](docs/missing_data_register.md) and [reference inventory](docs/reference_design_inventory.md)
- [Traditional design workflow](docs/traditional_design_workflow.md): the 2019 process this study is compared with

## Source, licence and citation

The [reference inventory](docs/reference_design_inventory.md) identifies the report tables and reconstruction assumptions. The repository contains the transcribed inputs needed to reproduce the experiments. Original documents in `data/raw/` are kept outside Git.

Original project software and documentation are distributed under the [MIT License](LICENSE). The transcribed report tables in `data/reference/` and the Holtrop & Mennen example in `data/literature/` are not covered by MIT; see [data/README.md](data/README.md). Cite the software using [CITATION.cff](CITATION.cff).
