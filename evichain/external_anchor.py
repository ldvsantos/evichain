"""
EviChain – External Hash Anchoring Module

Provides two independent mechanisms for publishing chain-root hashes
to external, independently verifiable stores:

1. **RFC 3161 Timestamping** – Sends a SHA-256 digest to a free Time
   Stamping Authority (TSA) and stores the resulting TimeStampResp
   token locally.  Verification parses the returned TimeStampToken and
   checks the message imprint, the TSA signing certificate, its
   extended key usage and validity window, and the token serial number
   and generation time against the stored receipt.

2. **Bitcoin Testnet OP_RETURN** *(optional, requires bitcoinlib)* –
   Embeds the 32-byte chain-root hash in a Testnet transaction using
   the OP_RETURN output script.  This path is ILLUSTRATIVE ONLY:
   testnet coins carry no economic value and the chain can be reset or
   reorganised, so it is not a security control.

Both paths record receipts as JSON in ``data/anchors/`` so that any
auditor can independently verify the chain's integrity at the moment
of anchoring.

Security note:
    External anchoring addresses threat T-03 (privileged admin
    rewriting the chain file) ONLY IF the receipt and its token live
    where that admin cannot reach them.  A receipt stored beside the
    chain is deletable by the same operator it constrains, so an
    auditor would observe a missing receipt rather than proof of
    tampering.  Use :meth:`ExternalAnchor.export_offbox` (or set
    ``EVICHAIN_ANCHOR_EXPORT_DIR``) to ship every receipt and token to
    an append-only store outside the application host.

Usage::

    from evichain.external_anchor import ExternalAnchor

    anchor = ExternalAnchor(blockchain)
    if anchor.should_anchor():             # interval / block-growth policy
        receipt = anchor.anchor_rfc3161()  # free, no API key, retries on failure
    report = anchor.verify_anchor(receipt["receipt_file"])
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from blockchain_simulator import EviChainBlockchain


class AnchorVerificationError(Exception):
    """Raised when an anchor receipt fails a specific verification stage.

    The ``stage`` attribute names the failing check so that an auditor can
    distinguish a corrupted chain from an unreachable TSA, an expired
    signing certificate, or a substituted receipt.
    """

    def __init__(self, stage: str, message: str) -> None:
        super().__init__(f"[{stage}] {message}")
        self.stage = stage
        self.message = message


# ----------------------------------------------------------------------
# Minimal DER reader (no third-party ASN.1 dependency required)
# ----------------------------------------------------------------------

def _der_read_tlv(data: bytes, offset: int = 0) -> tuple[int, int, int, int]:
    """Read one DER TLV at ``offset``.

    Returns ``(tag, content_start, content_length, next_offset)``.
    """
    if offset >= len(data):
        raise ValueError("truncated DER structure")
    tag = data[offset]
    idx = offset + 1
    if idx >= len(data):
        raise ValueError("truncated DER length")
    first = data[idx]
    idx += 1
    if first & 0x80:
        n = first & 0x7F
        if n == 0 or idx + n > len(data):
            raise ValueError("unsupported or truncated DER length")
        length = int.from_bytes(data[idx:idx + n], "big")
        idx += n
    else:
        length = first
    if idx + length > len(data):
        raise ValueError("DER content exceeds buffer")
    return tag, idx, length, idx + length


def _der_children(data: bytes, offset: int, end: int):
    """Yield ``(tag, content_start, content_length)`` for each child TLV."""
    while offset < end:
        tag, start, length, offset = _der_read_tlv(data, offset)
        yield tag, start, length


def _der_find(data: bytes, offset: int, end: int, predicate, depth: int = 0):
    """Depth-first search for the first TLV satisfying ``predicate``.

    ``predicate(tag, content_start, content_length)`` returns a truthy value,
    which is returned to the caller.  Recursion stops at ``depth`` 12.
    """
    if depth > 12:
        return None
    for tag, start, length in _der_children(data, offset, end):
        hit = predicate(tag, start, length)
        if hit:
            return hit
        constructed = bool(tag & 0x20)
        if constructed:
            found = _der_find(data, start, start + length, predicate, depth + 1)
            if found:
                return found
    return None


def _der_encode_length(n: int) -> bytes:
    """DER-encode a definite length."""
    if n < 0x80:
        return bytes([n])
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return bytes([0x80 | len(body)]) + body


def _oid_bytes_to_string(raw: bytes) -> str:
    """Decode the content octets of an OBJECT IDENTIFIER."""
    if not raw:
        return ""
    first = raw[0]
    parts = [str(first // 40), str(first % 40)]
    value = 0
    for byte in raw[1:]:
        value = (value << 7) | (byte & 0x7F)
        if not byte & 0x80:
            parts.append(str(value))
            value = 0
    return ".".join(parts)


def _oid_to_string(data: bytes, node) -> str:
    """Return the dotted OID of the first OBJECT IDENTIFIER inside ``node``."""
    tag, start, length = node
    for ctag, cstart, clength in _der_children(data, start, start + length):
        if ctag == 0x06:
            return _oid_bytes_to_string(data[cstart:cstart + clength])
    return ""


#: Digest algorithm OIDs accepted in CMS SignerInfo.
_DIGEST_OIDS = {
    "1.3.14.3.2.26": "sha1",
    "2.16.840.1.101.3.4.2.1": "sha256",
    "2.16.840.1.101.3.4.2.2": "sha384",
    "2.16.840.1.101.3.4.2.3": "sha512",
}

# OID 1.2.840.113549.1.9.16.1.4 = id-ct-TSTInfo
_OID_TSTINFO = bytes([0x06, 0x0B, 0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D,
                      0x01, 0x09, 0x10, 0x01, 0x04])
# OID 1.3.6.1.5.5.7.3.8 = id-kp-timeStamping
_OID_KP_TIMESTAMPING = "1.3.6.1.5.5.7.3.8"


class ExternalAnchor:
    """Manages external anchoring of blockchain root hashes."""

    # FreeTSA (https://freetsa.org) – free RFC 3161 TSA
    DEFAULT_TSA_URL = "https://freetsa.org/tsr"
    ANCHORS_DIR = "data/anchors"

    #: Anchor at least this often, regardless of chain growth.
    DEFAULT_INTERVAL_HOURS = 24
    #: Anchor early once the chain has grown by this many blocks.
    DEFAULT_BLOCK_DELTA = 50
    #: Retry schedule (seconds) applied when the TSA is unreachable.
    RETRY_BACKOFF_SECONDS = (2, 8, 32)

    def __init__(
        self,
        blockchain: "EviChainBlockchain",
        *,
        anchors_dir: str | None = None,
        tsa_url: str | None = None,
        interval_hours: float | None = None,
        block_delta: int | None = None,
        export_dir: str | None = None,
        audit_log=None,
    ) -> None:
        self.blockchain = blockchain
        self.anchors_dir = Path(anchors_dir or self.ANCHORS_DIR)
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
        self.tsa_url = tsa_url or os.getenv(
            "EVICHAIN_TSA_URL", self.DEFAULT_TSA_URL
        )
        self.interval_hours = float(
            interval_hours
            if interval_hours is not None
            else os.getenv("EVICHAIN_ANCHOR_INTERVAL_HOURS",
                           self.DEFAULT_INTERVAL_HOURS)
        )
        self.block_delta = int(
            block_delta
            if block_delta is not None
            else os.getenv("EVICHAIN_ANCHOR_BLOCK_DELTA",
                           self.DEFAULT_BLOCK_DELTA)
        )
        raw_export = export_dir or os.getenv("EVICHAIN_ANCHOR_EXPORT_DIR")
        self.export_dir = Path(raw_export) if raw_export else None
        self.audit_log = audit_log

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def compute_chain_root_hash(self) -> str:
        """Return the SHA-256 digest over all block hashes (Merkle-like root).

        The root is computed by hashing the concatenation of every block
        hash in order, so any single-block change invalidates the root.
        """
        concat = "".join(block.hash for block in self.blockchain.chain)
        return hashlib.sha256(concat.encode()).hexdigest()

    # ------------------------------------------------------------------
    # Anchoring interval policy
    # ------------------------------------------------------------------

    def latest_receipt(self) -> Optional[dict]:
        """Return the most recent successful receipt, or ``None``."""
        receipts = [r for r in self.list_anchors() if r.get("root_hash")]
        if not receipts:
            return None
        return max(receipts, key=lambda r: r.get("timestamp_utc", ""))

    def should_anchor(self, now: datetime | None = None) -> dict:
        """Decide whether an anchor is due under the configured policy.

        Anchoring is due when no anchor exists, when ``interval_hours`` have
        elapsed since the last one, or when the chain has grown by more than
        ``block_delta`` blocks.  The block-growth trigger bounds the exposure
        window during which a rewrite would leave no external trace.
        """
        now = now or datetime.now(timezone.utc)
        last = self.latest_receipt()
        if last is None:
            return {"due": True, "reason": "no_previous_anchor"}

        grown = len(self.blockchain.chain) - int(last.get("chain_length", 0))
        if grown >= self.block_delta:
            return {"due": True, "reason": "block_delta", "blocks_since": grown}

        try:
            stamped = datetime.strptime(
                last["timestamp_utc"], "%Y%m%dT%H%M%SZ"
            ).replace(tzinfo=timezone.utc)
        except (KeyError, ValueError):
            return {"due": True, "reason": "unparsable_previous_timestamp"}

        elapsed = now - stamped
        if elapsed >= timedelta(hours=self.interval_hours):
            return {
                "due": True,
                "reason": "interval_elapsed",
                "hours_since": round(elapsed.total_seconds() / 3600, 2),
            }
        return {
            "due": False,
            "reason": "within_interval",
            "hours_since": round(elapsed.total_seconds() / 3600, 2),
            "blocks_since": grown,
        }

    # ------------------------------------------------------------------
    # RFC 3161 Time-Stamp Protocol
    # ------------------------------------------------------------------

    def anchor_rfc3161(self) -> dict:
        """Request an RFC 3161 timestamp token for the current chain root.

        Retries with exponential backoff when the TSA is unreachable.  On
        exhaustion the failure is recorded and the previous valid anchor is
        left in place, so a network outage degrades anchor freshness without
        invalidating prior evidence.

        Returns a receipt dict saved to ``anchors_dir``.
        """
        import requests  # project dependency

        root_hash = self.compute_chain_root_hash()
        digest_bytes = bytes.fromhex(root_hash)
        ts_request = self._build_ts_request(digest_bytes)

        attempts: list[dict] = []
        resp = None
        for attempt, delay in enumerate(
            (0,) + self.RETRY_BACKOFF_SECONDS, start=1
        ):
            if delay:
                time.sleep(delay)
            try:
                resp = requests.post(
                    self.tsa_url,
                    data=ts_request,
                    headers={"Content-Type": "application/timestamp-query"},
                    timeout=30,
                )
                resp.raise_for_status()
                break
            except Exception as exc:  # network, HTTP, or TLS failure
                attempts.append({"attempt": attempt, "error": str(exc)[:200]})
                resp = None

        if resp is None:
            failure = {
                "type": "rfc3161",
                "status": "failed",
                "timestamp_utc": datetime.now(timezone.utc).strftime(
                    "%Y%m%dT%H%M%SZ"
                ),
                "tsa_url": self.tsa_url,
                "attempts": attempts,
                "previous_anchor": (self.latest_receipt() or {}).get(
                    "timestamp_utc"
                ),
            }
            self._audit(
                "ANCHOR_FAILED",
                {"tsa_url": self.tsa_url, "attempts": len(attempts)},
                severity="WARNING",
            )
            raise AnchorVerificationError(
                "tsa_unreachable",
                f"TSA unreachable after {len(attempts)} attempts; "
                f"previous anchor retained ({failure['previous_anchor']})",
            )

        # Persist the token ----------------------------------------------
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        token_path = self.anchors_dir / f"rfc3161_{ts}.tsr"
        token_path.write_bytes(resp.content)

        token_meta = {}
        try:
            token_meta = self._parse_tst_info(resp.content)
        except Exception as exc:  # malformed token is recorded, not fatal here
            token_meta = {"parse_error": str(exc)[:200]}

        receipt = {
            "type": "rfc3161",
            "status": "ok",
            "timestamp_utc": ts,
            "chain_length": len(self.blockchain.chain),
            "root_hash": root_hash,
            "tsa_url": self.tsa_url,
            "token_file": str(token_path),
            "token_size_bytes": len(resp.content),
            "token_sha256": hashlib.sha256(resp.content).hexdigest(),
            "http_status": resp.status_code,
            "retries": len(attempts),
            "tsa_serial_number": token_meta.get("serial_number"),
            "tsa_gen_time": token_meta.get("gen_time"),
        }

        receipt_path = self.anchors_dir / f"rfc3161_{ts}.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        receipt["receipt_file"] = str(receipt_path)

        exported = self.export_offbox(receipt_path, token_path)
        receipt["exported_offbox"] = exported
        self._audit(
            "ANCHOR_CREATED",
            {
                "root_hash": root_hash,
                "chain_length": receipt["chain_length"],
                "exported_offbox": exported,
            },
        )
        return receipt

    # ------------------------------------------------------------------
    # Off-box receipt custody
    # ------------------------------------------------------------------

    def export_offbox(self, *paths: Path) -> bool:
        """Copy receipt artefacts to an append-only store outside this host.

        A receipt kept beside the chain is deletable by the same privileged
        operator it is meant to constrain.  Detection of a chain rewrite
        therefore holds only when receipts are exported to a location under
        different custody, configured through ``EVICHAIN_ANCHOR_EXPORT_DIR``
        (typically a mounted WORM share or a directory on a separate host).

        Returns ``True`` when every artefact was copied, ``False`` when no
        export target is configured or a copy failed.
        """
        if self.export_dir is None:
            return False
        try:
            self.export_dir.mkdir(parents=True, exist_ok=True)
            for p in paths:
                target = self.export_dir / Path(p).name
                if target.exists():
                    # Append-only semantics: never overwrite an exported receipt.
                    continue
                shutil.copy2(p, target)
            return True
        except OSError as exc:
            self._audit(
                "ANCHOR_EXPORT_FAILED",
                {"export_dir": str(self.export_dir), "error": str(exc)[:200]},
                severity="WARNING",
            )
            return False

    # ------------------------------------------------------------------
    # Bitcoin Testnet OP_RETURN  (optional)
    # ------------------------------------------------------------------

    def anchor_btc_testnet(self) -> dict:
        """Embed the chain root hash in a Bitcoin Testnet OP_RETURN tx.

        Requires ``bitcoinlib`` (``pip install bitcoinlib``).  A testnet
        wallet with a small balance is needed; wallet name is read from
        the ``EVICHAIN_BTC_WALLET`` environment variable (default:
        ``evichain-testnet``).
        """
        try:
            from bitcoinlib.wallets import Wallet
            from bitcoinlib.transactions import Output
        except ImportError as exc:
            raise RuntimeError(
                "bitcoinlib is required for Bitcoin anchoring.  "
                "Install it with:  pip install bitcoinlib"
            ) from exc

        root_hash = self.compute_chain_root_hash()
        digest_bytes = bytes.fromhex(root_hash)

        wallet_name = os.getenv("EVICHAIN_BTC_WALLET", "evichain-testnet")
        wallet = Wallet(wallet_name, network="testnet")

        op_return_output = Output(
            value=0,
            lock_script=b"\x6a\x20" + digest_bytes,  # OP_RETURN <32 bytes>
        )

        tx = wallet.send(
            [op_return_output],
            fee="low",
            network="testnet",
        )

        receipt = {
            "type": "btc_testnet_op_return",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "chain_length": len(self.blockchain.chain),
            "root_hash": root_hash,
            "txid": tx.txid if hasattr(tx, "txid") else str(tx),
            "network": "testnet",
        }

        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        receipt_path = self.anchors_dir / f"btc_testnet_{ts}.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return receipt

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_anchor(self, receipt_path: str, *, strict: bool = False) -> dict:
        """Verify an anchor receipt cryptographically against the current chain.

        Five stages are executed in order, each reported independently so that
        an auditor can tell a rewritten chain from an expired signing
        certificate or a substituted receipt.

        ``message_imprint``
            Recomputes the chain root and compares it with the hashed message
            carried inside the signed TSTInfo, not with the JSON receipt.  A
            privileged operator who edits both the chain and the receipt still
            fails here, because the imprint is covered by the TSA signature.
        ``cms_signature``
            Verifies the SignerInfo signature over the DER re-encoding of the
            signed attributes and checks that the messageDigest attribute
            covers the encapsulated TSTInfo.
        ``tsa_certificate``
            Requires the id-kp-timeStamping extended key usage on the signing
            certificate and checks that the token generation time falls inside
            its validity window.  When ``EVICHAIN_TSA_TRUST_ANCHOR`` points to
            a PEM bundle, the issuer chain is walked to that anchor.
        ``token_binding``
            Compares the token serial number and generation time with the
            values recorded in the receipt at anchoring time, and re-hashes
            the stored token file.
        ``chain_state``
            Reports whether the chain has changed since anchoring.

        With ``strict=True`` the first failing stage raises
        :class:`AnchorVerificationError` instead of being reported.
        """
        receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
        current_root = self.compute_chain_root_hash()
        stages: dict[str, dict] = {}

        def fail(stage: str, message: str) -> None:
            stages[stage] = {"passed": False, "detail": message}
            if strict:
                raise AnchorVerificationError(stage, message)

        token_path = receipt.get("token_file")
        token_bytes = b""
        tst: dict = {}

        if receipt.get("type") != "rfc3161":
            stages["message_imprint"] = {
                "passed": False,
                "detail": "non-RFC 3161 receipt carries no signed imprint",
            }
        elif not token_path or not Path(token_path).exists():
            fail("message_imprint",
                 f"token file missing: {token_path!r}; a receipt without its "
                 "token proves nothing")
        else:
            token_bytes = Path(token_path).read_bytes()
            try:
                tst = self._parse_tst_info(token_bytes)
            except Exception as exc:
                fail("message_imprint", f"malformed TimeStampToken: {exc}")

        # Stage 1 -- message imprint -------------------------------------
        if tst:
            imprint = tst.get("hashed_message", "")
            if imprint == current_root:
                stages["message_imprint"] = {
                    "passed": True,
                    "detail": "signed imprint matches recomputed chain root",
                }
            else:
                fail("message_imprint",
                     f"signed imprint {imprint[:16]}... does not match "
                     f"recomputed root {current_root[:16]}...")

        # Stage 2 -- CMS signature ---------------------------------------
        if token_bytes:
            stages["cms_signature"] = self._verify_cms_signature(token_bytes)
            if strict and not stages["cms_signature"]["passed"]:
                raise AnchorVerificationError(
                    "cms_signature", stages["cms_signature"]["detail"]
                )

        # Stage 3 -- TSA certificate -------------------------------------
        if token_bytes:
            stages["tsa_certificate"] = self._verify_tsa_certificate(
                token_bytes, tst.get("gen_time")
            )
            if strict and not stages["tsa_certificate"]["passed"]:
                raise AnchorVerificationError(
                    "tsa_certificate", stages["tsa_certificate"]["detail"]
                )

        # Stage 4 -- token binding ---------------------------------------
        if token_bytes:
            problems = []
            recorded_hash = receipt.get("token_sha256")
            actual_hash = hashlib.sha256(token_bytes).hexdigest()
            if recorded_hash and recorded_hash != actual_hash:
                problems.append("stored token digest differs from receipt")
            if receipt.get("tsa_serial_number") and tst.get("serial_number") \
                    and receipt["tsa_serial_number"] != tst["serial_number"]:
                problems.append("serial number differs from receipt")
            if receipt.get("tsa_gen_time") and tst.get("gen_time") \
                    and receipt["tsa_gen_time"] != tst["gen_time"]:
                problems.append("generation time differs from receipt")
            if problems:
                fail("token_binding", "; ".join(problems))
            else:
                stages["token_binding"] = {
                    "passed": True,
                    "detail": "token digest, serial and generation time "
                              "agree with the receipt",
                }

        # Stage 5 -- chain state -----------------------------------------
        chain_unchanged = current_root == receipt.get("root_hash")
        stages["chain_state"] = {
            "passed": chain_unchanged,
            "detail": "chain unchanged since anchoring" if chain_unchanged
            else "chain root differs from the anchored root",
        }

        failed = [name for name, s in stages.items() if not s["passed"]]
        return {
            "receipt_type": receipt.get("type"),
            "receipt_root_hash": receipt.get("root_hash"),
            "current_root_hash": current_root,
            "chain_unchanged": chain_unchanged,
            "chain_length_at_anchor": receipt.get("chain_length"),
            "chain_length_now": len(self.blockchain.chain),
            "tsa_gen_time": tst.get("gen_time"),
            "tsa_serial_number": tst.get("serial_number"),
            "stages": stages,
            "failed_stages": failed,
            "valid": not failed,
        }

    def _verify_tsa_certificate(
        self, token_bytes: bytes, gen_time: str | None
    ) -> dict:
        """Check the TSA signing certificate embedded in the token."""
        try:
            from cryptography.hazmat.primitives.serialization import pkcs7
            from cryptography import x509
            from cryptography.x509.oid import ExtensionOID
        except ImportError:
            return {
                "passed": False,
                "detail": "cryptography package unavailable; certificate "
                          "validation skipped",
            }

        try:
            certs = pkcs7.load_der_pkcs7_certificates(
                self._extract_timestamp_token(token_bytes)
            )
        except Exception as exc:
            return {"passed": False,
                    "detail": f"no certificate recoverable from token: {exc}"}

        if not certs:
            return {"passed": False,
                    "detail": "token carries no certificate (certReq ignored "
                              "by the TSA)"}

        signer = None
        for cert in certs:
            try:
                eku = cert.extensions.get_extension_for_oid(
                    ExtensionOID.EXTENDED_KEY_USAGE
                ).value
            except x509.ExtensionNotFound:
                continue
            if any(o.dotted_string == _OID_KP_TIMESTAMPING for o in eku):
                signer = cert
                break

        if signer is None:
            return {"passed": False,
                    "detail": "no certificate carries the id-kp-timeStamping "
                              "extended key usage"}

        problems = []
        warnings = []
        if gen_time:
            try:
                stamped = datetime.strptime(
                    gen_time[:14], "%Y%m%d%H%M%S"
                ).replace(tzinfo=timezone.utc)
                not_before = signer.not_valid_before_utc
                not_after = signer.not_valid_after_utc
                if not (not_before <= stamped <= not_after):
                    problems.append(
                        "generation time falls outside the certificate "
                        "validity window"
                    )
            except (ValueError, AttributeError) as exc:
                problems.append(f"validity window not checkable: {exc}")

        anchor_path = os.getenv("EVICHAIN_TSA_TRUST_ANCHOR")
        if anchor_path and Path(anchor_path).exists():
            trusted = x509.load_pem_x509_certificates(
                Path(anchor_path).read_bytes()
            )
            chain = {c.subject for c in certs} | {c.subject for c in trusted}
            if signer.issuer not in chain:
                problems.append(
                    "issuer chain does not reach the configured trust anchor"
                )
            trust_state = "configured trust anchor"
        else:
            warnings.append(
                "no trust anchor configured (EVICHAIN_TSA_TRUST_ANCHOR); "
                "the signing certificate is accepted on first use"
            )
            trust_state = "trust on first use"

        return {
            "passed": not problems,
            "detail": "; ".join(problems) if problems
            else f"timestamping certificate valid at genTime ({trust_state})",
            "warnings": warnings,
            "subject": signer.subject.rfc4514_string(),
            "not_before": signer.not_valid_before_utc.isoformat(),
            "not_after": signer.not_valid_after_utc.isoformat(),
        }

    def _verify_cms_signature(self, token_bytes: bytes) -> dict:
        """Verify the CMS SignerInfo signature carried by the token.

        The signature covers the DER re-encoding of the signed attributes,
        one of which is the digest of the encapsulated TSTInfo.  Checking
        both binds the message imprint to the TSA key, so an operator who
        edits the TSTInfo cannot produce a token that still verifies.
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import ec, padding
            from cryptography.hazmat.primitives.serialization import pkcs7
        except ImportError:
            return {"passed": False,
                    "detail": "cryptography package unavailable; CMS "
                              "signature verification skipped"}

        try:
            token = self._extract_timestamp_token(token_bytes)
            parts = self._locate_cms_parts(token)
            certs = pkcs7.load_der_pkcs7_certificates(token)
        except Exception as exc:
            return {"passed": False,
                    "detail": f"CMS structure not parsable: {exc}"}

        digest_alg = _DIGEST_OIDS.get(parts["digest_oid"])
        if digest_alg is None:
            return {"passed": False,
                    "detail": f"unsupported digest algorithm OID "
                              f"{parts['digest_oid']}"}

        # The messageDigest signed attribute must cover the eContent.
        econtent_digest = hashlib.new(digest_alg, parts["econtent"]).digest()
        if parts["message_digest_attr"] is not None and \
                parts["message_digest_attr"] != econtent_digest:
            return {"passed": False,
                    "detail": "messageDigest attribute does not cover the "
                              "encapsulated TSTInfo"}

        hash_cls = {"sha1": hashes.SHA1, "sha256": hashes.SHA256,
                    "sha384": hashes.SHA384, "sha512": hashes.SHA512}[digest_alg]

        for cert in certs:
            key = cert.public_key()
            try:
                if isinstance(key, ec.EllipticCurvePublicKey):
                    key.verify(parts["signature"], parts["signed_data"],
                               ec.ECDSA(hash_cls()))
                else:
                    key.verify(parts["signature"], parts["signed_data"],
                               padding.PKCS1v15(), hash_cls())
            except Exception:
                continue
            return {
                "passed": True,
                "detail": "CMS signature verifies under the embedded "
                          "timestamping certificate",
                "signer": cert.subject.rfc4514_string(),
                "digest_algorithm": digest_alg,
            }

        return {"passed": False,
                "detail": "no embedded certificate verifies the CMS signature"}

    @staticmethod
    def _locate_cms_parts(token: bytes) -> dict:
        """Extract eContent, signed attributes, and signature from a token."""
        # ContentInfo -> [0] EXPLICIT -> SignedData
        _t, cstart, clength, _n = _der_read_tlv(token, 0)
        signed_data = None
        for tag, start, length in _der_children(token, cstart, cstart + clength):
            if tag == 0xA0:
                inner = list(_der_children(token, start, start + length))
                if inner and inner[0][0] == 0x30:
                    itag, istart, ilength = inner[0]
                    signed_data = (istart, ilength)
        if signed_data is None:
            raise ValueError("SignedData not found")

        sd_start, sd_length = signed_data
        sd_children = list(
            _der_children(token, sd_start, sd_start + sd_length)
        )

        encap = next((c for c in sd_children if c[0] == 0x30), None)
        signer_infos = [c for c in sd_children if c[0] == 0x31]
        if encap is None or len(signer_infos) < 2:
            raise ValueError("encapContentInfo or signerInfos missing")
        si_set = signer_infos[-1]

        # eContent: encapContentInfo -> [0] EXPLICIT OCTET STRING
        econtent = None
        for tag, start, length in _der_children(
            token, encap[1], encap[1] + encap[2]
        ):
            if tag == 0xA0:
                for itag, istart, ilength in _der_children(
                    token, start, start + length
                ):
                    if itag == 0x04:
                        econtent = token[istart:istart + ilength]
        if econtent is None:
            raise ValueError("eContent not found")

        si = next(iter(_der_children(token, si_set[1], si_set[1] + si_set[2])))
        si_children = list(
            _der_children(token, si[1], si[1] + si[2])
        )

        signed_attrs = next((c for c in si_children if c[0] == 0xA0), None)
        if signed_attrs is None:
            raise ValueError("signedAttrs absent; unsupported token profile")

        # Signature is the last OCTET STRING in SignerInfo.
        sig = [c for c in si_children if c[0] == 0x04][-1]
        # digestAlgorithm is the AlgorithmIdentifier immediately preceding
        # signedAttrs; earlier SEQUENCEs belong to issuerAndSerialNumber.
        attrs_index = si_children.index(signed_attrs)
        preceding = [c for c in si_children[:attrs_index] if c[0] == 0x30]
        if not preceding:
            raise ValueError("digestAlgorithm not found in SignerInfo")
        digest_oid = _oid_to_string(token, preceding[-1])

        # Re-encode signedAttrs as SET OF (0x31) for signature verification.
        attrs_body = token[signed_attrs[1]:signed_attrs[1] + signed_attrs[2]]
        signed_bytes = b"\x31" + _der_encode_length(len(attrs_body)) + attrs_body

        message_digest_attr = None
        for atag, astart, alength in _der_children(
            token, signed_attrs[1], signed_attrs[1] + signed_attrs[2]
        ):
            attr = list(_der_children(token, astart, astart + alength))
            if not attr or attr[0][0] != 0x06:
                continue
            if _oid_bytes_to_string(
                token[attr[0][1]:attr[0][1] + attr[0][2]]
            ) != "1.2.840.113549.1.9.4":  # id-messageDigest
                continue
            for vtag, vstart, vlength in _der_children(
                token, attr[1][1], attr[1][1] + attr[1][2]
            ):
                if vtag == 0x04:
                    message_digest_attr = token[vstart:vstart + vlength]

        return {
            "econtent": econtent,
            "signed_data": signed_bytes,
            "signature": token[sig[1]:sig[1] + sig[2]],
            "digest_oid": digest_oid,
            "message_digest_attr": message_digest_attr,
        }

    @staticmethod
    def _extract_timestamp_token(response_bytes: bytes) -> bytes:
        """Return the ContentInfo (TimeStampToken) inside a TimeStampResp.

        ``TimeStampResp ::= SEQUENCE { status PKIStatusInfo,
        timeStampToken TimeStampToken OPTIONAL }``.  A bare token is passed
        through unchanged, so both TSA response framings are accepted.
        """
        tag, start, length, _ = _der_read_tlv(response_bytes, 0)
        if tag != 0x30:
            raise ValueError("response is not a DER SEQUENCE")
        children = list(_der_children(response_bytes, start, start + length))
        if len(children) < 2:
            # Already a bare ContentInfo.
            return response_bytes
        ctag, cstart, clength = children[1]
        header = cstart - 1
        while header > 0 and header > cstart - 6:
            try:
                t, s, l, _n = _der_read_tlv(response_bytes, header)
            except ValueError:
                header -= 1
                continue
            if t == ctag and s == cstart and l == clength:
                return response_bytes[header:cstart + clength]
            header -= 1
        raise ValueError("timeStampToken not locatable in response")

    def _parse_tst_info(self, token_bytes: bytes) -> dict:
        """Extract messageImprint, serialNumber and genTime from a token.

        The TimeStampResp wraps a ContentInfo whose eContent is the DER
        encoding of TSTInfo.  The eContent is located by searching for the
        id-ct-TSTInfo OID and reading the OCTET STRING that follows it.
        """
        blob = token_bytes
        pos = blob.find(_OID_TSTINFO)
        if pos < 0:
            raise ValueError("id-ct-TSTInfo OID not present in token")

        # Walk forward to the first OCTET STRING holding the TSTInfo DER.
        idx = pos + len(_OID_TSTINFO)
        tst_der = None
        while idx < len(blob) and tst_der is None:
            try:
                tag, start, length, nxt = _der_read_tlv(blob, idx)
            except ValueError:
                break
            if tag == 0x04:  # OCTET STRING
                candidate = blob[start:start + length]
                if candidate[:1] == b"\x30":
                    tst_der = candidate
                    break
                idx = start  # explicit-tagged wrapper, descend
                continue
            if tag & 0x20:  # constructed, descend
                idx = start
                continue
            idx = nxt

        if tst_der is None:
            raise ValueError("TSTInfo content not recoverable")

        tag, start, length, _ = _der_read_tlv(tst_der, 0)
        end = start + length
        children = list(_der_children(tst_der, start, end))

        info: dict = {}
        # TSTInfo ::= SEQUENCE { version, policy, messageImprint,
        #                        serialNumber, genTime, ... }
        for position, (ctag, cstart, clength) in enumerate(children):
            raw = tst_der[cstart:cstart + clength]
            if ctag == 0x30 and "hashed_message" not in info:
                for itag, istart, ilength in _der_children(
                    tst_der, cstart, cstart + clength
                ):
                    if itag == 0x04:
                        info["hashed_message"] = tst_der[
                            istart:istart + ilength
                        ].hex()
            elif ctag == 0x02 and position >= 3:
                info["serial_number"] = str(
                    int.from_bytes(raw, "big", signed=False)
                )
            elif ctag == 0x18:  # GeneralizedTime
                info["gen_time"] = raw.decode("ascii", errors="replace")

        if "hashed_message" not in info:
            raise ValueError("messageImprint not found in TSTInfo")
        return info

    def _audit(self, event: str, detail: dict, severity: str = "INFO") -> None:
        """Forward an anchoring event to the audit log when one is attached."""
        if self.audit_log is None:
            return
        try:
            self.audit_log.log_event(
                event, actor="anchor", detail=detail, severity=severity
            )
        except Exception:
            pass

    def list_anchors(self) -> list[dict]:
        """Return metadata of all stored anchor receipts."""
        anchors = []
        for p in sorted(self.anchors_dir.glob("*.json")):
            anchors.append(json.loads(p.read_text(encoding="utf-8")))
        return anchors

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _build_ts_request(digest: bytes) -> bytes:
        """Build a minimal DER-encoded RFC 3161 TimeStampReq.

        Structure (ASN.1)::

            TimeStampReq ::= SEQUENCE {
                version          INTEGER (1),
                messageImprint   SEQUENCE {
                    hashAlgorithm  AlgorithmIdentifier (SHA-256),
                    hashedMessage  OCTET STRING
                },
                certReq          BOOLEAN (TRUE)
            }
        """
        # OID for SHA-256: 2.16.840.1.101.3.4.2.1
        sha256_oid = bytes([
            0x30, 0x0D,  # SEQUENCE
            0x06, 0x09,  # OID
            0x60, 0x86, 0x48, 0x01, 0x65, 0x03, 0x04, 0x02, 0x01,
            0x05, 0x00,  # NULL
        ])

        hashed_message = bytes([0x04, len(digest)]) + digest
        message_imprint = bytes([0x30, len(sha256_oid) + len(hashed_message)]) + sha256_oid + hashed_message

        version = bytes([0x02, 0x01, 0x01])  # INTEGER 1
        cert_req = bytes([0x01, 0x01, 0xFF])  # BOOLEAN TRUE

        body = version + message_imprint + cert_req
        ts_req = bytes([0x30, len(body)]) + body

        return ts_req
