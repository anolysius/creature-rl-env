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
across structurally distinct collection-RPGs under an environment-level held-out split.
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
(Section 5), so one policy can act on all of them.

**Verifiable rewards (RLVR).** The episode goal is a chain of **boolean-verifiable
subgoals** — catch ≥ C creatures, evolve ≥ 1, defeat gym[k] for k = 1..N, terminal:
defeat the final boss — each a yes/no goal-state, never hand-tuned dense shaping. The
primary metric is subgoals completed (and steps-to-completion).

**Procedural generation + seed split.** A seed deterministically generates the region
(creature/gym placement, boss types) and a **per-seed hidden type chart**. `reset(seed)`
reproduces a region exactly. Train and held-out test seeds are **structurally disjoint**
(an offset guard prevents leakage), which is what makes generalization *measurable*.

**Throughput.** The core engine is numpy-only and vectorizable; measured throughput is
**~266k steps/s/core** (≈ 5× the 50k target) [run-derived; env-validation].

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

---

## 5. Genre generalization: an honest foundation (not yet the claim)

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
thresholds.

---

## 6. Related work

CritterGym is a **procedural-generalization** benchmark and should be compared to
**Procgen**, **Craftax**, and **XLand-MiniGrid**, not to Pokémon-playing agents:

- **Procgen** randomizes level *layout* and splits train/test. CritterGym randomizes rule
  *values* (the hidden type chart) on top of layout — one notch beyond layout-only.
- **Craftax** emphasizes speed (JAX) and open-ended achievements; its lesson — *throughput
  is the adoption gate* — directly informs our numpy-first → JAX-port roadmap.
- **XLand-MiniGrid** targets meta-RL across task distributions; CritterGym's env-family
  split targets the related but distinct *genre*-level transfer.

Pokémon-RL is a metaphor, not a peer: we traded its difficulty for measurability.

---

## 7. Honest limitations

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

## 8. Conclusion

CritterGym is an instrument for *measuring* agency and generalization, built on verifiable
rewards and a procgen seed split. We show that rule inference is provably load-bearing
under a team-commit economy, that a learned policy acquires it, and that an env-family
abstraction begins to measure genre-level transfer with honest, skill-structural signals.
We are explicit about what is proven (instance generalization, load-bearing inference) and
what is a foundation (genre generalization). The next steps are scaling difficulty while
keeping the seed split (so instance generalization becomes "hard-and-gap≈0"), adding more
structurally distinct families with a learned policy on a held-out family, and a JAX port
for throughput.

---

*All figures and their sources are listed in `docs/paper/README.md`. Honesty over headline
is a deliberate property of this project: we would rather report a foundation than overclaim
a proof.*
