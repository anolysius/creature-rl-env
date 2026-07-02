"""Demo the buyer/seller flow for a packaged sealed held-out eval (monetization-surface #4).

Walks the M5-EC1 sales surface end-to-end, printing each step so the *packaging* is visible:

    1. SELLER  builds a signed :class:`EvalManifest` for a private :class:`SealedEvalSet`
               and hands it to the buyer — the manifest carries NO secret seeds/offset.
    2. BUYER   self-checks their declared training seeds against the manifest alone
               (no secret needed) before submitting.
    3. SELLER  issues a signed :class:`SignedCertificate`: contamination verdict +, for a
               clean submission, the RLVR scorecard.
    4. VERIFIER (holds the seller's key — think a trusted leaderboard) verifies the signature
               and that the certificate binds to the manifest's commitment.

It runs two cases: a CLEAN submission (scored, ok=True) and a CONTAMINATED one (a training seed
in the held-out region -> ok=False, not scored, still signed). Certificate tampering is shown to
be detected.

    python scripts/package_sealed_eval.py

Honest scope: signatures are HMAC-SHA256 over a *shared secret* — the verifier must hold the
seller's key (prototype). A real hosted product needs asymmetric signing (buyer verifies without
the secret) and server-side secret custody so the sealed seeds never ship. This demo shows the
packaging / commitment / tamper-evidence *flow* only; it is not a hosted product. Wiring real
sale / pricing / hosting is a human gate.
"""
from __future__ import annotations

from critter_gym.eval_harness import SealedEvalSet
from critter_gym.eval_package import (
    HONEST_SCOPE,
    build_manifest,
    issue_certificate,
    manifest_self_check,
    verify_certificate,
    verify_manifest,
)
from critter_gym.learnability import reference_arm
from critter_gym.region import TEST_SEED_OFFSET

# Shared secret + key id. In a real product the key lives server-side (see HONEST_SCOPE).
_KEY = b"seller-secret-key-prototype"
_KEY_ID = "seller-2026-q3"


def _rule(title: str) -> None:
    print(f"\n{'=' * 4} {title} {'=' * (60 - len(title))}")


def main() -> None:
    # A small, cheap sealed set so the demo scores quickly.
    sealed = SealedEvalSet(
        master_seed=20260701, n_worlds=4, num_types=6, max_steps=80,
        grid_size=6, boss_hp=48, boss_atk=9, boss_def=9,
    )

    _rule("1. SELLER builds + signs the buyer manifest")
    manifest = build_manifest(sealed, _KEY, _KEY_ID)
    print(manifest.to_json())
    print(f"\nmanifest signature valid (verifier holds key): {verify_manifest(manifest, _KEY)}")
    print("note: the manifest carries a seed COMMITMENT (one-way hash), never the secret seeds.")

    _rule("2. BUYER self-checks declared training seeds (manifest only, no secret)")
    clean_train = range(0, 500)
    dirty_train = [3, 17, TEST_SEED_OFFSET + 42]  # one seed illegally in the held-out region
    print(f"clean train seeds  [0..500)          -> legal? "
          f"{manifest_self_check(manifest, clean_train)}")
    print(f"dirty train seeds  [3,17,OFFSET+42]  -> legal? "
          f"{manifest_self_check(manifest, dirty_train)}")

    _rule("3+4. CLEAN submission -> signed ok=True certificate, verified")
    submission = reference_arm("oracle")  # a scripted strong agent stands in for a real one
    cert = issue_certificate(submission, clean_train, sealed, _KEY, _KEY_ID)
    print(f"ok={cert.ok}  scored={cert.scorecard is not None}")
    if cert.scorecard is not None:
        sc = cert.scorecard
        print(
            f"  scorecard: mean_gyms={sc['mean_gyms_cleared']}  cleared_rate={sc['cleared_rate']}  "
            f"frac_of_oracle={sc['frac_of_oracle']}  inference_score={sc['inference_score']}"
        )
    print(f"signature valid: {verify_certificate(cert, _KEY)}")
    print(f"binds to manifest (same eval): {verify_certificate(cert, _KEY, manifest=manifest)}")

    _rule("3+4. CONTAMINATED submission -> signed ok=False certificate (not scored), verified")
    dirty_cert = issue_certificate(submission, dirty_train, sealed, _KEY, _KEY_ID)
    print(f"ok={dirty_cert.ok}  scored={dirty_cert.scorecard is not None}  "
          f"(contamination: {dirty_cert.contamination})")
    print(f"negative certificate is still a valid signed artifact: "
          f"{verify_certificate(dirty_cert, _KEY)}")

    _rule("Tamper check: forging a field breaks the signature")
    forged = cert._replace(ok=not cert.ok)
    print(f"forged (flipped ok) verifies? {verify_certificate(forged, _KEY)}  (expected False)")

    _rule("Honest scope")
    print(HONEST_SCOPE)
    print("\nReal sale / pricing / hosting / asymmetric signing = human gate — not done here.")


if __name__ == "__main__":
    main()
