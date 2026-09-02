"""
EviChain - Chain Validation Scalability Plot

Regenerates the linear-scaling figure for the chain validation
benchmark directly from the measured results in
``sttt_benchmark_results.json``.  No value is hard-coded here: the
script fails rather than plotting if the benchmark archive is absent,
so the figure can never drift from the numbers reported in the paper.

Run with:  python plot_validation_scalability.py
"""

from __future__ import annotations

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "sttt_benchmark_results.json")
OUT_DIRS = [
    os.path.join(HERE, "data"),
    os.path.join(HERE, "..", "artigo", "figuras", "en"),
    os.path.join(HERE, "..", "artigo", "manuscrito", "en", "ddgov"),
]
BASENAME = "fig6_validation_scalability"


def load_measurements():
    """Return (sizes, means, stdevs) from the benchmark archive."""
    if not os.path.exists(RESULTS):
        sys.exit(
            "sttt_benchmark_results.json not found. "
            "Run run_all_benchmarks.py first."
        )
    with open(RESULTS, "r", encoding="utf-8") as fh:
        data = json.load(fh)

    entries = sorted(
        data["chain_validation"].values(), key=lambda e: e["chain_length"]
    )
    sizes = [e["chain_length"] for e in entries]
    means = [e["mean_ms"] for e in entries]
    stdevs = [e.get("stdev_ms", 0.0) for e in entries]
    return sizes, means, stdevs, data.get("timestamp", "unknown")


def least_squares(xs, ys):
    """Return (slope, intercept, r_squared) for an ordinary least-squares fit."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sxy / sxx
    intercept = my - slope * mx
    ss_res = sum((y - (slope * x + intercept)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else float("nan")
    return slope, intercept, r2


def main() -> None:
    sizes, means, stdevs, stamp = load_measurements()
    slope, intercept, r2 = least_squares(sizes, means)
    throughput = 1.0 / slope

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.linewidth": 0.6,
        "figure.dpi": 300,
    })

    fig, ax = plt.subplots(figsize=(3.4, 2.4))

    fit_x = [0, max(sizes) * 1.05]
    fit_y = [slope * x + intercept for x in fit_x]
    ax.plot(fit_x, fit_y, color="0.55", linewidth=0.9, zorder=1,
            label=r"OLS fit ($R^2 = %.4f$)" % r2)

    ax.errorbar(sizes, means, yerr=stdevs, fmt="o", color="black",
                markersize=4, elinewidth=0.8, capsize=2.5, zorder=2,
                label="measured mean $\\pm$ s.d. ($n = 10$)")

    ax.set_xlabel("Chain length $N$ (blocks)")
    ax.set_ylabel("Validation time (ms)")
    ax.set_xlim(0, max(sizes) * 1.05)
    ax.set_ylim(0, max(means) * 1.2)
    ax.grid(True, linewidth=0.3, color="0.85", zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)

    ax.annotate(
        "%.1f blocks ms$^{-1}$" % throughput,
        xy=(sizes[-1], means[-1]), xytext=(-6, -22),
        textcoords="offset points", fontsize=7.5, ha="right",
    )

    fig.tight_layout(pad=0.3)

    written = []
    for d in OUT_DIRS:
        d = os.path.abspath(d)
        if not os.path.isdir(d):
            continue
        for ext in ("pdf", "png"):
            path = os.path.join(d, "%s.%s" % (BASENAME, ext))
            fig.savefig(path, bbox_inches="tight")
            written.append(path)
    plt.close(fig)

    print("Benchmark archive timestamp: %s" % stamp)
    print("Slope: %.5f ms/block  |  Intercept: %.3f ms  |  R^2: %.5f"
          % (slope, intercept, r2))
    print("Throughput: %.1f blocks per millisecond" % throughput)
    for p in written:
        print("Wrote %s" % p)


if __name__ == "__main__":
    main()
