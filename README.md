# CritterGym

> A procedurally-generated **creature-collection reinforcement-learning environment** for
> benchmarking long-horizon agency, strategic reasoning, and generalization — fast, headless,
> and Gymnasium-compatible. **Built for AI/RL researchers, not gamers.**

CritterGym is an *instrument for measuring agent capability* (long-horizon planning, online
rule inference, generalization), not a game. Rewards are **verifiable** (RLVR — boolean
subgoal completion, not hand-tuned shaping), and a **procedural-generation seed split** lets
you *measure* generalization instead of asserting it.

## Install

```bash
pip install -e .                # core (numpy-only engine + Gymnasium API)
pip install -e ".[rl]"          # + PPO training scripts (stable-baselines3)
pip install -e ".[viz]"         # + matplotlib metric plots
pip install -e ".[render]"      # + GIF encoding (imageio)
```

Python 3.9+. The core engine is numpy-only; heavy learning deps live behind extras.

## Quickstart

```python
import gymnasium as gym
from critter_gym.registration import register_envs

register_envs()
env = gym.make("CritterGym-procgen-v0")   # procedural world + per-seed hidden type chart
obs, info = env.reset(seed=42)            # reset(seed) reproduces a region exactly
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
```

**Registered environments (6):**

| id | what |
|---|---|
| `CritterGym-v0` | fixed M1 world (catch → gym battles → boss → evolve); env *family A* baseline |
| `CritterGym-procgen-v0` | procedural region + per-seed hidden type chart (train/test seed split) |
| `CritterGym-commit-v0` | team-commit boss economy (makes inferring the chart load-bearing) |
| `CritterGym-forage-v0` | env *family B* — contact-collect (genre generalization) |
| `CritterGym-duel-v0` | env *family C* — type-agnostic stamina/commit duel battle |
| `CritterGym-muster-v0` | env *family D* — collection-gated power (muster before you win) |

## What it measures

- **Verifiable subgoals (RLVR):** catch ≥ C creatures · evolve ≥ 1 · defeat each gym · defeat the final boss.
- **(A) Instance generalization — measured.** Held-out *seeds* give a new map + a new hidden
  type chart. A trained agent defeats bosses at **45% (held-out) vs 40% (held-in)** — a gap
  ≈ 0 (generalization, not memorization). Engine throughput ≈ **266k steps/s/core**.
- **Rule inference is load-bearing.** Under the team-commit economy, a scripted four-arm gate
  (42 held-out seeds) freezes `oracle − type_blind ≥ 0.20` and `infer − probe ≥ 0.10`: knowing
  the chart is decisive, and *inferring* recurring matchups beats *probing* each fight. A
  learned PPO policy acquires it (lands at/above the `infer` reference on a gym-clear-only metric).
- **(B) Genre generalization — a foundation, not yet a claim.** An env-*family* abstraction
  measures transfer across structurally distinct collection-RPGs (env-level leave-one-out).
  On four families across three axes (collection / battle-system / progression) the gaps are
  *policy-specific*: e.g. on the duel family an A-tuned policy fails to transfer (gap ≈ +3.9)
  while an appropriate policy transfers (≈ +0.2). This stands up the machinery — it is **not**
  a proof of genre generalization (that needs many more families).

Full results, sources, and honest caveats: **[`docs/paper/critter-gym.md`](docs/paper/critter-gym.md)**
(figure→source map in [`docs/paper/README.md`](docs/paper/README.md)). Scope SSOT: [`DESIGN.md`](DESIGN.md) §3.1.1.

## Positioning (honest)

CritterGym is a **procedural-generalization** benchmark; compare it to **Procgen / Craftax /
XLand-MiniGrid**, not to Pokémon. **Pokémon is a plain-language metaphor** (creatures + type
matchups + gyms make the task legible), **not a competitive claim** — we traded Pokémon's
open-ended difficulty for *measurability*. Instance generalization (A) is measured; genre
generalization (B) is an honest *foundation*, not a proof. Honesty over headline.

## Reproducibility

Seeded and deterministic: `reset(seed)` reproduces a region exactly, and train/test seeds are
structurally disjoint (a leak guard prevents flattering the gap). Reference configs are pinned.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for dev setup and the task lifecycle.

## Citation

```bibtex
@misc{crittergym2026,
  title  = {CritterGym: A Procedurally-Generated Creature-Collection Benchmark for
            Measuring Long-Horizon Agency and Generalization},
  author = {CritterGym contributors},
  year   = {2026},
  note   = {Working draft, docs/paper/critter-gym.md}
}
```

## Release status

- **License:** MIT (see [`LICENSE`](LICENSE)).
- **Open-source publication** (listing on Prime Intellect Hub, making the repository public) is
  a maintainer action, not yet performed — these local artifacts prepare the release.

## License

[MIT](LICENSE).
