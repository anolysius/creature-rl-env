# Competitive analysis — CritterGym vs OSS RL benchmarks (honest, gap-finder)

> **Purpose.** An honest comparison of CritterGym against open-source RL benchmarks, written
> *before* public release. It is deliberately a **gap-finder**: wherever we *cannot* honestly
> claim an advantage, that is a functional gap to prioritize (see the **Gap register** at the
> end). It is **not** a marketing piece — peer-superior axes are stated first and clearly.
>
> **Honesty caveats (read first).**
> - Our figures are grounded in code/measurements (sources: `docs/paper/README.md`, `DESIGN.md` §3.1.1).
> - **Peer facts come from general knowledge and may be outdated or wrong.** Anything not
>   well-established is marked **[verify]** and must be checked against primary sources before
>   any public release. Precise peer numbers (throughput, dates) are deliberately avoided.
> - **No head-to-head was run.** Cross-benchmark "speed/difficulty" rows are *qualitative* and
>   note the comparison basis; our `~266k steps/s/core` is **numpy on one CPU core**, not
>   comparable as a raw number to peers' **JAX-on-GPU** figures (different unit + hardware).

---

## 1. Peers compared

Per DESIGN §3.1.1 positioning, our honest peer set is the **procedural-generalization** family,
not Pokémon-playing agents:

- **Procgen** (OpenAI) — 16 procedurally-generated arcade games, train/test *level* split, fast
  native engine, short-horizon. Widely adopted for generalization research. [verify: details]
- **Crafter / Craftax** — open-ended 2D survival with an achievement tree; **Craftax** is a
  JAX reimplementation+extension that runs **orders of magnitude faster on GPU**. Medium horizon. [verify]
- **XLand-MiniGrid** — JAX gridworld for **meta-RL** over very large *rule-set/task* distributions;
  fast on GPU. [verify]
- **NetHack Learning Environment (NLE) / MiniHack** — an extremely deep, hard, partially-opaque
  roguelike; procedurally generated dungeons; long-horizon and notoriously difficult. [verify]

---

## 2. Capability matrix

`✅` strong · `◐` partial/foundation · `❌` absent/weak. Peer cells are qualitative **[verify]**.

| Axis | CritterGym (sourced) | Procgen | Craftax | XLand-MiniGrid | NetHack/NLE |
|---|---|---|---|---|---|
| Procgen + train/test split | ✅ randomizes **rule *values*** (per-seed hidden type chart), not just layout | ✅ layout [verify] | ✅ world [verify] | ✅ rule-sets [verify] | ◐ dungeons [verify] |
| "Eval that doesn't rot" (regenerable held-out, RLVR-verified) | ◐ **property** (DESIGN §9 layer 1); fresh world per eval | ◐ [verify] | ◐ [verify] | ◐ [verify] | ❌ one game [verify] |
| Long-horizon subgoal chain | ✅ catch→evolve→gyms→boss | ❌ short [verify] | ◐ medium [verify] | ◐ [verify] | ✅ very long [verify] |
| Strategic / online rule inference (infer-the-meta load-bearing) | ✅ **scripted gate proves it** (gates frozen ≥0.20/≥0.10) | ❌ [verify] | ❌ [verify] | ◐ meta-RL adaptation [verify] | ◐ implicit [verify] |
| Verifiable rewards (RLVR, boolean subgoals) | ✅ | ◐ shaped+sparse [verify] | ◐ achievements [verify] | ◐ [verify] | ◐ score [verify] |
| Genre / env-level generalization (env families) | ◐ **foundation (4 families, 3 axes)** — *not a proof* | ❌ [verify] | ❌ [verify] | ✅ task-dist (meta-RL) [verify] | ❌ [verify] |
| Speed / throughput | ✅ **JAX vmap: ~950M steps/s on GPU (T4, overworld; M4-EC3 met, 95× the ≥10M target)** / ~480M CPU; was numpy ~266k/s/core | fast native [verify] | **JAX GPU, much faster** [verify] | **JAX GPU, fast** [verify] | moderate [verify] |
| Maturity / adoption | ❌ **0 — not yet released** | ✅ broad [verify] | ◐ growing [verify] | ◐ [verify] | ✅ established [verify] |
| Difficulty (absolute) | ◐ **hard for current baselines, incl. a memory agent** (recurrent PPO 43% of oracle on a deep partial-obs config; was ❌toy) — not yet vs SOTA | ◐ [verify] | ◐ [verify] | ◐ [verify] | ✅ very hard [verify] |

---

## 3. Honest tradeoffs (where we lose, stated first)

**Where peers are clearly ahead of us today:**

- **Speed (Craftax / XLand) — largely closed.** This *was* our #1 gap (numpy CPU vs peers' JAX-GPU).
  It is now substantially closed: the hot path is ported to functional JAX (parity 0, 4/4 families) and
  **M4-EC3 is measured on GPU — ~950M steps/s vmap on a T4 (overworld), 95× the ≥10M target** (CPU vmap
  ~480M). Craftax's lesson (*throughput is the adoption gate*) is no longer a blocking gap. *Honest
  boundary: single run, free T4, overworld slice; a clean full-episode GPU figure on better hardware is
  a minor follow-up (CPU full-episode already clears the EC at ~22M/s). Peers' exact figures stay
  `[verify]`; we don't claim to out-run them, only that we are now in the same (GPU-vectorized) class.*
- **Maturity & adoption (Procgen, NetHack).** These are established, cited, and integrated into
  toolchains. CritterGym has **zero adoption** and is not even public yet. Adoption is the
  network-effect moat (DESIGN §9 layer 3) we have **not** earned.
- **Absolute difficulty (NetHack, Crafter).** NetHack is a brutal frontier; our env is currently
  *toy* (a ~0 generalization gap on an easy task predicts little about hard-task capability,
  per DESIGN §3.1.1).
- **Meta-RL task breadth (XLand-MiniGrid).** XLand spans enormous rule-set distributions; our
  genre work is **4 families** — a foundation, not breadth.

**Where we are genuinely differentiated (honestly scoped):**

- **Randomizing rule *values*, not just layout.** A per-seed *hidden* type chart sits one notch
  above layout-only procgen: the agent must *infer* rules online, and we **prove** that inference
  is load-bearing (scripted four-arm gate), not merely assert it.
- **Verifiable rewards (RLVR) + the "eval that doesn't rot" property.** A freshly generated,
  never-seen world per evaluation, verified by construction — un-gameable and regenerable
  (DESIGN §9 layer 1). This is a *property* we have; it is not yet a *realized* moat.
- **Env-family / genre-generalization *direction*.** An env-level held-out split across
  structurally distinct collection-RPGs is a direction most peers don't target — but for us it
  is a **foundation (not a proof)** today.

**Net:** our differentiation is real but mostly **methodological/prospective**; on the axes that
drive adoption *now* (speed, maturity, difficulty), peers lead. This is consistent with DESIGN
§9's self-assessment: *"one toy env, no adoption → the moat is prospective."*

---

## 4. Peer-fact verify-list (check before any public claim)

Do **not** publish these as fact until checked against primary sources (papers/repos):

- Procgen: exact game count, reward structure, license, throughput basis. [verify]
- Craftax/Crafter: throughput figures + hardware, achievement set, license, JAX claims. [verify]
- XLand-MiniGrid: task-distribution size, meta-RL framing, throughput, license. [verify]
- NetHack/NLE/MiniHack: difficulty/benchmark framing, procedural-generation details, license. [verify]
- Any "peer lacks X" claim (e.g. "no rule inference") — confirm before asserting a peer *weakness*.

---

## 5. Gap register (the gap-finder output → next functional work)

Each row: something we **cannot honestly claim today** → the **feature** that would close it →
the **milestone exit-criterion** it unblocks. This is the prioritization input for "functional
readiness before release."

| We can't yet claim… | because… | needed feature | unblocks |
|---|---|---|---|
| "competitively fast" | numpy CPU engine; peers are JAX-GPU. **Substantially de-risked + demonstrated** (`jax-hotpath-foundation` + `jax-battle-port` + `jax-env-integration` + `jax-rl-demo`): overworld, commit-mode battle, **and the composed full-episode env** (family A) ported to functional JAX, parity-proven (0 mismatch incl. full obs), vmap **~34–1047× numpy on CPU**; a **JAX-native A2C now actually trains** family A on CPU **in seconds** (learning curve rises; **~170× the existing numpy/sb3 path**; held-out gap ≈ 0) — not just "an RL loop *can* train on it" but a measured loop that *does* (single-run/CPU/A2C-lite signal). **All four families (A/B/C/D) now vectorize end-to-end** (`jax-family-integration` + `jax-duel-integration`: forage/muster/duel mirrored at 0 mismatch, incl. duel's type-agnostic RPS battle and its charge obs), with a tuned PPO baseline (`jax-ppo-tuned`). Remaining: **GPU measurement only** | **GPU bench** (`vectorized-bench`, M4-EC3) | throughput/adoption (Craftax lesson); §4 perf target; M4 |
| "a hard benchmark" | env is toy; gap≈0 on easy task. **Discrimination resolution widened** (`difficulty-dynamic-range`): a pilot falsified the "oracle ceiling" framing (oracle already clears ~all gyms; capability already separated ≈+1.0/gym; starter diversification is defeated by the tournament chart), so the confirmed lever was the score's **dynamic range** — fixing the gym count grows the scripted oracle−blind spread **+1.3 (3 gyms) → +4.9 (8)** with winnability preserved (0.88). This sharpens *capability discrimination*, **not** absolute hardness (making a learned policy unable to reach oracle is still open). **Headroom now measured (`jax-ppo-tuned`):** a tuned PPO baseline (GAE+clip, on-device JAX) reaches only **32%** of the scripted oracle on the default world and **15%** on the hard 8-gym config (held-out gym-clears; gap≈0 so it generalizes; ≥ A2C-lite) — and on the hard config sits *below* the non-reasoning `type_blind` arm, a clear capability ladder (oracle ≫ type_blind > PPO) with large measured headroom. So "hard-and-learnable" is now evidenced by a real RL baseline, not just scripted arms (single run / small net / CPU — a baseline, not a sweep). **Hard *even for a strong memory agent* (`memory-headroom`):** going deeper — a bigger map + longer horizon under the same 5×5 view (grid 16, 5 gyms, 420 steps; parity 0 re-established) — keeps the strongest agent we have (recurrent PPO) at **43% of oracle (2.01±1.05 / 4.69, 5 runs)** with the memoryless feedforward PPO at **11%**; the pre-registered `classify_headroom` (frac 0.75, frozen) returns **hard-and-learnable robust** (opt-bound 3.06 ≪ 3.52). So the env is **not toy for a memory agent**: there is a parity-proven config with large oracle headroom that a recurrent PPO does not close (it recovers a *smaller* share than at grid 10's 53%, with larger absolute headroom). | ~~stronger/multi-run baselines~~ ✅ (5-run robust, headroom survives feedforward scaling AND a recurrent PPO) → **deeper still / multi-type bosses + SOTA-class agents** to push absolute difficulty further | DESIGN §3.1.1; jax-throughput.md; meaningful (A) |
| "generalizes within the genre" | 4 families = foundation; no learned policy on held-out family | **more structurally-distinct families + a *learned* policy tested on an unseen family** | (B) claim; **M5** genre-generalization surface; moat layer 2 |
| "robust learnability result" | single-run, modest-N signal. **Hardened (`ppo-headroom-rigor` + `headroom-baseline-strength`):** the oracle headroom is now 5-run robust AND **survives a stronger baseline** — a capacity×budget sweep (width 64→256, depth 1→2, budget to ~20M steps) finds the *best* PPO plateaus at **41% (default) / 25% (hard)** of oracle, with depth and budget-beyond-~600-iters *not helping* (the bottleneck is not capacity/compute). So the headroom is **not a tiny-net artifact**. **Qualified (`recurrent-baseline`):** that "robust" was robust only to *feedforward* scaling — testing the recurrence axis it did not rule out, a recurrent (GRU) A2C under partial observability (5×5 view on grid 10) reaches **46% of oracle vs the feedforward's 18%** (robust memory effect; the GRU is *narrower*, so the gain is memory not capacity). So **much of the feedforward headroom was a no-memory limitation that recurrence recovers** — CritterGym's difficulty is substantially a *memory/partial-observability* challenge (it cleanly discriminates memory-capable agents), though recurrence still leaves headroom (46% < oracle). **Confirmed under PPO (`recurrent-ppo`):** the A2C memory effect was **not an algorithm artifact** — a recurrent GRU **PPO** (sequence-preserving env-axis minibatch + hidden replay, *correctness-gated* by deterministic replay-faithfulness + env-permutation-invariance tests) reaches **53% of oracle vs feedforward PPO's 24%** at Q1's *exact* `default` partial-obs config (robust, +0.56 > max std; recurrent net *narrower* so gain=memory). Recurrence still leaves headroom under PPO too (53% < oracle, far below 0.75·oracle so the headline headroom stands), and is robust across both A2C and PPO. **Still open:** oracle is a scripted proxy; 3-seed/CPU; one partial-obs config; deeper absolute difficulty (multi-type bosses / longer horizon) to test headroom against a *strong* memory agent | **deeper absolute difficulty** to test headroom against a strong *memory* agent (recurrence axis now settled for A2C+PPO) | tightens (A); arXiv numbers |
| "an adopted standard" | not released; 0 users | **public OSS release + arXiv submission, then community use** | moat layer 3 (trust); M3-EC4/EC5 |
| "monetizable eval" | no *hosted* product yet, but the **measurement foundation is built** (`sealed-eval-harness` → `llm-eval-adapter`/`-run`/`claude-cli-provider` → `stateful-llm-agent` → `render-obs-legibility`/`battle-legibility` → `inference-score-metric`): a contamination-proof sealed harness scores an **agentic LLM** end-to-end, with a single un-gameable KPI — `inference_score = (submission − type_blind)/(oracle − type_blind)` ∈ [0,1] (`0`=plays without the hidden chart, `1`=expert) — quantifying *in-context hidden-rule inference* on a never-seen world. **First probe** (claude-opus-4-8 via subscription Claude CLI, an inference-gated demonstrator config — oracle 3.00 / type_blind 0.00): **inference_score = 0.00** (it does not beat the chart-blind baseline). *Read honestly:* this is a **non-saturated, discriminating eval** signal (headroom on an unsolved capability — the property that makes an eval worth selling), **not** "frontier LLMs can't do it" — it is one **small** probe (2 worlds × 60 steps, single config, scripted-oracle proxy, single run) needing fuller measurement. Still missing for *monetization*: **server-side sealed infra + hosted eval-as-a-service + a private held-out set** (the in-process harness is a foundation, not the product); customers/pricing/release stay human-gated. | **hosted private held-out eval set** (server-side secret seeds + submission sandbox) / harder custom envs | DESIGN §8 revenue; M5 |

**Reading this register:** the maintainer's plan — *functional readiness first, release last* — is
well-supported. The highest-leverage pre-release items are **difficulty scaling** and **family
breadth + a learned held-out-family result** (they convert our methodological differentiation into
defensible claims), with a **JAX port** as the adoption enabler. The comparison confirms we should
**not** release until at least difficulty + genre breadth move from "toy/foundation" toward "hard/claim".

---

*Sources for our figures: `docs/paper/critter-gym.md` + `docs/paper/README.md`; scope SSOT
`DESIGN.md` §3.1.1 and the moat self-assessment `DESIGN.md` §9. Peer facts marked [verify] are
unverified general knowledge pending primary-source checks.*
