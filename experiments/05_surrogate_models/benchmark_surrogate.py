"""Measure held-out error and prediction time against the Sprint 2 physics sweep."""
import json
from pathlib import Path
from statistics import median
from time import perf_counter
from timeit import repeat

import pandas as pd
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from marine_concept_ai.design_space import DWT_REQUIRED_T, evaluate_candidate

ROOT = Path(__file__).resolve().parents[2]
TABLES = ROOT / "results/tables"
FEATURES = ["lpp_m", "breadth_m", "draught_m", "cb_target"]
TARGETS = ["disp_pchip_t", "dwt_worst_t"]
SEED = 20261109


def main():
    sweep = pd.read_csv(TABLES / "s2_sweep_candidates.csv")
    candidates = sweep.loc[sweep["geometry_ok"] & sweep["candidate_id"].ne("REF")]
    train, test = train_test_split(candidates, test_size=0.2, random_state=SEED)
    inputs = test[FEATURES].to_numpy()

    # Time the same input batch through the full evaluator. Labels for error
    # measurement come from the archived sweep, whose CSV rounds the inputs.
    start = perf_counter()
    for point in inputs:
        evaluate_candidate(*map(float, point), holtrop=False)
    physics_s = perf_counter() - start

    models = {
        "linear": LinearRegression(),
        "quadratic_ridge": make_pipeline(
            StandardScaler(), PolynomialFeatures(2, include_bias=False), Ridge(alpha=0.01)
        ),
    }
    summary = dict(seed=SEED, train_rows=len(train), test_rows=len(test),
                   test_candidate_ids=test["candidate_id"].tolist(), physics_batch_s=physics_s, models={})
    actual = test[TARGETS].to_numpy()
    meets_dwt = actual[:, 1] >= DWT_REQUIRED_T
    for name, model in models.items():
        model.fit(train[FEATURES].to_numpy(), train[TARGETS].to_numpy())
        predicted = model.predict(inputs)
        batch_s = median(repeat(lambda: model.predict(inputs), repeat=5, number=500)) / 500
        predicts_meets = predicted[:, 1] >= DWT_REQUIRED_T
        summary["models"][name] = {
            "metrics": {
                target: dict(mae_t=mean_absolute_error(actual[:, i], predicted[:, i]),
                             rmse_t=root_mean_squared_error(actual[:, i], predicted[:, i]),
                             max_abs_error_t=float(abs(actual[:, i] - predicted[:, i]).max()))
                for i, target in enumerate(TARGETS)
            },
            "dwt_false_passes": int((predicts_meets & ~meets_dwt).sum()),
            "dwt_false_fails": int((~predicts_meets & meets_dwt).sum()),
            "prediction_batch_s": batch_s,
            "physics_to_prediction_time_ratio": physics_s / batch_s,
        }
    result = json.dumps(summary, indent=2, allow_nan=False)
    (TABLES / "surrogate_benchmark.json").write_text(result + "\n")
    print(json.dumps(summary["models"], indent=2))


if __name__ == "__main__":
    main()
