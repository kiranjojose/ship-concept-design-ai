#!/usr/bin/env bash
# Reproduce the tests and headline results of this repository with one command.
#
#   ./reproduce.sh          tests, length-sweep replay, displacement search, surrogate benchmark
#   ./reproduce.sh --full   the same, plus the 300-case sweep and its figures (about 80 s more)
#
# Run inside an environment where `pip install -e '.[dev,ml]'` has been done.
# Timings in the results files depend on the machine; every other value is seeded.
set -euo pipefail
cd "$(dirname "$0")"

full=0
case "${1:-}" in
  "") ;;
  --full) full=1 ;;
  *) echo "usage: $0 [--full]" >&2; exit 2 ;;
esac

step() { printf '\n==> %s\n' "$1"; }

step "Test suite (expect 2 xfailed: the open Holtrop benchmark items)"
python -m pytest -rx

if [ "$full" -eq 1 ]; then
  step "300-case design-space sweep -> results/tables/s2_*"
  python experiments/03_design_space/run_sweep.py
  step "Sweep figures -> results/figures/s2_*"
  python experiments/03_design_space/make_figures.py
fi

step "Replay of the 2019 length sweep (Tables 2.3-2.4)"
python experiments/03_design_space/rerun_report_sweep.py

step "Displacement search: random vs differential evolution -> results/tables/displacement_search.json"
python experiments/04_optimization/compare_search.py

step "Surrogate benchmark -> results/tables/surrogate_benchmark.json"
python experiments/05_surrogate_models/benchmark_surrogate.py

step "Done. Compare with docs/technical_summary.md"
