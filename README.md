# CritterGym

[![ci](https://github.com/anolysius/creature-rl-env/actions/workflows/ci.yml/badge.svg)](https://github.com/anolysius/creature-rl-env/actions/workflows/ci.yml)

> A procedurally-generated **creature-collection reinforcement-learning environment** for
> benchmarking long-horizon agency, strategic reasoning, and generalization — fast, headless,
> and Gymnasium-compatible. **Built for AI/RL researchers, not gamers.**

CritterGym is an *instrument for measuring agent capability* (long-horizon planning, online
rule inference, generalization), not a game. Rewards are **verifiable** (RLVR — boolean
subgoal completion, not hand-tuned shaping), and a **procedural-generation seed split** lets
you *measure* generalization instead of asserting it.

**Live:** [leaderboard & gameplay](https://anolysius.github.io/creature-rl-env/) ·
[how the exam works](https://anolysius.github.io/creature-rl-env/how-it-works.html)
(win condition, the hidden type chart, and why there is no grinding)

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

## What can you do with it? (guides)

CritterGym is one env that supports four research workflows. Each guide is a short, runnable
recipe (한국어 mirror linked inside each):

| I want to… | Guide |
|---|---|
| **Train an RL policy** + reproduce the PPO-vs-oracle headroom and the generalization gap | [how-to/train-a-policy](docs/how-to/train-a-policy.md) |
| **Evaluate an LLM agent** on the sealed, contamination-proof held-out eval (`inference_score`) | [how-to/evaluate-an-llm-agent](docs/how-to/evaluate-an-llm-agent.md) |
| **Measure genre transfer** — does a policy generalize to an env *family* it never trained on? | [how-to/measure-genre-transfer](docs/how-to/measure-genre-transfer.md) |
| Look up the **observation / action / reward contract** and the env-variant knobs | [reference/observation-action-space](docs/reference/observation-action-space.md) |

한국어 가이드: 각 문서 안의 `.ko.md` 링크 · 시작하기 → [README.ko.md](README.ko.md)

## Reporting problems (and how corrections work)

Bug reports and challenges to any published number are **welcome** — open a GitHub issue.
Every figure in this repo ships with its reproduction command and seeds; if something does
not reproduce, that is a finding, not an annoyance. Confirmed errors are fixed and the
correction is **published in `docs/CHANGELOG.md`** (this project has downgraded its own
results before and will do it again). Provenance, transparently: this project was built by
a human-directed AI coding agent (Claude) — every commit carries an AI co-authorship
trailer, and measurements follow pre-registered decision rules frozen before data.

## What it measures

- **Verifiable subgoals (RLVR):** catch ≥ C creatures · evolve ≥ 1 · defeat each gym · defeat the final boss.
- **Competitively fast (JAX) — measured.** The hot path is ported to functional JAX
  (`critter_gym.jax_env`) and **parity-proven against the numpy env (0 mismatch)**, so the
  seed→trajectory reproducibility is preserved across the port. On **CPU** it vectorizes to
  **≈27–60× numpy for full episodes and up to ≈1047× for the pure battle step** under `vmap`
  (numpy ≈123–410k steps/s; a single jit env is *slower* — the win is entirely batched
  vectorization). A JAX-native PPO **trains on it in seconds** (≈170× the numpy/sb3 path).
  *Honest scope: CPU, single-run directions; the ≥10M steps/s GPU target (M4-EC3) is unmeasured.*
- **All four env families vectorize (A/B/C/D).** critter (A), forage (B), **duel (C — a
  type-agnostic RPS/stamina battle)**, and muster (D) all run on the one JAX engine at parity
  0 — full family breadth, not just the baseline family.
- **(A) Instance generalization — measured.** Held-out *seeds* give a new map + a new hidden
  type chart. A trained agent defeats bosses at **45% (held-out) vs 40% (held-in)** — a gap
  ≈ 0 (generalization, not memorization).
- **Hard *and* learnable (measured headroom).** A tuned PPO baseline (GAE+clip, on-device JAX)
  reaches only **21–28% of the scripted oracle** on held-out seeds (**5-run robust**; default
  3-gym and hard 8-gym configs), generalizes (held-in ≈ held-out), and on the hard config sits
  *below* the non-reasoning `type_blind` arm — a clear capability ladder (oracle ≫ type_blind >
  PPO) with large measured headroom. *A baseline/signal at this budget, not a tuned SOTA sweep.*
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

**Reproduce the two headline tables (throughput + oracle headroom) with one command:**

```bash
pip install -e ".[jax,rl]"
python scripts/reproduce_results.py --quick    # fast smoke (seconds)
python scripts/reproduce_results.py --runs 5   # full multi-run headroom (minutes)
```

Numbers are generated live (nothing hardcoded); each sub-bench prints its own honest framing.

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

- **Version:** `1.0.0rc1` — a **release candidate**. The free open-source env is feature-complete
  (M0–M2 ✅; M3 launch-readiness mostly ✅; M4 throughput ✅ on CPU), and the headline results are
  parity-proven and reproducible.
- **Public since July 2026:** the repository is open and the
  [live site](https://anolysius.github.io/creature-rl-env/) (leaderboard, gameplay, community
  submission track) is up.
- **Remaining before a `1.0.0` tag (each an explicit gate):** the **≥10M steps/s GPU** measurement
  (M4-EC3; CPU vmap already clears it on the pure slices), the **arXiv writeup** (M3-EC4, draft in
  `docs/paper/`), and the **version tag / eval-hub listing** — each a maintainer (human) decision.
- **License:** MIT (see [`LICENSE`](LICENSE)).

## License

[MIT](LICENSE).
