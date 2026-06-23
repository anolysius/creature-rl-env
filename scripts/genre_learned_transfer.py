#!/usr/bin/env python3
"""Does a *learned* policy transfer to an UNSEEN env family? — genre transfer ([rl]).

This is the missing piece for a real DESIGN §3.1.1 (B) genre-generalization claim: prior
(B) work compared *scripted* policies (skill-structural contrasts on families C/D), but a
credible claim needs a **learned** policy that generalizes to an env family it never trained
on. Here we train PPO on **train families** (random family per episode) and measure transfer
to a **held-out family**.

Obs constraint: a single PPO net needs one observation space. As of the obs-harmonization
task every family shares ONE harmonized obs space (``env_family.HARMONIZED_OBS_KEYS`` — the
charge keys are 0-masked on non-duel families, real on ``duel``), so ``assert_obs_compatible``
now accepts all four families and one net *can* train across them including duel. This default
run still measures ``{critter, forage} → muster`` (the first learned-transfer measurement);
expanding the train distribution to include duel is the next task.

Honest scope: one train-set → one held-out family is **not** a genre-generalization proof —
it is the *first learned-policy transfer measurement*. We *report* the gap (with std); a weak
transfer (a large gap) is an honest result — "learned genre transfer is hard / (B) is still
open" — not a failure. Single run, modest N → a signal. Nothing here is a pass/fail threshold.

Usage:
    pip install -e ".[rl]"
    python scripts/genre_learned_transfer.py --timesteps 60000
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass

import gymnasium as gym

from critter_gym.env_family import REQUIRED_OBS_KEYS, make_family
from critter_gym.generalization import evaluate, split_train_pool
from critter_gym.region import heldout_seeds

TRAIN_FAMILIES = ["critter", "forage"]
HELDOUT_FAMILY = "muster"
N_TRAIN = 64
N_HELDIN = 16
N_HELDOUT = 16


def assert_obs_compatible(families: list[str]) -> None:
    """Raise if the families don't share one observation space (needed for a single net).

    A family-agnostic learned policy needs identical obs keys across every family it sees.
    Since the obs-harmonization task all families expose ``HARMONIZED_OBS_KEYS`` (duel's
    charge keys are 0-masked elsewhere), so all four — including duel — are now accepted;
    this guard still fails loudly if a future family forks the obs space.
    """
    key_sets = {f: frozenset(make_family(f).observation_space.spaces) for f in families}
    shared = set.intersection(*(set(k) for k in key_sets.values())) if key_sets else set()
    if not REQUIRED_OBS_KEYS.issubset(shared):
        raise ValueError("families must all expose REQUIRED_OBS_KEYS")
    for f, ks in key_sets.items():
        if set(ks) != set(next(iter(key_sets.values()))):
            raise ValueError(
                f"family {f!r} has a different obs space {sorted(set(ks) ^ shared)}; "
                "a single learned net needs obs-identical families (duel is excluded)"
            )


@dataclass(frozen=True)
class TransferReport:
    """A learned policy's mean on its train families (held-in) vs an unseen family."""

    train_families: tuple[str, ...]
    heldout_family: str
    heldin_mean: float
    heldin_std: float
    heldout_mean: float
    heldout_std: float

    @property
    def gap(self) -> float:
        """Env-level transfer gap (train families − unseen family). Reported, not thresholded."""
        return self.heldin_mean - self.heldout_mean


class _MultiFamilyEnv(gym.Env):
    """Training env that cycles through ``families`` (one per reset) over a seed pool.

    All families must be obs-identical (checked by the caller). Each reset picks the next
    (family, seed) so PPO trains on a mix of train families without ever seeing the held-out one.
    """

    def __init__(self, families: list[str], seeds: tuple[int, ...]) -> None:
        super().__init__()
        self._families = list(families)
        self._seeds = tuple(int(s) for s in seeds)
        probe = make_family(self._families[0])
        self.observation_space = probe.observation_space
        self.action_space = probe.action_space
        self._env = probe
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        fam = self._families[self._i % len(self._families)]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        self._env = make_family(fam)  # type: ignore[assignment]
        return self._env.reset(seed=s, options=options)

    def step(self, action):  # type: ignore[no-untyped-def]
        return self._env.step(action)


def _family_factory(name: str):
    return lambda: make_family(name)


def train_and_transfer(
    train_families: list[str] = TRAIN_FAMILIES,
    heldout_family: str = HELDOUT_FAMILY,
    timesteps: int = 60_000,
    *,
    n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
    seed: int = 0,
) -> TransferReport:
    """Train PPO on ``train_families`` and measure transfer to the unseen ``heldout_family``.

    Importable so a CI smoke test can use a tiny budget. Raises ImportError if ``[rl]`` is
    missing (callers gate with importorskip). Held-in eval seeds are carved disjoint from the
    learning seeds; the held-out *family* is never trained on (family-level split).
    """
    assert_obs_compatible([*train_families, heldout_family])
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    warnings.filterwarnings("ignore")
    learn_seeds, heldin = split_train_pool(range(N_TRAIN), n_eval=n_heldin)
    heldout = heldout_seeds(n_heldout)

    def make_train_env() -> gym.Env:
        return _MultiFamilyEnv(train_families, learn_seeds)

    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]),
                verbose=0, n_steps=512, seed=seed)
    model.learn(timesteps, progress_bar=False)

    def policy(obs: dict) -> int:
        return int(model.predict(obs, deterministic=True)[0])

    # Held-in: mean over train families on held-in seeds (disjoint from learning seeds).
    heldin_returns: list[float] = []
    for fam in train_families:
        heldin_returns.extend(evaluate(_family_factory(fam), policy, heldin).returns)
    out = evaluate(_family_factory(heldout_family), policy, heldout)

    import numpy as np

    return TransferReport(
        train_families=tuple(train_families),
        heldout_family=heldout_family,
        heldin_mean=float(np.mean(heldin_returns)) if heldin_returns else 0.0,
        heldin_std=float(np.std(heldin_returns)) if heldin_returns else 0.0,
        heldout_mean=out.mean,
        heldout_std=out.std,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=60_000)
    args = parser.parse_args()
    try:
        rep = train_and_transfer(timesteps=args.timesteps)
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    print(f"learned genre transfer | PPO timesteps={args.timesteps:,}\n")
    print(f"train families {rep.train_families} → held-out family '{rep.heldout_family}'\n")
    print("| set | mean (±std) |")
    print("|---|---|")
    print(f"| held-in (train families) | {rep.heldin_mean:.3f} ±{rep.heldin_std:.3f} |")
    print(f"| held-out (unseen family) | {rep.heldout_mean:.3f} ±{rep.heldout_std:.3f} |")
    print(f"\nenv-level transfer gap (held-in − held-out family) = {rep.gap:+.3f}")
    print(
        "\nReported, not pass/fail. This is the FIRST learned-policy genre-transfer "
        "measurement; one train-set → one held-out family is NOT a genre proof. A large gap "
        "means the learned policy did not transfer to the unseen family's mechanic — an "
        f"honest '(B) is still open' signal. Single run, N={N_HELDIN}/{N_HELDOUT}, low budget, "
        "duel excluded (obs harmonization future). See DESIGN §3.1.1."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
