"""Compare searches at equal budgets using the common physics evaluator."""
import argparse
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from scipy.optimize import differential_evolution

from marine_concept_ai.design_space import DWT_REQUIRED_T, evaluate_candidate
from marine_concept_ai.sampling.lhs import DESIGN_VARIABLES, load_design_space, random_uniform

ROOT = Path(__file__).resolve().parents[2]
POPULATION = 16
SCREEN_SCALES = {
    "draught vs Bhorsagar depth": 1.0,
    "draught vs Hay Point": 1.0,
    "beam vs Hay Point": 1.0,
    "freeboard D-T": 1.0,
    "GM0 (KM - KG)": 1.0,
    "hold volume / cargo mass": 0.1,
}


def score(row):
    if not row["geometry_ok"]:
        return float("inf")
    violation = max(0.0, -row["dwt_margin_worst_t"]) / 1000
    violation += sum(max(0.0, -row[f"margin::{check}"]) / scale for check, scale in SCREEN_SCALES.items())
    if violation:
        return 1 + violation
    displacement = row["disp_pchip_t"]
    return displacement / (DWT_REQUIRED_T + displacement)


def compare(bounds, generations, seed):
    budget = POPULATION * (1 + generations)
    random_points = random_uniform(bounds, budget, seed).to_numpy()
    limits = [(bounds[var]["min"], bounds[var]["max"]) for var in DESIGN_VARIABLES]
    for method in ("random", "differential_evolution"):
        best = None
        feasible_count = 0
        evaluations = 0

        def evaluate(point):
            nonlocal best, feasible_count, evaluations
            evaluations += 1
            row = evaluate_candidate(*map(float, point), holtrop=False)
            value = score(row)
            if value < 1:
                feasible_count += 1
                if best is None or row["disp_pchip_t"] < best["disp_pchip_t"]:
                    best = row
            return value

        start = perf_counter()
        if method == "random":
            for point in random_points:
                evaluate(point)
        else:
            # Start with the same 16 points as random search. Each generation
            # consumes one new evaluation per member, with no polishing calls.
            differential_evolution(
                evaluate, limits, init=random_points[:POPULATION], maxiter=generations,
                seed=seed, polish=False, tol=0, atol=0,
                callback=lambda x, convergence: evaluations >= budget,
            )
        if evaluations != budget:
            raise RuntimeError(f"{method} stopped after {evaluations} of {budget} evaluations")
        yield dict(method=method, seed=seed, evaluations=evaluations,
                   passing_screen=feasible_count, elapsed_s=perf_counter() - start, best=best)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--seeds", type=int, nargs="+", default=[20261109, 20261110, 20261111])
    parser.add_argument("--output", type=Path, default=ROOT / "results/tables/displacement_search.json")
    args = parser.parse_args()
    if args.generations < 1:
        parser.error("--generations must be positive")
    bounds = load_design_space()["design_space"]
    results = []
    for seed in args.seeds:
        for result in compare(bounds, args.generations, seed):
            results.append(result)
            best = result["best"]
            displacement = best["disp_pchip_t"] if best else None
            print(result["method"], seed, "best displacement (t)", displacement, flush=True)
    args.output.write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
