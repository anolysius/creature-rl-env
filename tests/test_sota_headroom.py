"""Pre-registered scaled-headroom classifier (numpy-only, CI — no jax) (sota-headroom).

#3 measured a *deliberately narrow* recurrent PPO (GRU h128) at 43% of oracle on the hard
config and called it hard-and-learnable ROBUST — but a narrow net leaves a capacity confound
("is it hard, or did we under-power the agent?"). `classify_scaled_headroom` takes a
capacity+budget *sweep* of the strongest arm, picks the best NON-tiny config as the credible
"materially stronger baseline", and applies the SAME pre-registered `classify_headroom`
(frac=0.75, k=1.0) to it — with a non-vacuity guard so an underfit sweep can't yield a hollow
"robust". The training itself needs jax; this decision rule is pure numpy so CI can prove its
branches deterministically.
"""

from __future__ import annotations

import pytest

from critter_gym.headroom import classify_scaled_headroom

TINY = "tiny h128"


def test_robust_hard_even_for_best_scaled() -> None:
    # best-scaled (wide) beats tiny but its optimistic bound stays well below 0.75*oracle.
    sweep = {TINY: [1.8, 2.0, 2.2], "wide h256": [2.3, 2.5, 2.4], "wider h384": [2.4, 2.6, 2.5]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wider h384"  # best non-tiny by mean (2.50 > 2.40)
    assert v.non_vacuous is True and v.exceeds is False
    assert v.verdict == "hard-and-learnable"  # mean 2.50 + std ~0.08 << 3.75


def test_closes_best_scaled_reaches_oracle_band() -> None:
    # best-scaled nearly reaches the oracle: pessimistic bound >= 0.75*oracle => closes.
    sweep = {TINY: [2.0, 2.1, 2.2], "wide h256": [4.0, 4.1, 4.2], "wider h384": [4.3, 4.4, 4.5]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wider h384"
    assert v.non_vacuous is True and v.exceeds is False
    assert v.verdict == "ppo-closes"  # mean 4.40 - std ~0.08 = 4.32 >= 3.75


def test_exceeds_oracle_flagged() -> None:
    # best-scaled beats the scripted oracle outright => oracle isn't a valid ceiling here.
    sweep = {TINY: [2.0, 2.0, 2.0], "wide h256": [5.5, 5.6, 5.7]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wide h256"
    assert v.exceeds is True and v.non_vacuous is True


def test_vacuous_best_scaled_does_not_beat_tiny() -> None:
    # every scaled config underfits (<= tiny) => the "robust" read would be hollow => vacuous.
    sweep = {TINY: [2.5, 2.6, 2.7], "wide h256": [2.0, 2.1, 2.2], "wider h384": [1.5, 1.6, 1.7]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wide h256"  # best non-tiny (2.10) but still < tiny (2.60)
    assert v.non_vacuous is False
    # verdict may compute as hard-and-learnable, but non_vacuous=False signals it's not usable.


def test_inconclusive_band_straddles_threshold() -> None:
    # run band straddles 0.75*oracle (=3.75): neither bound clears it.
    sweep = {TINY: [2.0, 2.0, 2.0], "wide h256": [3.0, 3.75, 4.5]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wide h256"
    assert v.verdict == "inconclusive"


def test_tiny_excluded_from_best_selection() -> None:
    # even if tiny has the highest mean, it is never selected as the strong baseline.
    sweep = {TINY: [4.9, 5.0, 5.1], "wide h256": [2.0, 2.1, 2.2]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert v.strong_label == "wide h256"
    assert v.non_vacuous is False  # scaled (2.1) < tiny (5.0)


def test_frac_and_k_are_honored() -> None:
    # a stricter frac lowers the threshold; the same runs then read differently.
    sweep = {TINY: [2.0, 2.0, 2.0], "wide h256": [3.0, 3.0, 3.0]}
    lenient = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY, frac=0.75)
    strict = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY, frac=0.5)
    assert lenient.verdict == "hard-and-learnable"  # 3.0 <= 3.75
    assert strict.verdict == "ppo-closes"  # 3.0 >= 2.5


def test_empty_sweep_raises() -> None:
    with pytest.raises(ValueError):
        classify_scaled_headroom({}, oracle=5.0, tiny_label=TINY)


def test_no_non_tiny_config_raises() -> None:
    # a sweep with only the tiny config has no strong baseline to classify.
    with pytest.raises(ValueError):
        classify_scaled_headroom({TINY: [2.0, 2.1]}, oracle=5.0, tiny_label=TINY)


def test_non_positive_oracle_raises() -> None:
    sweep = {TINY: [2.0], "wide h256": [3.0]}
    with pytest.raises(ValueError):
        classify_scaled_headroom(sweep, oracle=0.0, tiny_label=TINY)


def test_missing_tiny_label_raises() -> None:
    with pytest.raises(ValueError):
        classify_scaled_headroom({"wide h256": [3.0]}, oracle=5.0, tiny_label=TINY)


def test_verdict_is_serializable_plain_types() -> None:
    sweep = {TINY: [2.0, 2.1], "wide h256": [2.5, 2.6]}
    v = classify_scaled_headroom(sweep, oracle=5.0, tiny_label=TINY)
    assert isinstance(v.strong_label, str)
    assert all(isinstance(x, float) for x in (v.strong_mean, v.strong_std, v.oracle, v.ratio))
    assert isinstance(v.verdict, str)
    assert isinstance(v.non_vacuous, bool) and isinstance(v.exceeds, bool)
