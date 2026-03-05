# EviChain — Security Documentation

> **Version:** 1.0.0  
> **Last updated:** 2026-03-04  
> **Methodology:** STRIDE (Microsoft SDL)  
> **Status:** Active  

---

## 1. Security Architecture Overview

EviChain is a **single-node blockchain simulator** designed for evidence
integrity in professional-council complaint processing. The system does **not**
operate a distributed network — all blocks are stored locally in a JSON file.

### What We Guarantee (Tamper-Evidence)

| Property | Mechanism |
|----------|-----------|
| **Integrity detection** | SHA-256 hash chain — any modification to a committed block is detectable via `is_chain_valid()` |
| **Non-repudiation** | Once mined, a transaction's hash proves existence at a specific timestamp |
| **Input sanitisation** | All user data is validated and type-checked; no `eval`/`exec` on inputs |
| **Transport security** | TLS termination at nginx reverse proxy (production) |
| **Secret management** | Credentials via environment variables; `.env` excluded from VCS |

### What We Do NOT Guarantee (Explicit Non-Claims)

| Property | Reason |
|----------|--------|
| **Immutability** | A privileged admin with file access CAN rewrite the chain. We claim tamper-evidence, not immutability. |
| **Byzantine fault tolerance** | No distributed consensus — single-node architecture |
| **Confidentiality at rest** | Blockchain JSON is plaintext; relies on OS file permissions |
| **DDoS resilience** | Application-level rate limiting only; infrastructure protection out of scope |
| **Formal verification** | Blockchain simulator has not been model-checked |

> **Note:** The distinction between *tamper-evident* and *immutable* is
> critical. An immutability claim would require a decentralised consensus
> mechanism (e.g., Byzantine fault-tolerant protocol with >2/3 honest nodes).
> Our single-node architecture provides detection, not prevention, of tampering.

---

## 2. Threat Model (STRIDE)

### 2.1 Adversary Classes

| Class | Description | Capabilities |
|-------|-------------|-------------|
| **External** | Network attacker without credentials | Public HTTP API only |
| **Unprivileged Insider** | Authenticated platform user | Submit complaints, query data |
| **Privileged Admin** | Server operator | File system, env vars, logs |

### 2.2 Threat Catalogue

| ID | Category | Adversary | Threat | Mitigation | Status |
|----|----------|-----------|--------|------------|--------|
| T-01 | Spoofing | External | Impersonation via public API | Anonymous by design; input validation; rate limiting | Accepted |
| T-02 | Spoofing | External | MITM on HTTP transport | TLS at reverse proxy (nginx + Let's Encrypt) | Mitigated |
| T-03 | Tampering | Privileged Admin | Rewrite blockchain JSON file | Hash-chain detects tampering; off-site backups; we do NOT claim immutability | Accepted |
| T-04 | Tampering | External | Malicious JSON payload | Strict field-level validation; safe JSON parsing | Mitigated |
| T-05 | Repudiation | Insider | Deny complaint submission | Timestamped hash in blockchain; server-side trace logs | Mitigated |
| T-06 | Info Disclosure | External | Data leak via error messages | Generic error responses; stack traces server-side only; security headers | Mitigated |
| T-07 | Info Disclosure | Admin | Secret exposure (.env, logs) | Env vars (no hardcoding); .gitignore; key rotation | Mitigated |
| T-08 | DoS | External | API flood exhausts resources | Rate limiter (30 req/min/IP); bounded PoW; worker pool limits | Mitigated |
| T-09 | EoP | External | Path traversal / injection | Flask `send_from_directory`; no SQL; no eval; pip audit | Mitigated |

### 2.3 Programmatic Access

The threat model is also available via API:

```
GET /api/security/threat-model   → full STRIDE catalogue (JSON)
GET /api/security/posture        → guarantees & non-guarantees
GET /api/security/summary        → high-level counts
```

---

## 3. Security Headers (OWASP)

The following headers are set on **every** HTTP response via Flask middleware:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | XSS filter (legacy browsers) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Permissions-Policy` | `geolocation=(), camera=(), microphone=()` | Restrict browser APIs |
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'; ...` | Content injection prevention |

---

## 4. Rate Limiting

- **Algorithm:** Sliding window, in-memory, per-IP
- **Window:** 60 seconds
- **Max requests:** 30 per IP per window
- **Scope:** All `/api/*` endpoints (static files excluded)
- **Response on limit:** HTTP 429 with JSON error body

---

## 5. Dependency Security

### 5.1 Runtime Dependencies

| Package | Version | Purpose | Known CVEs |
|---------|---------|---------|------------|
| Flask | ≥2.0.0 | Web framework | Check `pip audit` |
| Waitress | ≥2.1.2 | Production WSGI server | — |
| Flask-CORS | ≥4.0.0 | CORS middleware | — |
| Gunicorn | ≥21.2.0 | WSGI server (Linux) | — |
| Requests | ≥2.25.0 | HTTP client (scraping) | — |
| OpenAI | ≥1.0.0 | GPT integration | — |
| BeautifulSoup4 | ≥4.12.0 | HTML parsing | — |
| lxml | ≥4.9.0 | XML/HTML parser | — |

### 5.2 Audit Commands

```bash
# Python dependencies
pip audit

# Check for outdated packages
pip list --outdated

# Generate SBOM (Software Bill of Materials)
pip install pip-audit
pip-audit --format json --output sbom.json
```

---

## 6. Data Flow & Trust Boundaries

```
┌──────────────┐       TLS        ┌──────────────┐
│   Browser /  │◄────────────────►│    nginx      │
│   Desktop    │                  │  (reverse     │
│   Client     │                  │   proxy)      │
└──────────────┘                  └──────┬───────┘
                                         │ HTTP (local)
                                  ┌──────▼───────┐
                                  │  Flask API   │
                                  │  (Waitress)  │
                                  ├──────────────┤
                                  │ Rate Limiter │◄── Trust Boundary
                                  │ Security Hdr │
                                  ├──────────────┤
                 ┌────────────────┤  Blockchain  │
                 │                │  Simulator   │
                 │                ├──────────────┤
                 │                │  AI Engine   │──► OpenAI API (TLS)
                 │                │  (GPT)       │
                 │                ├──────────────┤
                 │                │ Investigador │──► Council APIs
                 │                │  Digital     │    (CONFEF, CFM, OAB)
                 │                └──────────────┘
                 │
          ┌──────▼───────┐
          │ blockchain_  │
          │ data.json    │◄── File system (Trust Boundary)
          └──────────────┘
```

---

## 7. Incident Response

### 7.1 Chain Corruption Detected

1. `is_chain_valid()` returns `False` → logged with block index
2. Alert admin via log monitoring
3. Restore from latest verified backup
4. Compare checksums against off-site copy

### 7.2 API Key Compromised

1. Revoke key immediately via OpenAI dashboard
2. Rotate `.env` / environment variable
3. Review access logs for unauthorised usage
4. Generate new key and redeploy

### 7.3 Reporting Vulnerabilities

Please report security vulnerabilities via email to the project maintainers.
Do not open public issues for security-sensitive matters.

---

## 8. Compliance Notes

- **LGPD (Lei 13.709/2018):** Anonymous complaints do not store PII of the
  complainant. Professional names are public registry data.
- **Marco Legal das Assinaturas Eletrônicas (Lei 14.063/2020):** O hash-chain
  fornece tamper-evidence (detecção de adulteração) para timestamping de
  evidências, mas não constitui assinatura eletrônica nos termos da Lei.
- **OWASP Top 10 (2021):** Addressed items: A01 (Broken Access Control — rate
  limiting), A03 (Injection — no SQL/eval), A05 (Security Misconfiguration —
  security headers), A09 (Security Logging — trace IDs).

---

## 9. Changelog

| Date | Version | Change |
|------|---------|--------|
| 2026-03-04 | 1.0.0 | Initial threat model, security headers, rate limiting |
