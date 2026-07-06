# CritterGym: A Procedurally-Generated Creature-Collection Benchmark for Measuring Long-Horizon Agency and Generalization

**Draft — arXiv writeup (M3-EC4).** This is a working draft, not a submission. Every
quantitative claim is traced to a source module/test in `docs/paper/README.md`. We
distinguish **CI-reproducible** figures (frozen by an assertion/gate in the test suite)
from **run-derived** figures (means from a particular run; the test freezes only a
threshold, not the exact value).

---

## Abstract

We present **CritterGym**, a procedurally-generated creature-collection reinforcement-
learning environment designed not as a game but as an **instrument for measuring agent
capability**: long-horizon planning, online rule inference, and generalization. The
creature-collection loop (explore → catch → build a team → evolve → defeat escalating
bosses) naturally produces the capability bundle frontier labs care about, while a
**procedural-generation knob with a train/test seed split** lets us *measure*
generalization rather than assert it. CritterGym contributes: (i) an environment whose
rewards are **verifiable** (RLVR — boolean subgoal completion, not hand-tuned dense
shaping); (ii) a battle economy under which **inferring a hidden, per-seed type chart is
provably load-bearing** (a scripted four-arm gate separates an *inferring* policy from a
*probing* one), and evidence that a **learned** policy acquires it; and (iii) an
**env-family abstraction** that begins to measure *genre*-level generalization — transfer
across structurally distinct collection-RPGs under an environment-level held-out split;
and (iv) a **contamination-proof sealed held-out eval** — a regenerable, un-memorizable
evaluation scored by verifiable subgoals with a *checkable* non-contamination guard — together
with an honest **frontier-LLM probe** whose iterative debugging is itself a case study in
eval validity: peeling back three stacked confounds (a rendering bug, a memory gap, and a
world-generation bug that did not guarantee an exploitable matchup) fixes the *measurement*, after
which a robust multi-run read of the frontier LLM is **inconclusive, near the chart-blind floor** —
a single run that looked like partial inference did not replicate. The eval is nonetheless validated:
a scripted inferrer robustly clears the band, so the model's near-floor result is a real signal, not
a harness artifact.
We are deliberate about scope: our instance-level generalization result is real and a
necessary floor, and our genre-generalization work is an honest **foundation**, not a
proof. We position CritterGym against procedural-generalization peers (Procgen, Craftax,
XLand-MiniGrid), and treat Pokémon strictly as a plain-language metaphor, not a
competitive claim.

---

## 1. Introduction and positioning

Benchmarks that measure *generalization* — not just performance on a fixed task — are
scarce. Fixed-ROM benchmarks (e.g. learning to play one game) cannot separate
memorization from capability, because there is only one instance. Procedural-generation
benchmarks (Procgen, Craftax, XLand-MiniGrid) fix this by randomizing instances and
splitting train/test, and CritterGym sits squarely in this family.

CritterGym's thesis is that the **creature-collection loop** packages several
capabilities researchers want — long-horizon planning, resource/inventory management,
memory, and **strategic** decision-making against a type meta — and that procedural
generation lets us split train vs. held-out test seeds and **actually measure
generalization**.

**On Pokémon.** Pokémon is used here only as a *plain-language metaphor* (creatures +
type matchups + gyms make the task instantly legible). It is **not** a competitive claim.
We traded Pokémon's open-ended *difficulty* for *measurability*; our headline mechanic
(infer a hidden type chart) is not even a Pokémon challenge (Pokémon's chart is fixed and
public). The honest comparison set is **Procgen / Craftax / XLand-MiniGrid**, not Pokémon.

---

## 2. Environment design

**Observation space (v1: structured/symbolic).** Agent position, a local tile patch,
party state (per creature: type, level, HP, moves), current objective flags, partial map
memory. Symbolic-first isolates *decision-making* from *perception* and keeps nets small.

**Action space.** `Discrete(6)`: `MOVE{N,S,E,W}`, `CATCH`, `NOOP`, reinterpreted inside a
turn-based battle sub-MDP. The same six-action interface is shared across every env family
(Section 6), so one policy can act on all of them.

**Verifiable rewards (RLVR).** The episode goal is a chain of **boolean-verifiable
subgoals** — catch ≥ C creatures, evolve ≥ 1, defeat gym[k] for k = 1..N, terminal:
defeat the final boss — each a yes/no goal-state, never hand-tuned dense shaping. The
primary metric is subgoals completed (and steps-to-completion).

**Procedural generation + seed split.** A seed deterministically generates the region
(creature/gym placement, boss types) and a **per-seed hidden type chart**. `reset(seed)`
reproduces a region exactly. Train and held-out test seeds are **structurally disjoint**
(an offset guard prevents leakage), which is what makes generalization *measurable*.

**Throughput.** The core engine is numpy-only (~266k–410k steps/s/core, ≈ 5–8× the 50k
target) and the hot path is additionally ported to functional JAX and parity-proven, giving
large `vmap` speedups on CPU — see Section 7 [run-derived].

---

## 3. Instance generalization (what we measure today)

Held-out *seeds* vary the map layout and the type-chart *values*, but every seed shares
one fixed **structure** (same obs/action space, same mechanics, same *form* of chart). So
"gap ≈ 0 across held-out seeds" proves the agent **did not memorize specific maps/charts
of this generator** — a real result (most benchmarks fail even this) and a *necessary
floor*. It sits one notch above Procgen: we randomize rule *values* (the chart), not just
layout.

A trained agent recorded on a **held-out seed** (a new map + new type chart it never saw)
defeats bosses at **45% (held-out)** vs **40% (held-in)** — an instance-generalization gap
≈ 0 [run-derived; killer-demo]. The absolute rate has clear headroom; the *claim* is the
near-zero gap (generalization, not memorization), not the magnitude.

---

## 4. Is rule inference load-bearing? Yes — and a learned policy acquires it

A hidden per-seed type chart is only meaningful if *inferring* it actually helps. Depth
alone did **not** make inference load-bearing: under the M1 battle economy, a "just attack
/ cycle the party" policy did as well as one that knew the chart — faint-triggered
force-switch let a multi-creature party brute-force the super-effective creature for free.

**The team-commit economy.** We introduce a boss economy (`CritterGym-commit-v0`,
`Battle(commit_mode=True)`) where you **commit one champion** to a boss — no mid-battle
switching, a fainted champion loses — with a higher super-effective multiplier and
stronger bosses. This (a) removes the free brute force and (b) makes within-battle probing
structurally impossible, so **cross-battle inference** of the recurring boss types becomes
the only cheap route.

**Scripted four-arm gate.** Over 42 fixed held-out seeds, a scripted gate
(`tests/test_reasoning_gate.py`) compares four arms. It **freezes (CI-reproducible)** two
gates: `oracle − type_blind ≥ 0.20` (type knowledge is decisive) and `infer − probe ≥
0.10` (an *inferring* policy that reuses recurring matchups beats a *probing* one that
re-discovers each battle). The **observed margins** are ≈ 0.48 and ≈ 0.36 respectively —
about 3× the asserted thresholds [run-derived means; the test freezes only the ≥0.20 /
≥0.10 gates]. This proves the *task structure* makes inference load-bearing — the
precondition the M1 economy lacked.

**Does a learned policy acquire it? (learnability).** We then ask whether a *learned*
policy acquires the skill. PPO trained on `CritterGym-commit-v0` is measured against the
four reference arms (`critter_gym.learnability`). To avoid a conflated metric (an episode's
return mixes gym-defeats with evolution reward, which can make a policy appear to exceed
even `oracle`), we report a **gym-clear-only** metric that separates the streams. On
held-out seeds the clean metric preserves the load-bearing ordering: **oracle/infer ≈ 4.19
≫ type_blind 1.81 > probe 1.06** [run-derived], and PPO lands at/above the `infer`
reference — a learned agent acquires effective champion selection, not blind play.

**Honest caveats (learnability).** (i) The gym-clear-only count is **bounded by num_gyms**,
so it trades evolution-inflation for a ceiling that compresses gaps between strong arms.
(ii) On this config **oracle == infer** (gym types recur often enough that one sighting
suffices), so the metric shows inference *suffices*, not that inference alone is
load-bearing — that is the scripted gate's job. (iii) Single config, modest eval N; the
`scripts/learnability.py --runs N` option averages PPO seeds to bound training variance,
but that path is non-CI. We report a **positive learnability signal**, not a tuned number.

**Hard *and* learnable: the oracle headroom (a tuned PPO baseline).** Beyond "a learned
policy acquires *effective selection*", we ask *how far a real RL baseline gets vs. the
scripted ceiling*. A tuned **PPO** (GAE(λ) + clipped surrogate + advantage normalization +
K-epoch minibatching, all on-device under `jit`+`vmap`; `critter_gym.jax_train.train_ppo`)
is evaluated on held-out seeds against the oracle on the *same* gym-clear metric
(`scripts/ppo_baseline.py`), with **pre-registered decision rules frozen before the data**
(R1 learns / R2 PPO ≥ A2C-lite / R3 PPO < 0.75·oracle ⇒ headroom). Measured **across 5 runs**
(`ppo-headroom-rigor`, a pre-registered classifier `critter_gym.headroom.classify_headroom`,
frac=0.75/k=1.0):

| config | PPO held-out gym-clears | oracle | type_blind | PPO / oracle | held-in − held-out |
|---|---|---|---|---|---|
| default (3 gyms) | 0.52 ± 0.06 | 1.84 | 0.59 | **28%** | +0.20 |
| hard (8 gyms) | 1.52 ± 0.28 | 7.28 | 2.03 | **21%** | +0.12 |

So PPO **learns** (R1), **beats A2C-lite** at equal budget (R2 — A2C nearly collapses on the
hard config), and **generalizes** (gap ≈ 0) — yet reaches only **21–28% of the scripted
oracle, robustly across 5 seeds** (R3: *hard-and-learnable*, the optimistic mean+std bound
stays far below 0.75·oracle on both configs). A striking honest data point: on the hard
config the tuned PPO (1.52) sits **below** the non-reasoning `type_blind` arm (2.03) — a clear
capability ladder (oracle 7.28 ≫ type_blind 2.03 > PPO 1.52) the current baseline can't climb.
*Honest scope: a tiny shared-trunk MLP, CPU, 200 iters (more compute/tuning would raise PPO —
the headroom is measured at this budget); the oracle is a scripted ceiling proxy; 5 runs, not
a large sweep.* This is the benchmark's results-table substance: a verifiably **hard-yet-
learnable** generalization task with a real RL baseline and large measured headroom.

---

## 5. The eval as a product: a contamination-proof sealed held-out, and a frontier-LLM probe

Section 4 measures *trained* policies. A second, complementary use of the same machinery is the
one frontier labs actually pay for: a **held-out evaluation that cannot be memorized, contaminated,
or gamed**. Because every world (map *and* hidden type chart) is regenerated from a seed, a fresh
never-seen instance can be produced per evaluation — the property a fixed-ROM benchmark structurally
cannot offer once it leaks into training corpora.

**Sealed held-out, with a contamination guard.** An evaluator constructs a `SealedEvalSet` from a
secret `master_seed`, which selects a *private* block of seeds inside the held-out region (seed ≥
`TEST_SEED_OFFSET` = 1,000,000); a different `master_seed` yields a fresh, disjoint block. A
submission is scored only on **verifiable subgoals** (gym-clears / catch / evolve — no hand-tuned
metric). Crucially, `verify_sealed` makes non-contamination *checkable*: it certifies that a
submitter's declared training seeds neither overlap the sealed block nor fall outside the train
region — i.e., "you could not have trained on this eval" is a verifiable property, not a promise.

**A single un-gameable KPI.** We summarize a submission with `inference_score = (submission −
type_blind) / (oracle − type_blind)`, clamped to [0,1]: `0` plays no better than a chart-*blind*
baseline, `1` matches a chart-*knowing* expert. It rises only by *inferring the hidden chart in
context on a never-seen world*, so it cannot be memorized or contaminated. Because a single read is
noisy, a **pre-registered classifier** (`classify_inference`, thresholds frozen before the data)
turns a multi-run set into a robust verdict (`infers` / `at-chart-blind-floor` / `inconclusive`).

**A frontier-LLM probe (honest, and instructive about eval design).** We drop a frontier LLM
(claude-opus-4-8) into the sealed worlds as an agentic submission — it reads a text rendering of the
observation and returns an action — on an inference-gated demonstrator config. The result is a
clean case study in *separating real capability limits from harness artifacts*:

- A first measurement read `inference_score = 0.00` (`at-chart-blind-floor`). Before drawing any
  capability conclusion, we audited the harness — and found the floor was **three stacked
  confounds**, the last of which lived in the eval's own world generation.
- A **rendering bug** mislabeled the observation map (environment creatures shown as wall glyphs,
  gyms shown as creatures, a real gym glyph never emitted). Only the LLM path consumed this
  rendering; scripted arms read the raw observation and were unaffected — which is exactly why the
  bug hid as "the LLM is bad" rather than "the map is wrong". Fixing it lifted an **engagement
  floor**: the agent now finds and enters gyms (battle moves per run rose ~4–13 → ~30–60).
- A second confound — the agent's memory discarded the per-move damage feedback that chart
  inference requires — was removed by giving it a battle-outcome memory (raw observed damage per
  enemy type, surfaced as facts, *no recommended move*). With both removed, the probe *still* read
  a super-effective-move rate near 0%, which we initially reported as a clean capability floor.
- A **third confound** was the decisive one, and it lived in the eval itself: the world generator
  did **not guarantee an exploitable matchup**. Its boss-placement filter admitted a boss type with
  *no* super-effective answer in the party (the per-seed chart can make a type beat all of the
  party's move types), so the *scripted oracle's* own super-effective-move rate collapsed from 100%
  to 5–23% as the world count grew. A "0% super-effective-move rate" therefore conflated two very
  different things — *the agent cannot infer the chart* and *no super-effective move existed to
  use*. We fixed the generator to guarantee, per world, at least one party move that is strictly
  super-effective against each placed boss (a procedural-correctness fix, not a battle-rule change).
- On the **validity-corrected** distribution, a *single-run* re-measurement of the frontier LLM read
  a super-effective-move rate of ≈50% (n = 8) — which looked like partial in-context inference. But
  a **robust multi-run probe did not confirm it**: three runs (n = 4) normalize to an SE-rate
  inference score of **0.10 ± 0.08 → `inconclusive`** (gym-based `inference_score` 0.04 ± 0.06, also
  inconclusive), with the LLM reading ≈14% super-effective — near the chart-blind floor, far below a
  scripted *inferring* arm (≈89%) and the oracle (100%). The single-run ≈50% did **not robustly
  replicate**; the current, honest read is *inconclusive, near the chart-blind floor*, not confirmed
  partial inference. (Caveat: the single run was n = 8 and the robust run n = 4 — different world
  counts, so different chart-blind floors, ≈27% vs ≈6%; an apples-to-apples n = 8 multi-run is
  follow-up work. The ≈50%↔≈14% gap nonetheless makes the single read look optimistic.)
- **The design is validated even though the prediction failed.** This is the robustness tooling
  catching an over-eager reading of one run — exactly its job. Critically, the eval *does* register
  inference when it is present: the scripted `infer` arm robustly reads ≈89% super-effective, cleanly
  separated from the floor. So the LLM's near-floor result is a **real signal about the model, not a
  harness artifact** — an eval whose anchors are validated yet keeps surprising the experimenter is
  behaving as an un-gameable eval should. The honest boundary that remains: with render and memory
  confounds removed and the matchup guaranteed, a residual *engagement/survival* confound (the agent
  logs few battle moves per episode) still separates "cannot infer" from "never sustains the
  inference loop" — a strong signal, not yet a clean verdict, and a reason for the n = 8 multi-run.

**Honest scope.** The current read is *inconclusive* (near the chart-blind floor), and even that is a
*signal, not a verdict*: one inference-gated band, few sealed worlds, a scripted-oracle/inferring-arm
proxy, a step cap of 40, and one model probed zero-shot — not a frontier-LLM ranking. The single-run
≈50% did not survive a three-run probe, so we report the robust `classify_inference` outcome
(`inconclusive`) rather than the optimistic single read, and flag an apples-to-apples n = 8 multi-run
as follow-up. The task is **hard, not impossible**: the scripted oracle clears it 100% and a scripted
inferrer reads ≈89% super-effective, so the band can express inference — the LLM simply does not yet
clear it. Three limitations are worth stating for eval
designers. (i) Under the current battle economy (minimum-1 attrition damage), the *gym-clear*
discriminating band is narrow — raise boss difficulty and even the oracle fails (it dies before it
can win), collapsing discrimination; lower it and a chart-blind agent attritions its way to a win.
The **super-effective-move rate** is the attrition-proof discriminator that survives this (oracle ≈
100% vs. chart-blind floor, with a battle-economy redesign for a broad, clean *difficulty curve* as
future work). (ii) That floor is itself **step-cap dependent** — the fixed-champion baseline reads
≈27% of super-effective moves at a 40-step cap but ≈7% at 200 (more steps accumulate more neutral
attrition moves), so a submission must be read against the band computed at the *same* cap (the
harness does this automatically). (iii) "Could not have trained on it" is enforced in-process here;
a deployed product needs server-side secret seeds and a submission sandbox. We report the mechanism
and an honest, evolving measurement, not a hosted service.

---

## 6. Genre generalization: an honest foundation (not yet the claim)

The harder claim is **genre** generalization: working across *structurally distinct*
collection-RPGs under an **environment-level** held-out split (train on env families
{A,B,C} → test on an unseen family D). This is exactly why a CritterGym-trained agent
cannot play Pokémon: Pokémon is a held-out *environment*, not a held-out seed.

**Env-family abstraction.** We formalize a shared obs/action contract (`Discrete(6)` +
required obs keys) and a family registry (`critter_gym.env_family`), so one
family-agnostic policy can be evaluated across families, and env-level transfer measured
by leave-one-out (`critter_gym.genre_generalization`).

**Four families on three structural axes:**

| Family | Mechanic | Structural axis |
|---|---|---|
| A `CritterEnv` | action-collect (`CATCH`) + type-matchup battle | (baseline) |
| B `ForageEnv` | contact-collect (step onto a creature) | **collection** |
| C `DuelEnv` | type-agnostic stamina/commit duel (no chart, no switching) | **battle system** |
| D `MusterEnv` | catching buffs party attack + strong bosses (muster before you win) | **progression** |

**Result: env-level gaps are policy-specific (skill-structural), not uniform difficulty.**

- *Family B is forgiving.* The minimal *collection*-axis change transfers with **gap ≈ 0**
  for an A-tuned policy — one collection mechanic is not a demanding axis.
- *Family C is skill-structural.* Its *battle system* makes family A's type-inference skill
  useless: an A-tuned policy **fails to transfer (gap ≈ +3.9)** while a C-appropriate policy
  transfers (**gap ≈ +0.2**) and wins the family (gym-clear ≈ 4.3) [run-derived]. The gap is
  a *wrong skill*, not raw difficulty. (Caveat: the duel boss plays a fixed deterministic
  pattern with charge exposed in obs, so the ≈4.3 win partly reflects opponent predictability,
  not duel skill alone; the skill-structural read still holds — the A-tuned policy has the
  same obs access and still floors.)
- *Family D is skill-structural on a different axis.* The collect-first ("muster") skill is
  **load-bearing on D** (muster policy gym-clear ≈ **1.42** ≫ rush policy **0.00**) yet
  **useless on A** (where catching gives no buff — muster ≤ rush; collecting only wastes
  steps) [run-derived; within-family contrast].

**Why the within-family contrast.** Family D uses stronger bosses (the calibration that
makes mustering load-bearing — part of its identity), so the *raw* cross-family leave-one-
out mean gap is **difficulty-confounded**. We therefore headline the **within-family
policy contrast** (same family config, vary only the policy), which holds difficulty
constant and isolates the skill. The raw cross-family mean is reported only as a secondary,
confounded signal.

**Honest scope.** This stands up the env-level measurement machinery end-to-end on **four**
families across three axes — a **foundation**, **not** a genre-generalization proof. A
credible genre claim needs **many** structurally distinct families and, ideally, a
*learned* policy tested on a held-out family. The measured gaps are *signals*, never pass
thresholds. *(All four families — including duel's structurally distinct battle system — are
also ported to the vectorized JAX engine at parity 0; see Section 7.)*

---

## 7. Throughput: a parity-proven JAX port

Throughput is the **adoption gate** for a procedural-generalization benchmark (the Craftax
lesson): researchers run billions of env steps and will not adopt a slow env. The numpy
engine (~266k–410k steps/s/core) is competitive per-core but cannot match peers' JAX-on-GPU
throughput, so the hot path is ported to **functional JAX** (`critter_gym.jax_env`). The
numpy env is OOP/mutable (Python dicts/sets, in-place mutation), so this is a *functional
rewrite* — world state becomes a flat array pytree and every branch becomes
`jnp.where`/`lax.cond` over arrays — done in **parity-gated stages** (overworld → battle →
composed env → families).

**Parity is the gate.** Each port reproduces the numpy env *exactly* (same seed + actions →
identical trajectory), protecting the non-negotiable seed→trajectory reproducibility. Parity
is **0 mismatch** on every observation key, reward, terminated, and truncated, across random
and scripted policies on fixed and per-seed charts (`tests/test_jax_*_parity.py`).

**Vectorization is the win, measured honestly.** The claim is not "JAX is fast" — a single
`jit` env is *slower* than numpy (per-call dispatch with nothing to amortize it). The gain is
entirely from `vmap` running thousands of envs in lock-step, and the benchmark always prints
all three rows (numpy / jax-single / jax-vmap) so the single-env regression is never hidden:

| surface | numpy (CPU) | jax vmap (CPU) | speedup |
|---|---|---|---|
| overworld step | ~410k/s | ~76.5M/s | ~186× |
| commit-mode battle step | ~112k/s | ~117M/s | ~1047× |
| non-commit full battle step | ~96k/s | ~43.5M/s | ~452× |
| full-episode env | ~130k/s | ~34–73× | 34–73× |
| duel (C) full-episode env | ~123k/s | ~5–10M/s | ~40–83× |

[run-derived; CPU, single run — a *direction*, not a tuned benchmark.] CPU `vmap` already
exceeds the ≥10M steps/s figure on the pure slices, though the EC is stated for GPU.

**All four families vectorize.** `make_jax_env(JaxEnvConfig(family=…))` mirrors critter (A),
forage (B), muster (D), and **duel (C)** — the type-agnostic RPS/stamina battle, which needed
a distinct battle branch (no type chart; simultaneous damage; charge state exposed in obs) —
each at parity 0. So the JAX engine covers the **full family breadth**, not just the baseline.

**It actually trains.** A JAX-native PPO (on-device `lax.scan` rollout + Adam under
`jit`+`vmap`) trains family A on CPU in seconds at **≈170× the existing numpy/sb3 path**; the
oracle-headroom table in Section 4 is produced on this loop.

**Honest boundary.** CPU, single-run directions; a single jit env is slower than numpy (the
win is batched `vmap`); the **≥10M steps/s GPU target (M4-EC3) is unmeasured** — the last open
M4 item. Reproduce the throughput table with `python scripts/reproduce_results.py`.

---

## 8. Related work

CritterGym is a **procedural-generalization** benchmark and should be compared to
**Procgen**, **Craftax**, and **XLand-MiniGrid**, not to Pokémon-playing agents:

- **Procgen** randomizes level *layout* and splits train/test. CritterGym randomizes rule
  *values* (the hidden type chart) on top of layout — one notch beyond layout-only.
- **Craftax** emphasizes speed (JAX) and open-ended achievements; its lesson — *throughput
  is the adoption gate* — directly informs our numpy-first → JAX-port roadmap.
- **XLand-MiniGrid** targets meta-RL across large ruleset distributions, and — like us —
  hides the rules from the agent. The distinction is an *axis*, not a level: XLand agents
  discover discrete rule *structure* across meta-trial adaptation, while CritterGym hides
  continuous mechanic *values* (the type chart) estimated from quantitative damage feedback
  within a single episode — and we verify the inference is load-bearing with a frozen
  scripted gate. Its env-family analogue also differs: our family split targets *genre*-level
  transfer.

Pokémon-RL is a metaphor, not a peer: we traded its difficulty for measurability.

---

## 9. Honest limitations

- **GPU throughput unmeasured.** The JAX port's CPU `vmap` already exceeds ≥10M steps/s on the
  pure slices, but the M4-EC3 target is stated for GPU and not yet measured; a single jit env
  is slower than numpy (the win is batched `vmap`, not per-env speed).
- **PPO headroom is a baseline, not a sweep.** The 21–28%-of-oracle headroom is a tiny MLP at
  200 iters on CPU over 5 runs — more compute/tuning would raise PPO; the oracle is a scripted
  ceiling proxy, not a true upper bound.
- **Genre generalization is a foundation, not a proof.** Four families across three axes
  demonstrate the env-level machinery and yield skill-structural signals (C, D), but a
  credible genre claim needs many more families and a learned policy on a held-out family.
- **Family D difficulty confound.** D's stronger bosses confound the raw cross-family mean;
  only the within-family policy contrast is honest. We report the contrast, not the raw gap.
- **Family C win partly reflects opponent predictability.** The duel boss plays a fixed
  deterministic pattern with charge exposed in obs, so the family-C ≈4.3 win is partly
  exploitation of a predictable opponent, not pure duel skill; the skill-structural *gap*
  (A-tuned floors with the same obs access) is the honest signal, not the absolute win rate.
- **Single-run, modest-N measurements.** The genre and learnability figures are single
  runs of scripted reference policies (or one PPO seed) over N ≈ 12–42 held-out seeds —
  *signals*, not tuned headline numbers.
- **Learnability metric bounds.** Gym-clear-only is bounded by num_gyms (ceiling
  compression) and cannot separate `oracle` from `infer` on the current config.
- **Absolute performance has headroom.** The instance-generalization demo defeats ~45% of
  held-out bosses; the *claim* is the near-zero gap, not the magnitude.
- **Reproducibility tiers.** We distinguish CI-frozen gates (e.g. the ≥0.20/≥0.10
  load-bearing gates) from run-derived means; only the former are reproduced by CI.

---

## 10. Conclusion

CritterGym is an instrument for *measuring* agency and generalization, built on verifiable
rewards and a procgen seed split. We show that rule inference is provably load-bearing
under a team-commit economy, that a learned policy acquires it, and that an env-family
abstraction begins to measure genre-level transfer with honest, skill-structural signals.
The hot path is **ported to functional JAX and parity-proven (0 mismatch)** for all four
families, vectorizing to ≈27–1047× numpy on CPU and training a JAX-native PPO in seconds —
turning "we *plan* to be fast" into a reproducible, parity-backed loop. That PPO baseline
also quantifies the **oracle headroom**: it reaches only 21–28% of the scripted ceiling
(5-run robust) while generalizing — the benchmark is **hard *and* learnable**. We are
explicit about what is proven (instance generalization, load-bearing inference, a fast
parity-proven engine) and what remains (a GPU throughput measurement; many more families and
a learned policy on a held-out family for a genre claim; deeper absolute difficulty).

---

*All figures and their sources are listed in `docs/paper/README.md`. Honesty over headline
is a deliberate property of this project: we would rather report a foundation than overclaim
a proof.*
