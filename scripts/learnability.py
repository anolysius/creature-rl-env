#!/usr/bin/env python3
"""Does a *learned* policy acquire chart inference? — PPO on commit-v0 ([rl] extra).

NOT part of the default suite (heavy, machine-dependent). Trains PPO on the
**team-commit** variant (``commit_battles=True``: boss fights commit one champion,
so inferring the hidden chart is load-bearing — reasoning-load-bearing / DESIGN
§3.1.1) on a pool of *training* seeds, then measures held-in vs held-out returns and
places the learned policy against the four scripted reference arms (oracle / infer /
type_blind / probe) via :mod:`critter_gym.learnability`.

Honest by construction: nothing here is a pass/fail threshold. We *report* where the
learned policy lands — at ``infer`` level (it learned to infer), at ``probe``/``blind``
level (it did not, with this budget), or between. Either outcome is a real result.

Usage:
    pip install -e ".[rl]"
    python scripts/learnability.py --timesteps 100000
"""

from __future__ import annotations

import argparse
import sys
import warnings

import gymnasium as gym

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import LearnabilityReport, measure_learnability
from critter_gym.region import heldout_seeds

# A small, fully-observed world so learning is visible in a short run, but with the
# commit economy + amplified matchups intact so champion choice actually matters.
LCFG = dict(
    grid_size=5, num_creatures=8, num_gyms=3, max_steps=80, patch_radius=4,
    vary=True, num_types=12, super_mult=3.0, boss_hp=140, boss_atk=18,
    commit_battles=True,
)
N_TRAIN = 64
N_HELDIN = 16
N_HELDOUT = 16


def make_env() -> CritterEnv:
    return CritterEnv(**LCFG)  # type: ignore[arg-type]


class _SeededReset(gym.Wrapper):
    """Reset cycles through a fixed learning-seed pool (held-in eval stays unseen)."""

    def __init__(self, env: gym.Env, seeds: tuple[int, ...]) -> None:
        super().__init__(env)
        self._seeds = tuple(int(s) for s in seeds)
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        return self.env.reset(seed=s, options=options)


def train_and_measure(timesteps: int, *, n_heldin: int = N_HELDIN,
                      n_heldout: int = N_HELDOUT, seed: int = 0) -> LearnabilityReport:
    """Train PPO ``timesteps`` on commit-v0 learn seeds; return the arm comparison.

    ``seed`` varies the PPO init so ``--runs`` can average over training runs.
    Importable so a CI smoke test can run a tiny budget. Raises ImportError if the
    ``[rl]`` extra is missing (callers gate with ``pytest.importorskip``).
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    from critter_gym.generalization import split_train_pool

    warnings.filterwarnings("ignore")
    learn_seeds, heldin = split_train_pool(range(N_TRAIN), n_eval=n_heldin)
    heldout = heldout_seeds(n_heldout)

    def make_train_env() -> gym.Env:
        return _SeededReset(make_env(), learn_seeds)

    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]),
                verbose=0, n_steps=512, seed=seed)
    model.learn(timesteps, progress_bar=False)

    def ppo_policy(obs: dict) -> int:
        return int(model.predict(obs, deterministic=True)[0])

    return measure_learnability(make_env, heldin, heldout, learned=ppo_policy)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=100_000)
    parser.add_argument("--runs", type=int, default=1,
                        help="train this many PPO seeds and average the learned policy "
                             "(mitigates — does not remove — the single-run caveat).")
    args = parser.parse_args()
    try:
        reports = [train_and_measure(args.timesteps, seed=i) for i in range(max(1, args.runs))]
    except ImportError:
        print('This demo needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    report = reports[0]
    print(f"commit-v0 PPO learnability | timesteps={args.timesteps:,} | runs={args.runs}\n")
    print(report.to_markdown())

    # Compare on the CLEAN gym-clear-only metric (evolution-free) — the metric that
    # decouples the conflated return so a learned policy can't appear to beat oracle
    # merely by evolving more (learnability-precision).
    lo, hi = report.heldout_gyms["probe"], report.heldout_gyms["infer"]
    learned_runs = [r.heldout_gyms["learned"] for r in reports]
    learned = sum(learned_runs) / len(learned_runs)
    band = hi - lo
    where = (
        "≈ infer (learned to infer the chart)" if band > 0 and learned >= lo + 0.7 * band
        else "≈ probe/blind (did NOT acquire inference at this budget)"
        if band <= 0 or learned <= lo + 0.3 * band
        else "between probe and infer (partial)"
    )
    band_txt = ""
    if len(reports) > 1:
        band_txt = f" [range {min(learned_runs):.3f}–{max(learned_runs):.3f}]"
    print(
        f"\nLearned gym-clear-only (held-out): mean={learned:.3f} "
        f"over {len(reports)} run(s){band_txt}  → sits {where}."
    )
    print("(Gym-clear-only: bosses defeated, evolution excluded. Reported, not pass/fail —")
    print(" single config, N modest, multi-run is [rl]/non-CI. See DESIGN §3.1.1 follow-up.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
