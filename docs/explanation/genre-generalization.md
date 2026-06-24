# Genre (environment-level) generalization — what (B) measures, and where it stands

> **Type:** explanation (Diátaxis — understanding-oriented). The *why* behind DESIGN §3.1.1 (B).
> **Scope SSOT:** `DESIGN.md` §3.1.1 (honest scope) · §9 (moat). **Code:** `src/critter_gym/env_family.py`,
> `src/critter_gym/genre_generalization.py`, `scripts/genre_learned_transfer.py`. This document is the
> living academic narrative of the genre-generalization thread; the per-task history lives in the
> CHANGELOG and archived reports.

---

## 1. Where this sits — CritterGym is a *measuring instrument*, not a game

CritterGym's purpose is to **measure agent capability** (long-horizon agency, strategic reasoning,
generalization) reproducibly — not to be entertaining. Two design bets make it a credible instrument:

- **RLVR (verifiable rewards).** Reward is *verifiable boolean subgoal completion* (caught / evolved /
  gym-boss defeated), not hand-tuned dense shaping. Success is un-gameable and unambiguous.
- **Rule-level procedural generation + train/test seed split.** Where Procgen randomizes *layout*,
  CritterGym randomizes the *rule values themselves* (a per-seed hidden type chart). A fixed-ROM
  memorizer (the Pokémon-Red strategy) cannot win; the agent must *infer the rules online*. This is the
  "eval that doesn't rot" property — a fresh, never-seen world per evaluation.

Within this instrument, **(B) targets the hardest generalization layer: genre / environment-level
generalization** — generalizing across *structurally distinct rule systems*, not just unseen seeds.

## 2. The construct — three layers of RL generalization, and which one (B) attacks

RL generalization research stratifies roughly into:

| Layer | "Generalize to…" | Typical benchmark | In CritterGym |
|---|---|---|---|
| **Instance-level** | held-out *seeds/levels* of one generator | Procgen (train→test levels) | `generalization.py` (seed split) — done |
| **Combinatorial/systematic** | unseen *combinations* of known parts | gSCAN, some meta-RL | partial (hidden chart inference) |
| **Environment/genre-level** | structurally *different rule systems / mechanics* | rare (XLand approximates via task-distributions) | **(B) — this thread** |

The third layer is **out-of-distribution (OOD) *environment* generalization** (cross-MDP transfer): can a
*single learned policy* act competently in a game whose collection mechanic, battle system, and
progression structure it has **never trained on**? Most benchmarks do not target this; it is a frontier.

Two prerequisites had to be built before it could even be measured:

1. **Structurally-distinct env families.** `critter` (A, catch + type-matchup battles), `forage` (B,
   contact-collect), `duel` (C, type-agnostic stamina/commit RPS battle — a *different battle system*),
   `muster` (D, collection-gated battle power + strong bosses). "Structurally distinct, not a seed
   variant" is *proven*, not asserted: `trajectory_signature` shows the same seed + same actions yields a
   **different** trajectory across families.
2. **A shared obs/action contract.** A single policy net needs one interface. `env_family.conforms`
   enforces it; `obs-harmonization` unified the observation space across all four families (duel's extra
   "charge" keys are 0-masked on the others — `HARMONIZED_OBS_KEYS`), so duel could finally enter a
   single-net experiment.

## 3. The measurement design — family-level leave-one-out (LOO) transfer

The core paradigm lifts the supervised train/test gap up to a **distribution over environments**:

- Hold one family out as the **unseen environment**; train a single policy on the other N−1 families.
- **Transfer gap = held-in mean − held-out-family mean** (episode-return units).
- The held-out family is **never trained on — not one episode** (family-level split, stronger than a
  seed split). This is what makes it genuinely OOD.

A *small* gap is the hypothesis that the policy learned something that crosses mechanics; a *large* gap is
the honest "it overfit to the training mechanics" result. The gap is always **reported as a signal, never
frozen as a pass threshold** — consistent with CritterGym's "measure, don't headline" discipline.

## 4. The crux — why a small gap can be a *mirage* (the central methodological point)

A shrinking transfer gap has **two completely different causes**, and conflating them is the classic trap:

1. **Real transfer** — strong on held-out *and* held-in (both high). The thing we want.
2. **Generalist-mediocrity** — *weak on held-in itself*, so the gap is small because *both* are low.

Cause (2) is a well-known multi-task-RL phenomenon: **task interference / the "generalist tax" / negative
transfer.** One network, one budget, several distinct MDPs → gradient interference means each is mastered
*less*. Empirically: widened-train held-in fell from ≈2.94 (2-family, #26 baseline) to ≈1.7–2.0 (3-family).
So the apparent gap collapse toward zero was **substantially this confound, not transfer.**

Every layer of rigor we added exists to separate cause (1) from cause (2):

- **Always read the absolute columns**, not just the gap. A small/negative gap with low held-in is a red flag.
- **Multi-run + std-across-runs** (transfer-rigor). A single-seed gap of −0.25 turned out to be **noise**:
  across 5 seeds the muster fold is +0.22 ± 0.45 / +0.44 ± 0.72 — the run-std *exceeds* the gap, so the sign
  is unstable. This is exactly the Henderson et al. ("Deep RL that Matters") lesson — single-seed RL
  conclusions are unreliable.
- **Budget ladder** (transfer-capacity-budget). transfer-rigor's "compute is not the bottleneck" was an
  over-extrapolation from 50k→150k. Extending the **budget** to 250k keeps lifting held-in (2.07 → **2.44**,
  with *tightening* run-std), approaching the recovery bar — while a **bigger net robustly *hurts*** at the
  same budget (it underfits). So among the cheap levers, **budget is still working and capacity is ruled
  out**; the pre-registered verdict is **PARTIAL** (held-in <2.5), and at 250k the anchor fold shows held-in
  2.44 / held-out 2.49 / **gap ≈ 0** — the first point with non-mediocre held-in *and* a zero gap, an
  encouraging but single-config signal, not a claim.
- **Pre-registered decision rules** (transfer-rigor). The "signal / artifact / inconclusive" thresholds
  were fixed *before* seeing the data, to block post-hoc narrative bias (the RL analogue of p-hacking).
- **Intervention/ablation** (transfer-skill-policy). Directly test whether the confound is *removable*:
  can held-in be raised back up? Via compute (transfer-rigor: barely) or via policy/obs improvements
  (transfer-skill-policy: no — a bigger net + obs scaling *underfit* at this budget and *lowered* held-in
  on all four folds). A pilot first showed a *whole-obs* `VecNormalize` actively *hurts* (it corrupts the
  small categorical keys — `in_battle`, `local_patch`, type ids), so it was excluded and only the large
  continuous keys were scaled.

## 5. Where (B) stands — the honest result

> **(B) transfers within a mechanic neighborhood but fails across battle systems — a characterized,
> partial claim.** Early widened-train results looked like a shrinking gap, but that was largely
> multi-task interference lowering held-in (generalist-mediocrity), with single-seed noise on top. Two
> levers were then probed: capacity (a bigger net) is ruled out — it *underfits* and lowers held-in; but
> **budget recovers held-in** past the pre-registered 2.5 bar (plateauing ≈2.75 at 400k–500k, below #26's
> 2.94). At that *recovered* skill, the confound-reduced full-LOO gap (400k, 5 seeds) is sharp: held-out
> `critter` −1.08, `forage` −1.48, `muster` −0.12 (≤0 — transfer to these is fine), but **`duel` +1.73 ±
> 0.61** (robust). So a learned policy **generalizes within the collection + type-matchup neighborhood even
> at recovered skill, and robustly fails only to `duel`** — the one structurally distinct battle system.
> (B)'s open frontier is therefore *localized* to **cross-battle-system transfer**, not generalization in
> general. Caveats: negative gaps partly reflect held-out family difficulty asymmetry (not pure transfer);
> the clean signal is the duel failure (at recovered held-in, so not a confound); single config, N=16,
> deterministic bosses, held-in plateaus below #26.
>
> **Why duel, and is it reachable (duel-fewshot-adapt):** the duel RPS depends on the charge obs, which
> is *degenerate (≡0)* across the train families — a feature with no gradient is **unlearnable zero-shot**
> (the general principle: genre transfer is zero-shot-blocked when the novel mechanic rides on a
> training-degenerate obs dimension). Few-shot fine-tuning on duel is **SLOW** (0.65→1.45 only at ~100k;
> ≤50k within noise), i.e. duel's battle system is a *genuinely new skill learned largely from scratch*,
> not a quick transfer. So (B) is a **sharply characterized partial result** — zero-shot within the
> mechanic neighborhood, zero-shot-blocked (for a known reason) and only slowly adaptable across a novel
> battle system — not "open" and not "solved".

Why this is a *result*, not a *failure*, for a benchmark:

- A benchmark's contribution is not "our agent does X" but **"this capability is measured *this* way, and the
  current simple approaches stall *here*."** (Procgen's contribution was precisely showing the train→test
  gap, i.e. where PPO fails to generalize.)
- A **null result with two hypotheses closed** (compute; simple policy/obs tweaks don't lift cross-genre
  held-in) is reusable knowledge — it narrows the next researcher's search space.
- An instrument that **catches its own mirage** (distinguishing real transfer from generalist-mediocrity)
  is demonstrating the trustworthiness that is the whole point (DESIGN §9, moat layer 3 = trust).

## 6. Open questions — what an actual (B) *claim* would require

Status update (duel-fewshot-adapt, thread close): the duel frontier is now *characterized*, not just
located. **Zero-shot to duel is mechanism-blocked** — its RPS depends on the charge obs, which is
*degenerate (≡0)* across the train families (proven by a deterministic guard), so it carries no gradient
and is unlearnable zero-shot. **Few-shot adaptation is SLOW** — fine-tuning on held-out duel lifts it
only at ~100k steps (0.65→1.45; ≤50k is within noise), so duel's RPS is a *genuinely new skill learned
largely from scratch*, not a quick transfer. Remaining work, if pursued:

1. **Faster cross-battle-system adaptation** — meta-RL / a mechanic-general representation that makes the
   degenerate feature *usable* (e.g. training distributions where charge varies), so duel needs less than
   ~100k. Pure budget/capacity is exhausted; this needs an architecture or distribution change.
2. **Mechanic-general representation** — obs/network that encodes environment structure (a family/task
   embedding, structured features) so the policy can *condition* on the mechanic instead of averaging over
   it (cf. contextual MDPs / task-conditioned policies).
3. **Curriculum** — easy-family → hard-family ordering to mitigate interference.
4. **Meta-RL / fast adaptation** — measure *few-shot adaptation* to the held-out family rather than
   zero-shot transfer (the XLand-MiniGrid framing).
5. **Accept and package** — if these also stall, the honest deliverable is "(B): a rigorously characterized
   open problem," which is itself a legitimate benchmark contribution.

## References (internal)

- `DESIGN.md` §3.1.1 — measured scope, every result reflected here (sourced, no fabrication).
- `src/critter_gym/env_family.py` — shared contract + `HARMONIZED_OBS_KEYS` + family registry.
- `src/critter_gym/genre_generalization.py` — env-level LOO machinery + scripted reference policies.
- `scripts/genre_learned_transfer.py` — learned-policy transfer: `train_and_transfer{,_loo,_loo_multirun}`,
  `--runs N` (multi-run), `--improved` (policy/obs ablation knobs).
- `docs/explanation/competitive-analysis.md` — gap register (this thread is the "families + learned policy" row).
