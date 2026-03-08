"""
EviChain – Append-Only Audit Log

Provides tamper-evident, append-only logging for all security-relevant
operations.  Each log entry is HMAC-signed with a chained digest so
that deletion or reordering of entries is detectable.

Deployment hardening (documented, not enforced by Python):

    # Linux: make the log directory immutable after initial creation
    sudo chattr +a /var/log/evichain/audit.jsonl

    # Run the application under a non-root service account
    sudo useradd --system --no-create-home evichain
    sudo chown evichain:evichain /var/log/evichain/
    sudo chmod 750 /var/log/evichain/

Role-separation guidance:

    * The ``evichain`` service account should NOT have root or sudo
      privileges.
    * The blockchain data file should be owned by ``evichain`` with
      mode 0640.
    * The audit log directory should have the Linux append-only
      attribute (``chattr +a``) so that even the service account
      cannot delete or overwrite past entries.
    * A separate ``evichain-admin`` account (or root) is required to
      rotate logs or change the append-only attribute.

This module addresses reviewer concern #2 (malicious administrator)
by creating an independent, append-only evidence trail that is
harder to tamper with than the blockchain file itself.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


class AuditLog:
    """Append-only, HMAC-chained audit logger."""

    def __init__(
        self,
        log_dir: str | Path | None = None,
        hmac_key: bytes | None = None,
    ) -> None:
        self.log_dir = Path(
            log_dir or os.getenv("EVICHAIN_AUDIT_DIR", "data/audit")
        )
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.log_dir / "audit.jsonl"

        # HMAC key: from env (hex-encoded) or generate & persist
        raw_key = os.getenv("EVICHAIN_AUDIT_HMAC_KEY")
        if hmac_key:
            self._hmac_key = hmac_key
        elif raw_key:
            self._hmac_key = bytes.fromhex(raw_key)
        else:
            key_path = self.log_dir / ".audit_key"
            if key_path.exists():
                self._hmac_key = bytes.fromhex(
                    key_path.read_text(encoding="utf-8").strip()
                )
            else:
                self._hmac_key = os.urandom(32)
                key_path.write_text(self._hmac_key.hex(), encoding="utf-8")

        # Chain digest: hash of previous entry's HMAC (or zeros for first)
        self._prev_digest = self._recover_last_digest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def log_event(
        self,
        event_type: str,
        *,
        actor: str = "system",
        detail: Optional[dict] = None,
        severity: str = "INFO",
    ) -> dict:
        """Append a single audit event.  Returns the entry dict."""
        entry = {
            "seq": self._next_seq(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "actor": actor,
            "severity": severity,
            "detail": detail or {},
            "prev_digest": self._prev_digest,
        }

        # Compute HMAC over canonical JSON
        canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
        entry_hmac = hmac.new(
            self._hmac_key, canonical.encode(), hashlib.sha256
        ).hexdigest()
        entry["hmac"] = entry_hmac

        # Append
        with open(self.log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

        self._prev_digest = entry_hmac
        return entry

    def verify_integrity(self) -> dict:
        """Verify the full audit log chain.

        Returns ``{"valid": True/False, "entries": N, "errors": [...]}``.
        """
        if not self.log_file.exists():
            return {"valid": True, "entries": 0, "errors": []}

        errors: list[str] = []
        prev_digest = "0" * 64
        count = 0

        with open(self.log_file, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    errors.append(f"Line {lineno}: invalid JSON")
                    continue

                stored_hmac = entry.pop("hmac", "")

                # Check chain link
                if entry.get("prev_digest") != prev_digest:
                    errors.append(
                        f"Line {lineno}: chain break "
                        f"(expected prev_digest={prev_digest[:16]}…)"
                    )

                # Re-compute HMAC
                canonical = json.dumps(entry, sort_keys=True, ensure_ascii=False)
                expected = hmac.new(
                    self._hmac_key, canonical.encode(), hashlib.sha256
                ).hexdigest()

                if not hmac.compare_digest(stored_hmac, expected):
                    errors.append(f"Line {lineno}: HMAC mismatch")

                prev_digest = stored_hmac
                count += 1

        return {"valid": len(errors) == 0, "entries": count, "errors": errors}

    # ------------------------------------------------------------------
    # Convenience event loggers
    # ------------------------------------------------------------------

    def log_complaint_submitted(self, complaint_id: str, actor: str = "user") -> dict:
        return self.log_event(
            "COMPLAINT_SUBMITTED", actor=actor,
            detail={"complaint_id": complaint_id},
        )

    def log_block_mined(self, block_index: int, block_hash: str) -> dict:
        return self.log_event(
            "BLOCK_MINED",
            detail={"block_index": block_index, "block_hash": block_hash},
        )

    def log_chain_validated(self, is_valid: bool, block_count: int) -> dict:
        return self.log_event(
            "CHAIN_VALIDATED",
            detail={"is_valid": is_valid, "block_count": block_count},
            severity="INFO" if is_valid else "WARNING",
        )

    def log_anchor_created(self, anchor_type: str, root_hash: str) -> dict:
        return self.log_event(
            "ANCHOR_CREATED",
            detail={"anchor_type": anchor_type, "root_hash": root_hash},
        )

    def log_security_event(self, description: str, severity: str = "WARNING") -> dict:
        return self.log_event(
            "SECURITY_EVENT",
            detail={"description": description},
            severity=severity,
        )

    def log_api_key_rotation(self, key_id: str) -> dict:
        return self.log_event(
            "API_KEY_ROTATED",
            detail={"key_id": key_id},
            severity="INFO",
        )

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _next_seq(self) -> int:
        """Return the next sequence number (1-based)."""
        if not self.log_file.exists():
            return 1
        count = sum(1 for _ in open(self.log_file, "r", encoding="utf-8") if _.strip())
        return count + 1

    def _recover_last_digest(self) -> str:
        """Read the HMAC of the last entry to continue the chain."""
        if not self.log_file.exists():
            return "0" * 64
        last_line = ""
        with open(self.log_file, "r", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    last_line = line.strip()
        if not last_line:
            return "0" * 64
        try:
            return json.loads(last_line).get("hmac", "0" * 64)
        except json.JSONDecodeError:
            return "0" * 64
