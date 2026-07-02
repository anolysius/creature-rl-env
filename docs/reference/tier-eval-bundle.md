# Tier eval bundle (sales-surface capstone) — reference

The end-to-end buyer flow that composes the two sales-surface pieces into one product:
[sealed-eval packaging](sealed-eval-packaging.md) (#4 — signed contamination-proof certificate)
and [env tiers](env-tiers.md) (#5 — named difficulty). `critter_gym.eval_marketplace` is
composition-only: it reuses the underlying contamination guard, signing, and commitment (no
reimplementation).

> **Honest scope (prototype).** Both honesty notes travel with every offer: the packaging note
> (HMAC over a *shared secret* — the verifier needs the seller's key; prototype) and the tier
> note (difficulty is **measured only**; SOTA/recurrent is **open**; a sealed variant may drop
> difficulty levers). Real sale / pricing / hosting is a human gate.

## The buyer flow

1. **Seller** publishes a catalog of `TierOffer`s — each = a tier's difficulty metadata + a
   signed, secret-free `EvalManifest` for that tier's sealed eval (distinct sealed block per tier).
2. **Buyer** picks a tier (sees its honest difficulty note) and submits an agent.
3. **Seller** issues a signed `SignedCertificate` for that tier's sealed eval — contaminated
   submissions get a signed `ok=False` certificate, unscored (delegated to `eval_package`).
4. **Verifier** checks the certificate binds to the chosen offer.

## Public API (`critter_gym.eval_marketplace`)

| Symbol | Role |
|---|---|
| `TierOffer` | A published offer: `tier_name`, `difficulty_note`, `harder_knobs`, signed `manifest`. `to_json`/`from_json`. |
| `build_tier_offer(tier, seed, key, key_id, **overrides)` | Build one signed offer. |
| `publish_catalog(tiers, seed, key, key_id)` | One offer per tier, each on a distinct sealed block (`seed + i`). |
| `SellerListing` | Single-source-of-truth handle binding `(tier, seed, key, key_id, overrides)` once — `.offer()` and `.issue_certificate()` can never drift (`.create(...)` constructor). |
| `issue_tier_certificate(submission, train, tier, seed, key, key_id, **overrides)` | Issue a signed certificate for a tier (delegates to `eval_package.issue_certificate`). |
| `verify_offer_certificate(offer, cert, key)` | True iff the cert is signed *and* binds to the offer's sealed eval. |
| `bundle_honesty(offer)` | `(tier difficulty_note, packaging honest_scope)` — surfaces both notes. |

## Binding contract (important)

Binding is by the sealed-eval **commitment** — a hash of the *resolved* knobs (grid/boss/types/…)
plus the secret seeds, **not the tier label**. A certificate binds to an offer iff it was issued
on the same resolved sealed eval. Consequences:

- A different tier, or the same tier on a different `master_seed`/overrides, → different
  commitment → fails to bind.
- Two tiers **overridden to identical resolved knobs and the same seed** would bind — the eval is
  what's bound, not the name. (This is why `SellerListing` fixes the overrides once.)

## Demo

```bash
python scripts/tier_eval_bundle_demo.py   # catalog -> pick -> submit -> signed cert -> verify
```

Shows a two-tier catalog with distinct commitments, both honesty notes, a scored clean
certificate that binds to the chosen tier (and not to another), and a contaminated submission
yielding a signed `ok=False` certificate.
