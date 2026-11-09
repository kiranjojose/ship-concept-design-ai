# marine-concept-ai

AI-assisted preliminary ship design: from traditional naval architecture to intelligent design-space exploration.

The first case study is a 75 000 DWT, 13 kn bulk carrier, the author's B.Tech design from 2019. It is reconstructed as a documented reference baseline, then re-implemented as a validated parametric engine. That engine is used for design-space exploration, optimisation and surrogate modelling.

Status: **Sprint 1 done: calculation engine validated against the report** (`docs/validation_sprint1.md`). WP1 reference documents:

- `docs/reference_design_inventory.md`: what source material exists
- `configs/reference_bulk_carrier.yaml`: the structured reference design (D1.1)
- `docs/traditional_design_workflow.md`: the original workflow (D1.2)
- `docs/missing_data_register.md`: gaps, discrepancies and assumptions (D1.3)

Principles:

- No invented reference values. Unknowns stay `null`.
- Every value has a unit and a source.
- Deterministic engineering models come first. AI is added only where it can be measured.

## Engine (Sprint 1)

```
python experiments/01_reference_reconstruction/run_reference.py   # rebuild the reference ship, write results/tables/s1_*
pytest                                                             # unit + reference tests
```

- `geometry` and `hydrostatics`: hull from the offset table; displacement, centres, metacentres, coefficients, wetted surface
- `resistance`: Holtrop–Mennen 1984, with the 1982 form-factor option and validity flags
- `propulsion`: PE → PD → PB → MCR with sourced efficiencies and margins
- `constraints`: port, freeboard, deadweight, GM and capacity checks
- `reference`: the reference ship as engine inputs

## Layout

The layout follows plan §14:

- `configs/`: design, design-space and experiment configs
- `data/`: `raw/` (not committed), `reference/` (transcribed tables), `processed/` and `synthetic/`
- `src/marine_concept_ai/`: the engineering library
- `experiments/`, `tests/`, `results/`, `docs/` and `app/`

## Setup

```
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
pytest
```
