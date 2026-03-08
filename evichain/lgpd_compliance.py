"""
EviChain – LGPD Compliance Mapping & DPIA Report Generator

Generates a Data Protection Impact Assessment (DPIA) report mapping
Brazilian LGPD (Lei 13.709/2018) articles to EviChain controls.

Provides:
    1. Article-by-article compliance matrix (LGPD → implemented control).
    2. GDPR cross-reference for international reviewers.
    3. JSON + HTML export of DPIA report.

Usage::

    from evichain.lgpd_compliance import LGPDComplianceReport
    report = LGPDComplianceReport()
    dpia = report.generate_dpia()
    report.export_json("data/lgpd_dpia.json")
    report.export_html("data/lgpd_dpia.html")
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------
# LGPD Article → Control mapping
# ---------------------------------------------------------------

LGPD_CONTROLS: list[dict] = [
    {
        "lgpd_article": "Art. 6, I",
        "lgpd_principle": "Finalidade",
        "gdpr_equivalent": "Art. 5(1)(b)",
        "description": "Personal data processed only for complaint management purposes.",
        "control_implemented": "Data collection limited to complaint-related fields; no secondary processing.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, II",
        "lgpd_principle": "Adequação",
        "gdpr_equivalent": "Art. 5(1)(b)",
        "description": "Data collected is adequate and relevant to complaint investigation.",
        "control_implemented": "Input form collects only necessary fields (title, description, council, category).",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, III",
        "lgpd_principle": "Necessidade",
        "gdpr_equivalent": "Art. 5(1)(c)",
        "description": "Collection limited to minimum necessary for regulatory purpose.",
        "control_implemented": "Anonymous submission supported; no mandatory PII beyond complaint text.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, VI",
        "lgpd_principle": "Transparência",
        "gdpr_equivalent": "Art. 5(1)(a), Art. 12-14",
        "description": "Clear information about data processing purposes.",
        "control_implemented": "Privacy notice in web UI; threat model publicly accessible via API.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, VII",
        "lgpd_principle": "Segurança",
        "gdpr_equivalent": "Art. 5(1)(f), Art. 32",
        "description": "Technical and organizational measures to protect personal data.",
        "control_implemented": "SHA-256 hash chaining, TLS in production, OWASP security headers, rate limiting, input sanitization.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, VIII",
        "lgpd_principle": "Prevenção",
        "gdpr_equivalent": "Art. 25, Art. 32",
        "description": "Preventive measures against data damage.",
        "control_implemented": "Blockchain tamper-evidence; append-only audit log; external hash anchoring.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 6, X",
        "lgpd_principle": "Responsabilização e prestação de contas",
        "gdpr_equivalent": "Art. 5(2)",
        "description": "Demonstrate compliance with data protection measures.",
        "control_implemented": "STRIDE threat model; DPIA report; open-source code; replication package.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 7, III",
        "lgpd_principle": "Base legal – administração pública",
        "gdpr_equivalent": "Art. 6(1)(e)",
        "description": "Processing necessary for public administration duties.",
        "control_implemented": "Professional councils are autarchic public bodies (Lei 9.696/1998); complaint processing is a legal duty.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 46",
        "lgpd_principle": "Medidas de segurança",
        "gdpr_equivalent": "Art. 32",
        "description": "Security measures to protect personal data from unauthorized access.",
        "control_implemented": "TLS transport encryption; content-security-policy headers; non-root service account deployment; HMAC-chained audit log.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 37",
        "lgpd_principle": "Registro de operações",
        "gdpr_equivalent": "Art. 30",
        "description": "Records of processing activities.",
        "control_implemented": "All evidence transactions recorded in blockchain with timestamps; audit log tracks all operations.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 38",
        "lgpd_principle": "Relatório de impacto (DPIA)",
        "gdpr_equivalent": "Art. 35",
        "description": "Data Protection Impact Assessment for high-risk processing.",
        "control_implemented": "This DPIA report; threat model with 9 catalogued threats.",
        "status": "compliant",
    },
    {
        "lgpd_article": "Art. 18, VI",
        "lgpd_principle": "Direito à eliminação",
        "gdpr_equivalent": "Art. 17",
        "description": "Right to erasure of personal data.",
        "control_implemented": "Blockchain by design is append-only; erasure of on-chain data conflicts with evidence integrity. Documented as non-guarantee. Off-chain PII can be redacted.",
        "status": "partial",
        "residual_risk": "Complaint text containing PII is stored on-chain and cannot be deleted without chain rewrite. Mitigation: anonymization of complaints encouraged in UI.",
    },
    {
        "lgpd_article": "Art. 48",
        "lgpd_principle": "Comunicação de incidente",
        "gdpr_equivalent": "Art. 33-34",
        "description": "Notification of data breaches to authority and data subjects.",
        "control_implemented": "Security event logging in audit log; chain validation detects tampering. Incident notification procedure to be defined by deploying council.",
        "status": "partial",
        "residual_risk": "Automated breach notification to ANPD not implemented. Institutional procedure required.",
    },
]


class LGPDComplianceReport:
    """Generates LGPD compliance mapping and DPIA reports."""

    def __init__(self) -> None:
        self.controls = LGPD_CONTROLS
        self._dpia: dict | None = None

    def generate_dpia(self) -> dict:
        """Generate a full DPIA report."""
        compliant = sum(1 for c in self.controls if c["status"] == "compliant")
        partial = sum(1 for c in self.controls if c["status"] == "partial")
        non_compliant = sum(1 for c in self.controls if c["status"] == "non_compliant")

        self._dpia = {
            "report_title": "EviChain – Data Protection Impact Assessment (DPIA)",
            "legal_basis": "LGPD (Lei 13.709/2018) / GDPR cross-reference",
            "system": "EviChain v2.0.0",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_controls": len(self.controls),
                "compliant": compliant,
                "partial": partial,
                "non_compliant": non_compliant,
                "compliance_rate_pct": round(
                    100 * compliant / len(self.controls), 1
                ),
            },
            "controls": self.controls,
            "residual_risks": [
                c for c in self.controls
                if c.get("residual_risk")
            ],
            "recommendations": [
                "Implement off-chain PII redaction mechanism for Art. 18 compliance.",
                "Define incident notification procedure per Art. 48 with deploying council.",
                "Conduct periodic DPIA review (annually or upon significant system change).",
            ],
        }
        return self._dpia

    def export_json(self, path: str = "data/lgpd_dpia.json") -> str:
        """Export DPIA as JSON file."""
        if not self._dpia:
            self.generate_dpia()
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            json.dumps(self._dpia, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return str(p)

    def export_html(self, path: str = "data/lgpd_dpia.html") -> str:
        """Export DPIA as a self-contained HTML report."""
        if not self._dpia:
            self.generate_dpia()

        rows = ""
        for c in self.controls:
            status_class = {
                "compliant": "color:green",
                "partial": "color:orange",
                "non_compliant": "color:red",
            }.get(c["status"], "")
            rows += (
                f"<tr>"
                f"<td>{c['lgpd_article']}</td>"
                f"<td>{c['lgpd_principle']}</td>"
                f"<td>{c['gdpr_equivalent']}</td>"
                f"<td>{c['control_implemented']}</td>"
                f"<td style='{status_class};font-weight:bold'>{c['status'].upper()}</td>"
                f"</tr>\n"
            )

        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>EviChain DPIA Report</title>
<style>
body{{font-family:sans-serif;margin:2em}}
table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #ccc;padding:6px 10px;text-align:left;font-size:0.9em}}
th{{background:#f4f4f4}}
</style></head>
<body>
<h1>EviChain – Data Protection Impact Assessment</h1>
<p>Generated: {self._dpia['generated_utc']}</p>
<h2>Summary</h2>
<ul>
<li>Total controls: {self._dpia['summary']['total_controls']}</li>
<li>Compliant: {self._dpia['summary']['compliant']}</li>
<li>Partial: {self._dpia['summary']['partial']}</li>
<li>Compliance rate: {self._dpia['summary']['compliance_rate_pct']}%</li>
</ul>
<h2>LGPD–GDPR Compliance Matrix</h2>
<table>
<tr><th>LGPD Article</th><th>Principle</th><th>GDPR Equiv.</th><th>Control</th><th>Status</th></tr>
{rows}
</table>
</body></html>"""

        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        return str(p)
