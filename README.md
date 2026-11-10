# Ship Concept Design AI

A reproducible preliminary-design study of a **75,000 DWT bulk carrier at 13 kn**. The case reconstructs Kiran Jose Puthussery's 2019 B.Tech design from the report's offset and sizing tables, then uses a common geometry and weight model to screen hull variants.

The historical sizing calculation gives **75,160.47 t DWT** for the selected 220.5 m ship. The same reference falls **1,195 t short** at nominal in the geometry-based sweep. Across 300 sampled variants, **80** meet the deadweight requirement in all modelled scenarios and pass the other evaluated screens. LOA remains unknown for those candidates. See the [Sprint 2 report](docs/design_space_sprint2.md) for the assumptions, scenario definitions and comparison with the original workflow.

## Reproduce the results

Run from a checkout with Python 3.10 or later.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,ml]'
pytest -rx
python experiments/03_design_space/rerun_report_sweep.py
python experiments/04_optimization/compare_search.py
python experiments/05_surrogate_models/benchmark_surrogate.py
```

| Experiment | What to look for |
|---|---|
| Historical length sweep | Nine grid lengths and the selected case from Tables 2.3–2.4. The 75,000 t grid crossing is 220.737 m. |
| Displacement optimisation | Uniform random search and differential evolution on the same bounds, initial points and physics evaluation budget. The objective is nominal displacement, with at least 75,000 t DWT in all modelled scenarios and the existing concept screens. |
| Surrogate benchmark | Linear and quadratic regression trained on the archived sweep. Compare held-out errors, threshold mistakes and prediction time against physics evaluation. |

The archived sweep is included. To regenerate it, run `python experiments/03_design_space/run_sweep.py`, then `python experiments/03_design_space/make_figures.py`. The [experiment results](results/tables) include the sampled designs and benchmark summaries.

## Benchmark results

With 96 physics evaluations per method and seed, differential evolution found lower displacement in two of three runs. Its best candidate displaced **89,319 t** and had **75,132 t** deadweight in the worst modelled scenario. The best random-search candidate displaced **90,335 t**. These are the best candidates observed at this budget. The [search results](results/tables/displacement_search.json) record each seed, the number of candidates passing the screen and the margins of each selected candidate.

On a fixed 240/60 train/test split, the quadratic ridge surrogate gave a worst-scenario deadweight MAE of **13.1 t**, versus **349.3 t** for the linear model. On the Mac, it predicted the 60 rows in about **0.12 ms**, versus **3.55 s** through the physics evaluator. Neither model crossed the 75,000 t threshold incorrectly in this split. The nearest test case was **536 t** from the threshold, so the split gives little evidence about near-boundary decisions. See the [held-out metrics and test IDs](results/tables/surrogate_benchmark.json).

## Model scope

- Geometry comes from the reference offset table and a Lackenby station shift. Hydrostatics are upright and even keel. Lightship is estimated with Watson–Gilfillan.
- The displacement search uses the fixed freeboard and scaled cargo volume and KG screens from Sprint 2. Candidate LOA remains unknown. Scenario coverage describes the specific geometry and weight variants implemented here.
- Holtrop resistance and installed power are indicators. The two expected test failures track the unresolved LCB and correlation allowance discrepancies in the [published worked-example benchmark](docs/validation_sprint1.md). Displacement optimisation uses the physics evaluator with Holtrop disabled.
- The surrogate approximates outputs from this engine within the sampled design space. Its held-out errors quantify agreement with the engine. Confirm proposed candidates with the physics evaluator.

## Source, licence and citation

The [reference inventory](docs/reference_design_inventory.md) identifies the report tables and reconstruction assumptions. The repository contains the transcribed inputs needed to reproduce the experiments. Original documents in `data/raw/` are kept outside Git.

Original project software and documentation are distributed under the [MIT License](LICENSE). The transcribed report tables in `data/reference/` and the Holtrop & Mennen example in `data/literature/` are not covered by MIT; see [data/README.md](data/README.md). Cite the software using [CITATION.cff](CITATION.cff).
