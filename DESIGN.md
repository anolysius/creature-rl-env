# CritterGym — Design Doc (v0.1, draft)

> A procedurally-generated **creature-collection RL environment** for benchmarking
> **long-horizon agency, strategic reasoning, and generalization** in a single world.
>
> Status: **Phase 0 — seeking feedback.** Nothing built yet. This doc exists to find out
> whether RL researchers would actually use it. Tear it apart.

---

## 1. TL;DR

Existing game-based RL benchmarks force a trade-off:

- **Pokémon Red** (PWhiddy, arXiv 2502.19920) — deep long-horizon, but a *single fixed ROM* →
  agents can memorize; you cannot measure **generalization**.
- **Crafter / Craftax** — broad-capability survival in one env, procedurally generated, fast (JAX),
  but **short-to-medium horizon** and no adversarial strategic layer.
- **Procgen** — gold standard for **generalization** via procedural generation, but each game is
  **short-horizon and shallow** (arcade-style).
- **NetHack (NLE)** — brutal long-horizon frontier (unsolved across 500k+ games), but enormous,
  opaque, and hard to shape.

**CritterGym** aims at the empty cell: **procedurally generated (→ generalization) +
long-horizon (tens of thousands of steps) + strategic adversarial play (type-matchup meta) +
verifiable subgoal rewards (RLVR-friendly)**, in one fast, headless, Gymnasium-compatible package.

One-line pitch: *"Procgen's generalization rigor × Pokémon's long horizon × Crafter's
one-env-many-skills × Craftax's JAX speed."*

---

## 2. The gap (why build this)

A frontier-agent benchmark ideally tests, **simultaneously and in one episode**:

| Capability            | Pokémon Red | Crafter/Craftax | Procgen | NetHack | **CritterGym** |
|-----------------------|:-----------:|:---------------:|:-------:|:-------:|:--------------:|
| Long horizon (10k+)   | ✅          | ◐ (med)         | ❌      | ✅      | ✅             |
| Generalization (procgen) | ❌       | ✅              | ✅      | ◐       | ✅ *(instance-level — §3.1.1)* |
| Strategic/adversarial | ◐ (battles) | ❌              | ❌      | ◐       | ✅ (type meta) |
| Verifiable subgoals   | shaped/brittle | ◐           | ❌      | ❌      | ✅ (RLVR)      |
| Memory / inventory mgmt | ✅        | ✅              | ❌      | ✅      | ✅             |
| Fast / vectorizable   | ❌ (emulator) | ✅ (JAX)       | ✅      | ◐       | ✅ (target)    |

The thesis: the **creature-collection loop** (explore → catch → build a team → evolve →
defeat escalating bosses) *naturally* produces long-horizon planning, resource/inventory
management, memory, and **strategic** decision-making (team composition vs. a type meta) —
the exact bundle frontier labs want, but with the procedural-generation knob that lets you
split train vs. held-out test seeds and **actually measure generalization** (instance-level
today; genre-level generalization is a deliberate roadmap target — see §3.1.1).

---

## 3. Environment spec (proposed)

### 3.1 World & procedural generation
- A seed → a **region**: tile map (grid), biomes, wild-creature spawn tables, item placements,
  and a sequence of **N gyms/bosses** with escalating difficulty.
- **Type system** is also (partially) procedural: a randomized but *internally consistent*
  rock-paper-scissors matrix over K elemental types per seed. → prevents memorizing a fixed
  type chart; forces the agent to **infer the meta** from experience.
- **Train seeds** vs **held-out test seeds**: the generalization benchmark. Report train and
  test scores separately (Procgen convention). **Scope caveat: this is *instance*-level
  generalization — see §3.1.1 before claiming "it generalizes".**

### 3.1.1 Generalization: the honest scope (read before claiming "it generalizes")

What the train/test **seed** split proves — and does *not* prove — stated plainly so we never overclaim:

- **(A) Instance generalization — what we measure today.** Held-out *seeds* vary the map layout and the
  type-chart *values*, but every seed shares one fixed **structure**: same obs/action space, same
  mechanics, same *form* of type chart. So "gap ≈ 0 across held-out seeds" proves the agent **didn't
  memorize specific maps/charts of this one generator** — a real result (most benchmarks fail even this)
  and a *necessary floor*. It sits one notch above Procgen (we randomize rule *values*, not just layout).
- **(B) Genre generalization — what we do NOT yet measure.** Working across *structurally distinct*
  collection-RPGs (different battle systems, collection/progression mechanics, rule *systems*) under an
  **environment-level** held-out split (train on env families {A,B,C} → test on an unseen family D).
  That is the claim that would justify "generalizes within the collection-RPG genre." *(This is also
  exactly why a CritterGym-trained agent can't play Pokémon: Pokémon is a held-out **environment** it
  has never seen — not a held-out seed.)* **Foundation in place (not yet the claim):** we now have an
  env-*family* abstraction (`critter_gym.env_family`, a shared obs/action contract + registry), **four**
  structurally-distinct families on three axes — family A (`CritterEnv`, action-collect + type-matchup
  battle), family B (`ForageEnv`, contact-collect, a *collection*-axis difference), family C (`DuelEnv`, a
  type-agnostic stamina/commit *battle-system* difference — no type chart, no switching), and family D
  (`MusterEnv`, collection-gated power — catching buffs the party and bosses are strong, a *progression*
  dependency: muster before you can win) — and env-level measurement (`critter_gym.genre_generalization`,
  leave-one-out train-families → unseen-family gap). This stands up the machinery end-to-end on **four**
  families — a *foundation*, **not** a genre-generalization proof: a credible claim still needs **many**
  structurally-distinct families. The measured gap is a *signal*, and its interpretation has a
  **policy-specific** discriminator: on held-out family B the minimal *collection* axis is forgiving (an
  A-tuned scripted policy transfers with gap≈0), whereas on held-out family C — whose *battle system* makes
  family A's type-inference skill useless — the **A-tuned policy fails to transfer (gap ≈ +3.9) while a
  C-appropriate policy transfers (gap ≈ +0.2)**, and on family D the **collect-first ("muster") skill is
  load-bearing**: a muster policy defeats bosses (gym-clear ≈ 1.4) while a rush policy that never collects
  floors (≈ 0.0), yet that same muster skill is **useless on family A** (where catching gives no buff, so
  muster ≤ rush — collecting only wastes steps). Those policy *contrasts* show families C and D have **skill-structural** env-level gaps (a
  wrong/absent skill, since each is winnable by the appropriate policy), not mere difficulty — the stronger
  structural axes family B lacked. Still a foundation, still not evidence of genre generalization across the
  *genre*. *(Family D uses stronger bosses — the calibration that makes mustering load-bearing, part of its
  identity — so its raw cross-family LOO mean gap is difficulty-confounded; the honest signal is the
  within-family policy contrast above, not the raw gap.)* **First *learned*-policy transfer measurement
  (genre-learned-transfer).** The contrasts above use *scripted* policies; a real (B) claim needs a *learned*
  policy that generalizes to an env family it never trained on. `scripts/genre_learned_transfer.py` trains
  PPO on train families {critter, forage} (one family per episode) and evaluates transfer to the **unseen family `muster`**. An initial
  run (PPO 50k, N=16/16) gives **held-in 2.94 ±2.02 vs held-out-family 0.38 ±0.70, transfer gap +2.56** — the
  learned policy does **not** transfer to the unseen family's mechanic (a gap far beyond std). This is the
  honest result: **learned genre transfer is hard and (B) remains open** — one train-set → one held-out
  family is a first measurement, not a proof. (Closing this gap — train a policy that *does* transfer to an
  unseen family — is the M5 / moat-layer-2 work.) **Obs harmonization (obs-harmonization task, an M5-enabler pursued before the M3 release ECs per the “functional-readiness-first” plan): all four families now share ONE observation space (`env_family.HARMONIZED_OBS_KEYS`; duel’s charge keys are 0-masked on the others), so `duel` — previously excluded from the single-net experiment because its charge keys forked the obs — is now includable. The widened-train-distribution transfer experiment (incl. duel + a mechanic-general policy) is the next task; this enabler only makes it constructible, it does not yet narrow the gap.)** **Widened-train LOO (genre-transfer-policy).** With the harmonized obs, a single PPO net was trained leave-one-out over all four families (the wider train distribution now includes duel) and transfer measured to each held-out family on the SAME gap metric as #26 (held-in − held-out family). Result (PPO 50k, N=16/16, single run): the unseen-`muster` gap narrows from #26's **+2.56** (2-family train) to **−0.25** (3-family train incl. duel); the other folds give `critter` −0.92, `forage` −1.48, `duel` +1.08 — the gaps collapse toward or below zero, a signal that a **wider train distribution helps unseen-family transfer**. **Honest caveat (read the absolute columns, not just the gap):** the widened-train *held-in* means also drop (≈2.94 → ≈1.1–2.0) — one net over three families at the same budget is a generalist-mediocre, so a narrower (or negative) gap partly reflects *uniformly modest skill across families*, NOT strong transfer; a negative gap (held-out > held-in) most likely means low absolute skill plus an easier held-out family, not super-transfer. So (B) moves from 'measured-as-open' (#26) toward 'a wider train set narrows the gap' (this task) — an encouraging signal, but a clean (B) claim still needs higher absolute skill + multi-run (single run / low budget / deterministic bosses here). **Multi-run robustness + budget (transfer-rigor).** #27's narrowed/negative gap was a single run; transfer-rigor repeats the widened-train LOO over **5 seeds** at two budgets (50k, 150k) and reports per-fold gap **mean ± std-across-runs** against a *pre-registered* decision rule (to avoid post-hoc narrative). Findings: (1) the gaps are **robustly much narrower than #26's +2.56** across all folds — that part holds. (2) But it is largely the **held-in drop**: widened held-in is ≈0.9–2.1 (≪ #26's 2.94); raising the budget 50k→150k lifts held-in only modestly (`muster` 1.73→2.07, still <2.5), so the generalist-mediocrity confound is *reduced, not removed* — absolute skill is bottlenecked by policy/obs/env, **not compute** (the single-seed pilot that showed *no* held-in rise was itself run-noise — the 5-run mean does rise, which is exactly why multi-run matters). (3) The specific #27 *negative* `muster` gap does **not** survive: across runs it is +0.22 ± 0.45 (50k) / +0.44 ± 0.72 (150k) — the run-std exceeds the gap, so by the pre-registered rule this fold is **inconclusive** (sign unstable); #27's −0.25 was run noise. (4) `duel` is robustly the *hardest* held-out family (gap +1.15 ± 0.11, std ≪ gap), `critter`/`forage` robustly negative. **Honest verdict:** a wider train set genuinely narrows the gap vs #26, but the narrowing is confounded by low absolute skill and the below-zero reading was noise — so (B) stays a *signal*, and a clean claim needs higher *absolute* skill (policy/obs improvements, not just compute or more seeds). **Policy/obs improvements (transfer-skill-policy).** That "needs higher absolute skill" claim was then tested directly: does improving the *policy/obs representation* raise widened held-in toward #26's ≈2.9? A pilot first showed a *whole-obs* `VecNormalize` **hurts** (it corrupts the small categorical keys — `in_battle`, `local_patch`, type ids), so it was rejected; the improved config is a bigger net (`net_arch=[256,256]`) + a *deterministic* scaling of only the large continuous keys (`player_hp`/`enemy_hp`/`player_level` ÷ their bound). Measured baseline-vs-improved, 5 seeds, 50k, per fold (held-in mean ± run-std): the improved config **does NOT raise held-in — it modestly LOWERS it** on all four folds (`muster` 1.73→1.15, `duel` 1.74→1.10, `critter` 0.86→0.65, `forage` 0.92→0.68; the drops mostly exceed the run-std), because a bigger net + rescaled inputs *underfit* at this small budget. **Honest negative:** neither more compute (transfer-rigor) nor these simple policy/obs levers lift widened held-in toward #26's single-family level, so the **generalist-mediocrity confound is stubborn** — (B) stays a *signal*, and removing the confound needs deeper work (architecture / curriculum / more capacity-with-budget, or accepting the env is genuinely hard to master across families at this scale), not the cheap levers. Per the pre-registered conditional, held-in did not rise so the confound-reduced gap re-measurement is not warranted. **Capacity × budget, scaled together (transfer-capacity-budget).** transfer-skill-policy raised the *net* but held the budget at 50k (so the big net underfit); transfer-rigor raised the *budget* only to 150k. The one untested cheap-ish point — scale **both** — was run as a 5-seed sweep on the `muster` anchor fold, against a pre-registered recovery threshold (held-in ≥ 2.5 ≈ #26 level). Result (held-in mean ± run-std): baseline-net @150k **2.07 ± 0.62** → baseline-net @250k **2.44 ± 0.35** → big-net[256,256] @250k **1.87 ± 0.39**. Two robust findings: (1) **budget keeps lifting held-in** (2.07→2.44, and the run-std *tightens*) — which **partly corrects transfer-rigor's "compute is not the bottleneck"**: that was an over-extrapolation from 50k→150k; out to 250k, budget is still clearly helping and approaches the recovery threshold. (2) **Capacity is NOT the lever — a bigger net robustly *hurts*** (1.87 < 2.44 at the same budget; it underfits / converges slower). The pre-registered verdict is **PARTIAL**: best held-in 2.44 clears the 2.07 budget-only ceiling but not the 2.5 recovery bar. Notably, at baseline-net @250k the fold shows held-in 2.44 / held-out 2.49 / gap **−0.05 ± 0.49** — the first point where held-in is **not** generalist-mediocre *and* the gap is ≈0, the most encouraging (B) signal so far. But it is a single fold, single config, with a large held-out std, and held-in is still <2.5, so it is **not** a claim. Per the pre-registered conditional, full-LOO confound-reduced gap re-measurement is **deferred** until held-in clears 2.5 — i.e. the honest next probe is *more budget* (with a diminishing-returns watch), not a bigger net. **The cheap/expensive boundary is therefore NOT closed: budget (cheap-ish) is still climbing toward recovery; capacity is ruled out as the lever.** **Budget recovery + confound-reduced gap (transfer-budget-recovery).** Pushing the baseline-net budget further (250k/400k/500k, 5 seeds) **recovers** widened held-in past the pre-registered 2.5 bar — it plateaus at **≈2.75** (400k≈500k; still below #26's 2.94 but clearly recovered, no longer generalist-mediocre). The single-seed pilot showing 1.4–2.2 was again noise — the *third* time multi-run corrected a single-seed read. With held-in thus recovered, the deferred **full-LOO confound-reduced gap** was re-measured at 400k (5 seeds) — the sharpest (B) result of the thread: held-out `critter` **−1.08**, `forage` **−1.48**, `muster` **−0.12** (≤0 — transfer to these three is fine; the policy does as well or better on the unseen family even at recovered skill), but `duel` **+1.73 ± 0.61** (robust, std ≪ gap). So (B) is **real but structurally bounded**: a learned policy generalizes *within* a mechanic neighborhood (collection + type-matchup variants) at recovered skill, but does **not** transfer to the one family with a structurally distinct battle system (`duel` — type-agnostic RPS/stamina vs the others' type-matchup). This *localizes* the open frontier to **cross-battle-system transfer**. Honest caveats: the negative gaps partly reflect held-out-family *difficulty asymmetry* (e.g. `forage` scores ≈4.0) not pure transfer quality — the clean signal is the **duel failure**, which sits at recovered held-in (2.65) so it is **not** generalist-mediocrity; single config, N=16, deterministic bosses, held-in plateaus at 2.75 < #26's 2.94. **Net: (B) moves from 'measured-as-open' to 'transfers within a mechanic neighborhood, fails across battle systems (duel)' — a characterized, partial, honest claim, not a blanket one.** **Zero-shot block mechanism + few-shot adaptation (duel-fewshot-adapt).** *Why* does duel fail? Its RPS depends on the `player_charge`/`enemy_charge` obs, but across the train families (critter/forage/muster) those keys are **constant 0 over a full rollout** (proven by a deterministic guard test) — a degenerate feature carries no gradient, so the charge mechanic is **unlearnable zero-shot**. General principle: *genre transfer is zero-shot-blocked when the novel mechanic depends on an obs dimension that is degenerate in the training distribution.* We then measured **few-shot adaptation** — fine-tuning the trained policy on held-out duel over an adapt-budget ladder (5 seeds; held-out eval seeds disjoint from fine-tune seeds): zero-shot **0.65 ± 0.20**, 25k 0.59, 50k 0.76, **100k 1.45 ± 0.48**. Pre-registered verdict **SLOW**: ≤50k does not clear z₀+σ₀ (within noise — the single-seed pilot's 50k≈1.6 was again noise, tempered by multi-run, the 4th such correction), but ~100k fine-tuning roughly doubles duel and clears it. So duel is **reachable by adaptation but only slowly** (~100k ≈ a large fraction of base training) — the RPS battle system is a *genuinely new skill learned largely from scratch*, not a quick transfer. **Net (B), thread close:** a learned policy transfers *zero-shot within the mechanic neighborhood*, is *zero-shot-blocked on a structurally novel battle system* (duel) for a characterizable reason (degenerate feature), and recovers duel *only with substantial fine-tuning* — few-shot, not instant. (B) is thus a sharply characterized partial result, not open and not solved. *(Caveats kept
  honest: a single N=12 held-out run of scripted reference policies — a signal, not a tuned number; and the
  duel boss plays a fixed deterministic pattern with charge exposed in obs, so the ≈4.3 win partly reflects
  opponent predictability, not duel skill alone. The skill-structural read still holds — the A-tuned policy
  has the same obs access and still floors ≈0.6.)*

**Positioning consequence.** Pokémon is a **plain-language metaphor** (creatures + type matchups + gyms →
the task is instantly legible), **not a competitive claim**. "We do what Pokémon-RL can't" overreaches:
we traded Pokémon's *difficulty* for *measurability*, and our headline mechanic (infer the hidden type
chart) is not even a Pokémon challenge (its chart is fixed and public). Benchmark us honestly against
**Procgen / Craftax / XLand-MiniGrid** (procedural-generalization peers), not against Pokémon.

**Roadmap consequence.** A credible generality claim requires (B): build **multiple structurally-distinct**
environments and split at the *environment* level — which is precisely the **M5 "custom/harder
environments"** surface. So custom environments are not merely a revenue add-on; they are the **test set
for the generality claim**. Until then, scale difficulty *while keeping the seed split*, so (A) becomes
"hard-and-gap≈0" rather than "toy-and-gap≈0" — a gap≈0 on a trivial env predicts little about capability.

*Toward "hard-and-gap≈0" (difficulty-generalization).* A pilot **falsified** a clean monotonic *scripted*
difficulty ladder: difficulty is multi-dimensional (a larger hidden chart raises *inference* difficulty
but makes *blind grinding easier*; boss stats are a cliff, not a gradient) and a scripted oracle caps at
~0.6 (3 starters vs 12 types). So we test the property the right way — with a **learned** policy, since a
scripted policy cannot memorize and its gap≈0 is trivial. `scripts/difficulty_generalization.py` trains PPO
on held-in seeds at several **difficulty points** (increasing knob intensity; *not* a calibrated ladder) and
reports the held-in vs held-out gap (held-in eval carved disjoint from learning seeds). An initial run
(PPO 40k/point, N=16/16, *single* run) landed every point's gap within its *per-seed* std — a weak signal
that, at that std/budget, could not tell a small real gap from zero.

*Multi-run rigor (difficulty-gap-rigor).* That weak signal was then upgraded the way (B)'s `transfer-rigor`
upgraded its single-seed reads: `--runs N` reports the gap **mean ± std-ACROSS-runs** (the run-to-run
variability of the gap point estimate — the quantity that decides whether a gap is real, not the within-run
per-seed std), at a **higher budget** (100k), against a **pre-registered** decision rule (`classify_gap`,
thresholds `floor=0.3`, `k=1.0`, frozen before the data). Result (PPO 100k, 5 runs, N=16/16): held-in is now
**well above the floor** (1.10 / 1.21 / 1.54 for d0/d1/d2 — the policy actually clears, so this is *not*
generalist-mediocrity), and every point's gap is `gap≈0-signal` (|gap| ≤ k·std-across-runs): d0 −0.225 ±0.350,
d1 −0.237 ±0.489, **d2 (12 types, strong bosses) −0.400 ±0.896** — and at d2 held-in *rises* to 1.54, i.e. the
learned policy keeps generalizing (gap≈0) even at the hardest knob setting, now **robust across 5 runs**, not
single-run noise. **No `real-gap` emerges** — the current difficulty knobs do not make the env exhibit a
train→test generalization gap. *Honest caveats:* the gaps are weakly **negative** (held-out marginally easier =
difficulty *asymmetry*, not super-transfer) but sign-unstable within std; the **std-across-runs grows with
difficulty** (0.35 → 0.49 → 0.90), so at the hardest point a small real gap still can't be pinned (it is
"robustly consistent with gap≈0", not "gap = 0 proven"); held-out ≈1.9/3 suggests the current knobs may not be
**hard enough to discriminate capability**. **So the open part of "hard-and-gap≈0" is now the *hard* side, not
the *gap* side:** gap≈0 holds robustly at a capable skill level, but making the env genuinely discriminating
(structural difficulty a learned policy can't easily solve — e.g. raising the scripted-oracle ceiling / deeper
inference load) is the next lever, and it would touch env mechanics (hence a JAX re-port; M4 is gated on spec
stability).

*Tuned-PPO headroom — the "hard" side, measured (jax-ppo-tuned).* The above used scripted arms and an A2C
*lite*; a proper **PPO** baseline (GAE(λ) + clipped surrogate + minibatch epochs, on-device JAX) now
quantifies how far a learned policy is from the scripted-oracle ceiling on **held-out** seeds, on the same
gym-clear yardstick (`scripts/ppo_baseline.py`, pre-registered rules). Measured (CPU, **5 runs**, 200 iters; `ppo-headroom-rigor`
hardened the single-run read with a pre-registered classifier frozen before the data — frac=0.75, k=1.0):
on the **default** commit world PPO clears **0.52 ± 0.06 of oracle's 1.84 gyms (28%)**; on the **hard** 8-gym
config **1.52 ± 0.28 of 7.28 (21%)** — with held-in≈held-out (gap≈0, generalizes) and PPO ≥ the A2C-lite at
equal budget (on the hard config A2C nearly collapses). The classifier finds the *optimistic* PPO bound
(mean+std = 0.58 / 1.80) still far below 0.75·oracle (1.38 / 5.46) on **both** configs → **`hard-and-learnable`,
robust across seeds** (not a lucky run). So the env is hard-and-learnable: a tuned baseline learns and
generalizes but reaches only **21–28% of the oracle**, and on the hard config even sits *below* the
non-reasoning `type_blind` arm (PPO 1.52 < 2.03) — a clear capability ladder (oracle 7.28 ≫ type_blind 2.03 >
PPO 1.52) the baseline can't climb. This is a *measured, multi-run-robust* large headroom (the "hard" side the
rigor thread left open), with honest caveats: a small MLP, CPU, 200 iters (more compute/tuning would raise PPO
— headroom is at *this* budget), the oracle is a scripted ceiling proxy, and robustness is 5 runs (not a large
sweep). Stronger baselines remain future work; the result is a baseline + a direction, not a closed claim.

*Discrimination resolution (difficulty-dynamic-range).* The first attempt at the *hard* side — diversifying the
starter party to "raise the oracle ceiling" — was **falsified by its pre-freeze pilot**, a useful negative
result worth recording: (1) winnability was never the cap (the scripted **oracle already clears ~all gyms
present**: ≈2.06 gym-clears at an episode mean of ≈2.0 gyms — the "~0.6" was a fraction of the *max* count of 3,
not of the gyms actually placed); (2) capability is **already discriminated** — scripted oracle vs `type_blind`
differ by ≈+1.0 gym-clear; (3) starter diversification does **not** help, because a single fixed champion
super-counters ≈half of a random *tournament* chart by chance, so widening the boss pool barely moves
`type_blind`; and (4) reducing type *recurrence* is forbidden — the per-seed chart is regenerated each seed, so
without in-episode recurrence inference becomes impossible and the moat collapses. The confirmed lever is
instead the score's **dynamic range**: with only ≈2 gyms/episode the oracle-vs-blind spread is compressed, so
raising and *fixing* the gym count widens it ~proportionally. Measured (scripted arms, held-out, gym-clear-only,
exact gym counts via the new `min_gyms` knob): the oracle−`type_blind` spread grows **+1.31 (3 gyms) → +2.56
(5) → +4.88 (8)** while the oracle still clears **0.88** of 8 gyms (winnability preserved at scale) — a
monotone, pre-registered "resolution-up" result (a *larger, finer score range for capability*, **not** a task a
learned policy can no longer solve — making PPO unable to reach oracle is deeper future work, explicitly out of
scope). On this config `infer ≈ oracle` (one sighting suffices), so the metric shows inference *suffices*, not
that it is solely load-bearing (that is the scripted gate's job, below). The redesign is **numpy-first**; the
JAX port (`jax_env`/`jax_train`, currently 3-gym hardcoded) is a deliberate follow-up once the spec is
validated (M4-R5). A learned-policy run at the wider range (PPO 60k, 3 runs, 8 gyms) keeps **gap≈0**
(held-in 1.67 vs held-out 1.85, gap −0.19 ±0.60 — `gap≈0-signal` by the pre-registered `classify_gap`), i.e.
the sharper resolution does **not** break generalization; note the learned policy (≈1.7/8) sits far below the
oracle (≈7/8), so the wider range exposes large capability headroom to discriminate. *(Caveat: single machine,
scripted resolution + a single learned config, N=16, multi-run — a signal, not a tuned number.)*

**Is infer-the-meta *load-bearing*? — yes, under the team-commit battle economy (scripted-arm proven).**
The hidden per-seed type chart is meant to force *online rule inference*. Depth alone (3 → 12 types, boss
types recurring within an episode) did **not** make inference load-bearing: a first pilot found that with
the M1 battle economy a "just attack / cycle the party" policy did as well as one that knew the chart —
faint-triggered *force-switch* let a multi-creature party brute-force the super-effective creature for
free, and switching cost a turn. The fix is the **team-commit** boss economy (`Battle(commit_mode=True)`,
env `CritterGym-commit-v0`): you commit **one champion** to a boss — no mid-battle switching, no
force-switch cycling, a fainted champion loses — with a higher super-effective multiplier and stronger
bosses so a wrong type pick is punished. This (a) removes the free brute force and (b) makes within-battle
probing structurally impossible, so cross-battle *inference* of the recurring boss types becomes the only
cheap route.

A scripted 4-arm gate (`tests/test_reasoning_gate.py`, numpy-only, 42 fixed held-out seeds) proves the
separation: **oracle 1.00 ≫ type_blind 0.52** (type knowledge is decisive) and **infer 0.84 > probe 0.47**
(an *inferring* policy that reuses recurring matchups beats a *probing* one that re-discovers each battle).

**Honest scope of the claim.** The scripted gate proves the *task structure* makes inference load-bearing —
a necessary precondition the M1 economy lacked. The *learnability* follow-up then asks whether a **learned**
policy acquires it: PPO trained on `CritterGym-commit-v0` (champion-select action UX, `scripts/learnability.py`)
is measured against the four reference arms (`critter_gym.learnability`). In an initial run it lands **well
above** the `type_blind`/`probe` floor and **at/above** the `infer` reference on held-out seeds — evidence a
learned agent does acquire effective champion selection, not blind play, and generalizes (held-out ≈ held-in,
no memorization). *Metric precision (learnability-precision):* the original return conflated gym-defeats with
evolution reward, so we now also report a **gym-clear-only** metric (bosses defeated, evolution excluded) that
decouples the streams — a learned policy can no longer appear to out-score `oracle` merely by evolving more.
On the clean metric the load-bearing ordering holds (`oracle ≥ infer ≫ type_blind > probe`). Caveats kept
honest and now stated precisely: (i) the gym-clear-only count is **bounded by `num_gyms`** (e.g. oracle ≈ 4.2/8
held-out), so it trades evolution-inflation for a ceiling that compresses gaps between strong arms; (ii)
`oracle == infer` on this config (gym types recur enough that one sighting suffices), so the metric **cannot by
itself separate inference from perfect knowledge** — it shows inference *suffices*, not that inference alone is
load-bearing (that is the scripted gate's job); (iii) it remains a single config with modest eval N — the
`scripts/learnability.py --runs N` option averages several PPO seeds to bound training variance, but that path
is `[rl]`/non-CI. So we report a **positive learnability signal**, not a tuned headline number. Honesty here
matters more than the headline.

### 3.2 Observation space
- **v1: structured/symbolic** (NOT pixels first): agent position, local tile patch, party
  (each creature: type, level, HP, moves), bag/items, current objective flags, partial map memory.
  Rationale: lets researchers isolate *decision-making* from *perception*; faster; smaller nets.
- **v2 (optional): pixel/tile-render channel** for vision-RL folks.

### 3.3 Action space
- Discrete: `MOVE{N,S,E,W}`, `INTERACT`, `CATCH`, `USE_ITEM(i)`, `SWITCH_CREATURE(i)`,
  `BATTLE_MOVE(j)`, `EVOLVE(i)`, `NOOP`. (Battle is a turn-based sub-MDP.)

### 3.4 Creatures / evolution / battle
- Each creature: type(s), base stats, a small move set, an **evolution threshold** (level or
  item-gated). Evolution = a deliberate long-horizon investment decision (when to evolve,
  which creature to invest in).
- Battle: turn-based, type-matchup damage, switching, items. Boss/gym fights are gated checkpoints.

### 3.5 The task & **verifiable rewards (RLVR)**
The episode goal is a chain of **boolean-verifiable subgoals**, not hand-tuned dense shaping:
1. `caught >= C` distinct creatures
2. `evolved >= 1`
3. `defeated gym[k]` for k = 1..N (escalating)
4. terminal: `defeated final boss` within step budget

Primary metric = **subgoals completed** (and steps-to-completion). This keeps rewards
*verifiable* (did the goal-state occur? yes/no) rather than brittle reward-shaping — the
property labs care about for RLVR-style training.

### 3.6 Difficulty / curriculum knobs
- region size, # gyms, type-chart complexity (K), spawn sparsity, step budget. → enables a
  difficulty ladder and curriculum research.

---

## 4. Technical design

- **API: Gymnasium** (single-agent) — instant interoperability with the whole RL ecosystem.
  Consider **PettingZoo** later if battles become multi-agent.
- **Engine: start CPU/NumPy** for correctness and fast iteration → **port hot path to JAX**
  once the spec stabilizes. Craftax showed JAX gives ~250× speedups and ~1B steps/hr on a
  single GPU; **throughput is the real adoption gate.**
- **Determinism**: full seedability; `reset(seed)` reproduces a region exactly.
- **Vectorized**: N parallel envs out of the box.

**Performance targets (v1):** structured-obs, ≥ 50k steps/s/core CPU; JAX path ≥ 10M steps/s on
one consumer GPU.

*M4 progress (jax-hotpath-foundation, foundation/de-risk — see [explanation/jax-throughput.md](explanation/jax-throughput.md)):*
the **overworld** step is ported to a functional JAX form (`critter_gym.jax_overworld`), is **parity-proven
against the numpy env** (0 mismatch, same seed → same trajectory), and **vmap-vectorizes to ~186× numpy on
CPU** (numpy ~410k → jax-vmap 76.5M steps/s at batch 16384; single-run direction, not a tuned benchmark) —
already clearing the ≥10M GPU target on CPU. Honest boundary: **battle is not yet ported** (hot-path port is
*partial*; M4-EC1 foundation), and a *single* jit env is slower than numpy (the win is entirely from vmap
vectorization, not per-env speed). Next: `jax-battle-port` → env integration → GPU bench.

*M4 follow-on (jax-battle-port → jax-env-integration → jax-rl-demo):* the commit-mode champion battle and
the composed **full-episode env** are now ported too (`jax_battle` / `jax_env`, parity 0 mismatch incl. full
obs, vmap ≈34–1047×), and a **JAX-native A2C** (`jax_train`) now **actually trains** family A on CPU **in
seconds** — the learning curve rises (mean episode return ≈1.8 → ≈10.0) and training runs ≈170× the existing
numpy/sb3 path (on-device vmap; CPU, single run, A2C-lite — a signal, not a tuned PPO). The env is now
**config-driven** (`jax-difficulty-report`/R5): `make_jax_env(cfg)` re-establishes parity (0 mismatch) at the
higher-gym *dynamic-range* difficulty config (8 gyms), which now also trains under `vmap` (≈63× sb3 on that
config) — so the sharper-discrimination config is the fast-to-train one. The **non-commit full battle**
(party + switch/item/force-switch/party-wipe) is now ported too (`jax-battle-full`: `jax_battle_full`,
parity 0 mismatch vs `Battle(commit_mode=False)`, vmap ≈452× — completing battle-engine coverage), and is
now **wired into the full-episode env** (`jax-noncommit-env-integration`): `make_jax_env(JaxEnvConfig(commit=
False))` mirrors `CritterEnv(commit_battles=False)` — the env's **default** path — at parity 0 mismatch
(13 obs keys + reward + term + trunc, full episodes, four policies incl. a force-switch/party-wipe loss),
vmap ≈36–60× (CPU). So **both battle economies (commit & non-commit) now vectorize end-to-end**. Family
breadth followed (`jax-family-integration`): `make_jax_env(JaxEnvConfig(family=…))` mirrors **forage** (B,
contact-collect) and **muster** (D, catch-buffs-attack — the buff flows into battle damage and is wiped by
evolution, mirrored with a `party_atk_boost` accumulator) at parity 0 mismatch (24 tests), so **three of the
four families (A/B/D — the type-matchup-battle families) now vectorize**; family A stays byte-identical.
Finally **duel (C)** — the structurally distinct, type-AGNOSTIC RPS/stamina battle — is now ported too
(`jax-duel-integration`): `make_jax_env(JaxEnvConfig(family=duel, commit=False))` mirrors `DuelEnv` (ATTACK/
CHARGE/GUARD vs a deterministic boss, *simultaneous* damage, charge accumulation, a 40-turn stalemate cap)
at parity 0 mismatch (13 obs keys incl. the duel-only `player_charge`/`enemy_charge` + reward + term + trunc,
fixed & per-seed charts, incl. a scripted-optimal policy that wins → evolves), vmap ≈40–83× (CPU). So **all
four families (A/B/C/D) now vectorize end-to-end** — full family breadth on one JAX engine. Remaining for a
full M4: GPU measurement (M4-EC3).

---

## 5. Benchmark & baselines (what ships with the paper)
- Baselines: random, scripted heuristic, PPO, (stretch) a recurrent/transformer agent.
- Report **train vs held-out test** subgoal completion + steps-to-goal.
- Public **leaderboard** + reproducible configs.

---

## 6. Roadmap
- **Phase 0 (now):** this doc → share with RL community → collect "would you use it?" signal.
- **Phase 1 (4–6 wks):** dumbest-possible playable env (10×10, 3 creatures, catch-only reward)
  → grow to full subgoal chain + procgen.
- **Phase 2 (2–4 wks):** baselines + leaderboard + short arXiv writeup; open-source (MIT);
  list on Prime Intellect Environments Hub.
- **Phase 3 (post-traction):** held-out eval sets, custom envs, or fundraise / acqui-hire.

---

## 7. Open questions for the community (please poke here)
1. Is **procedural generalization in a long-horizon creature game** actually useful to you, or
   is Pokémon Red "enough"?
2. Structured obs first vs pixels first — which unlocks more research?
3. Is the **procedural type-chart** (infer-the-meta) a compelling novelty or a gimmick?
4. What would make you cite/use this over Crafter/Craftax for long-horizon work?
5. Right step-budget / difficulty for it to be *hard but not NetHack-impossible*?

---

## 8. Sustainability (brief, honest)
Env is **free + open-source** (credibility & adoption). Potential revenue *later*: private
held-out eval sets (un-gameable benchmarking for labs), commissioned custom/harder
environments, consulting. Or the benchmark's standing becomes a fundraising / acqui-hire story.
This is **not** a game-sales business — the customer is RL researchers and labs.

---

## 9. Moat — what's actually defensible (differentiation ≠ moat)

- **Differentiation** = why we're better *now*: long-horizon strategy + **infer-the-meta** (hidden
  per-seed rules) + verifiable generalization. Real, but these are **copyable ideas** — once published,
  a competitor reimplements them.
- **Moat** = why nobody catches up. It is **not** any single mechanic (procgen, train/test split,
  infer-the-meta are all table-stakes methodology). The moat is a *property* + *accumulation* + *trust*:

> **"The eval that doesn't rot."** Static benchmarks (MMLU, SWE-bench, a Pokémon ROM) leak into training
> data and saturate → they die. Ours mints a **freshly-generated, never-seen world per evaluation**
> (ultimately a never-seen *game*), **verified by construction (RLVR)** → **un-gameable and infinitely
> regenerable** as models improve.

Three compounding layers (only layer 1 exists today; 2–3 must be *earned*):

1. **Regenerable private held-out** — un-gameable *by construction* (can't train on a world that's
   minted at eval time). This is built into today's design — the hardest seed.
2. **A corpus of structurally-distinct, RLVR-verified, calibrated environments** — an *accumulation*
   moat (a competitor must rebuild the whole library + calibration to match). This is the
   **environment-level / genre generalization** surface (§3.1.1, M5) — the form that makes the moat
   matter at the level frontier labs care about.
3. **Standard / trust** — being *the* benchmark labs report on (network effect). Earned by being first,
   credible, and reproducible.

**Honest status:** today we have layer 1's *property* but not a *realized* moat (one toy env, no
adoption). The moat is prospective; the roadmap is the plan to earn layers 2–3. (This restates §8's
"scarce parts" as a defensibility argument, not just a revenue line.)

## 10. What you can do with CritterGym (use cases)

The product is a **measuring instrument**, not an agent. Jobs it is hired for:

**For frontier labs / agent builders** *(monetization surface — private held-out)*:
- **Prove generalization, not memorization.** Drop your trained agent → get train vs **held-out** score +
  the generalization gap. A small gap on a *freshly-minted* world is a trustworthy "it learned a skill"
  claim for a model card / paper (un-gameable, so the number can't be inflated by contamination).
- **Stress-test online rule-inference / adaptation.** The infer-the-meta mechanic = "dropped into a world
  with *unknown rules*, experiment, deduce them, exploit" — a clean proxy for agents that must adapt to
  novel tools / APIs / environments.
- **Capability diagnosis, not just a score.** RLVR boolean subgoals (explore / catch / team-build /
  type-meta / boss) expose *which* capability is missing (e.g., explores fine but can't infer the meta).
- *(roadmap, §3.1.1-B)* **Measure cross-*game* generality** — does your agent generalize to *games it
  never trained on*? The strongest generality signal, on a held-out **environment** split.

**For RL researchers** *(free OSS env — adoption surface)*:
- **A research sandbox** for long-horizon / meta-RL algorithms with a **built-in generalization metric**
  (train/test split) and verifiable rewards — fast & vectorizable (numpy → JAX).
- **Reproducible, seeded, pinned configs** → comparable results across papers.
- **Curriculum / sample-efficiency / scaling-of-generalization** studies via the difficulty knobs (§3.6).

**Reproduce the demo:** `pip install -e ".[rl,render]" && python scripts/killer_demo.py` → trains on
train seeds, drops the agent on an unseen held-out seed, records the boss-defeat GIF, and reports the
held-in vs held-out defeat rate (the generalization signal).

---

*Prior art referenced: Pokémon Red RL (arXiv 2502.19920; PWhiddy/PokemonRedExperiments),
Crafter (danijar/crafter), Craftax (arXiv 2402.16801), Procgen (arXiv 1912.01588),
NetHack Learning Environment (nethackchallenge.com). Market context: Anthropic as largest
RL-env buyer (epoch.ai), broad commoditizing vendor pool (SemiAnalysis), General Intuition
$134M seed → ~$2B raise talks for game-clip agent training.*
