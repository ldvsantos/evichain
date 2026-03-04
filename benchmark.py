#!/usr/bin/env python3
"""
EviChain — Load Testing & Benchmark Suite
==========================================

Standalone benchmark script that measures API latency and throughput
WITHOUT external dependencies (no locust, no autocannon).

Generates JSON metrics suitable for inclusion in the academic article
with statistical rigour: mean, median, p95, p99, std-dev, 95% CI.

Usage:
    python benchmark.py                         # defaults to localhost:5000
    python benchmark.py --host http://server:5000 --requests 500
    python benchmark.py --output results.json

Outputs
-------
- Console summary with formatted table
- JSON file with raw measurements for reproducibility

Addresses SoftwareX reviewer criticism: "No load/stress testing provided."
"""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Tuple


# ── Configuration ────────────────────────────────────────────────

DEFAULT_HOST = "http://localhost:5000"
DEFAULT_TOTAL_REQUESTS = 200
DEFAULT_CONCURRENCY = 10


# ── Data Structures ──────────────────────────────────────────────

@dataclass
class RequestResult:
    """Result of a single HTTP request."""
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    success: bool
    error: str = ""
    timestamp: float = 0.0


@dataclass
class EndpointStats:
    """Aggregated statistics for one endpoint."""
    endpoint: str
    method: str
    total_requests: int = 0
    successful: int = 0
    failed: int = 0
    latencies_ms: List[float] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return (self.successful / self.total_requests * 100) if self.total_requests else 0

    @property
    def mean_ms(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0

    @property
    def median_ms(self) -> float:
        return statistics.median(self.latencies_ms) if self.latencies_ms else 0

    @property
    def stdev_ms(self) -> float:
        return statistics.stdev(self.latencies_ms) if len(self.latencies_ms) > 1 else 0

    @property
    def p95_ms(self) -> float:
        return self._percentile(95)

    @property
    def p99_ms(self) -> float:
        return self._percentile(99)

    @property
    def min_ms(self) -> float:
        return min(self.latencies_ms) if self.latencies_ms else 0

    @property
    def max_ms(self) -> float:
        return max(self.latencies_ms) if self.latencies_ms else 0

    @property
    def ci_95(self) -> Tuple[float, float]:
        """95% confidence interval for the mean (t-distribution approximation)."""
        if len(self.latencies_ms) < 2:
            return (self.mean_ms, self.mean_ms)
        n = len(self.latencies_ms)
        se = self.stdev_ms / math.sqrt(n)
        # z=1.96 for 95% CI (normal approximation, valid for n≥30)
        margin = 1.96 * se
        return (self.mean_ms - margin, self.mean_ms + margin)

    def _percentile(self, p: int) -> float:
        if not self.latencies_ms:
            return 0
        sorted_l = sorted(self.latencies_ms)
        k = (len(sorted_l) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return sorted_l[int(k)]
        return sorted_l[f] * (c - k) + sorted_l[c] * (k - f)

    def to_dict(self) -> Dict:
        ci = self.ci_95
        return {
            "endpoint": self.endpoint,
            "method": self.method,
            "total_requests": self.total_requests,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate_pct": round(self.success_rate, 2),
            "latency_ms": {
                "mean": round(self.mean_ms, 2),
                "median": round(self.median_ms, 2),
                "stdev": round(self.stdev_ms, 2),
                "min": round(self.min_ms, 2),
                "max": round(self.max_ms, 2),
                "p95": round(self.p95_ms, 2),
                "p99": round(self.p99_ms, 2),
                "ci_95_lower": round(ci[0], 2),
                "ci_95_upper": round(ci[1], 2),
            },
        }


@dataclass
class BenchmarkResult:
    """Complete benchmark run result."""
    timestamp: str
    host: str
    total_requests: int
    concurrency: int
    duration_seconds: float
    requests_per_second: float
    endpoints: List[Dict]
    system_info: Dict


# ── HTTP Helpers ─────────────────────────────────────────────────

def http_request(url: str, method: str = "GET", body: bytes = None,
                 headers: dict = None) -> RequestResult:
    """Execute a single HTTP request and measure latency."""
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    start = time.perf_counter()

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()  # consume body
            elapsed = (time.perf_counter() - start) * 1000
            return RequestResult(
                endpoint=url, method=method,
                status_code=resp.status,
                latency_ms=elapsed, success=True,
                timestamp=time.time()
            )
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            endpoint=url, method=method,
            status_code=e.code,
            latency_ms=elapsed, success=False,
            error=str(e), timestamp=time.time()
        )
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        return RequestResult(
            endpoint=url, method=method,
            status_code=0,
            latency_ms=elapsed, success=False,
            error=str(e), timestamp=time.time()
        )


# ── Benchmark Scenarios ──────────────────────────────────────────

def create_sample_complaint() -> bytes:
    """Create a realistic complaint payload for benchmarking."""
    return json.dumps({
        "titulo": "Benchmark Test Complaint",
        "nomeDenunciado": "Profissional Teste",
        "descricao": (
            "Esta é uma denúncia de teste gerada automaticamente pelo "
            "benchmark suite do EviChain. O profissional realizou "
            "procedimento sem habilitação no dia 01/01/2025 no consultório "
            "localizado na Rua Teste, nº 123. A consequência foi um dano "
            "físico leve ao paciente que precisou de atendimento hospitalar."
        ),
        "conselho": "CREF",
        "categoria": "Exercício Ilegal",
        "anonymous": True,
        "assunto": "Exercício ilegal da profissão",
        "prioridade": "alta",
        "finalidade": "Apuração disciplinar",
    }).encode("utf-8")


BENCHMARK_SCENARIOS = [
    # (name, method, path, body_factory)
    ("health_check", "GET", "/api/health", None),
    ("blockchain_info", "GET", "/api/blockchain-info", None),
    ("list_complaints", "GET", "/api/complaints", None),
    ("get_stats", "GET", "/api/stats", None),
    ("threat_model", "GET", "/api/security/threat-model", None),
    ("security_posture", "GET", "/api/security/posture", None),
    ("submit_complaint", "POST", "/api/submit-complaint", create_sample_complaint),
]


# ── Benchmark Runner ─────────────────────────────────────────────

def run_scenario(host: str, scenario: tuple, n_requests: int,
                 concurrency: int) -> EndpointStats:
    """Run N requests for a single scenario with given concurrency."""
    name, method, path, body_fn = scenario
    url = f"{host.rstrip('/')}{path}"
    stats = EndpointStats(endpoint=f"{method} {path}", method=method)

    def single_request(_: int) -> RequestResult:
        body = body_fn() if body_fn else None
        return http_request(url, method=method, body=body)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(single_request, i) for i in range(n_requests)]
        for f in as_completed(futures):
            result = f.result()
            stats.total_requests += 1
            if result.success:
                stats.successful += 1
            else:
                stats.failed += 1
            stats.latencies_ms.append(result.latency_ms)

    return stats


def run_benchmark(host: str, total_requests: int = DEFAULT_TOTAL_REQUESTS,
                  concurrency: int = DEFAULT_CONCURRENCY,
                  scenarios: list = None) -> BenchmarkResult:
    """Run the full benchmark suite."""
    if scenarios is None:
        scenarios = BENCHMARK_SCENARIOS

    # Distribute requests across scenarios
    requests_per_scenario = max(1, total_requests // len(scenarios))

    print(f"\n{'='*60}")
    print(f"  EviChain Benchmark Suite")
    print(f"  Host: {host}")
    print(f"  Total requests: {requests_per_scenario * len(scenarios)}")
    print(f"  Concurrency: {concurrency}")
    print(f"  Scenarios: {len(scenarios)}")
    print(f"{'='*60}\n")

    all_stats: List[EndpointStats] = []
    start_time = time.perf_counter()

    for scenario in scenarios:
        name = scenario[0]
        print(f"  Running: {name} ({requests_per_scenario} requests, "
              f"{concurrency} concurrent)...", end="", flush=True)

        stats = run_scenario(host, scenario, requests_per_scenario, concurrency)
        all_stats.append(stats)

        print(f"  mean={stats.mean_ms:.1f}ms  p95={stats.p95_ms:.1f}ms  "
              f"ok={stats.successful}/{stats.total_requests}")

    total_duration = time.perf_counter() - start_time
    total_reqs = sum(s.total_requests for s in all_stats)

    # System info for reproducibility
    import platform
    sys_info = {
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
    }

    result = BenchmarkResult(
        timestamp=datetime.now().isoformat(),
        host=host,
        total_requests=total_reqs,
        concurrency=concurrency,
        duration_seconds=round(total_duration, 2),
        requests_per_second=round(total_reqs / total_duration, 2),
        endpoints=[s.to_dict() for s in all_stats],
        system_info=sys_info,
    )

    # Print summary table
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Duration : {total_duration:.2f}s")
    print(f"  Throughput      : {total_reqs / total_duration:.1f} req/s")
    print(f"{'='*60}")
    print(f"  {'Endpoint':<30} {'Mean':>8} {'Median':>8} {'P95':>8} {'P99':>8} {'OK%':>6}")
    print(f"  {'-'*30} {'---':>8} {'---':>8} {'---':>8} {'---':>8} {'---':>6}")

    for s in all_stats:
        print(f"  {s.endpoint:<30} {s.mean_ms:>7.1f}ms {s.median_ms:>7.1f}ms "
              f"{s.p95_ms:>7.1f}ms {s.p99_ms:>7.1f}ms {s.success_rate:>5.1f}%")

    print(f"{'='*60}\n")

    return result


# ── Blockchain-Specific Benchmarks ───────────────────────────────

def benchmark_mining(difficulty_range: range = range(1, 6),
                     n_samples: int = 20) -> Dict:
    """Benchmark mining performance across different difficulty levels.

    This runs in-process (no HTTP) to measure raw blockchain performance.
    """
    # Import here to avoid circular imports if run from project root
    sys.path.insert(0, os.path.dirname(__file__))
    from blockchain_simulator import Block

    print(f"\n{'='*60}")
    print(f"  Mining Benchmark (PoW)")
    print(f"  Difficulties: {list(difficulty_range)}")
    print(f"  Samples per difficulty: {n_samples}")
    print(f"{'='*60}\n")

    results = {}

    for difficulty in difficulty_range:
        timings = []
        nonces = []

        for _ in range(n_samples):
            block = Block(
                index=1,
                timestamp=time.time(),
                data={"test": f"benchmark-{difficulty}"},
                previous_hash="0" * 64,
            )
            start = time.perf_counter()
            block.mine_block(difficulty)
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)
            nonces.append(block.nonce)

        mean_t = statistics.mean(timings)
        median_t = statistics.median(timings)
        stdev_t = statistics.stdev(timings) if len(timings) > 1 else 0
        se = stdev_t / math.sqrt(len(timings))
        ci_lower = mean_t - 1.96 * se
        ci_upper = mean_t + 1.96 * se

        results[f"difficulty_{difficulty}"] = {
            "difficulty": difficulty,
            "n_samples": n_samples,
            "mean_ms": round(mean_t, 2),
            "median_ms": round(median_t, 2),
            "stdev_ms": round(stdev_t, 2),
            "min_ms": round(min(timings), 2),
            "max_ms": round(max(timings), 2),
            "ci_95": [round(ci_lower, 2), round(ci_upper, 2)],
            "mean_nonce": round(statistics.mean(nonces)),
            "max_nonce": max(nonces),
        }

        print(f"  Difficulty {difficulty}: mean={mean_t:.1f}ms  "
              f"median={median_t:.1f}ms  CI95=[{ci_lower:.1f}, {ci_upper:.1f}]  "
              f"nonces={round(statistics.mean(nonces))}")

    print(f"\n{'='*60}\n")
    return results


def benchmark_chain_validation(chain_sizes: list = None,
                               n_samples: int = 10) -> Dict:
    """Benchmark chain validation time as a function of chain length."""
    if chain_sizes is None:
        chain_sizes = [10, 50, 100, 250, 500]

    sys.path.insert(0, os.path.dirname(__file__))
    from blockchain_simulator import EviChainBlockchain

    print(f"\n{'='*60}")
    print(f"  Chain Validation Benchmark")
    print(f"  Sizes: {chain_sizes}")
    print(f"{'='*60}\n")

    results = {}
    tmp_file = "_benchmark_chain_tmp.json"

    for size in chain_sizes:
        # Build a chain of the desired size (difficulty=1 for speed)
        bc = EviChainBlockchain(data_file=tmp_file)
        bc.difficulty = 1  # fast mining for benchmark purposes

        for i in range(size):
            bc.add_evidence_transaction({"titulo": f"Bench-{i}", "descricao": f"test-{i}"})
            bc.mine_pending_transactions()

        # Measure validation
        timings = []
        for _ in range(n_samples):
            start = time.perf_counter()
            bc.is_chain_valid()
            elapsed = (time.perf_counter() - start) * 1000
            timings.append(elapsed)

        mean_t = statistics.mean(timings)
        stdev_t = statistics.stdev(timings) if len(timings) > 1 else 0

        results[f"chain_{size}"] = {
            "chain_length": size,
            "n_samples": n_samples,
            "mean_ms": round(mean_t, 2),
            "stdev_ms": round(stdev_t, 2),
            "blocks_per_ms": round(size / mean_t, 2) if mean_t > 0 else 0,
        }

        print(f"  Size {size:>4}: validation mean={mean_t:.2f}ms  "
              f"({size / mean_t:.0f} blocks/ms)")

    # Cleanup temp file
    try:
        os.remove(tmp_file)
    except OSError:
        pass

    print(f"\n{'='*60}\n")
    return results


# ── Main ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="EviChain Benchmark Suite")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server URL (default: {DEFAULT_HOST})")
    parser.add_argument("--requests", type=int, default=DEFAULT_TOTAL_REQUESTS,
                        help=f"Total requests across all scenarios (default: {DEFAULT_TOTAL_REQUESTS})")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY,
                        help=f"Concurrent workers (default: {DEFAULT_CONCURRENCY})")
    parser.add_argument("--output", default="benchmark_results.json",
                        help="Output JSON file (default: benchmark_results.json)")
    parser.add_argument("--mining-only", action="store_true",
                        help="Run only the mining benchmark (no HTTP)")
    parser.add_argument("--validation-only", action="store_true",
                        help="Run only the chain validation benchmark")
    parser.add_argument("--full", action="store_true",
                        help="Run all benchmarks (HTTP + mining + validation)")

    args = parser.parse_args()
    all_results = {"run_timestamp": datetime.now().isoformat()}

    if args.mining_only:
        all_results["mining"] = benchmark_mining()
    elif args.validation_only:
        all_results["chain_validation"] = benchmark_chain_validation()
    elif args.full:
        # HTTP benchmarks
        http_result = run_benchmark(args.host, args.requests, args.concurrency)
        all_results["http_benchmark"] = {
            "host": http_result.host,
            "total_requests": http_result.total_requests,
            "concurrency": http_result.concurrency,
            "duration_seconds": http_result.duration_seconds,
            "requests_per_second": http_result.requests_per_second,
            "endpoints": http_result.endpoints,
            "system_info": http_result.system_info,
        }
        # Mining benchmark
        all_results["mining"] = benchmark_mining()
        # Validation benchmark
        all_results["chain_validation"] = benchmark_chain_validation()
    else:
        # Default: HTTP benchmarks only
        http_result = run_benchmark(args.host, args.requests, args.concurrency)
        all_results["http_benchmark"] = {
            "host": http_result.host,
            "total_requests": http_result.total_requests,
            "concurrency": http_result.concurrency,
            "duration_seconds": http_result.duration_seconds,
            "requests_per_second": http_result.requests_per_second,
            "endpoints": http_result.endpoints,
            "system_info": http_result.system_info,
        }

    # Save results
    output_path = args.output
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to: {output_path}")


if __name__ == "__main__":
    main()
