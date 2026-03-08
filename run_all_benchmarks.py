#!/usr/bin/env python3
"""
Run all benchmarks for the STTT manuscript and output JSON + formatted table.
d=1..4 with n=20 samples; d=5 with n=5 samples (real values, not estimates).
Chain validation with N=10..500.
"""
import sys, os, json, time, math, statistics
sys.path.insert(0, os.path.dirname(__file__))

from blockchain_simulator import Block
from benchmark import benchmark_chain_validation


def percentile(data, p):
    sorted_d = sorted(data)
    k = (len(sorted_d) - 1) * p / 100
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_d[int(k)]
    return sorted_d[f] * (c - k) + sorted_d[c] * (k - f)


def run_mining(difficulty, n_samples):
    timings = []
    nonces = []
    for i in range(n_samples):
        block = Block(
            index=1,
            timestamp=time.time(),
            data={"test": "benchmark-" + str(difficulty)},
            previous_hash="0" * 64,
        )
        start = time.perf_counter()
        block.mine_block(difficulty)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)
        nonces.append(block.nonce)
        print("    sample %d/%d: %.1f ms (nonce=%d)" % (i+1, n_samples, elapsed, block.nonce))

    mean_t = statistics.mean(timings)
    median_t = statistics.median(timings)
    stdev_t = statistics.stdev(timings) if len(timings) > 1 else 0
    se = stdev_t / math.sqrt(len(timings))
    ci_lower = mean_t - 1.96 * se
    ci_upper = mean_t + 1.96 * se
    p95 = percentile(timings, 95)
    p99 = percentile(timings, 99)

    return {
        "difficulty": difficulty,
        "n_samples": n_samples,
        "mean_ms": round(mean_t, 1),
        "median_ms": round(median_t, 1),
        "stdev_ms": round(stdev_t, 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(p99, 1),
        "ci_95_lower": round(ci_lower, 1),
        "ci_95_upper": round(ci_upper, 1),
        "mean_nonce": round(statistics.mean(nonces)),
        "max_nonce": max(nonces),
        "raw_timings_ms": [round(t, 2) for t in timings],
    }


if __name__ == "__main__":
    print("=" * 60)
    print("  EviChain Full Benchmark Suite for STTT Manuscript")
    print("=" * 60)

    all_mining = {}

    # d=1..4 with n=20
    for d in range(1, 5):
        print("\n  [Mining] Difficulty d=%d, n=20" % d)
        all_mining["d%d" % d] = run_mining(d, 20)

    # d=5 with n=5 (real, not estimated)
    print("\n  [Mining] Difficulty d=5, n=5 (real measurements)")
    all_mining["d5"] = run_mining(5, 5)

    # Chain validation
    print("\n  [Chain Validation] N=10..500, n=10 samples each")
    chain_val = benchmark_chain_validation(
        chain_sizes=[10, 50, 100, 250, 500], n_samples=10
    )

    # Save JSON
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "python_version": sys.version,
        "mining": all_mining,
        "chain_validation": chain_val,
    }
    outfile = os.path.join(os.path.dirname(__file__), "sttt_benchmark_results.json")
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print("\nResults saved to: " + outfile)

    # Print formatted table for manuscript
    print("\n" + "=" * 80)
    print("  MANUSCRIPT TABLE: Mining Performance (Tab. 3)")
    print("=" * 80)
    print("  %-12s %10s %10s %10s %10s %20s" % (
        "Difficulty", "Mean(ms)", "Median(ms)", "P95(ms)", "Stdev(ms)", "95% CI (ms)"))
    print("  " + "-" * 72)
    for d in range(1, 6):
        r = all_mining["d%d" % d]
        print("  d=%-9d %10.1f %10.1f %10.1f %10.1f    [%.1f, %.1f]" % (
            d, r["mean_ms"], r["median_ms"], r["p95_ms"],
            r["stdev_ms"], r["ci_95_lower"], r["ci_95_upper"]))

    print("\n" + "=" * 80)
    print("  MANUSCRIPT TABLE: Chain Validation Scalability")
    print("=" * 80)
    for s in [10, 50, 100, 250, 500]:
        key = "chain_%d" % s
        r = chain_val[key]
        print("  N=%-5d  mean=%.2f ms  (%s blocks/ms)" % (
            s, r["mean_ms"], r["blocks_per_ms"]))

    print("\nDone.")
