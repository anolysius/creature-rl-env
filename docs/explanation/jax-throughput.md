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

Why this is a *result* for a benchmark, not just plumbing: it converts "we *plan* to be fast" into
"we have a parity-proven, vectorizable engine path with a measured ~100×+ CPU headroom" — a concrete
step toward the adoption gate, with the honest boundary (battle, GPU) explicitly marked.

## 5. Open questions — what a full M4 claim requires

1. **Battle port** (`jax-battle-port`) — functional rewrite of the turn-based battle sub-MDP with
   parity against the numpy battle. The harder half of the hot path.
2. **Env integration** (`jax-env-integration`) — wrap the JAX step as a batched/vectorized Gymnasium
   surface so RL training loops actually consume it (not just a bench).
3. **GPU throughput** (`vectorized-bench`) — measure M4-EC3's ≥10M steps/s on GPU (CPU vmap already
   clears it, but the EC is stated for GPU).
4. **Spec-stability watch** — if the (A) difficulty-scaling work changes env mechanics (starters,
   bosses, reward economy), the port needs updating. The foundation deliberately ports only the stable
   overworld core to minimize this, but the risk is non-zero (DESIGN §4 gates M4 on "spec stable").

## References (internal)

- `DESIGN.md` §4 — throughput target + measured direction.
- `src/critter_gym/jax_overworld.py` — `OverworldState` pytree + functional `overworld_step` + parity bridge.
- `tests/test_jax_parity.py` — numpy↔JAX parity + jit/vmap guards (`importorskip`, CI numpy-only).
- `scripts/bench_throughput.py` — numpy/jax-single/jax-vmap throughput, honest framing.
- `docs/explanation/competitive-analysis.md` — gap register ("competitively fast" row).
