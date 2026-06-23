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
  PPO on train families {critter, forage} (one family per episode; obs-identical — `duel` is excluded since
  its charge keys break a single net) and evaluates transfer to the **unseen family `muster`**. An initial
  run (PPO 50k, N=16/16) gives **held-in 2.94 ±2.02 vs held-out-family 0.38 ±0.70, transfer gap +2.56** — the
  learned policy does **not** transfer to the unseen family's mechanic (a gap far beyond std). This is the
  honest result: **learned genre transfer is hard and (B) remains open** — one train-set → one held-out
  family is a first measurement, not a proof. (Closing this gap — train a policy that *does* transfer to an
  unseen family — is the M5 / moat-layer-2 work.) *(Caveats kept
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
(PPO 40k/point, N=16/16) lands every point's gap **within its per-seed std** — including the hardest point
(d2: held-out 0.94 ±1.64, gap +0.06) — i.e. generalization is consistent with gap≈0 even at higher
intensity, for a *learned* policy. Caveats kept honest: a single run, a low training budget (absolute
performance has headroom), and large std → a **signal**, not a tuned number.

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
