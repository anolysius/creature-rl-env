"""Tier eval bundle — the end-to-end sales-surface capstone (monetization-surface).

#4 (:mod:`critter_gym.eval_package`) makes an eval's result a signed, contamination-proof
certificate; #5 (:mod:`critter_gym.env_tier`) makes difficulty a named, validated tier. They
lived as separate pieces. This module composes them into the *buyer flow* a customer actually
experiences — pick a difficulty tier, get a signed no-secret manifest for its sealed eval,
submit, and receive a signed certificate that **binds to that tier's sealed eval**:

- :class:`TierOffer` — what a seller publishes per tier: the tier's difficulty metadata + a
  signed :class:`~critter_gym.eval_package.EvalManifest` for its sealed eval.
- :func:`build_tier_offer` / :func:`publish_catalog` — build one / many offers.
- :class:`SellerListing` — a single-source-of-truth handle binding ``(tier, master_seed, key,
  key_id, overrides)`` once, so ``offer()`` and ``issue_certificate()`` can never drift apart
  (a re-entry mismatch is structurally impossible).
- :func:`issue_tier_certificate` / :func:`verify_offer_certificate` — issue a certificate for a
  tier; verify it binds to a given offer (via the sealed-eval commitment).
- :func:`bundle_honesty` — surface **both** honesty notes so neither is lost.

This module only *composes* the two underlying modules — it reuses their contamination guard,
signing, and commitment (no reimplementation). Both honesty layers travel with an offer: the
packaging ``HONEST_SCOPE`` (HMAC over a shared secret — prototype) and the tier's
``difficulty_note`` (measured difficulty only; SOTA/recurrent is open; a sealed variant may drop
difficulty levers). Real sale / pricing / hosting is a human gate.
"""
from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any, NamedTuple

from critter_gym.env_tier import build_sealed, get_tier
from critter_gym.eval_package import (
    EvalManifest,
    SignedCertificate,
    Submission,
    build_manifest,
    issue_certificate,
    verify_certificate,
)


class TierOffer(NamedTuple):
    """A seller's published offer for one difficulty tier.

    Carries the tier's difficulty metadata *and* a signed, secret-free manifest for its sealed
    eval — so a buyer sees which difficulty they are buying and can verify the manifest."""

    tier_name: str
    difficulty_note: str
    harder_knobs: tuple[str, ...]
    manifest: EvalManifest

    def to_json(self) -> str:
        return json.dumps(
            {
                "tier_name": self.tier_name,
                "difficulty_note": self.difficulty_note,
                "harder_knobs": list(self.harder_knobs),
                "manifest": self.manifest._asdict(),
            },
            sort_keys=True,
        )

    @classmethod
    def from_json(cls, s: str) -> TierOffer:
        d = json.loads(s)
        return cls(
            tier_name=d["tier_name"],
            difficulty_note=d["difficulty_note"],
            harder_knobs=tuple(d["harder_knobs"]),
            manifest=EvalManifest(**d["manifest"]),
        )


def build_tier_offer(
    tier_name: str, master_seed: int, key: bytes, key_id: str, **sealed_overrides: Any
) -> TierOffer:
    """Build a signed offer for ``tier_name``: its sealed manifest + difficulty metadata."""
    spec = get_tier(tier_name)
    sealed = build_sealed(tier_name, master_seed, **sealed_overrides)
    manifest = build_manifest(sealed, key, key_id)
    return TierOffer(
        tier_name=tier_name,
        difficulty_note=spec.difficulty_note,
        harder_knobs=spec.harder_knobs,
        manifest=manifest,
    )


def publish_catalog(
    tier_names: Sequence[str], master_seed: int, key: bytes, key_id: str
) -> list[TierOffer]:
    """Build one offer per tier, each on a *distinct* sealed block (``master_seed + i``)."""
    return [
        build_tier_offer(name, master_seed + i, key, key_id)
        for i, name in enumerate(tier_names)
    ]


def issue_tier_certificate(
    submission: Submission,
    declared_train_seeds: Sequence[int] | range,
    tier_name: str,
    master_seed: int,
    key: bytes,
    key_id: str,
    **sealed_overrides: Any,
) -> SignedCertificate:
    """Issue a signed certificate for a submission on ``tier_name``'s sealed eval.

    Delegates the contamination guard + scoring + signing to
    :func:`~critter_gym.eval_package.issue_certificate` (a contaminated submission gets a signed
    ``ok=False`` certificate, unscored) — no reimplementation here."""
    sealed = build_sealed(tier_name, master_seed, **sealed_overrides)
    return issue_certificate(submission, declared_train_seeds, sealed, key, key_id)


def verify_offer_certificate(offer: TierOffer, cert: SignedCertificate, key: bytes) -> bool:
    """True iff ``cert`` is validly signed *and* binds to ``offer``'s sealed eval.

    Binding is by the sealed-eval commitment — a hash of the *resolved* knobs (grid/boss/types/
    …) plus the secret seeds, NOT the tier label. So a certificate binds iff it was issued on the
    same resolved sealed eval: a different tier, or the same tier on a different master_seed/
    overrides, yields a different commitment and fails. (Two tiers overridden to identical
    resolved knobs *and* the same seed would bind — the eval is what's bound, not the name.)"""
    return verify_certificate(cert, key, manifest=offer.manifest)


def bundle_honesty(offer: TierOffer) -> tuple[str, str]:
    """Both honesty notes for an offer: (tier difficulty_note, packaging honest_scope).

    Surfacing both is the capstone's honesty contract — neither layer's caveat is lost."""
    return offer.difficulty_note, offer.manifest.honest_scope


class SellerListing(NamedTuple):
    """A single-source-of-truth seller handle for one tier listing.

    Binds ``(tier_name, master_seed, key, key_id, overrides)`` once so :meth:`offer` and
    :meth:`issue_certificate` always use identical parameters — the offer and any certificate
    issued through it are guaranteed to bind (a re-entry mismatch is impossible)."""

    tier_name: str
    master_seed: int
    key: bytes
    key_id: str
    overrides: tuple[tuple[str, Any], ...] = ()

    @classmethod
    def create(
        cls, tier_name: str, master_seed: int, key: bytes, key_id: str, **overrides: Any
    ) -> SellerListing:
        return cls(tier_name, master_seed, key, key_id, tuple(sorted(overrides.items())))

    def _overrides(self) -> dict[str, Any]:
        return dict(self.overrides)

    def offer(self) -> TierOffer:
        return build_tier_offer(
            self.tier_name, self.master_seed, self.key, self.key_id, **self._overrides()
        )

    def issue_certificate(
        self, submission: Submission, declared_train_seeds: Sequence[int] | range
    ) -> SignedCertificate:
        return issue_tier_certificate(
            submission, declared_train_seeds, self.tier_name, self.master_seed,
            self.key, self.key_id, **self._overrides(),
        )
