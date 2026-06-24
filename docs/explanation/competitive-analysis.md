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
| Speed / throughput | numpy, **~266k steps/s/core (CPU)** [basis differs] | fast native [verify] | **JAX GPU, much faster** [verify] | **JAX GPU, fast** [verify] | moderate [verify] |
| Maturity / adoption | ❌ **0 — not yet released** | ✅ broad [verify] | ◐ growing [verify] | ◐ [verify] | ✅ established [verify] |
| Difficulty (absolute) | ❌ **toy** (gap≈0 on an easy env) | ◐ [verify] | ◐ [verify] | ◐ [verify] | ✅ very hard [verify] |

---

## 3. Honest tradeoffs (where we lose, stated first)

**Where peers are clearly ahead of us today:**

- **Speed (Craftax / XLand).** JAX-on-GPU benchmarks run vastly faster than our numpy CPU
  engine. Craftax's own lesson — *throughput is the adoption gate* — is a gap for us until a JAX
  port exists. (Note: our `~266k/s/core` is CPU-per-core and **not** directly comparable to a
  GPU figure; do not present them in the same unit.)
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
| "competitively fast" | numpy CPU engine; peers are JAX-GPU. **Partly de-risked** (`jax-hotpath-foundation`): overworld step ported to functional JAX, parity-proven, vmap **~186× numpy on CPU** (76.5M steps/s, single-run direction) — but **battle not yet ported** (port partial) | **finish JAX port of hot path** (battle → env integration → GPU bench) | throughput/adoption (Craftax lesson); §4 perf target; M4 |
| "a hard benchmark" | env is toy; gap≈0 on easy task | **scale difficulty while keeping the seed split** ("hard-and-gap≈0") | DESIGN §3.1.1 roadmap; meaningful (A) |
| "generalizes within the genre" | 4 families = foundation; no learned policy on held-out family | **more structurally-distinct families + a *learned* policy tested on an unseen family** | (B) claim; **M5** genre-generalization surface; moat layer 2 |
| "robust learnability result" | single-run, modest-N signal | **multi-run / multi-seed learnability + learning curves** | tightens (A); arXiv numbers |
| "an adopted standard" | not released; 0 users | **public OSS release + arXiv submission, then community use** | moat layer 3 (trust); M3-EC4/EC5 |
| "monetizable eval" | no private held-out eval product | **private held-out eval set / harder custom envs** | DESIGN §8 revenue; M5 |

**Reading this register:** the maintainer's plan — *functional readiness first, release last* — is
well-supported. The highest-leverage pre-release items are **difficulty scaling** and **family
breadth + a learned held-out-family result** (they convert our methodological differentiation into
defensible claims), with a **JAX port** as the adoption enabler. The comparison confirms we should
**not** release until at least difficulty + genre breadth move from "toy/foundation" toward "hard/claim".

---

*Sources for our figures: `docs/paper/critter-gym.md` + `docs/paper/README.md`; scope SSOT
`DESIGN.md` §3.1.1 and the moat self-assessment `DESIGN.md` §9. Peer facts marked [verify] are
unverified general knowledge pending primary-source checks.*
