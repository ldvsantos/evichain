#!/usr/bin/env python3
"""
EviChain – Load Test for STTT Manuscript (Table 4)
===================================================
Tests 100, 250, 500 concurrent workers against the running server.
Produces the exact data needed for the manuscript load test table.

Requires: server running on localhost:5000.
"""
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


HOST = "http://localhost:5000"
DURATION_S = 15  # seconds per user level

# Endpoint definitions
READ_ENDPOINTS = [
    ("GET", "/api/health"),
    ("GET", "/api/blockchain-info"),
    ("GET", "/api/complaints"),
    ("GET", "/api/stats"),
]
SECURITY_ENDPOINTS = [
    ("GET", "/api/security/threat-model"),
    ("GET", "/api/security/posture"),
]
WRITE_PAYLOAD = json.dumps({
    "titulo": "Load test complaint",
    "descricao": (
        "O profissional realizou procedimento sem registro "
        "na academia Fit, Feira de Santana, em 01/01/2025. "
        "Consequencia: lesao leve."
    ),
    "nomeDenunciado": "Teste",
    "conselho": "CREF",
    "categoria": "exercicio_ilegal",
    "assunto": "Exercício ilegal",
    "finalidade": "Apuração",
    "anonymous": True,
}).encode("utf-8")
WRITE_ENDPOINTS = [
    ("POST", "/api/submit-complaint"),
]


def do_request(method, path, body=None):
    """Execute one request, return (latency_ms, status_code)."""
    url = HOST + path
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    start = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
            elapsed = (time.perf_counter() - start) * 1000
            return elapsed, resp.status
    except urllib.error.HTTPError as e:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, e.code
    except Exception:
        elapsed = (time.perf_counter() - start) * 1000
        return elapsed, 0


def percentile(data, p):
    if not data:
        return 0
    s = sorted(data)
    k = (len(s) - 1) * p / 100
    f, c = int(k), min(int(k) + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f)


def run_load_test(n_workers, category_name, endpoints, body=None):
    """
    Hammer endpoints with n_workers threads for DURATION_S seconds.
    Returns dict with P95, rps, success details.
    """
    latencies = []
    status_counts = {}
    stop_time = time.time() + DURATION_S
    request_count = 0

    def worker():
        nonlocal request_count
        local_lats = []
        local_status = {}
        while time.time() < stop_time:
            for method, path in endpoints:
                if time.time() >= stop_time:
                    break
                lat, status = do_request(method, path, body)
                local_lats.append(lat)
                local_status[status] = local_status.get(status, 0) + 1
        return local_lats, local_status

    start = time.time()
    with ThreadPoolExecutor(max_workers=n_workers) as pool:
        futures = [pool.submit(worker) for _ in range(n_workers)]
        for f in as_completed(futures):
            lats, st = f.result()
            latencies.extend(lats)
            for code, cnt in st.items():
                status_counts[code] = status_counts.get(code, 0) + cnt

    elapsed = time.time() - start
    total = len(latencies)
    ok_count = status_counts.get(200, 0)
    rate_limited = status_counts.get(429, 0)

    p95 = percentile(latencies, 95) if latencies else 0
    rps = total / elapsed if elapsed > 0 else 0

    return {
        "category": category_name,
        "workers": n_workers,
        "total_requests": total,
        "ok_200": ok_count,
        "rate_limited_429": rate_limited,
        "other_errors": total - ok_count - rate_limited,
        "elapsed_s": round(elapsed, 1),
        "p95_ms": round(p95, 0),
        "rps": round(rps, 1),
        "mean_ms": round(statistics.mean(latencies), 1) if latencies else 0,
        "status_distribution": status_counts,
    }


def reset_rate_limiter():
    """Send a single request to /api/health to verify connectivity."""
    try:
        do_request("GET", "/api/health")
    except Exception:
        pass


if __name__ == "__main__":
    print("=" * 70)
    print("  EviChain Load Test for STTT Manuscript (Table 4)")
    print("  Host:", HOST)
    print("  Duration per level:", DURATION_S, "seconds")
    print("=" * 70)

    # Verify server is up
    lat, status = do_request("GET", "/api/health")
    if status != 200:
        print("  ERROR: Server not responding on", HOST)
        sys.exit(1)
    print("  Server is up (health check: %.0f ms)\n" % lat)

    all_results = []
    user_levels = [10, 50, 100]

    for n_users in user_levels:
        print("  --- %d concurrent workers ---" % n_users)

        # Read endpoints
        print("    Read endpoints...", end="", flush=True)
        r = run_load_test(n_users, "Read", READ_ENDPOINTS)
        all_results.append(r)
        print("  P95=%dms  rps=%.0f  ok=%d/%d  429=%d" % (
            r["p95_ms"], r["rps"], r["ok_200"], r["total_requests"], r["rate_limited_429"]))

        time.sleep(2)  # let rate limiter window slide

        # Security endpoints
        print("    Security endpoints...", end="", flush=True)
        r = run_load_test(n_users, "Security", SECURITY_ENDPOINTS)
        all_results.append(r)
        print("  P95=%dms  rps=%.0f  ok=%d/%d  429=%d" % (
            r["p95_ms"], r["rps"], r["ok_200"], r["total_requests"], r["rate_limited_429"]))

        time.sleep(2)

        # Write endpoints
        print("    Write endpoints...", end="", flush=True)
        r = run_load_test(min(n_users, 5), "Write", WRITE_ENDPOINTS, WRITE_PAYLOAD)
        all_results.append(r)
        print("  P95=%dms  rps=%.0f  ok=%d/%d  429=%d" % (
            r["p95_ms"], r["rps"], r["ok_200"], r["total_requests"], r["rate_limited_429"]))

        time.sleep(3)
        print()

    # Save
    outfile = "load_test_results.json"
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump({"results": all_results, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")},
                  f, indent=2)
    print("  Results saved to:", outfile)

    # Print manuscript table
    print("\n" + "=" * 70)
    print("  MANUSCRIPT TABLE: Load Test Results (Tab. 4)")
    print("=" * 70)
    print("  %-25s %8s %8s %8s %8s %8s %8s" % (
        "", "10u P95", "10u rps", "50u P95", "50u rps", "100u P95", "100u rps"))
    print("  " + "-" * 73)

    for cat in ["Read", "Security", "Write"]:
        row = "  %-25s" % cat
        for n in user_levels:
            match = [r for r in all_results if r["category"] == cat and r["workers"] == n
                     or (cat == "Write" and r["category"] == "Write" and
                         r["workers"] == min(n, 5))]
            if match:
                m = match[0]
                row += " %7.0f %7.0f" % (m["p95_ms"], m["rps"])
            else:
                row += "     ---     ---"
        print(row)

    print("=" * 70)
    print("Done.")
