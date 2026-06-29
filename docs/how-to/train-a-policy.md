# How to: train a policy on CritterGym

> 한국어: [train-a-policy.ko.md](train-a-policy.ko.md)

CritterGym is a standard Gymnasium env, so any RL library works. This guide shows the fastest
path with the bundled baselines, then how to roll your own.

## 0. Install the RL extra

```bash
pip install -e ".[rl,jax]"
```

`[rl]` pulls the PPO/recurrent baseline deps; `[jax]` gives the vectorized fast path.

## 1. Train your own policy (any library)

```python
import gymnasium as gym
from critter_gym.registration import register_envs

register_envs()
env = gym.make("CritterGym-procgen-v0")     # procedural + per-seed hidden type chart
obs, info = env.reset(seed=42)              # train seeds are < 1_000_000

# ... your training loop: obs is a Dict, action_space is Discrete(6) ...
# See docs/reference/observation-action-space.md for the obs/action contract.
```

Train on **train-region** seeds (`< 1_000_000`) only — keep the held-out region untouched so your
generalization number stays honest.

## 2. Reproduce the bundled PPO baseline + oracle headroom

```bash
python scripts/ppo_baseline.py            # tuned JAX PPO vs the scripted oracle ceiling, held-out
python scripts/reproduce_results.py --quick   # smoke; --runs 5 for the full headline tables
```

These report, on **held-out** seeds, how close a learned policy gets to a scripted **oracle**
(the *headroom* that makes the benchmark hard). The PPO config (lr, GAE-λ, entropy, seeds) is
pinned in `scripts/ppo_baseline.py`. Numbers are generated live — nothing is hardcoded.

For the memory-agent baseline (partial observability is load-bearing here), see
`scripts/recurrent_ppo_baseline.py`.

## 3. Measure the generalization gap (Procgen-style)

```bash
python scripts/train_ppo.py               # trains on train seeds, then reports held-in vs held-out
```

This uses `critter_gym.generalization` to score the trained policy on held-in (training-region)
vs held-out (test-region) seeds — a new map **and** a new hidden type chart per held-out seed.
The gap is *reported*, not used as a pass/fail threshold.

## Honest notes

- The bundled baselines are small MLPs on modest budgets — a *headroom* yardstick, **not** a
  tuned SOTA. Beating them is expected; the point is the gap to the oracle.
- Throughput: the JAX path is parity-proven against numpy (0 mismatch) and vmaps to ~hundreds of
  millions of steps/s; see `scripts/bench_throughput.py`.
