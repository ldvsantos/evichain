"""Write endpoint latency benchmark with mining_time_ms extraction."""
import json, time, urllib.request, statistics

# Wait for rate limiter reset
print("Waiting 65s for rate limiter reset...")
time.sleep(65)

results = []
for i in range(5):
    payload = json.dumps({
        "titulo": f"Benchmark Write Test {i+1}",
        "nomeDenunciado": f"Profissional Teste {i+1}",
        "descricao": f"Denuncia de teste numero {i+1} para benchmark de latencia do endpoint de submissao. O profissional atuou irregularmente na regiao exercendo atividade sem registro.",
        "conselho": "CREF",
        "categoria": "Exercicio ilegal",
        "assunto": "Teste benchmark",
        "finalidade": "Medicao de desempenho",
        "anonymous": True
    }).encode("utf-8")

    t0 = time.monotonic()
    req = urllib.request.Request(
        "http://127.0.0.1:5000/api/submit-complaint",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    t1 = time.monotonic()
    body = json.loads(resp.read())

    total_ms = (t1 - t0) * 1000
    mining_ms = body.get("mining_time_ms", -1)
    block_idx = body.get("block_index", "?")
    print(f"Sample {i+1}: total={total_ms:.1f}ms, mining={mining_ms}ms, block={block_idx}")
    results.append({"total_ms": total_ms, "mining_ms": mining_ms, "block": block_idx})
    time.sleep(1)

print()
print("=== SUMMARY ===")
totals = [r["total_ms"] for r in results]
minings = [r["mining_ms"] for r in results]
overheads = [t - m for t, m in zip(totals, minings)]

print(f"Total latency:     mean={statistics.mean(totals):.1f}ms, median={statistics.median(totals):.1f}ms, min={min(totals):.1f}ms, max={max(totals):.1f}ms, stdev={statistics.stdev(totals):.1f}ms")
print(f"Mining only:       mean={statistics.mean(minings):.1f}ms, median={statistics.median(minings):.1f}ms, min={min(minings):.1f}ms, max={max(minings):.1f}ms, stdev={statistics.stdev(minings):.1f}ms")
print(f"Pipeline overhead: mean={statistics.mean(overheads):.1f}ms, median={statistics.median(overheads):.1f}ms, min={min(overheads):.1f}ms, max={max(overheads):.1f}ms, stdev={statistics.stdev(overheads):.1f}ms")

# Also run read endpoint baselines
print("\n=== READ ENDPOINT BASELINE ===")
endpoints = [
    ("GET", "/api/health"),
    ("GET", "/api/blockchain-info"),
    ("GET", "/api/complaints"),
    ("GET", "/api/stats"),
    ("GET", "/api/security/threat-model"),
    ("GET", "/api/security/posture"),
]

for method, path in endpoints:
    times = []
    for _ in range(10):
        t0 = time.monotonic()
        req = urllib.request.Request(f"http://127.0.0.1:5000{path}")
        try:
            resp = urllib.request.urlopen(req)
            resp.read()
            status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        t1 = time.monotonic()
        times.append((t1 - t0) * 1000)
        time.sleep(0.1)
    
    ok_times = times  # all include both 200 and 429
    print(f"{path}: mean={statistics.mean(ok_times):.1f}ms, median={statistics.median(ok_times):.1f}ms, P95={sorted(ok_times)[int(len(ok_times)*0.95)]:.1f}ms, max={max(ok_times):.1f}ms")

# Save results
output = {
    "write_endpoint": {
        "samples": results,
        "total_mean_ms": statistics.mean(totals),
        "total_median_ms": statistics.median(totals),
        "mining_mean_ms": statistics.mean(minings),
        "mining_median_ms": statistics.median(minings),
        "overhead_mean_ms": statistics.mean(overheads),
    }
}
with open("write_benchmark_results.json", "w") as f:
    json.dump(output, f, indent=2)
print("\nResults saved to write_benchmark_results.json")
