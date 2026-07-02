"""Tests for the buyer/seller packaging of the sealed held-out eval (monetization-surface #4).

These pin the *sales-surface* invariants that sit on top of the eval-product moat engine
(``eval_harness``): a distributable manifest that never leaks the secret seeds, a commitment
that catches a post-hoc eval swap (rug-pull), and a signed certificate whose contamination
verdict + score cannot be forged or altered. The signing is HMAC-SHA256 over a shared secret
(honest prototype scope); these tests pin the tamper-evidence and no-leak guarantees that make
the packaged eval trustworthy.
"""
from __future__ import annotations

import json

from critter_gym.eval_harness import SealedEvalSet
from critter_gym.eval_package import (
    EvalManifest,
    SignedCertificate,
    build_manifest,
    issue_certificate,
    manifest_self_check,
    seed_commitment,
    sign_payload,
    verify_certificate,
    verify_manifest,
    verify_signature,
)
from critter_gym.learnability import reference_arm
from critter_gym.region import TEST_SEED_OFFSET

KEY = b"seller-secret-key-prototype"
KEY_ID = "seller-2026-q3"


def _small_sealed(master_seed: int = 7) -> SealedEvalSet:
    # Small + cheap: 3 worlds on a tiny grid so scoring runs fast in the test suite.
    return SealedEvalSet(
        master_seed=master_seed, n_worlds=3, num_types=6, max_steps=60,
        grid_size=6, boss_hp=40, boss_atk=8, boss_def=8,
    )


# --- Step 1: canonical signing ---------------------------------------------------------

def test_sign_verify_round_trip():
    payload = {"a": 1, "b": [2, 3], "c": "x"}
    sig = sign_payload(payload, KEY)
    assert verify_signature(payload, sig, KEY)


def test_sign_is_canonical_key_order_independent():
    # Same content, different insertion order -> identical signature (canonical serialization).
    sig1 = sign_payload({"a": 1, "b": 2}, KEY)
    sig2 = sign_payload({"b": 2, "a": 1}, KEY)
    assert sig1 == sig2


def test_verify_fails_on_tampered_payload():
    payload = {"score": 0.9, "ok": True}
    sig = sign_payload(payload, KEY)
    tampered = {"score": 0.9, "ok": False}
    assert not verify_signature(tampered, sig, KEY)


def test_verify_fails_on_wrong_key():
    payload = {"a": 1}
    sig = sign_payload(payload, KEY)
    assert not verify_signature(payload, sig, b"different-key")


# --- Step 2: seed commitment (rug-pull guard, no leak) ---------------------------------

def test_commitment_deterministic():
    assert seed_commitment(_small_sealed(7)) == seed_commitment(_small_sealed(7))


def test_commitment_differs_for_different_master_seed():
    assert seed_commitment(_small_sealed(7)) != seed_commitment(_small_sealed(8))


def test_commitment_does_not_leak_seeds():
    sealed = _small_sealed(7)
    commit = seed_commitment(sealed)
    # No secret eval seed appears anywhere in the commitment string (it is a one-way hash).
    for s in sealed._eval_seeds():
        assert str(s) not in commit
    # And the commitment is a plain sha256 hex digest (no embedded structure).
    assert len(commit) == 64 and all(c in "0123456789abcdef" for c in commit)


# --- Step 3: buyer manifest (no secret + signed) ---------------------------------------

def test_manifest_round_trip():
    m = build_manifest(_small_sealed(7), KEY, KEY_ID)
    restored = EvalManifest.from_json(m.to_json())
    assert restored == m


def test_manifest_hides_secret_seeds_and_offset():
    sealed = _small_sealed(7)
    m = build_manifest(sealed, KEY, KEY_ID)
    blob = m.to_json()
    for s in sealed._eval_seeds():
        assert str(s) not in blob
    # The secret offset must not appear either.
    assert str(sealed._offset()) not in blob


def test_manifest_signature_valid_and_tamper_evident():
    m = build_manifest(_small_sealed(7), KEY, KEY_ID)
    assert verify_manifest(m, KEY)
    # Flip a public config field -> signature no longer matches.
    tampered = m._replace(boss_hp=m.boss_hp + 1)
    assert not verify_manifest(tampered, KEY)
    # Swap the commitment (rug-pull attempt) -> detected.
    swapped = m._replace(seed_commitment="0" * 64)
    assert not verify_manifest(swapped, KEY)


def test_manifest_self_check_catches_illegal_train_region():
    # Buyer pre-flight with the manifest alone (no secret): a "train" seed in the held-out
    # region is illegal and caught without the seller's SealedEvalSet.
    m = build_manifest(_small_sealed(7), KEY, KEY_ID)
    assert manifest_self_check(m, range(0, 100))
    assert not manifest_self_check(m, [10, 20, TEST_SEED_OFFSET + 5])


# --- Step 4: signed certificate (contamination-proof, tamper-evident) ------------------

def test_clean_submission_gets_signed_ok_certificate():
    sealed = _small_sealed(7)
    cert = issue_certificate(reference_arm("oracle"), range(0, 200), sealed, KEY, KEY_ID)
    assert isinstance(cert, SignedCertificate)
    assert cert.ok is True
    assert cert.scorecard is not None  # a clean submission is actually scored
    assert verify_certificate(cert, KEY)


def test_contaminated_submission_gets_signed_not_ok_certificate():
    sealed = _small_sealed(7)
    # Declaring a training seed in the held-out region is contamination -> ok=False.
    dirty_seeds = [1, 2, TEST_SEED_OFFSET + 3]
    cert = issue_certificate(reference_arm("oracle"), dirty_seeds, sealed, KEY, KEY_ID)
    assert cert.ok is False
    assert cert.scorecard is None  # a contaminated submission is not scored
    # The *negative* certificate is still a valid, signed artifact (integrity of the verdict).
    assert verify_certificate(cert, KEY)


def test_certificate_field_tamper_is_detected():
    sealed = _small_sealed(7)
    cert = issue_certificate(reference_arm("oracle"), range(0, 200), sealed, KEY, KEY_ID)
    forged = cert._replace(ok=not cert.ok)
    assert not verify_certificate(forged, KEY)


def test_certificate_commitment_binds_to_manifest():
    sealed = _small_sealed(7)
    m = build_manifest(sealed, KEY, KEY_ID)
    cert = issue_certificate(reference_arm("oracle"), range(0, 200), sealed, KEY, KEY_ID)
    # The certificate's commitment matches the manifest's -> proves same eval set.
    assert cert.seed_commitment == m.seed_commitment
    assert verify_certificate(cert, KEY, manifest=m)
    # A certificate for a *different* sealed set fails the manifest cross-check.
    other = issue_certificate(reference_arm("oracle"), range(0, 200), _small_sealed(8), KEY, KEY_ID)
    assert not verify_certificate(other, KEY, manifest=m)


def test_certificate_json_round_trip():
    sealed = _small_sealed(7)
    cert = issue_certificate(reference_arm("oracle"), range(0, 200), sealed, KEY, KEY_ID)
    restored = SignedCertificate.from_json(cert.to_json())
    assert restored == cert
    assert verify_certificate(restored, KEY)


def test_manifest_json_is_actual_json():
    m = build_manifest(_small_sealed(7), KEY, KEY_ID)
    parsed = json.loads(m.to_json())
    assert parsed["key_id"] == KEY_ID
    # The honest-scope note travels with the artifact and names its shared-secret limit.
    assert "prototype" in parsed["honest_scope"].lower()
