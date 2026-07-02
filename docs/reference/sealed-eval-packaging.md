# Sealed eval packaging (buyer/seller) — reference

The M5-EC1 *sales surface* on top of the sealed held-out eval engine
(`critter_gym.eval_harness`). Where the engine seals, verifies, and scores in-process, this
layer (`critter_gym.eval_package`) makes an eval **distributable and its results non-forgeable**:
a signed manifest a seller hands a buyer, a commitment that catches a post-hoc eval swap, and a
signed certificate binding the contamination verdict + score.

> **Honest scope (prototype).** Signatures are **HMAC-SHA256 over a shared secret** — the
> verifier must hold the seller's key (think: a trusted leaderboard). A real hosted product needs
> **asymmetric** signing (buyer verifies without the secret) and **server-side** secret custody
> so the sealed seeds never ship. This layer demonstrates the packaging / commitment /
> tamper-evidence *flow* only. Real sale, pricing, hosting, and asymmetric signing are a
> **human gate** (DESIGN §8 · CLAUDE.md monetization honesty gate).

## Public API (`critter_gym.eval_package`)

| Symbol | Role |
|---|---|
| `sign_payload(payload, key) -> str` | HMAC-SHA256 hexdigest over a canonical (sorted-key) serialization. |
| `verify_signature(payload, sig, key) -> bool` | Constant-time (`hmac.compare_digest`) signature check. |
| `seed_commitment(sealed) -> str` | One-way sha256 over the sorted secret seeds + world config. Rug-pull guard; reveals no seeds. |
| `EvalManifest` | Distributable, **signed** description of a sealed eval. No secret seeds/offset. |
| `build_manifest(sealed, key, key_id) -> EvalManifest` | Seller builds + signs a buyer-facing manifest. |
| `verify_manifest(manifest, key) -> bool` | Tamper-evidence: any field change breaks the signature. |
| `manifest_self_check(manifest, train_seeds) -> bool` | Buyer pre-flight (manifest only, no secret): are all train seeds in the training region? |
| `SignedCertificate` | Signed result: contamination verdict + (clean only) RLVR scorecard. |
| `issue_certificate(submission, train_seeds, sealed, key, key_id) -> SignedCertificate` | Seller runs the guard, scores iff clean, signs. |
| `verify_certificate(cert, key, *, manifest=None) -> bool` | Signature check; with `manifest`, also binds the commitment. |
| `HONEST_SCOPE` | The prototype-limit note embedded in every manifest/certificate. |

## The four guarantees

1. **Contamination-proof** — a submission whose declared training seeds overlap the sealed block
   or sit in the held-out region gets `ok=False` and is **not scored**; the negative certificate
   is still signed (a non-forgeable "you contaminated" verdict).
2. **Tamper-evident** — flipping any field of a signed manifest or certificate breaks
   `verify_manifest` / `verify_certificate`.
3. **No secret leak** — the manifest carries a one-way commitment, never the secret seeds/offset;
   the commitment cannot be reversed to the seeds.
4. **Rug-pull bound** — the commitment binds seeds + world config, so a seller cannot swap the
   eval after issuing without the commitment (and thus the signature / manifest cross-check)
   failing.

## Demo

```bash
python scripts/package_sealed_eval.py   # seller -> buyer -> verify, clean + contaminated cases
```

Prints the signed manifest, the buyer self-check, a scored clean certificate, a not-scored
contaminated certificate (both signature-valid), a tamper check, and the honest-scope note.

## Follow-ups (human-gated)

- Asymmetric signing (Ed25519 via `cryptography`) so a buyer verifies without the seller's key.
- Server-side secret custody so the sealed seeds never ship.
- Real distribution / pricing / hosting.
