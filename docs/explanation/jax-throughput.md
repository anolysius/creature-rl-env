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

Why this is a *result* for a benchmark, not just plumbing: it converts "we *plan* to be fast" into
"we have a parity-proven, vectorizable **full-episode env** (family A) an RL loop **actually trains
on** — a JAX-native A2C learns it on CPU in seconds, ~170× the existing numpy/sb3 path" — a concrete
step toward the adoption gate, with the honest boundary (other families, full battle, GPU, tuned PPO)
explicitly marked.

## 5. Open questions — what a full M4 claim requires

1. ~~**Battle port** (`jax-battle-port`)~~ — ✅ done for the **commit-mode champion** path (parity-proven,
   1047× vmap). Remaining: **`jax-battle-full`** — the full non-commit battle (3-creature party + SWITCH +
   ITEM + force-switch + party-wipe terminal), which needs dynamic party indexing and `lax.scan`.
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
- `src/critter_gym/jax_train.py` — JAX-native A2C (region bank + `lax.scan` rollout + manual Adam) + `learning_verdict` (pre-registered R1 rule) + `evaluate`.
- `tests/test_jax_parity.py` / `tests/test_jax_train.py` — numpy↔JAX parity + train-loop smoke (`importorskip`, CI numpy-only).
- `scripts/bench_throughput.py` / `scripts/jax_rl_demo.py` — step throughput (honest framing) / RL learning demo (curve + train-throughput vs sb3).
- `docs/explanation/competitive-analysis.md` — gap register ("competitively fast" row).
