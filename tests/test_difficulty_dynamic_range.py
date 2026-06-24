"""difficulty-dynamic-range — gym-count dynamic range widens discrimination resolution.

numpy-only (scripted arms, deterministic) so it runs in core CI. Asserts:
  - region ``min_gyms`` floor/exact control (+ default keeps the historical region),
  - the oracle-vs-blind gym-clear spread GROWS with the gym count (finer resolution),
  - winnability survives at scale (oracle clears most gyms),
  - backward-compat: ``min_gyms=None`` reproduces the prior region bit-for-bit.
The learned-policy gap (PPO) lives in ``scripts/difficulty_generalization.py`` (``[rl]``).
"""
from __future__ import annotations

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.learnability import measure_learnability
from critter_gym.region import generate_region, heldout_seeds

# A small fully-observed commit world so scripted arms run fast; gym count is the knob.
_BASE = dict(grid_size=6, num_creatures=5, max_steps=160, patch_radius=5, vary=True,
             commit_battles=True, num_types=12, super_mult=3.0, boss_hp=150, boss_atk=16)


def _spread(num_gyms: int, seeds: tuple[int, ...]) -> tuple[float, float]:
    """(oracle − type_blind gym-clear spread, oracle/num_gyms) on held-out ``seeds``."""
    cfg = dict(_BASE, num_gyms=num_gyms, min_gyms=num_gyms)  # exact count
    heldin = (0,)  # training-region (split guard); we read the held-out arm means
    rep = measure_learnability(lambda: CritterEnv(**cfg), heldin, seeds)
    o = rep.heldout_gyms["oracle"]
    b = rep.heldout_gyms["type_blind"]
    return o - b, o / num_gyms


# -- region min_gyms control --------------------------------------------------
def test_min_gyms_exact_count():
    # min_gyms == max_gyms fixes the per-seed gym count exactly.
    for seed in range(8):
        r = generate_region(seed, 6, 5, 8, vary=True, num_types=12, super_mult=3.0, min_gyms=8)
        assert len(r.gyms) == 8


def test_min_gyms_floor():
    # a floor below max still guarantees at least `min_gyms` gyms.
    for seed in range(16):
        r = generate_region(seed, 6, 5, 8, vary=True, num_types=12, super_mult=3.0, min_gyms=4)
        assert 4 <= len(r.gyms) <= 8


def test_min_gyms_validation():
    import pytest
    with pytest.raises(ValueError):
        generate_region(0, 6, 5, 3, vary=True, num_types=12, super_mult=3.0, min_gyms=4)  # > max
    with pytest.raises(ValueError):
        generate_region(0, 6, 5, 3, vary=True, num_types=12, super_mult=3.0, min_gyms=0)  # < 1


def test_backward_compat_min_gyms_none():
    # min_gyms=None must reproduce the prior region bit-for-bit (no RNG-order shift).
    for seed in range(12):
        a = generate_region(seed, 10, 5, 3, vary=True, num_types=12, super_mult=3.0)
        b = generate_region(seed, 10, 5, 3, vary=True, num_types=12, super_mult=3.0, min_gyms=None)
        assert a.gyms == b.gyms
        assert a.creatures == b.creatures
        assert a.agent_start == b.agent_start
        assert a.chart.beats == b.chart.beats


# -- discrimination resolution scales with gym count --------------------------
def test_resolution_grows_with_gym_count():
    seeds = tuple(heldout_seeds(8))
    spread3, _ = _spread(3, seeds)
    spread8, win8 = _spread(8, seeds)
    # the oracle-vs-blind spread must widen materially with more gyms (finer resolution)
    assert spread8 > spread3 + 1.0
    # winnability survives at scale: oracle still clears most gyms
    assert win8 >= 0.70


def test_winnability_low_gym():
    # at the historical gym count, oracle clears essentially all present gyms.
    seeds = tuple(heldout_seeds(8))
    _, win3 = _spread(3, seeds)
    assert win3 >= 0.90


def test_classify_resolution_rule():
    # the pre-registered resolution verdict is a pure function of the rows.
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from difficulty_generalization import ResolutionRow, classify_resolution

    up = [
        ResolutionRow(3, 3.0, 3.0, 1.7, 1.2),   # spread 1.3
        ResolutionRow(5, 5.0, 5.0, 2.4, 1.9),   # spread 2.6
        ResolutionRow(8, 7.1, 7.1, 2.2, 1.6),   # spread 4.9, oracle/gyms 0.89
    ]
    assert classify_resolution(up) == "resolution-up"
    # non-monotone spread → insufficient
    bad = [
        ResolutionRow(3, 3.0, 3.0, 0.5, 0.5),   # spread 2.5
        ResolutionRow(8, 7.1, 7.1, 5.2, 5.0),   # spread 1.9 (dropped) + < 2.0
    ]
    assert classify_resolution(bad) == "insufficient"
