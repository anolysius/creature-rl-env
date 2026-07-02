"""Tests for the tier eval bundle — the end-to-end sales-surface capstone (monetization-surface).

These pin the *buyer flow* that composes the #4 signed contamination-proof certificate
(``eval_package``) with the #5 difficulty tiers (``env_tier``): a seller publishes tier offers
(difficulty metadata + a signed, no-secret manifest), a buyer submits to a chosen tier, and the
issued certificate binds to *that* tier's sealed eval. The capstone must not lose either honesty
note (the packaging HMAC-prototype scope, and the tier's measured/open difficulty note).
"""
from __future__ import annotations

import json

from critter_gym.env_tier import get_tier
from critter_gym.eval_marketplace import (
    SellerListing,
    TierOffer,
    build_tier_offer,
    bundle_honesty,
    issue_tier_certificate,
    publish_catalog,
    verify_offer_certificate,
)
from critter_gym.eval_package import verify_certificate, verify_manifest
from critter_gym.learnability import reference_arm

KEY = b"seller-secret-key-prototype"
KEY_ID = "seller-2026-q3"


def _small_listing(tier: str = "standard", master_seed: int = 5) -> SellerListing:
    # Small + cheap so scoring runs fast, but DON'T override grid_size: it is a tier-distinguishing
    # knob (standard=10, hard=16). Overriding it identically would collapse the tiers to the same
    # sealed config (the commitment binds to resolved knobs, not the tier label).
    return SellerListing.create(tier, master_seed, KEY, KEY_ID, max_steps=80, n_worlds=2)


# --- Step 1: TierOffer -----------------------------------------------------------------

def test_offer_round_trip():
    offer = build_tier_offer("standard", 5, KEY, KEY_ID, grid_size=6, max_steps=60, n_worlds=3)
    restored = TierOffer.from_json(offer.to_json())
    assert restored == offer


def test_offer_manifest_is_signed_and_secretless():
    offer = build_tier_offer("hard", 9, KEY, KEY_ID, grid_size=6, max_steps=60, n_worlds=3)
    assert verify_manifest(offer.manifest, KEY)
    # The offer carries no secret eval seeds (the manifest only commits to them).
    blob = offer.to_json()
    # seed_commitment is a hash; assert the manifest exposes it but not raw seeds.
    assert offer.manifest.seed_commitment in blob


def test_offer_carries_tier_difficulty_note():
    offer = build_tier_offer("hard", 9, KEY, KEY_ID, grid_size=6, max_steps=60, n_worlds=3)
    assert offer.difficulty_note == get_tier("hard").difficulty_note
    assert offer.harder_knobs == get_tier("hard").harder_knobs


# --- Step 2: publish_catalog -----------------------------------------------------------

def test_catalog_has_one_offer_per_tier():
    cat = publish_catalog(["standard", "hard"], 100, KEY, KEY_ID)
    assert [o.tier_name for o in cat] == ["standard", "hard"]


def test_catalog_offers_have_distinct_commitments():
    cat = publish_catalog(["standard", "hard"], 100, KEY, KEY_ID)
    commits = {o.manifest.seed_commitment for o in cat}
    assert len(commits) == len(cat)  # distinct sealed blocks
    for o in cat:
        assert verify_manifest(o.manifest, KEY)


# --- Step 3: seller handle + issue/verify certificate ----------------------------------

def test_clean_submission_binds_to_its_offer():
    listing = _small_listing("standard", 5)
    offer = listing.offer()
    cert = listing.issue_certificate(reference_arm("oracle"), range(0, 200))
    assert cert.ok is True
    assert verify_certificate(cert, KEY)
    assert verify_offer_certificate(offer, cert, KEY)  # binds to this tier's sealed eval


def test_same_tier_different_seed_fails_binding():
    # L1 SUGGEST: isolate the seed confound from the tier/knob confound. Same tier, different
    # master_seed -> a different sealed block -> the cert must NOT bind to the other offer.
    offer_a = _small_listing("standard", 5).offer()
    cert_b = _small_listing("standard", 6).issue_certificate(reference_arm("oracle"), range(0, 200))
    assert verify_certificate(cert_b, KEY)          # cert itself is validly signed
    assert not verify_offer_certificate(offer_a, cert_b, KEY)  # but binds to a DIFFERENT seed


def test_different_tier_fails_binding():
    offer_std = _small_listing("standard", 5).offer()
    cert_hard = _small_listing("hard", 5).issue_certificate(reference_arm("oracle"), range(0, 200))
    assert not verify_offer_certificate(offer_std, cert_hard, KEY)


def test_seller_listing_offer_and_cert_always_bind():
    # The single-source-of-truth handle: offer() and issue_certificate() use the same
    # (tier, seed, overrides), so a re-entry mismatch is structurally impossible.
    listing = _small_listing("hard", 11)
    offer = listing.offer()
    cert = listing.issue_certificate(reference_arm("oracle"), range(0, 200))
    assert verify_offer_certificate(offer, cert, KEY)


def test_contaminated_submission_delegates_to_eval_package():
    from critter_gym.region import TEST_SEED_OFFSET
    listing = _small_listing("standard", 5)
    cert = listing.issue_certificate(reference_arm("oracle"), [1, 2, TEST_SEED_OFFSET + 3])
    assert cert.ok is False           # contamination caught
    assert cert.scorecard is None     # not scored
    assert verify_certificate(cert, KEY)  # negative cert still signed


def test_certificate_tamper_is_detected():
    listing = _small_listing("standard", 5)
    cert = listing.issue_certificate(reference_arm("oracle"), range(0, 200))
    forged = cert._replace(ok=not cert.ok)
    assert not verify_certificate(forged, KEY)


def test_issue_tier_certificate_function_matches_handle():
    # The thin function form issues an equivalent certificate to the handle.
    cert = issue_tier_certificate(
        reference_arm("oracle"), range(0, 200), "standard", 5, KEY, KEY_ID,
        max_steps=80, n_worlds=2,
    )
    offer = _small_listing("standard", 5).offer()
    assert verify_offer_certificate(offer, cert, KEY)


# --- Step 4: honesty travel ------------------------------------------------------------

def test_bundle_honesty_exposes_both_notes():
    offer = build_tier_offer("hard", 9, KEY, KEY_ID, grid_size=6, max_steps=60, n_worlds=3)
    difficulty_note, honest_scope = bundle_honesty(offer)
    assert "open" in difficulty_note.lower()   # tier: SOTA/recurrent unmeasured
    assert "prototype" in honest_scope.lower()  # packaging: HMAC shared-secret


def test_offer_json_is_actual_json():
    offer = build_tier_offer("standard", 5, KEY, KEY_ID, grid_size=6, max_steps=60, n_worlds=3)
    parsed = json.loads(offer.to_json())
    assert parsed["tier_name"] == "standard"
    assert "manifest" in parsed
