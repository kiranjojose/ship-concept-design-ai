"""Figures for the Sprint 2 sweep (reads results/tables/s2_*.csv, writes results/figures/s2_*.png)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TAB, FIG = ROOT / "results" / "tables", ROOT / "results" / "figures"
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"
CLASSES = [  # (key, label, colour, marker) - fixed order
    ("robust", "≥ 75,000 t in every scenario", "#2a78d6", "o"),
    ("nominal_only", "≥ 75,000 t at nominal only", "#eda100", "D"),
    ("short", "short of 75,000 t", "#a3a29b", "x"),
    ("other_fail", "fails freeboard or stowage", "#eb6834", "^"),
]


def classify(c):
    cls = c.dwt_verdict.replace({"best_case_only": "short"})
    return cls.where(c.fails_other_than_dwt.isna(), "other_fail")


def style(ax):
    ax.grid(color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)


def scatter(ax, c, x, y, ref):
    for key, label, col, m in CLASSES:
        g = c[c.cls == key]
        ax.scatter(g[x], g[y], s=22, c=col, marker=m, lw=1.2 if m == "x" else 0.6,
                   edgecolors="white" if m != "x" else None, label=f"{label} ({len(g)})")
    ax.scatter(ref[x], ref[y], s=140, marker="*", c=INK, edgecolors="white", lw=0.8, zorder=5,
               label="reference (2019 design, rebuilt)")
    style(ax)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(TAB / "s2_sweep_candidates.csv")
    ref = d[d.candidate_id == "REF"].iloc[0]
    c = d[d.candidate_id != "REF"].copy()
    c["cls"] = classify(c)

    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    scatter(axs[0], c, "lpp_m", "breadth_m", ref)
    axs[0].set(xlabel="LPP (m)", ylabel="B (m)")
    scatter(axs[1], c, "draught_m", "cb", ref)
    axs[1].set(xlabel="T (m)", ylabel="CB from geometry (on LPP)")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="lower center", ncol=3, frameon=False, fontsize=8)
    fig.suptitle(f"Deadweight feasibility of {len(c)} Latin-hypercube candidates at 13 kn", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0.1, 1, 0.95))
    fig.savefig(FIG / "s2_feasible_region.png", dpi=200)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 4.2))
    scatter(ax, c, "disp_pchip_t", "dwt_margin_worst_t", ref)
    ax.axhline(0, color=INK, lw=1)
    ax.text(c.disp_pchip_t.min(), 300, "75,000 t requirement, worst case", fontsize=8, color=INK)
    ax.set(xlabel="Displacement from rebuilt geometry, ×1.006 (t)",
           ylabel="Worst-case DWT margin (t)\n(linear offsets, high lightship)")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "s2_dwt_margin_vs_displacement.png", dpi=200)
    plt.close(fig)

    r = pd.read_csv(TAB / "s2_recovery_one_at_a_time.csv")
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    vars_ = ["L", "B", "T", "CB"]
    y = range(len(vars_))
    for off, basis, col, lab in ((-0.18, "nominal", "#2a78d6", "nominal"),
                                 (0.18, "worst", "#eb6834", "worst case")):
        v = r[r.dwt_basis == basis].set_index("variable").loc[vars_]
        ax.barh([i + off for i in y], v.change_pct, height=0.34, color=col, label=lab)
        for i, (pct, ch) in enumerate(zip(v.change_pct, v.change)):
            unit = "" if vars_[i] == "CB" else " m"
            ax.text(pct + 0.05, i + off, f"+{ch:.3f}{unit}" if vars_[i] == "CB" else f"+{ch:.2f}{unit}",
                    va="center", fontsize=7.5, color=INK)
    ax.set_yticks(list(y), vars_)
    ax.invert_yaxis()
    ax.set_xlabel("Change from the reference needed for 75,000 t, others fixed (%)")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    style(ax)
    fig.tight_layout()
    fig.savefig(FIG / "s2_recovery_one_at_a_time.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    main()
