"""
EviChain – Load Benchmark (Locust)

Simulates concurrent user load against the EviChain API to measure
P95 latency, throughput (req/s), and error rates.

Run headless (CLI):
    locust -f load_benchmark.py --host http://localhost:5000 \\
           --users 100 --spawn-rate 10 --run-time 60s --headless \\
           --csv data/load_benchmark

Run with web UI:
    locust -f load_benchmark.py --host http://localhost:5000

Produces CSV files in data/ for inclusion in the manuscript.
"""

from __future__ import annotations

import json
import random
import string
import time

from locust import HttpUser, between, task, events
from locust.runners import MasterRunner


class EviChainUser(HttpUser):
    """Simulates a typical EviChain user session."""

    wait_time = between(0.5, 2)  # seconds between requests

    # ── Read-heavy tasks (70% of traffic) ──

    @task(20)
    def health_check(self):
        self.client.get("/api/health", name="/api/health")

    @task(15)
    def blockchain_info(self):
        self.client.get("/api/blockchain-info", name="/api/blockchain-info")

    @task(15)
    def list_complaints(self):
        self.client.get("/api/complaints", name="/api/complaints")

    @task(10)
    def system_stats(self):
        self.client.get("/api/stats", name="/api/stats")

    @task(5)
    def threat_model(self):
        self.client.get(
            "/api/security/threat-model", name="/api/security/threat-model"
        )

    @task(5)
    def security_posture(self):
        self.client.get(
            "/api/security/posture", name="/api/security/posture"
        )

    # ── Write tasks (30% of traffic) ──

    @task(20)
    def submit_complaint(self):
        payload = {
            "titulo": f"Load test complaint {_random_id()}",
            "descricao": (
                "Este é um teste de carga automatizado. "
                "O profissional João da Silva, CREF 012345-G/BA, "
                "está atuando sem registro válido na academia "
                "Fitness Plus em Feira de Santana desde janeiro de 2025."
            ),
            "nomeDenunciado": "João da Silva",
            "conselho": random.choice(["CREF", "CRM", "OAB", "CREA"]),
            "categoria": "exercicio_ilegal",
            "assunto": "Exercício ilegal da profissão",
            "finalidade": "Apuração de irregularidade",
            "anonymous": True,
        }
        with self.client.post(
            "/api/submit-complaint",
            json=payload,
            name="/api/submit-complaint",
            catch_response=True,
        ) as resp:
            if resp.status_code == 429:
                resp.success()  # rate-limited is expected under load
            elif resp.status_code != 200:
                resp.failure(f"status {resp.status_code}")

    @task(10)
    def ai_analysis(self):
        payload = {
            "texto": (
                "Quero denunciar um profissional que está atuando "
                "irregularmente como personal trainer sem registro "
                "no CREF na cidade de Salvador, Bahia."
            ),
            "conselho": "CREF",
            "categoria": "exercicio_ilegal",
        }
        with self.client.post(
            "/api/assistente/analisar",
            json=payload,
            name="/api/assistente/analisar",
            catch_response=True,
        ) as resp:
            if resp.status_code in (200, 429):
                resp.success()
            else:
                resp.failure(f"status {resp.status_code}")


def _random_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))
