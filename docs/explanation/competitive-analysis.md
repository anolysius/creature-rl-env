# Competitive analysis — CritterGym vs OSS RL benchmarks (honest, gap-finder)

> **Purpose.** An honest comparison of CritterGym against open-source RL benchmarks, written
> *before* public release. It is deliberately a **gap-finder**: wherever we *cannot* honestly
> claim an advantage, that is a functional gap to prioritize (see the **Gap register** at the
> end). It is **not** a marketing piece — peer-superior axes are stated first and clearly.
>
> **Honesty caveats (read first).**
> - Our figures are grounded in code/measurements (sources: `docs/paper/README.md`, `DESIGN.md` §3.1.1).
> - **Peer facts were verified against primary sources on 2026-07-06** (official repos and
>   papers — see §4 for the verification record and per-claim sources). Peer numbers cited
>   here carry their measurement context (hardware, batch size) — they are *not* head-to-head
>   comparisons with our numbers (different units and hardware).
> - **No head-to-head was run.** Cross-benchmark "speed/difficulty" rows remain *qualitative*.

---

## 1. Peers compared

Per DESIGN §3.1.1 positioning, our honest peer set is the **procedural-generalization** family,
not Pokémon-playing agents:

- **Procgen** (OpenAI, NeurIPS'19 paper) — 16 procedurally-generated arcade games; the core
  protocol is a train/test *level* split (e.g., train on 500 levels, test on the full
  distribution). C++ native engine, thousands of steps/s per CPU core; short episodes
  (typical caps ~1000 steps); per-game hand-designed rewards (shaped+sparse mix). MIT.
  Broadly adopted (order of 10³ citations; NeurIPS 2020 competition).
- **Crafter / Craftax** — Crafter (MIT): open-ended 2D survival, 22 achievements (+small
  health-delta reward term). **Craftax** (MIT, ICML 2024 Spotlight): JAX
  reimplementation+extension, officially **257× (Classic) / 169×** faster than Crafter under
  PureJaxRL PPO (~406k / ~267k steps/s at 4096 parallel envs on an RTX 4090); pitches itself
  as **long-horizon** (up to 100k-step episodes, deep exploration/memory).
- **XLand-MiniGrid** (Apache-2.0) — JAX gridworld for **meta-RL** over large task/ruleset
  distributions (pre-sampled benchmarks up to **3M unique rulesets**); millions of steps/s
  simulation on GPU, training throughput ~1M steps/s on a single A100. **Task rules and goals
  are hidden from the agent** — discovery through interaction is its core design point.
- **NetHack Learning Environment (NLE) / MiniHack** (NGPL / Apache-2.0) — an extremely deep,
  hard roguelike; procedurally generated dungeons over a **fixed, publicly-documented
  rulebook** (the NetHack wiki); episodes run tens of thousands of turns. Still effectively
  unsolved in 2026 (best LLM agents ~1.5% game progression in BALROG). Fast *CPU* env
  (~14.4k steps/s) but not GPU/JAX-vectorized. Established (NeurIPS'20/'21, 483-team
  competition).

---

## 2. Capability matrix

`✅` strong · `◐` partial/foundation · `❌` absent/weak. Peer cells verified 2026-07-06 (§4).

| Axis | CritterGym (sourced) | Procgen | Craftax | XLand-MiniGrid | NetHack/NLE |
|---|---|---|---|---|---|
| Procgen + train/test split | ✅ randomizes **rule *values*** (per-seed hidden type chart), not just layout | ✅ layout/assets only (rules fixed) | ✅ world layout (core rule values fixed; per-episode potion-ID permutation only) | ✅ rulesets (up to 3M; **hidden** from agent) | ◐ dungeons (rulebook fixed & public) |
| "Eval that doesn't rot" (regenerable held-out, RLVR-verified) | ✅ **shipped**: sealed regenerable sets + seed commitments + signed certificates | ❌ (one-off private test envs in the 2020 competition; no ongoing offering) | ❌ | ❌ (benchmarks public on HF) | ❌ (one-off unseen seeds in the 2021 competition) |
| Long-horizon subgoal chain | ✅ catch→evolve→gyms→boss | ❌ short (~10³-step caps) | ◐ Crafter medium / **Craftax long** (up to 10⁵ steps) | ◐ | ✅ very long (10⁴–10⁵ turns) |
| Strategic / online rule inference (infer-the-meta load-bearing) | ✅ **scripted gate proves it** (gates frozen ≥0.20/≥0.10); parametric *values* estimated from in-episode damage feedback | ❌ (rules fixed) | ❌ (core rules fixed) | ✅ **hidden rules discovered through interaction** (rule-*structure* across meta-trials — a different axis, see §3) | ◐ implicit (rulebook public; discovery not measurable) |
| Verifiable rewards (RLVR, boolean subgoals) | ✅ | ❌ hand-designed per game | ◐ achievements (+health term) | ◐ | ◐ score |
| Genre / env-level generalization (env families) | ◐ **foundation (4 families, 3 axes)** — *not a proof* | ❌ | ❌ | ✅ task-dist (meta-RL) | ❌ |
| Speed / throughput | ✅ **JAX vmap: ~950M steps/s on GPU (T4, overworld; M4-EC3 met, 95× the ≥10M target)** / ~480M CPU | fast native CPU (10³/s/core) | **~406k steps/s** (RTX 4090, b4096) | ~10⁶ steps/s training (A100) | ~14.4k steps/s (CPU; not GPU-vectorized) |
| Maturity / adoption | ❌ **0 — not yet released** | ✅ broad (10³ citations) | ◐ growing (ICML'24 Spotlight, ~10² citations) | ◐ | ✅ established |
| Difficulty (absolute) | ◐ **hard for current baselines, incl. a memory agent** (recurrent PPO 43% of oracle on a deep partial-obs config) — not yet vs SOTA | ◐ | ◐ | ◐ | ✅ very hard (unsolved) |

> Peer throughput cells are the peers' own published figures on their own hardware — **not
> comparable as raw numbers** to ours (different envs, units, batch regimes, hardware).

---

## 3. Honest tradeoffs (where we lose, stated first)

**Where peers are clearly ahead of us today:**

- **Maturity & adoption (Procgen, NetHack).** These are established, cited, and integrated
  into toolchains. CritterGym has **zero adoption** and is not yet public. Adoption is the
  network-effect moat (DESIGN §9 layer 3) we have **not** earned.
- **Absolute difficulty (NetHack).** NetHack remains effectively unsolved in 2026 (best LLM
  agents ~1.5% progression); our env is hard for the agents we measured (recurrent PPO 43%
  of oracle) but is far shallower mechanically and unmeasured against SOTA-class agents.
- **Mechanical depth / richness (NetHack, Craftax).** Their worlds have orders of magnitude
  more mechanics; ours is deliberately minimal (measurability first). A reviewer can fairly
  call our *game* thin even where our *measurement* is sharp.
- **Meta-RL task breadth (XLand-MiniGrid).** XLand spans millions of rulesets; our genre
  work is **4 families** — a foundation, not breadth.

**Where we are genuinely differentiated (honestly scoped, post-verification):**

- **Randomizing rule *values*, with proof the inference is load-bearing.** vs Procgen/Craftax
  this is clean: their procgen covers layout/world (Craftax's per-episode potion-ID shuffle is
  the only rule-ish exception; core combat/crafting values are fixed), ours randomizes the
  combat chart per seed. vs **XLand-MiniGrid the distinction is an *axis*, not a *level*** —
  XLand agents also face hidden rules, discovered as discrete *structure* across meta-trial
  adaptation; CritterGym hides continuous mechanic *values* estimated from quantitative damage
  feedback within a single episode, and we **prove** the inference is load-bearing with a
  frozen scripted four-arm gate rather than asserting it. (Earlier drafts said "one notch
  above" the field here; for XLand that was an overstatement and is retired.)
- **The contamination-proof eval as a shipped product.** A regenerable sealed held-out set
  with seed commitments, signed manifests/certificates, seasonal public exam re-issue, and a
  forced self-reported community track. Verified across all four peers: **none ships an
  ongoing regenerable private-eval offering** (Procgen '20 and NetHack '21 used one-off
  private/unseen tests in competitions — events, not products). This is our cleanest
  differentiator, and it is *shipped*, not prospective.
- **Verifiable rewards (RLVR) + measurement discipline.** Boolean subgoals by construction,
  pre-registered decision rules, honest-falsify culture — peers' rewards are hand-designed
  (Procgen), achievement-based (Crafter), or score-based (NLE).
- **A fixed public rulebook can't measure rule *discovery*.** NetHack's rules are in every
  LLM's training data (BALROG shows models hold the wiki knowledge yet score ~1.5% — a
  *knowing-doing* gap). So NLE measures execution under complexity, powerfully — but not
  discovery-of-mechanics. Our per-seed hidden charts measure exactly that. (Honest boundary:
  contamination does **not** make NetHack easy or its evals invalid — do not overclaim.)

**Net:** our differentiation is real on two axes (value-level rule inference with proof;
sealed regenerable eval product) and the speed gap is closed; on adoption, absolute
difficulty, and mechanical depth, peers lead. Release converts the first two from "true"
to "usable".

---

## 4. Verification record (replaces the pre-release verify-list)

All peer claims above were checked against **primary sources** on **2026-07-06** by four
parallel research passes (one per peer), each returning per-claim verdicts + sources; wrong
or overstated claims were corrected in place (notably: XLand "one notch above" retired;
Craftax horizon corrected to long; NLE "moderate speed" corrected to "fast CPU, not
GPU-vectorized"; Procgen/NetHack one-off competition held-outs acknowledged).

Primary sources: Procgen [repo](https://github.com/openai/procgen) ·
[paper](https://arxiv.org/abs/1912.01588) — Crafter [repo](https://github.com/danijar/crafter)
· Craftax [repo](https://github.com/MichaelTMatthews/Craftax) ·
[paper](https://arxiv.org/abs/2402.16801) — XLand-MiniGrid
[repo](https://github.com/dunnolab/xland-minigrid) · [paper](https://arxiv.org/abs/2312.12044)
— NLE [repo](https://github.com/heiner/nle) · [paper](https://arxiv.org/abs/2006.13760) ·
[BALROG](https://arxiv.org/abs/2411.13543) · [NetHack Challenge
report](https://proceedings.mlr.press/v176/hambro22a/hambro22a.pdf).

**Release-policy checks (same date, primary documents):**

- **Publishing Claude benchmark results** — no restriction found in Anthropic's Consumer
  Terms (eff. 2025-10-08), Usage Policy (eff. 2025-09-15), Commercial Terms (eff.
  2025-06-17), or Claude Code legal docs (all fetched 2026-07-06); "benchmark"/"evaluation"
  do not appear as restricted activities. Publishing our measured scores with honest model
  labels is in bounds.
- **Batch eval via a personal subscription CLI** — GRAY: prohibitions target third parties
  routing *others'* traffic through subscription credentials; first-party scripted use of the
  official CLI is documented, but plan limits "assume ordinary, individual usage" and
  developer workloads are steered to API keys. Operational stance recorded in
  `docs/how-to`/runner docstrings already ("keep eval runs small; prefer the API for big
  runs"); final published headline numbers should prefer API-metered runs when practical.

---

## 5. Gap register (the gap-finder output → next functional work)

Each row: something we **cannot honestly claim today** → the **feature** that would close it →
the **milestone exit-criterion** it unblocks. This is the prioritization input for "functional
readiness before release."

| We can't yet claim… | because… | needed feature | unblocks |
|---|---|---|---|
| "an adopted standard" | not released; 0 users | **public OSS release, then community use** | moat layer 3 (trust); M3-EC5 |
| "hard for SOTA-class agents" | strongest measured agent = recurrent PPO (43% of oracle); NetHack-class depth absent | SOTA-agent measurements / deeper mechanics (multi-type bosses measured; stronger levers = human-gated design decisions) | Difficulty (absolute) ✅ 격상 |
| "generalizes within the genre" (learned) | 4 families = foundation; no learned policy on held-out family | **a *learned* policy tested on an unseen family** | (B) claim; moat layer 2 |
| "monetizable eval (hosted)" | sealed eval is in-process; no server-side custody/hosted service | hosted private held-out + submission sandbox (human-gated productization) | DESIGN §8 revenue; M5 |

(Resolved since the first draft of this document: competitive speed → JAX port + GPU
measurement done; "hard benchmark" → hard-for-memory-agent robust; measurement foundation →
sealed eval + inference band + arena instrument shipped. Full history: `docs/CHANGELOG.md`.)

---

*Sources for our figures: `docs/paper/critter-gym.md` + `docs/paper/README.md`; scope SSOT
`DESIGN.md` §3.1.1 and the moat self-assessment `DESIGN.md` §9. Peer facts: §4 verification
record (primary sources, 2026-07-06).*
