"""Demo the end-to-end tier eval bundle — the sales-surface capstone (monetization-surface).

Walks the buyer flow that composes the #4 signed certificate with the #5 difficulty tiers:

    1. SELLER  publishes a catalog of tier offers (difficulty metadata + a signed, no-secret
               manifest for each tier's sealed eval).
    2. BUYER   picks a tier (sees its honest difficulty note), then submits.
    3. SELLER  issues a signed certificate for that tier's sealed eval (via a SellerListing —
               one source of truth, so the offer and certificate always bind).
    4. VERIFIER checks the certificate binds to the chosen offer (and NOT to a different tier),
               and that a contaminated submission still yields a signed ok=False certificate.

    python scripts/tier_eval_bundle_demo.py

Honest scope: two honesty notes travel with every offer — the packaging note (HMAC over a shared
secret, prototype) and the tier note (difficulty is measured only; SOTA/recurrent is open; a
sealed variant may drop difficulty levers). This demo shows the composition *flow* only; real
sale / pricing / hosting is a human gate.
"""
from __future__ import annotations

from critter_gym.eval_marketplace import (
    SellerListing,
    bundle_honesty,
    publish_catalog,
    verify_offer_certificate,
)
from critter_gym.learnability import reference_arm
from critter_gym.region import TEST_SEED_OFFSET

_KEY = b"seller-secret-key-prototype"
_KEY_ID = "seller-2026-q3"


def _rule(title: str) -> None:
    print(f"\n{'=' * 4} {title} {'=' * max(4, 56 - len(title))}")


def main() -> None:
    _rule("1. SELLER publishes a tier catalog")
    catalog = publish_catalog(["standard", "hard"], master_seed=20260701, key=_KEY, key_id=_KEY_ID)
    for offer in catalog:
        print(f"\n[{offer.tier_name}]  commitment={offer.manifest.seed_commitment[:16]}...  "
              f"harder={', '.join(offer.harder_knobs) or '(baseline)'}")
        print(f"  difficulty: {offer.difficulty_note}")

    _rule("2. BUYER picks the 'hard' tier + sees both honesty notes")
    # Re-list the chosen tier as a single-source-of-truth handle (same seed as the catalog offer).
    hard_seed = 20260701 + [o.tier_name for o in catalog].index("hard")
    listing = SellerListing.create("hard", hard_seed, _KEY, _KEY_ID, max_steps=120, n_worlds=3)
    offer = listing.offer()
    difficulty_note, honest_scope = bundle_honesty(offer)
    print(f"tier difficulty note : {difficulty_note}")
    print(f"packaging honest note: {honest_scope}")

    _rule("3. BUYER submits -> SELLER issues a signed tier certificate")
    submission = reference_arm("oracle")  # a scripted strong agent stands in for a real one
    cert = listing.issue_certificate(submission, range(0, 500))
    print(f"ok={cert.ok}  scored={cert.scorecard is not None}")
    if cert.scorecard is not None:
        sc = cert.scorecard
        print(f"  scorecard: mean_gyms={sc['mean_gyms_cleared']}  "
              f"frac_of_oracle={sc['frac_of_oracle']}  inference_score={sc['inference_score']}")

    _rule("4. VERIFIER checks binding + contamination")
    print(f"binds to the chosen 'hard' offer: {verify_offer_certificate(offer, cert, _KEY)}")
    other = SellerListing.create("standard", hard_seed, _KEY, _KEY_ID, max_steps=120, n_worlds=3)
    print(f"binds to a DIFFERENT ('standard') offer: "
          f"{verify_offer_certificate(other.offer(), cert, _KEY)}  (expected False)")
    dirty = listing.issue_certificate(submission, [3, 17, TEST_SEED_OFFSET + 42])
    print(f"contaminated submission -> ok={dirty.ok}  scored={dirty.scorecard is not None}  "
          f"(negative cert still binds as a valid signed artifact: "
          f"{verify_offer_certificate(offer, dirty, _KEY)})")

    _rule("Honest scope")
    print("Both notes travel with every offer: packaging = HMAC shared-secret (prototype);")
    print("tier = measured difficulty only, SOTA/recurrent OPEN, sealed may drop levers.")
    print("Real sale / pricing / hosting = human gate — not done here.")


if __name__ == "__main__":
    main()
