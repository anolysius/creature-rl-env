# JAX throughput — why we port the hot path, what we measure, where it stands

> **Type:** explanation (Diátaxis — understanding-oriented). The *why* behind DESIGN §4 (throughput)
> + milestones.md **M4**. **Scope SSOT:** `DESIGN.md` §4. **Code:** `src/critter_gym/jax_overworld.py`,
> `scripts/bench_throughput.py`, `tests/test_jax_parity.py`. This is the living narrative of the
> JAX-throughput thread; per-task history lives in the CHANGELOG and archived reports.

---

## 1. Why speed is a first-class requirement (not an optimization afterthought)

CritterGym is a *measuring instrument* for AI/RL researchers, not a game. For an instrument to be
*adopted*, it has to be **fast enough to train on**. This is the **Craftax lesson**: a procedurally
generated RL benchmark lives or dies on throughput, because researchers run billions of environment
steps and will not adopt a slow env no matter how clever its measurement design is. Our competitive
analysis names this as the #1 pre-release gap: peers (Procgen/Craftax/XLand) run on JAX-GPU at
≫1M steps/s, while our numpy CPU engine sits at ~266k–410k steps/s/core. **Speed is the adoption gate.**

There is also an internal multiplier: every RL experiment we run (the (B) transfer thread's
multi-run sweeps, the (A) difficulty-scaling work, learnability) is bottlenecked by env throughput.
A fast vectorized engine makes all downstream research cheaper, not just the public benchmark.

## 2. Why the numpy env can't just be `jit`-compiled

The numpy env (`critter_gym.envs.critter_env`) is OOP and mutable: world state lives in Python
containers (`self._creatures` is a `set`, `self._gym_tiles` a `dict`), and the transition uses Python
control flow (`if tile in self._creatures`, `for c in self._party`). `jax.jit` traces a *functional*
computation over arrays — it cannot compile Python dict lookups or in-place mutation. So a JAX port is
not a flag; it is a **functional rewrite**: world state becomes a flat array *pytree*, and every branch
becomes `jnp.where` / `lax.cond` / `lax.scan` over arrays.

Because that rewrite is substantial and branchy (especially the battle sub-MDP), we **de-risk in
stages** rather than porting everything at once.

## 3. The measurement design — parity-gated functional port, vectorization-first

- **Port one slice at a time, functionally.** State → a flat pytree (`OverworldState`); transition → a
  pure `(state, action) -> (state, reward, flag)` function. Procgen stays in numpy (it runs once per
  `reset`, not on the hot path); only the per-step transition is JAX.
- **Parity is the gate.** A port is only trustworthy if it reproduces the numpy env *exactly*. The
  parity test drives the **real** `CritterEnv`/`ForageEnv` and the JAX port from the same seed + same
  action sequence and asserts identical trajectories (position, caught, reward, battle-entry step). This
  protects the non-negotiable seed→trajectory reproducibility (north-star #3) across the port.
- **Vectorization is the win, measured honestly.** The throughput claim is *not* "JAX is fast." It is
  "JAX is fast *when vectorized*." A single env under `jit` is **slower** than numpy (per-call dispatch
  overhead with nothing to amortize it); the gain comes entirely from `vmap` running thousands of envs
  in lock-step. The benchmark always prints all three rows (numpy / jax-single / jax-vmap) so the
  single-env regression is visible, never hidden behind the vmap headline.

## 4. Where the thread stands — the honest result

> **Foundation de-risked: the overworld transition ports to functional JAX cleanly, reproduces the
> numpy env bit-for-bit, and vectorizes to ~186× numpy on CPU alone — but battle is not yet ported, so
> the hot-path port is partial.** The `jax-hotpath-foundation` task ported the *overworld* step (move +
> family-A `CATCH` / family-B contact-collect + battle-entry as a returned flag; battle itself
> excluded). Results (single machine, single run — a *direction*, not a tuned benchmark): jit compiles
> for both families; numpy↔JAX parity is **exact (0 mismatch)** against the real env; throughput —
> numpy ~410k steps/s, **jax single ~55k (0.13×, slower)**, jax **vmap 26.5M (b=1024) → 76.5M
> (b=16384) = up to 186× numpy**. CPU vmap already exceeds M4-EC3's ≥10M steps/s *GPU* target by ~7.6×
> (GPU itself is out of this foundation task's scope). So the core feasibility questions are answered
> **yes**: the env *can* be functionally ported and vectorized, with parity preserved.
>
> **Caveats (kept honest):** CPU-only, single run — a direction; GPU unmeasured. **Battle is not
> ported** — the hot-path port is therefore *partial* (M4-EC1 *foundation*, not complete); only the
> overworld is vectorized. The battle sub-MDP (`battle.py`: turn order, type chart, switching,
> commit-window, scripted opponent) is a branchy state machine and the harder port (estimated
> medium-high), needing `lax.cond`/`lax.scan` over fixed-length party arrays. The port uses int32
> counters (JAX x64 is off by default on Python 3.9); the env's value ranges fit int32, so this is
> correct, not a shortcut.

> **Update (jax-battle-port): the commit-mode champion battle is now ported too.** The battle sub-MDP's
> load-bearing path — the *commit-mode champion fight* the env uses for gym bosses (`commit_battles=True`,
> `CritterGym-commit-v0`; one committed champion vs one boss, no switching) — was ported functionally
> (`critter_gym.jax_battle`, `jax.lax.cond` for speed order + `jnp.where` for faint/terminal). Parity
> against the real `Battle(commit_mode=True)` is **exact (0 mismatch)** across 45 fixed-chart + 24 per-seed
> (`vary`) configs, including the integer damage formula and the `max(0, ·)` hp clamp — *a parity bug
> (unclamped negative hp) was caught by the pre-freeze pilot and fixed before implementation.* Throughput:
> numpy ~112k steps/s → **jax vmap ~117M (b=1024), 1047× numpy** (the battle step is pure arithmetic, so it
> vectorizes even better than the overworld). Still CPU/single-run, and the **full non-commit battle**
> (3-creature party + SWITCH + ITEM + force-switch + party-wipe) remains for the follow-up
> `jax-battle-full`. So overworld + commit-battle now cover *most* of the hot path's load-bearing surface.

> **Update (jax-env-integration): the overworld and commit-battle ports are now composed into a single
> full-episode vectorized env.** `critter_gym.jax_env` exposes `jax_env_step(state, action) -> (state,
> obs, reward, terminated, truncated)` — a `lax.cond` mode dispatch (overworld branch: move/catch/
> battle-entry; battle branch: commit-window cycle or one commit-mode turn, with gym-defeat, level-up,
> evolution) — so an RL loop can `vmap` thousands of full episodes. Parity against the real
> `CritterEnv(commit_battles=True)` (family A) is **exact (0 mismatch)** on **every obs key including the
> 5×5 egocentric `local_patch`, reward, terminated and truncated**, across random and gym-clearing
> policies on fixed and per-seed charts. Throughput: numpy ~130k steps/s → **jax vmap ~34× (b=1024) to
> ~73× (b=4096)** — lower than the pure slices because full-episode control flow diverges per env (some
> in battle, some in overworld), an honest cost of composition, but still a large win on the surface the
> RL loop actually consumes. *Three bugs were caught by layered verification before/at review: two by the
> pre-freeze pilot (a tracer-indexing error; champions wrongly attacking on NOOP/SWITCH), one latent
> variable-gym-count bug found in implementation (fixed with a `gym_active` mask), and one `truncated`-
> semantics gap (numpy computes terminated/truncated independently — both can be True) caught by the
> adversarial L3 reviewer. Multi-layer review caught edges a single pass would miss.* Remaining: families
> B/C/D, the full non-commit battle (`jax-battle-full`), and GPU measurement.

> **Update (jax-rl-demo): the vectorized env now actually trains a policy — fast, on CPU, in
> seconds.** The prior updates measured *step* throughput; this one closes M4 as a *demonstration*:
> a minimal **JAX-native** actor-critic (`critter_gym.jax_train`, A2C) whose policy, `lax.scan`
> rollout, advantage and Adam update all run **on-device under `jit` + `vmap`** trains family-A
> commit-mode in one run. (Wrapping the JAX env in an off-the-shelf sb3 loop would cross the
> host↔device boundary every step and lose the vmap win — hence a from-scratch loop; procgen `reset`
> stays numpy via a fixed *region bank* of training seeds, and episodes auto-reset to their own bank
> entry so the whole rollout is a single jitted scan.) **Pre-registered decision rule** (frozen
> before the data, to block post-hoc spin): branch *(a) "learns + fast"* iff the curve's late-window
> mean clears the early-window mean by more than the late-window noise (`mean_late − mean_early ≥
> std_late`), else *(b)* report throughput with learning as a partial signal. **Measured (CPU, single
> run — a signal, not a tuned benchmark):** the learning curve **rises (mean episode return ≈1.8 →
> ≈10.0**, rise 0.041 ≫ std_late 0.003) → **branch (a)**; training throughput **≈0.66M env-steps/s**
> (1.23M steps in ≈1.9s; a separate run saw ≈1.1M — single-run variance) vs the repo's existing
> numpy/sb3 path **≈3.8k env-steps/s** → **≈170× faster** (the win is on-device vmap lock-step,
> consistent with the step benchmark). A held-out-seed eval of the greedy policy gives **≈1.44 vs
> held-in ≈1.00** (seed split; gap ≈ 0, consistent with the (A) no-memorization story — a signal, not
> a tuned number). **Honest boundary:** A2C-lite (not a tuned PPO), CPU, single run; the metric is
> reward-per-step (a clean monotone proxy); the sb3 baseline is the *existing single-env* path (many
> parallel sb3 processes would narrow the ratio but stay below on-device vmap); GPU still unmeasured.
> So "fast enough to train on" is no longer a plan — it is a demonstrated, parity-backed loop.

> **Update (jax-difficulty-report / R5): the JAX env is now config-driven, so the higher-gym
> *dynamic-range* difficulty config trains under `vmap` too.** The port had baked the world's shape
> constants (grid, step budget, **max gym count**, boss stats) as module globals, so it could only run
> the default 3-gym world — not the `difficulty-dynamic-range` config (8 gyms) where capability
> discrimination is sharper. Those constants are now a `JaxEnvConfig` captured by `make_jax_env(cfg)`'s
> closures (JAX needs static shapes, so the config is compile-time, not a traced arg); the module-level
> `jax_env_step`/`jax_reset`/`encode_obs` are the **default-config instances**, so existing imports,
> parity tests and the benchmark are byte-for-byte unchanged. **Parity re-established at the high-gym
> config** (grid 6, **8 gyms**, `patch_radius=5` → an 11×11 patch *larger than the grid*, num_types 12,
> super_mult 3.0, boss 150/16): **0 mismatch** vs the real `CritterEnv(**cfg)` on every obs key + reward
> + terminated + truncated, across random and gym-clearing policies on training and held-out seeds
> (`tests/test_jax_difficulty_parity.py`). `jax_train` is config-aware (it derives the obs dim from the
> env — the larger patch changes it — and trains on either config), so the high-gym learned-gap that was
> a slow sb3 run (`difficulty_generalization --range-gap`) now runs on the JAX engine: measured **~196k
> env-steps/s vmap vs ~3.1k for sb3 on the same config = ~63× faster** (CPU, single run; lower than the
> default world's multiplier because the longer, more-divergent 8-gym episodes vectorize less uniformly —
> an honest cost). So the two threads compose: the sharper-discrimination difficulty config is now also
> the fast-to-train one. *Scope kept honest: this re-ports family-A commit at the high-gym config; the
> scripted resolution arms (oracle/blind) stay numpy (they peek env internals), and GPU / other families
> / a tuned PPO remain future work.*

> **Update (jax-noncommit-env-integration): the env's *default* (non-commit) battle is now wired
> into the full-episode JAX env — both battle economies vectorize end-to-end.** `jax-battle-full`
> had ported the non-commit battle (party + SWITCH + force-switch + party-wipe) as a *standalone*
> turn step; the unified `jax_env` itself stayed commit-only. `make_jax_env(JaxEnvConfig(commit=False))`
> now dispatches a non-commit battle branch inside the composed step, mirroring `CritterEnv(commit_battles=
> False)` — the env id `CritterGym-v0` / `CritterGym-procgen-v0` default. The integration is small but
> exact: the in-battle action map (`<4`→MOVE, `4`→SWITCH to the *cyclic* next-alive, `5`→a wasted ITEM
> turn), one non-commit turn (Phase-1 switch / Phase-2 speed-ordered moves with a fainted attacker
> skipped / Phase-3 force-switch to the *first-in-order* alive member), party-wipe / boss-dead / battle
> max-turns termination, and on a win the post-force-switch active clears the gym, levels up and evolves.
> A subtlety the **freeze-time pilot** surfaced: Phase-1 SWITCH and Phase-3 force-switch use *different*
> next-alive orders in numpy (cyclic-from-active vs first-in-party-order) — mirrored separately (a cyclic
> loop vs `argmax`), the kind of off-by-one that silently breaks parity. **Parity: 0 mismatch** vs the
> real `CritterEnv(commit_battles=False)` on every obs key + reward + terminated + truncated, over full
> episodes, fixed & per-seed charts, under four policies (random, gym-clearing, switch-heavy, and a
> never-attack policy that *loses* — exercising force-switch + party-wipe + the no-reward loss exit),
> with a non-vacuity guard asserting the battery actually triggers those paths (`tests/test_jax_noncommit_env_parity.py`,
> 32 tests). **Measured (CPU, single run, vmap-only):** numpy ~139k steps/s · jax vmap **5.08M (b=1024) =
> 36× / 8.35M (b=16384) = 60×** — on par with the commit full-env row (same overworld, a different battle
> economy). *Honest boundary: family A, CPU, single run; the speedup is vmap-only (a single jitted env is
> slower); potions are inert because the env's action space never emits a valid ITEM index (mirrored
> exactly); GPU / other families / tuned PPO remain future work.*

> **Update (jax-ppo-tuned): a tuned-PPO baseline quantifies the oracle *headroom* — the
> benchmark is hard *and* learnable.** The demo above trained an A2C-*lite* (truncated returns,
> one grad step) — a speed signal, not a baseline. `train_ppo` upgrades it to a real **PPO**:
> GAE(λ) with value bootstrap, a clipped surrogate, advantage normalization, and `epochs ×
> num_minibatches` updates per rollout — all still on-device under `jit`+`vmap` (the A2C `train`
> is untouched, so the demo/its tests are unchanged). `gae` is a pure function tested at the
> exact (γ,λ) identities (γ=1,λ=1 → Monte-Carlo, λ=0 → 1-step TD). With a matching gym-clear
> eval (`evaluate_gym_clears`, the *same* yardstick as the scripted oracle arms), `scripts/ppo_baseline.py`
> reports, on **held-out** seeds, how close PPO gets to the oracle ceiling on two commit-mode
> configs. **Measured (CPU, single run, 200 iters — a baseline/signal, pre-registered rules R1
> learns / R2 PPO≥A2C / R3 PPO<0.75·oracle ⇒ headroom):**
>
> | config | PPO held-out gym-clears | oracle | type_blind | PPO/oracle | held-in/out gap | A2C-lite |
> |---|---|---|---|---|---|---|
> | default (3 gyms) | 0.52 ± 0.06 | 1.84 | 0.59 | **28%** | +0.20 | 0.72 |
> | hard (8 gyms) | 1.52 ± 0.28 | 7.28 | 2.03 | **21%** | +0.12 | 2.26 |
>
> *(5-run means ± std-across-runs — `ppo-headroom-rigor` hardened the single-run read into a
> robust one: a pre-registered classifier (`critter_gym.headroom.classify_headroom`, frac=0.75,
> k=1.0, frozen before the data) finds the **optimistic** PPO bound (mean+std = 0.58 / 1.80) still
> far below 0.75·oracle (1.38 / 5.46) on **both** configs → verdict `hard-and-learnable`, robust,
> not seed noise. The single-run 32%/15% lands at 28%/21% across 5 seeds.)*
>
> So PPO **learns** (R1, branch a), **beats A2C-lite** at equal budget (R2 — A2C nearly collapses
> on the hard config), and **generalizes** (held-in≈held-out, gap≈0) — yet reaches only **21–28%
> of the scripted oracle, robustly across 5 seeds** (R3: *hard-and-learnable*, not a reframe). A striking
> honest data point: on the hard config the tuned PPO (1.52) sits **below the non-reasoning `type_blind`
> arm (2.03)** — a clear capability ladder (oracle 7.28 ≫ type_blind 2.03 > PPO 1.52) the current baseline
> can't climb. *Honest boundary: a tiny shared-trunk MLP, CPU, 200 iters (more compute/tuning would raise
> PPO — the headroom is measured at this budget); the oracle is a scripted ceiling proxy; the robustness
> is 5 runs, not a large sweep.*
> This is the benchmark's results-table substance: competitively fast **and** a verifiably
> hard-yet-learnable generalization task with a real RL baseline and large measured headroom.

Why this is a *result* for a benchmark, not just plumbing: it converts "we *plan* to be fast" into
"we have a parity-proven, vectorizable **full-episode env** (family A, **now config-driven**) an RL loop
**actually trains on** — a JAX-native A2C learns the default world on CPU in seconds (~170× sb3) and the
sharper high-gym difficulty config ~63× sb3" — a concrete step toward the adoption gate, with the honest
boundary (other families, full battle, GPU, tuned PPO, scripted-arm JAX-ification) explicitly marked.

## 5. Open questions — what a full M4 claim requires

1. ~~**Battle port** (`jax-battle-port`)~~ — ✅ done for the **commit-mode champion** path (parity-proven,
   1047× vmap). ~~**Full non-commit battle** (`jax-battle-full`)~~ — ✅ done: `critter_gym.jax_battle_full`
   ports the non-commit battle (P-creature party + SWITCH + ITEM(potion) + faint force-switch + party-wipe
   terminal) as a branch-free `(state, action) -> state` turn step (dynamic party indexing via gather +
   `argmax` next-alive, no `lax.scan` needed for the single-turn step). Parity vs `Battle(commit_mode=False)`
   is **0 mismatch** (party hp / active idx / boss hp / winner / turn / done) across an action battery
   (attack/switch/item-heal/force-switch/party-wipe/truncation) + random sequences on fixed & per-seed
   charts; vmap **~452× numpy** (CPU). *Marginal-utility note: gym bosses use commit-mode (already the
   load-bearing path); this completes battle coverage for the env's default (non-commit) path.* ~~Wiring it
   into a non-commit `jax_env` full episode is a separate follow-up.~~ — ✅ done (`jax-noncommit-env-integration`):
   `make_jax_env(JaxEnvConfig(commit=False))` composes it into the full episode at **0 mismatch** vs
   `CritterEnv(commit_battles=False)` (the env's default), vmap **36–60×** (CPU).
2. ~~**Env integration** (`jax-env-integration`)~~ — ✅ done for **family A commit-mode**: a composed
   full-episode `jax_env_step` with full obs+reward+term+trunc parity, vmap-batchable (34–73×).
   ~~**Trains on** (`jax-rl-demo`)~~ — ✅ a JAX-native A2C (`critter_gym.jax_train`) learns family A on
   CPU in seconds (≈170× the existing numpy/sb3 path; learning curve rises, held-out gap ≈ 0).
   Remaining: families B/C/D, a thin Gymnasium `VectorEnv` adapter if an off-the-shelf loop needs the
   gym API, and a tuned PPO.
3. **GPU throughput** (`vectorized-bench`) — measure M4-EC3's ≥10M steps/s on GPU (CPU vmap already
   clears it on the slices, but the EC is stated for GPU).
4. **Spec-stability watch** — if the (A) difficulty-scaling work changes env mechanics (starters,
   bosses, reward economy), the port needs updating. The foundation deliberately ports only the stable
   overworld core to minimize this, but the risk is non-zero (DESIGN §4 gates M4 on "spec stable").

## References (internal)

- `DESIGN.md` §4 — throughput target + measured direction.
- `src/critter_gym/jax_overworld.py` — `OverworldState` pytree + functional `overworld_step` + parity bridge.
- `src/critter_gym/jax_env.py` — `JaxEnvConfig` + `make_jax_env(cfg)` factory (config-driven; default-config module-level fns preserved).
- `src/critter_gym/jax_battle.py` / `jax_battle_full.py` — commit-mode champion battle / non-commit full battle (party + switch/item/force-switch/party-wipe) functional ports (parity-proven).
- `src/critter_gym/jax_train.py` — JAX-native A2C (region bank + `lax.scan` rollout + manual Adam) + `EnvSpec`/`difficulty_env_spec` (config-aware) + `learning_verdict` (pre-registered R1 rule) + `evaluate`.
- `tests/test_jax_parity.py` / `tests/test_jax_train.py` / `tests/test_jax_difficulty_parity.py` — numpy↔JAX parity (default + high-gym config) + train-loop smoke (`importorskip`, CI numpy-only).
- `scripts/bench_throughput.py` / `scripts/jax_rl_demo.py` — step throughput (honest framing) / RL learning demo (curve + train-throughput vs sb3).
- `docs/explanation/competitive-analysis.md` — gap register ("competitively fast" row).
