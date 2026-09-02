"""
EviChain - RFC 3161 External Anchoring Test Suite

Exercises the four verification stages of
``ExternalAnchor.verify_anchor``: message imprint recomputation, TSA
signing-certificate validation, token binding, and chain-state
comparison.  A stored FreeTSA response fixture keeps the suite
deterministic and offline; the live TSA round trip runs only when
``EVICHAIN_TSA_LIVE=1`` is set.

Run with:  pytest tests/test_external_anchor.py -v
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from evichain.external_anchor import (  # noqa: E402
    AnchorVerificationError,
    ExternalAnchor,
)

FIXTURE = Path(__file__).parent / "fixtures" / "freetsa_response.tsr"
#: SHA-256 of the payload that was timestamped when the fixture was captured.
FIXTURE_IMPRINT = (
    "e7c0ce61ebc12ced280a77b0839de50ddd27432a9e2fe955c1eb77c71a54366a"
)


class _FakeBlock:
    def __init__(self, h: str) -> None:
        self.hash = h


class _FakeChain:
    """Minimal stand-in exposing only the ``chain`` attribute used here."""

    def __init__(self, hashes):
        self.chain = [_FakeBlock(h) for h in hashes]


def _chain_producing(root_hex: str) -> _FakeChain:
    """Build a chain whose concatenated block hashes digest to ``root_hex``.

    The fixture was timestamped over ``sha256(b"evichain-test")``, so a
    single block whose hash is the literal string ``evichain-test``
    reproduces that imprint through ``compute_chain_root_hash``.
    """
    return _FakeChain(["evichain-test"])


@pytest.fixture()
def anchor(tmp_path):
    return ExternalAnchor(
        _chain_producing(FIXTURE_IMPRINT),
        anchors_dir=str(tmp_path / "anchors"),
    )


def _write_receipt(anchor: ExternalAnchor, tmp_path: Path, **overrides) -> str:
    token = FIXTURE.read_bytes()
    token_path = tmp_path / "fixture.tsr"
    token_path.write_bytes(token)
    info = anchor._parse_tst_info(token)

    receipt = {
        "type": "rfc3161",
        "status": "ok",
        "timestamp_utc": "20260728T130405Z",
        "chain_length": len(anchor.blockchain.chain),
        "root_hash": anchor.compute_chain_root_hash(),
        "tsa_url": anchor.tsa_url,
        "token_file": str(token_path),
        "token_sha256": hashlib.sha256(token).hexdigest(),
        "tsa_serial_number": info.get("serial_number"),
        "tsa_gen_time": info.get("gen_time"),
    }
    receipt.update(overrides)
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt), encoding="utf-8")
    return str(path)


@pytest.mark.skipif(not FIXTURE.exists(), reason="TSA fixture not available")
class TestTokenParsing:
    def test_imprint_matches_timestamped_payload(self, anchor):
        info = anchor._parse_tst_info(FIXTURE.read_bytes())
        assert info["hashed_message"] == FIXTURE_IMPRINT

    def test_serial_and_gen_time_present(self, anchor):
        info = anchor._parse_tst_info(FIXTURE.read_bytes())
        assert info["serial_number"].isdigit()
        assert info["gen_time"].endswith("Z")

    def test_malformed_token_rejected(self, anchor):
        with pytest.raises(ValueError):
            anchor._parse_tst_info(b"\x30\x03\x02\x01\x00")


@pytest.mark.skipif(not FIXTURE.exists(), reason="TSA fixture not available")
class TestCertificateStage:
    def test_timestamping_certificate_recovered(self, anchor):
        token = FIXTURE.read_bytes()
        info = anchor._parse_tst_info(token)
        result = anchor._verify_tsa_certificate(token, info["gen_time"])
        assert result["passed"] is True
        assert "not_before" in result and "not_after" in result

    def test_missing_trust_anchor_is_reported_as_warning(self, anchor):
        token = FIXTURE.read_bytes()
        info = anchor._parse_tst_info(token)
        monkeyed = os.environ.pop("EVICHAIN_TSA_TRUST_ANCHOR", None)
        try:
            result = anchor._verify_tsa_certificate(token, info["gen_time"])
        finally:
            if monkeyed is not None:
                os.environ["EVICHAIN_TSA_TRUST_ANCHOR"] = monkeyed
        assert any("trust anchor" in w for w in result["warnings"])

    def test_gen_time_outside_validity_window_fails(self, anchor):
        token = FIXTURE.read_bytes()
        result = anchor._verify_tsa_certificate(token, "19900101000000Z")
        assert result["passed"] is False
        assert "validity window" in result["detail"]


@pytest.mark.skipif(not FIXTURE.exists(), reason="TSA fixture not available")
class TestCmsSignatureStage:
    def test_genuine_token_signature_verifies(self, anchor):
        result = anchor._verify_cms_signature(FIXTURE.read_bytes())
        assert result["passed"] is True
        assert result["digest_algorithm"] in {"sha1", "sha256", "sha384",
                                              "sha512"}

    def test_bit_flip_in_signature_is_rejected(self, anchor):
        corrupted = bytearray(FIXTURE.read_bytes())
        corrupted[-3] ^= 0xFF
        result = anchor._verify_cms_signature(bytes(corrupted))
        assert result["passed"] is False


@pytest.mark.skipif(not FIXTURE.exists(), reason="TSA fixture not available")
class TestVerifyAnchor:
    def test_intact_chain_passes_all_stages(self, anchor, tmp_path):
        report = anchor.verify_anchor(_write_receipt(anchor, tmp_path))
        assert report["valid"] is True
        assert report["failed_stages"] == []
        assert report["stages"]["message_imprint"]["passed"] is True

    def test_rewritten_chain_fails_imprint_not_only_receipt(
        self, anchor, tmp_path
    ):
        """A privileged operator who edits chain and receipt still fails.

        The receipt's ``root_hash`` is updated to the rewritten chain, so
        the naive field comparison would pass.  Verification must still
        reject the anchor because the imprint is covered by the TSA
        signature and cannot be recomputed by the operator.
        """
        path = _write_receipt(anchor, tmp_path)
        anchor.blockchain.chain[0].hash = "tampered"
        forged = json.loads(Path(path).read_text(encoding="utf-8"))
        forged["root_hash"] = anchor.compute_chain_root_hash()
        Path(path).write_text(json.dumps(forged), encoding="utf-8")

        report = anchor.verify_anchor(path)
        assert report["valid"] is False
        assert "message_imprint" in report["failed_stages"]
        assert report["stages"]["chain_state"]["passed"] is True

    def test_deleted_token_named_as_failing_stage(self, anchor, tmp_path):
        path = _write_receipt(anchor, tmp_path)
        Path(json.loads(Path(path).read_text(encoding="utf-8"))
             ["token_file"]).unlink()
        report = anchor.verify_anchor(path)
        assert "message_imprint" in report["failed_stages"]
        assert "token file missing" in \
            report["stages"]["message_imprint"]["detail"]

    def test_substituted_receipt_fails_token_binding(self, anchor, tmp_path):
        path = _write_receipt(
            anchor, tmp_path, tsa_serial_number="999999999"
        )
        report = anchor.verify_anchor(path)
        assert "token_binding" in report["failed_stages"]

    def test_strict_mode_raises_typed_error(self, anchor, tmp_path):
        path = _write_receipt(anchor, tmp_path)
        anchor.blockchain.chain[0].hash = "tampered"
        with pytest.raises(AnchorVerificationError) as exc:
            anchor.verify_anchor(path, strict=True)
        assert exc.value.stage == "message_imprint"


class TestAnchoringPolicy:
    def test_first_anchor_is_always_due(self, anchor):
        assert anchor.should_anchor()["due"] is True

    def test_block_growth_triggers_early_anchor(self, tmp_path):
        chain = _FakeChain([f"h{i}" for i in range(60)])
        a = ExternalAnchor(chain, anchors_dir=str(tmp_path / "anchors"),
                           block_delta=50)
        (a.anchors_dir / "rfc3161_20260101T000000Z.json").write_text(
            json.dumps({"type": "rfc3161", "timestamp_utc":
                        "20260101T000000Z", "chain_length": 5,
                        "root_hash": "x"}),
            encoding="utf-8",
        )
        decision = a.should_anchor()
        assert decision["due"] is True
        assert decision["reason"] == "block_delta"

    def test_recent_anchor_within_interval_is_not_due(self, tmp_path):
        from datetime import datetime, timezone

        chain = _FakeChain(["h0"])
        a = ExternalAnchor(chain, anchors_dir=str(tmp_path / "anchors"),
                           interval_hours=24, block_delta=50)
        now = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (a.anchors_dir / f"rfc3161_{now}.json").write_text(
            json.dumps({"type": "rfc3161", "timestamp_utc": now,
                        "chain_length": 1, "root_hash": "x"}),
            encoding="utf-8",
        )
        assert a.should_anchor()["due"] is False


class TestOffBoxExport:
    def test_export_disabled_without_target(self, anchor, tmp_path):
        f = tmp_path / "r.json"
        f.write_text("{}", encoding="utf-8")
        assert anchor.export_offbox(f) is False

    def test_export_copies_and_never_overwrites(self, tmp_path):
        out = tmp_path / "offbox"
        a = ExternalAnchor(_FakeChain(["h0"]),
                           anchors_dir=str(tmp_path / "anchors"),
                           export_dir=str(out))
        f = tmp_path / "r.json"
        f.write_text('{"v":1}', encoding="utf-8")
        assert a.export_offbox(f) is True
        assert (out / "r.json").read_text(encoding="utf-8") == '{"v":1}'

        f.write_text('{"v":2}', encoding="utf-8")
        a.export_offbox(f)
        assert (out / "r.json").read_text(encoding="utf-8") == '{"v":1}'


@pytest.mark.skipif(
    os.getenv("EVICHAIN_TSA_LIVE") != "1",
    reason="live TSA round trip disabled (set EVICHAIN_TSA_LIVE=1)",
)
class TestLiveTSA:
    def test_round_trip_against_public_tsa(self, tmp_path):
        a = ExternalAnchor(_FakeChain(["h0", "h1"]),
                           anchors_dir=str(tmp_path / "anchors"))
        receipt = a.anchor_rfc3161()
        report = a.verify_anchor(receipt["receipt_file"])
        assert report["valid"] is True
