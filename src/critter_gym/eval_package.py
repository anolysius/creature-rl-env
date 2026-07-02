"""Buyer/seller packaging for the sealed held-out eval — the M5-EC1 sales-surface prototype.

The eval-product initiative built the *functional* moat engine in :mod:`critter_gym.eval_harness`
(:class:`~critter_gym.eval_harness.SealedEvalSet`, :func:`~critter_gym.eval_harness.verify_sealed`,
:func:`~critter_gym.eval_harness.score_agent`). Those live only in-process — there is no way to
*hand the eval to a buyer* or *prove a result was not forged*. This module adds exactly that
missing sales surface, additively (it imports the harness; the harness does not import it):

- :func:`sign_payload` / :func:`verify_signature` — HMAC-SHA256 over a canonical serialization.
  This is the tamper-evidence primitive every artifact below reuses.
- :func:`seed_commitment` — a one-way hash binding a :class:`SealedEvalSet` to its eval block +
  world config. It lets a buyer detect a *rug-pull* (the seller swapping the eval after issuing
  a certificate) without ever revealing the secret seeds.
- :class:`EvalManifest` — the *distributable* description of an eval a seller hands a buyer. It
  carries the public config + the commitment + the honest-scope note, and is itself **signed**,
  so any field tampering is detected. It deliberately omits the secret seeds and offset.
- :class:`SignedCertificate` — the issued, signed result: the contamination verdict
  (:func:`verify_sealed`) and, for a clean submission, the RLVR scorecard
  (:func:`score_agent`). A *contaminated* submission still gets a signed ``ok=False``
  certificate — the negative verdict is a first-class, non-forgeable artifact.

**Honest scope (prototype).** Signatures are HMAC-SHA256 over a *shared secret*: the verifier
must hold the same key the seller signed with (think: a trusted leaderboard). A real hosted
product needs **asymmetric** signing (so a buyer verifies without the secret) and **server-side**
secret custody so the sealed seeds never ship at all. This module demonstrates the packaging /
commitment / tamper-evidence *flow* only — it is not a hosted product. That upgrade is a
human-gated follow-up (DESIGN §8 · CLAUDE.md monetization honesty gate).
"""
from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Mapping, Sequence
from typing import Any, NamedTuple

from critter_gym.eval_harness import (
    _SEALED_BASE,
    Scorecard,
    SealedCertificate,
    SealedEvalSet,
    Submission,
    score_agent,
    verify_sealed,
)
from critter_gym.region import TEST_SEED_OFFSET

#: Prototype honesty note, embedded in every manifest/certificate so the shared-secret limit
#: travels *with* the artifact and cannot be silently dropped.
HONEST_SCOPE = (
    "HMAC-SHA256 over a shared secret (prototype): the verifier must hold the seller's key. "
    "A real hosted product needs asymmetric signing (buyer verifies without the secret) and "
    "server-side secret custody so the sealed seeds never ship. This artifact demonstrates the "
    "packaging/commitment/tamper-evidence flow only."
)


# --- Step 1: canonical serialization + HMAC signing (the tamper-evidence primitive) ----

def _canonical(payload: Mapping[str, Any]) -> bytes:
    """Deterministic bytes for a payload — sorted keys, tight separators, UTF-8.

    Signing and verifying share this one function so a signature computed at issue time matches
    a signature recomputed after a JSON round-trip (SSOT for the signed byte-string)."""
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign_payload(payload: Mapping[str, Any], key: bytes) -> str:
    """HMAC-SHA256 hexdigest of the canonical serialization of ``payload``."""
    return hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()


def verify_signature(payload: Mapping[str, Any], sig: str, key: bytes) -> bool:
    """True iff ``sig`` is the signature of ``payload`` under ``key`` (constant-time compare)."""
    expected = sign_payload(payload, key)
    return hmac.compare_digest(expected, str(sig))


# --- Step 2: seed commitment (rug-pull guard; one-way, no leak) -------------------------

def seed_commitment(sealed: SealedEvalSet) -> str:
    """A one-way commitment to the sealed eval block + world config.

    Binding both the (sorted) secret seeds *and* the world knobs means a seller cannot swap the
    eval — for a different block or a re-tuned boss — after issuing a manifest/certificate without
    the commitment changing (and the signature then failing). sha256 is one-way, so the
    commitment reveals nothing about the seeds themselves."""
    material = {
        "seeds": sorted(sealed._eval_seeds()),
        "num_types": sealed.num_types,
        "commit_battles": sealed.commit_battles,
        "max_steps": sealed.max_steps,
        "grid_size": sealed.grid_size,
        "boss_hp": sealed.boss_hp,
        "boss_atk": sealed.boss_atk,
        "boss_def": sealed.boss_def,
    }
    return hashlib.sha256(b"critter-commit:" + _canonical(material)).hexdigest()


# --- Step 3: buyer manifest (no secret + signed) ---------------------------------------

class EvalManifest(NamedTuple):
    """The distributable description of a sealed eval a seller hands a buyer.

    Public config + the seed commitment + the honest-scope note, all signed. Deliberately omits
    the secret seeds and offset — a buyer can plan against it and self-check their training
    seeds, but cannot reconstruct the eval block."""

    n_worlds: int
    grid_size: int
    boss_hp: int
    boss_atk: int
    boss_def: int
    num_types: int
    max_steps: int
    commit_battles: bool
    test_seed_offset: int  # public region boundary: training seeds must be below this
    sealed_base: int       # public: sealed blocks live at/above this (informational)
    seed_commitment: str
    key_id: str
    honest_scope: str
    sig: str

    def _payload(self) -> dict[str, Any]:
        """Everything the signature covers (all fields except ``sig``)."""
        d = self._asdict()
        d.pop("sig")
        return d

    def to_json(self) -> str:
        return json.dumps(self._asdict(), sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> EvalManifest:
        return cls(**json.loads(s))


def build_manifest(sealed: SealedEvalSet, key: bytes, key_id: str) -> EvalManifest:
    """Build and sign a buyer-facing manifest for ``sealed`` (no secret seeds/offset)."""
    payload: dict[str, Any] = {
        "n_worlds": sealed.n_worlds,
        "grid_size": sealed.grid_size,
        "boss_hp": sealed.boss_hp,
        "boss_atk": sealed.boss_atk,
        "boss_def": sealed.boss_def,
        "num_types": sealed.num_types,
        "max_steps": sealed.max_steps,
        "commit_battles": sealed.commit_battles,
        "test_seed_offset": TEST_SEED_OFFSET,
        "sealed_base": _SEALED_BASE,
        "seed_commitment": seed_commitment(sealed),
        "key_id": key_id,
        "honest_scope": HONEST_SCOPE,
    }
    sig = sign_payload(payload, key)
    return EvalManifest(**payload, sig=sig)


def verify_manifest(manifest: EvalManifest, key: bytes) -> bool:
    """True iff the manifest's signature is valid under ``key`` (tamper-evident)."""
    return verify_signature(manifest._payload(), manifest.sig, key)


def manifest_self_check(
    manifest: EvalManifest, declared_train_seeds: Sequence[int] | range
) -> bool:
    """Buyer pre-flight with the manifest alone: are all declared train seeds legal?

    Without the seller's :class:`SealedEvalSet` a buyer cannot check overlap with the (secret)
    sealed block, but they *can* catch the always-illegal case — a "training" seed in the
    held-out region (``>= test_seed_offset``). Returns True iff every declared seed is in the
    training region. The full overlap guard is the seller's :func:`verify_sealed`."""
    return all(int(s) < manifest.test_seed_offset for s in declared_train_seeds)


# --- Step 4: signed certificate (contamination-proof, tamper-evident) ------------------

def _round_floats(d: Mapping[str, Any], ndigits: int = 6) -> dict[str, Any]:
    """Round float fields so the signed payload round-trips through JSON byte-identically."""
    return {k: (round(v, ndigits) if isinstance(v, float) else v) for k, v in d.items()}


class SignedCertificate(NamedTuple):
    """The signed result of a submission on a sealed eval set.

    ``contamination`` is the :func:`verify_sealed` verdict as a dict; ``scorecard`` is the
    :func:`score_agent` scorecard as a dict for a *clean* submission, or ``None`` for a
    contaminated one (scoring a contaminated submission would be meaningless). The whole thing
    is signed, so both a positive and a negative verdict are non-forgeable artifacts."""

    ok: bool
    key_id: str
    seed_commitment: str
    contamination: dict[str, Any]
    scorecard: dict[str, Any] | None
    honest_scope: str
    sig: str

    def _payload(self) -> dict[str, Any]:
        d = self._asdict()
        d.pop("sig")
        return d

    def to_json(self) -> str:
        return json.dumps(self._asdict(), sort_keys=True)

    @classmethod
    def from_json(cls, s: str) -> SignedCertificate:
        return cls(**json.loads(s))


def issue_certificate(
    submission: Submission,
    declared_train_seeds: Sequence[int] | range,
    sealed: SealedEvalSet,
    key: bytes,
    key_id: str,
) -> SignedCertificate:
    """Run the contamination guard, score iff clean, and issue a signed certificate.

    A clean submission (``verify_sealed(...).ok``) is scored with :func:`score_agent`. A
    contaminated one is *not* scored — the certificate is issued ``ok=False`` with a null
    scorecard, and is still signed so the negative verdict cannot be repudiated or altered."""
    contamination: SealedCertificate = verify_sealed(declared_train_seeds, sealed)
    scorecard: dict[str, Any] | None = None
    if contamination.ok:
        card: Scorecard = score_agent(submission, sealed)
        scorecard = _round_floats(card._asdict())

    payload: dict[str, Any] = {
        "ok": bool(contamination.ok),
        "key_id": key_id,
        "seed_commitment": seed_commitment(sealed),
        "contamination": dict(contamination._asdict()),
        "scorecard": scorecard,
        "honest_scope": HONEST_SCOPE,
    }
    sig = sign_payload(payload, key)
    return SignedCertificate(**payload, sig=sig)


def verify_certificate(
    cert: SignedCertificate, key: bytes, *, manifest: EvalManifest | None = None
) -> bool:
    """True iff the certificate's signature is valid (and, if given, binds to ``manifest``).

    When ``manifest`` is supplied, the certificate's ``seed_commitment`` must equal the
    manifest's — proving the certificate was issued for *that* eval set, not a swapped one."""
    if not verify_signature(cert._payload(), cert.sig, key):
        return False
    return manifest is None or cert.seed_commitment == manifest.seed_commitment
