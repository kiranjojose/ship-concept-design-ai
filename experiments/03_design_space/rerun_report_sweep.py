"""Replay the published Table 2.3 sizing cases on the nominal weight model."""
from csv import DictReader
from pathlib import Path
from statistics import median
from timeit import repeat

from marine_concept_ai.weights import lightship_watson_gilfillan

TABLE = Path(__file__).resolve().parents[2] / "data/reference/dimension_sweep_table_2_3.csv"
TARGET_DWT_T = 75_000


def replay():
    cases = []
    with TABLE.open(newline="") as source:
        for row in DictReader(line for line in source if not line.startswith("#")):
            length, beam, depth, draught, displacement = (
                float(row[key]) for key in ("lbp_m", "breadth_m", "depth_m", "draught_m", "displacement_t")
            )
            # The printed CB is rounded. Recover the value implied by the published displacement.
            cb = displacement / (length * beam * draught * 1.025 * 1.006)
            lightship = lightship_watson_gilfillan(length, beam, depth, draught, cb, displacement).lightship_t
            cases.append((length, displacement - lightship))
    return cases


if __name__ == "__main__":
    cases = replay()
    # The CSV's final row is the report's separately selected case.
    grid, selected = cases[:-1], cases[-1]
    below, above = next(
        (left, right) for left, right in zip(grid, grid[1:]) if left[1] < TARGET_DWT_T <= right[1]
    )
    crossing = below[0] + (above[0] - below[0]) * (TARGET_DWT_T - below[1]) / (above[1] - below[1])
    for length, deadweight in grid:
        print(f"LPP {length:6.1f} m   DWT {deadweight:9.2f} t")
    print(f"Grid crossing (linear interpolation): {crossing:.3f} m")
    print(f"Report-selected case: LPP {selected[0]:.1f} m   DWT {selected[1]:.2f} t")
    timings = repeat(replay, number=1000, repeat=5)
    print(f"Median replay time for {len(cases)} rows: {median(timings):.3f} ms")
