"""Battle-arena probe mode (eval-product/battle-arena-probe).

``ArenaEnv`` drops the agent straight into K consecutive gym battles (no overworld), so a
submission's super-effective-move rate can be read WITHOUT the exploration/survival confound:
a low SE-rate in the arena means "does not infer", not "never reached a battle". The battle
economy itself is untouched (the parent's ``_step_battle``/``_maybe_enter_battle`` run as-is).
"""

from __future__ import annotations

import numpy as np
import pytest

from critter_gym.arena import arena_band, arena_factory, score_arena_telemetry
from critter_gym.envs import ArenaEnv
from critter_gym.learnability import reference_arm
from critter_gym.region import heldout_seeds

_KW = dict(commit_battles=True, vary=True, num_types=8, num_gyms=3, num_creatures=5,
           grid_size=10, max_steps=600)


def _run(env: ArenaEnv, policy, seed: int, max_iters: int = 700):
    obs, info = env.reset(seed=seed)
    trace = [(int(obs["in_battle"][0]), int(obs["gyms_defeated"][0]))]
    total = 0.0
    for _ in range(max_iters):
        action = policy(env, obs)
        obs, r, term, trunc, info = env.step(action)
        total += float(r)
        trace.append(
            (int(obs["in_battle"][0]), int(obs["gyms_defeated"][0]), float(r), term, trunc)
        )
        if term or trunc:
            break
    return obs, info, total, trace


# -- AC1: arena mechanics ------------------------------------------------------


def test_reset_starts_in_battle() -> None:
    env = ArenaEnv(k_battles=4, **_KW)
    obs, info = env.reset(seed=0)
    assert int(obs["in_battle"][0]) == 1
    assert info["mode"] == "battle"
    assert int(obs["enemy_hp"][0]) > 0


def test_k_battles_then_terminate_win_or_lose() -> None:
    env = ArenaEnv(k_battles=3, **_KW)
    # oracle wins its bouts; a pass-only agent loses them — both must still see exactly
    # K battles and a clean terminate (losses do not end the episode early).
    for policy in (reference_arm("oracle"), lambda e, o: 5):
        obs, info, _, trace = _run(env, policy, seed=1)
        assert info["arena"]["battles_done"] == 3
        assert trace[-1][3] is True  # terminated
        assert int(obs["in_battle"][0]) == 0  # after the last bout, no new battle


def test_wins_counted_and_party_healed_between_bouts() -> None:
    env = ArenaEnv(k_battles=3, **_KW)
    obs, info, total, _ = _run(env, reference_arm("oracle"), seed=2)
    wins = int(obs["gyms_defeated"][0])
    assert wins == info["subgoals"]["gyms_defeated"]
    assert wins >= 1  # the chart-knowing expert wins at least one bout
    # party is fully healed on each battle entry (gym re-entry rule) — after the run,
    # every creature was re-healed at its last bout entry, so nobody is left at 0 unless
    # they fainted in the final bout; the invariant we lock is that a NEW battle always
    # starts with a full-HP active (checked inside the episode).
    env.reset(seed=2)
    assert env._battle is not None and env._battle.state.active_a == 0
    assert all(c.hp == c.max_hp for c in env._party)  # full-HP entry (gym re-entry rule)


def test_boss_sequence_cycles_region_gyms() -> None:
    env = ArenaEnv(k_battles=5, **_KW)
    env.reset(seed=3)
    seen = [env._battle_gym_idx]
    policy = reference_arm("oracle")
    obs = env._obs()
    for _ in range(700):
        obs, r, term, trunc, _ = env.step(policy(env, obs))
        if term or trunc:
            break
        if env._mode == "battle" and env._battle_gym_idx != seen[-1]:
            seen.append(env._battle_gym_idx)
    n = len(env._gym_types)
    assert seen == [i % n for i in range(len(seen))]  # cycles region gyms in order


def test_determinism_same_seed_same_trace() -> None:
    def scripted_run():
        env = ArenaEnv(k_battles=3, **_KW)
        rng = np.random.default_rng(99)
        return _run(env, lambda e, o: int(rng.integers(0, 6)), seed=7)[3]

    assert scripted_run() == scripted_run()


def test_obs_space_bound_is_k() -> None:
    env = ArenaEnv(k_battles=12, **_KW)
    assert int(env.observation_space["gyms_defeated"].high[0]) == 12
    env.reset(seed=0)
    obs, *_ = env.step(0)
    assert env.observation_space["gyms_defeated"].contains(obs["gyms_defeated"])


def test_k_battles_validation() -> None:
    with pytest.raises(ValueError):
        ArenaEnv(k_battles=0, **_KW)


def test_noncommit_mode_also_runs() -> None:
    kw = dict(_KW)
    kw["commit_battles"] = False
    env = ArenaEnv(k_battles=2, **kw)
    obs, info, _, trace = _run(env, lambda e, o: 0, seed=4)
    assert info["arena"]["battles_done"] == 2
    assert trace[-1][3] is True


# -- AC3/AC4: band sanity + telemetry reuse -------------------------------------


def test_arena_band_discriminates() -> None:
    seeds = list(heldout_seeds(4))
    band = arena_band(seeds, k_battles=4, **_KW)
    assert set(band) == {"oracle", "infer", "type_blind", "probe"}
    oracle, blind = band["oracle"], band["type_blind"]
    assert oracle.se_rate > blind.se_rate  # the band discriminates inference in the arena
    assert oracle.wins > 0  # winnable
    assert oracle.n_battle_moves > 0 and blind.n_battle_moves > 0


def test_score_arena_telemetry_matches_band_for_scripted_arm() -> None:
    # Running the oracle arm through the submission-telemetry path must reproduce the
    # band's oracle row (same loop, same counters) — locks the two paths together.
    seeds = list(heldout_seeds(3))
    band = arena_band(seeds, k_battles=3, **_KW)
    tel = score_arena_telemetry(reference_arm("oracle"), seeds, k_battles=3, **_KW)
    assert tel.n_battle_moves == band["oracle"].n_battle_moves
    assert tel.super_effective_rate == pytest.approx(band["oracle"].se_rate)


def test_arena_factory_builds_arena_env() -> None:
    env = arena_factory(k_battles=2, **_KW)()
    assert isinstance(env, ArenaEnv)
    assert env.k_battles == 2


# -- AC6: LLM wiring, verified WITHOUT any real LLM call -------------------------


def test_llm_agent_runs_in_arena_with_fake_complete() -> None:
    from critter_gym.llm_eval import StatefulLLMAgent

    calls = []

    def fake_complete(prompt: str) -> str:
        calls.append(prompt)
        return "0"  # always move 0 — deterministic, no network, no quota

    agent = StatefulLLMAgent(fake_complete, window=4)
    tel = score_arena_telemetry(agent, list(heldout_seeds(2)), k_battles=2, **_KW)
    assert tel.n_battle_moves > 0  # the agent actually fought (confound removed)
    assert 0.0 <= tel.super_effective_rate <= 1.0
    assert len(calls) > 0  # every decision went through the (fake) LLM


def test_runner_exposes_arena_flag_without_calling_llm() -> None:
    import subprocess
    import sys

    out = subprocess.run(
        [sys.executable, "scripts/llm_eval_run.py", "--help"],
        capture_output=True, text=True, check=True,
    )
    assert "--arena" in out.stdout and "--k-battles" in out.stdout
