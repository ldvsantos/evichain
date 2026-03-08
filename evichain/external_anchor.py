"""
EviChain – External Hash Anchoring Module

Provides two independent mechanisms for publishing chain-root hashes
to external, independently verifiable stores:

1. **RFC 3161 Timestamping** – Sends a SHA-256 digest to a free Time
   Stamping Authority (TSA) and stores the resulting TimeStampResp
   token locally.  Verification re-computes the hash and checks the
   token against the TSA certificate.

2. **Bitcoin Testnet OP_RETURN** *(optional, requires bitcoinlib)* –
   Embeds the 32-byte chain-root hash in a Testnet transaction using
   the OP_RETURN output script, creating a publicly auditable anchor.

Both paths record receipts as JSON in ``data/anchors/`` so that any
auditor can independently verify the chain's integrity at the moment
of anchoring.

Security note:
    External anchoring mitigates threat T-03 (privileged admin
    rewriting the chain file) by creating an independent verification
    path that the admin cannot retroactively alter.

Usage::

    from evichain.external_anchor import ExternalAnchor

    anchor = ExternalAnchor(blockchain)
    receipt = anchor.anchor_rfc3161()       # free, no API key
    receipt = anchor.anchor_btc_testnet()   # requires funded testnet wallet
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from blockchain_simulator import EviChainBlockchain


class ExternalAnchor:
    """Manages external anchoring of blockchain root hashes."""

    # FreeTSA (https://freetsa.org) – free RFC 3161 TSA
    DEFAULT_TSA_URL = "https://freetsa.org/tsr"
    ANCHORS_DIR = "data/anchors"

    def __init__(
        self,
        blockchain: "EviChainBlockchain",
        *,
        anchors_dir: str | None = None,
        tsa_url: str | None = None,
    ) -> None:
        self.blockchain = blockchain
        self.anchors_dir = Path(anchors_dir or self.ANCHORS_DIR)
        self.anchors_dir.mkdir(parents=True, exist_ok=True)
        self.tsa_url = tsa_url or os.getenv(
            "EVICHAIN_TSA_URL", self.DEFAULT_TSA_URL
        )

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
    # RFC 3161 Time-Stamp Protocol
    # ------------------------------------------------------------------

    def anchor_rfc3161(self) -> dict:
        """Request an RFC 3161 timestamp token for the current chain root.

        Returns a receipt dict saved to ``anchors_dir``.
        Requires the ``requests`` library (already a project dependency).
        """
        import requests  # project dependency

        root_hash = self.compute_chain_root_hash()
        digest_bytes = bytes.fromhex(root_hash)

        # Build a minimal TimeStampReq (DER) ---------------------------
        ts_request = self._build_ts_request(digest_bytes)

        resp = requests.post(
            self.tsa_url,
            data=ts_request,
            headers={"Content-Type": "application/timestamp-query"},
            timeout=30,
        )
        resp.raise_for_status()

        # Persist the token ----------------------------------------------
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        token_path = self.anchors_dir / f"rfc3161_{ts}.tsr"
        token_path.write_bytes(resp.content)

        receipt = {
            "type": "rfc3161",
            "timestamp_utc": ts,
            "chain_length": len(self.blockchain.chain),
            "root_hash": root_hash,
            "tsa_url": self.tsa_url,
            "token_file": str(token_path),
            "token_size_bytes": len(resp.content),
            "http_status": resp.status_code,
        }

        receipt_path = self.anchors_dir / f"rfc3161_{ts}.json"
        receipt_path.write_text(
            json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return receipt

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

    def verify_anchor(self, receipt_path: str) -> dict:
        """Verify a previously saved anchor receipt against current chain.

        Returns a dict with ``valid`` (bool) and ``details``.
        """
        receipt = json.loads(
            Path(receipt_path).read_text(encoding="utf-8")
        )
        current_root = self.compute_chain_root_hash()
        chain_unchanged = current_root == receipt["root_hash"]

        return {
            "receipt_type": receipt["type"],
            "receipt_root_hash": receipt["root_hash"],
            "current_root_hash": current_root,
            "chain_unchanged": chain_unchanged,
            "chain_length_at_anchor": receipt["chain_length"],
            "chain_length_now": len(self.blockchain.chain),
            "valid": chain_unchanged,
        }

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
