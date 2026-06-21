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
| Generalization (procgen) | ❌       | ✅              | ✅      | ◐       | ✅             |
| Strategic/adversarial | ◐ (battles) | ❌              | ❌      | ◐       | ✅ (type meta) |
| Verifiable subgoals   | shaped/brittle | ◐           | ❌      | ❌      | ✅ (RLVR)      |
| Memory / inventory mgmt | ✅        | ✅              | ❌      | ✅      | ✅             |
| Fast / vectorizable   | ❌ (emulator) | ✅ (JAX)       | ✅      | ◐       | ✅ (target)    |

The thesis: the **creature-collection loop** (explore → catch → build a team → evolve →
defeat escalating bosses) *naturally* produces long-horizon planning, resource/inventory
management, memory, and **strategic** decision-making (team composition vs. a type meta) —
the exact bundle frontier labs want, but with the procedural-generation knob that lets you
split train vs. held-out test seeds and **actually measure generalization**.

---

## 3. Environment spec (proposed)

### 3.1 World & procedural generation
- A seed → a **region**: tile map (grid), biomes, wild-creature spawn tables, item placements,
  and a sequence of **N gyms/bosses** with escalating difficulty.
- **Type system** is also (partially) procedural: a randomized but *internally consistent*
  rock-paper-scissors matrix over K elemental types per seed. → prevents memorizing a fixed
  type chart; forces the agent to **infer the meta** from experience.
- **Train seeds** vs **held-out test seeds**: the generalization benchmark. Report train and
  test scores separately (Procgen convention).

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

*Prior art referenced: Pokémon Red RL (arXiv 2502.19920; PWhiddy/PokemonRedExperiments),
Crafter (danijar/crafter), Craftax (arXiv 2402.16801), Procgen (arXiv 1912.01588),
NetHack Learning Environment (nethackchallenge.com). Market context: Anthropic as largest
RL-env buyer (epoch.ai), broad commoditizing vendor pool (SemiAnalysis), General Intuition
$134M seed → ~$2B raise talks for game-clip agent training.*
