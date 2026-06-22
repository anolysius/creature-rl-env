"""Tests for the numpy-only reproducible leaderboard (M3-EC2).

Exercised with the shipped ``random``/``scripted`` baselines (no torch) — the
leaderboard format and its reproducibility are verifiable in the core CI.
"""

from __future__ import annotations

import inspect
import json

import numpy as np

from critter_gym import leaderboard as lb
from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.leaderboard import BenchmarkSpec, Leaderboard, run_benchmark
from critter_gym.region import TEST_SEED_OFFSET

# A small spec so the core tests stay fast; the env config mirrors DEFAULT_SPEC.
SPEC = BenchmarkSpec(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40, patch_radius=3,
                     n_heldin=12, n_heldout=12)


def _core_policies():
    rng = np.random.default_rng(0)
    return {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=SPEC.grid_size),
    }


# -- AC1 / AC5: format + ranking ----------------------------------------------


def test_leaderboard_ranks_by_heldout_descending() -> None:
    board = run_benchmark(SPEC, _core_policies())
    assert isinstance(board, Leaderboard)
    means = [e.heldout_mean for e in board.entries]
    assert means == sorted(means, reverse=True)  # held-out descending
    assert [e.rank for e in board.entries] == list(range(1, len(board.entries) + 1))
    # scripted generalizes better than random → ranks first.
    assert board.entries[0].name == "scripted"


def test_markdown_has_rank_and_numbers() -> None:
    board = run_benchmark(SPEC, _core_policies())
    md = board.to_markdown()
    assert "rank" in md and "held-in" in md and "held-out" in md and "gap" in md
    assert "scripted" in md and "random" in md


# -- AC4: reproducibility -----------------------------------------------------


def test_same_spec_same_json() -> None:
    a = run_benchmark(SPEC, {"scripted": lambda o: greedy_policy(o, grid_size=SPEC.grid_size)})
    b = run_benchmark(SPEC, {"scripted": lambda o: greedy_policy(o, grid_size=SPEC.grid_size)})
    assert a.to_json() == b.to_json()  # deterministic policy + pinned spec


def test_json_embeds_spec_and_round_trips() -> None:
    board = run_benchmark(SPEC, _core_policies())
    parsed = json.loads(board.to_json())
    assert parsed["spec"] == SPEC.to_dict()  # pinned config travels with the result
    entry_keys = set(parsed["entries"][0])
    assert entry_keys == {"rank", "name", "heldin_mean", "heldout_mean", "gap"}


# -- AC6: leak guard inherited from the scoring layer -------------------------


def test_spec_seeds_respect_the_split() -> None:
    assert all(s < TEST_SEED_OFFSET for s in SPEC.heldin_eval_seeds())
    assert all(s >= TEST_SEED_OFFSET for s in SPEC.heldout_eval_seeds())


# -- AC3: leaderboard pulls in no learning dependency -------------------------


def test_leaderboard_is_numpy_only() -> None:
    src = inspect.getsource(lb)
    assert "import torch" not in src
    assert "stable_baselines3" not in src
    assert "sb3_contrib" not in src
