# EviChain — Replication Package
# ================================
#
# This script sets up and runs the complete evaluation pipeline
# for replicating the results reported in the STTT article.
#
# Prerequisites:
#   - Python 3.10+
#   - pip install -r requirements.txt
#
# Usage:
#   python run_replication.py              # full replication
#   python run_replication.py --quick      # quick smoke test
#   python run_replication.py --output-dir results/
#
# Output:
#   results/
#     ├── benchmark_results.json       # API & mining benchmarks
#     ├── evaluation_results.json      # Quality & integrity metrics
#     ├── threat_model.json            # STRIDE catalogue export
#     ├── dpia_report.json             # LGPD/GDPR compliance report
#     ├── replication_summary.json     # Overall summary
#     └── replication_package.zip      # Self-contained archive

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path


def ensure_project_path():
    """Ensure the project root is in sys.path."""
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def run_replication(output_dir: str = "replication_results",
                    quick: bool = False) -> dict:
    """Run the full replication pipeline."""
    ensure_project_path()

    os.makedirs(output_dir, exist_ok=True)

    summary = {
        "replication_timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "quick_mode": quick,
        "steps": {},
    }

    print(f"\n{'='*60}")
    print(f"  EviChain Replication Package Runner")
    print(f"  Output: {output_dir}/")
    print(f"  Mode: {'quick' if quick else 'full'}")
    print(f"{'='*60}\n")

    # ── Step 1: Export Threat Model ──
    print("  [1/6] Exporting threat model...")
    try:
        from evichain.threat_model import (
            get_threat_catalogue, get_security_posture, get_threat_summary
        )
        threat_data = {
            "threats": get_threat_catalogue(),
            "posture": get_security_posture(),
            "summary": get_threat_summary(),
        }
        threat_path = os.path.join(output_dir, "threat_model.json")
        with open(threat_path, "w", encoding="utf-8") as f:
            json.dump(threat_data, f, indent=2, ensure_ascii=False)
        summary["steps"]["threat_model"] = {"status": "ok", "file": threat_path}
        print(f"        Saved to {threat_path}")
    except Exception as e:
        summary["steps"]["threat_model"] = {"status": "error", "error": str(e)}
        print(f"        Error: {e}")

    # ── Step 2: Mining Benchmark ──
    print("  [2/6] Running mining benchmark...")
    try:
        from benchmark import benchmark_mining, benchmark_chain_validation

        mining_results = benchmark_mining(
            difficulty_range=range(1, 5) if quick else range(1, 6),
            n_samples=5 if quick else 20,
        )
        benchmark_data = {"mining": mining_results}

        if not quick:
            print("        Running chain validation benchmark...")
            val_results = benchmark_chain_validation(
                chain_sizes=[10, 50, 100] if quick else [10, 50, 100, 250, 500],
                n_samples=3 if quick else 10,
            )
            benchmark_data["chain_validation"] = val_results

        bench_path = os.path.join(output_dir, "benchmark_results.json")
        with open(bench_path, "w", encoding="utf-8") as f:
            json.dump(benchmark_data, f, indent=2, ensure_ascii=False)
        summary["steps"]["benchmark"] = {"status": "ok", "file": bench_path}
        print(f"        Saved to {bench_path}")
    except Exception as e:
        summary["steps"]["benchmark"] = {"status": "error", "error": str(e)}
        print(f"        Error: {e}")

    # ── Step 3: Evaluation Metrics ──
    print("  [3/6] Running evaluation metrics...")
    try:
        from evaluation_metrics import run_full_evaluation

        eval_path = os.path.join(output_dir, "evaluation_results.json")
        run_full_evaluation(
            blockchain_file="data/blockchain_data.json",
            output=eval_path,
        )
        summary["steps"]["evaluation"] = {"status": "ok", "file": eval_path}
        print(f"        Saved to {eval_path}")
    except Exception as e:
        summary["steps"]["evaluation"] = {"status": "error", "error": str(e)}
        print(f"        Error: {e}")

    # ── Step 4: System Info ──
    print("  [4/6] Collecting system info...")
    try:
        import platform
        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "timestamp": datetime.now().isoformat(),
        }

        # Collect installed packages
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                system_info["installed_packages"] = json.loads(result.stdout)
        except Exception:
            system_info["installed_packages"] = "could not collect"

        summary["steps"]["system_info"] = {"status": "ok", "data": system_info}
    except Exception as e:
        summary["steps"]["system_info"] = {"status": "error", "error": str(e)}

    # ── Step 5: LGPD/GDPR Compliance Report ──
    print("  [5/6] Generating LGPD/GDPR compliance report...")
    try:
        from evichain.lgpd_compliance import LGPDComplianceMatrix
        lgpd = LGPDComplianceMatrix()
        dpia_path = os.path.join(output_dir, "dpia_report.json")
        lgpd.generate_dpia_report(dpia_path, fmt="json")
        summary["steps"]["lgpd_compliance"] = {
            "status": "ok",
            "file": dpia_path,
            "compliance_summary": lgpd.compliance_summary(),
        }
        print(f"        Saved to {dpia_path}")
    except Exception as e:
        summary["steps"]["lgpd_compliance"] = {"status": "error", "error": str(e)}
        print(f"        Error: {e}")

    # ── Save Summary ──
    summary_path = os.path.join(output_dir, "replication_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # ── Step 6: Build replication ZIP archive ──
    print("  [6/6] Building replication ZIP archive...")
    try:
        zip_path = os.path.join(output_dir, "replication_package.zip")
        project_root = Path(__file__).resolve().parent
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Include all result files
            for fname in os.listdir(output_dir):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath) and fname != "replication_package.zip":
                    zf.write(fpath, f"results/{fname}")
            # Include key source files
            source_files = [
                "benchmark.py",
                "evaluation_metrics.py",
                "run_replication.py",
                "requirements.txt",
                "blockchain_simulator.py",
                "evichain/threat_model.py",
                "evichain/external_anchor.py",
                "evichain/audit_log.py",
                "evichain/lgpd_compliance.py",
                "evichain/settings.py",
                "evichain/services.py",
                "load_benchmark.py",
            ]
            for sf in source_files:
                sf_full = project_root / sf
                if sf_full.exists():
                    zf.write(str(sf_full), f"src/{sf}")
            # Include test files
            test_dir = project_root / "tests"
            if test_dir.exists():
                for tf in test_dir.rglob("*.py"):
                    rel = tf.relative_to(project_root)
                    zf.write(str(tf), f"src/{rel}")
            # Include README
            readme = project_root / "README.md"
            if readme.exists():
                zf.write(str(readme), "README.md")

        summary["steps"]["zip_archive"] = {"status": "ok", "file": zip_path}
        print(f"        Saved to {zip_path}")
    except Exception as e:
        summary["steps"]["zip_archive"] = {"status": "error", "error": str(e)}
        print(f"        Error: {e}")

    # Update summary with zip info and re-save
    summary_path = os.path.join(output_dir, "replication_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Report
    ok_count = sum(1 for s in summary["steps"].values() if s.get("status") == "ok")
    total = len(summary["steps"])

    print(f"\n{'='*60}")
    print(f"  Replication complete: {ok_count}/{total} steps succeeded")
    print(f"  Results in: {output_dir}/")
    print(f"{'='*60}\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EviChain Replication Package")
    parser.add_argument("--output-dir", default="replication_results",
                        help="Output directory (default: replication_results/)")
    parser.add_argument("--quick", action="store_true",
                        help="Quick mode with reduced samples")
    args = parser.parse_args()

    run_replication(output_dir=args.output_dir, quick=args.quick)
