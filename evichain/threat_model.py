#!/usr/bin/env python3
"""
EviChain — Formal Threat Model & Security Posture
==================================================

This module defines a **formal threat model** for the EviChain platform,
following the STRIDE taxonomy (Microsoft) and documenting exactly what the
system **does** and **does not** guarantee.

The threat model was created proactively in response to standard security-review
criteria used by academic journals (e.g., SoftwareX) and follows guidance from
OWASP Application Threat Modeling.

Key design decision
-------------------
EviChain uses a *simulated* single-node blockchain — there is **no** distributed
consensus, no decentralised network and no economically-backed immutability.
The correct security claim is **tamper-evidence**, not immutability.

Any modification to historical blocks is detectable via hash-chain validation,
but an attacker with write access to the data file *can* rewrite the entire
chain.  The model below makes this distinction explicit.

References
----------
- Shostack, A. (2014). *Threat Modeling: Designing for Security*. Wiley.
- OWASP Threat Modeling Cheat Sheet (2023).
- STRIDE taxonomy — Microsoft SDL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List


# ── Adversary Classes ──────────────────────────────────────────────

class AdversaryClass(Enum):
    """Three adversary classes ordered by increasing capability."""

    EXTERNAL = "external"
    """Network attacker without system credentials (e.g., script-kiddie,
    automated scanner).  Can only interact via the public HTTP API."""

    UNPRIVILEGED_INSIDER = "unprivileged_insider"
    """Authenticated user of the platform (e.g., a complainant or analyst).
    Can submit complaints and queries but has no server-side access."""

    PRIVILEGED_ADMIN = "privileged_admin"
    """Operator with shell/file-system access to the server.  Can read/write
    the blockchain JSON file, environment variables, and logs."""


# ── STRIDE Threat Catalogue ───────────────────────────────────────

class StrideCategory(Enum):
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFO_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


@dataclass(frozen=True)
class Threat:
    """A single identified threat entry."""

    id: str
    category: StrideCategory
    adversary: AdversaryClass
    description: str
    asset: str
    mitigation: str
    residual_risk: str
    status: str = "mitigated"  # mitigated | accepted | open


# ── Threat Registry ───────────────────────────────────────────────

THREAT_CATALOGUE: List[Threat] = [
    # ── Spoofing ──
    Threat(
        id="T-01",
        category=StrideCategory.SPOOFING,
        adversary=AdversaryClass.EXTERNAL,
        description=(
            "An external attacker submits a complaint impersonating a "
            "legitimate user through the public API."
        ),
        asset="Complaint submission endpoint",
        mitigation=(
            "The system accepts anonymous complaints by design (regulatory "
            "requirement).  Input validation sanitises all fields.  Rate "
            "limiting middleware restricts submissions per IP."
        ),
        residual_risk="Low — anonymous submission is a feature, not a bug.",
        status="accepted",
    ),
    Threat(
        id="T-02",
        category=StrideCategory.SPOOFING,
        adversary=AdversaryClass.EXTERNAL,
        description="API responses could be spoofed in transit (MITM).",
        asset="HTTP transport",
        mitigation=(
            "Production deployment uses TLS termination at the reverse "
            "proxy (nginx) with certificates from Let's Encrypt / ACM."
        ),
        residual_risk="Negligible when TLS is enforced.",
        status="mitigated",
    ),

    # ── Tampering ──
    Threat(
        id="T-03",
        category=StrideCategory.TAMPERING,
        adversary=AdversaryClass.PRIVILEGED_ADMIN,
        description=(
            "An administrator with file-system access rewrites the "
            "blockchain JSON data file, forging/deleting historical blocks."
        ),
        asset="Blockchain data file (blockchain_data.json)",
        mitigation=(
            "Hash-chain validation detects any modification to previous "
            "blocks (tamper-evidence).  Periodic off-site backups and "
            "SHA-256 checksum snapshots provide an audit trail.  "
            "NOTE: We explicitly do NOT claim immutability — the single-node "
            "architecture cannot prevent a privileged rewrite, only detect it."
        ),
        residual_risk=(
            "Medium — tamper-evidence ≠ tamper-proof.  A privileged admin "
            "can regenerate valid hashes.  External timestamping or "
            "periodic anchoring to a public blockchain could reduce this."
        ),
        status="accepted",
    ),
    Threat(
        id="T-04",
        category=StrideCategory.TAMPERING,
        adversary=AdversaryClass.EXTERNAL,
        description=(
            "Malicious JSON payload in complaint submission manipulates "
            "server-side data structures."
        ),
        asset="Complaint submission endpoint / blockchain state",
        mitigation=(
            "Strict input validation with field-level type checking.  "
            "JSON body parsing with safe defaults.  No eval/exec on "
            "user-supplied data."
        ),
        residual_risk="Low.",
        status="mitigated",
    ),

    # ── Repudiation ──
    Threat(
        id="T-05",
        category=StrideCategory.REPUDIATION,
        adversary=AdversaryClass.UNPRIVILEGED_INSIDER,
        description=(
            "A complainant denies having submitted a specific complaint."
        ),
        asset="Complaint records",
        mitigation=(
            "Each complaint is timestamped and hashed into a block.  "
            "The blockchain provides a non-repudiation chain: once mined, "
            "the transaction hash proves existence at a specific time.  "
            "Trace IDs are logged server-side for correlation."
        ),
        residual_risk=(
            "Low — hash-chain provides cryptographic proof of existence."
        ),
        status="mitigated",
    ),

    # ── Information Disclosure ──
    Threat(
        id="T-06",
        category=StrideCategory.INFO_DISCLOSURE,
        adversary=AdversaryClass.EXTERNAL,
        description=(
            "Sensitive complaint data leaked via API responses, error "
            "messages or log files."
        ),
        asset="Complaint content, complainant identity",
        mitigation=(
            "Anonymous complaints omit identity fields.  Error responses "
            "return generic messages; stack traces are logged server-side "
            "only.  Security headers (X-Content-Type-Options, "
            "X-Frame-Options, CSP) are set via middleware."
        ),
        residual_risk="Low with proper deployment configuration.",
        status="mitigated",
    ),
    Threat(
        id="T-07",
        category=StrideCategory.INFO_DISCLOSURE,
        adversary=AdversaryClass.PRIVILEGED_ADMIN,
        description=(
            "OpenAI API key or other secrets exposed through environment "
            "variables, .env files, or source code."
        ),
        asset="API credentials",
        mitigation=(
            "Secrets loaded from environment variables (never hardcoded).  "
            ".env files excluded from version control via .gitignore.  "
            "Key rotation policy documented."
        ),
        residual_risk="Low.",
        status="mitigated",
    ),

    # ── Denial of Service ──
    Threat(
        id="T-08",
        category=StrideCategory.DENIAL_OF_SERVICE,
        adversary=AdversaryClass.EXTERNAL,
        description=(
            "Flood of complaint submissions exhausts server resources "
            "(CPU via Proof of Work mining, disk via JSON writes)."
        ),
        asset="API availability",
        mitigation=(
            "Rate limiting middleware limits requests per IP per window.  "
            "Mining difficulty is fixed at 4 (bounded computation).  "
            "Waitress/gunicorn worker pool limits concurrency."
        ),
        residual_risk=(
            "Medium — sustained DDoS requires infrastructure-level "
            "protection (CloudFlare, AWS WAF) beyond application scope."
        ),
        status="mitigated",
    ),

    # ── Elevation of Privilege ──
    Threat(
        id="T-09",
        category=StrideCategory.ELEVATION_OF_PRIVILEGE,
        adversary=AdversaryClass.EXTERNAL,
        description=(
            "External attacker gains admin-level access through API "
            "vulnerabilities (e.g., path traversal, injection)."
        ),
        asset="Server integrity",
        mitigation=(
            "Flask's send_from_directory prevents path traversal.  "
            "No SQL database (eliminates SQLi).  No eval/exec on inputs.  "
            "Dependencies kept up-to-date via pip audit."
        ),
        residual_risk="Low.",
        status="mitigated",
    ),
]


# ── Security Guarantees / Non-Guarantees ──────────────────────────

@dataclass(frozen=True)
class SecurityPosture:
    """Explicit documentation of what the system does/does not guarantee."""

    guarantees: List[str] = field(default_factory=lambda: [
        "Tamper-evidence: any modification to a historical block is "
        "detectable via SHA-256 hash-chain validation.",

        "Non-repudiation: once mined, a transaction's existence at a "
        "specific time is cryptographically provable.",

        "Input sanitisation: all user-supplied data is validated and "
        "type-checked before processing.",

        "Transport security: TLS is enforced in production deployments.",

        "Secret management: credentials are loaded from environment "
        "variables, never hardcoded.",
    ])

    non_guarantees: List[str] = field(default_factory=lambda: [
        "Immutability: a privileged administrator CAN rewrite the entire "
        "chain (single-node architecture).  We claim tamper-evidence, "
        "not immutability.",

        "Byzantine fault tolerance: there is no distributed consensus.  "
        "The blockchain is a local data structure for integrity checking.",

        "Confidentiality at rest: the blockchain JSON file is stored in "
        "plaintext.  File-system permissions are the primary access control.",

        "DDoS resilience: the application does not include infrastructure-"
        "level DDoS protection.",

        "Formal verification: the blockchain simulator has not been "
        "formally verified (model-checked).",
    ])


# ── Export helpers ────────────────────────────────────────────────

def get_threat_catalogue() -> List[Dict]:
    """Return the threat catalogue as a list of dicts (JSON-serialisable)."""
    return [
        {
            "id": t.id,
            "category": t.category.value,
            "adversary": t.adversary.value,
            "description": t.description,
            "asset": t.asset,
            "mitigation": t.mitigation,
            "residual_risk": t.residual_risk,
            "status": t.status,
        }
        for t in THREAT_CATALOGUE
    ]


def get_security_posture() -> Dict:
    """Return the security posture as a dict."""
    posture = SecurityPosture()
    return {
        "guarantees": posture.guarantees,
        "non_guarantees": posture.non_guarantees,
    }


def get_threat_summary() -> Dict:
    """Return a high-level summary suitable for the article's security section."""
    by_status = {}
    by_category = {}
    by_adversary = {}

    for t in THREAT_CATALOGUE:
        by_status[t.status] = by_status.get(t.status, 0) + 1
        by_category[t.category.value] = by_category.get(t.category.value, 0) + 1
        by_adversary[t.adversary.value] = by_adversary.get(t.adversary.value, 0) + 1

    return {
        "total_threats": len(THREAT_CATALOGUE),
        "by_status": by_status,
        "by_category": by_category,
        "by_adversary": by_adversary,
        "methodology": "STRIDE (Microsoft SDL)",
        "adversary_classes": [e.value for e in AdversaryClass],
    }
