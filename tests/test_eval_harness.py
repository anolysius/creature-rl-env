"""Tests for the sealed held-out eval harness (eval-product/sealed-eval-harness).

The harness is the M5-enabler prototype of a *contamination-proof* eval: a private block
of held-out worlds the submitter never sees, RLVR-verified scoring, and a contamination
guard that proves the submitter could not have trained on the eval. These tests pin the
moat-load-bearing invariants: the sealed block is held-out + deterministic + regenerable,
the guard catches a train/eval leak, and scoring uses only verifiable subgoals.
"""
from __future__ import annotations

from critter_gym.eval_harness import (
    InferenceBaseline,
    InferenceTelemetry,
    Scorecard,
    SealedEvalSet,
    inference_baseline,
    score_agent,
    score_inference_telemetry,
    se_inference_score,
    verify_sealed,
)
from critter_gym.inference_rigor import classify_inference
from critter_gym.learnability import reference_arm
from critter_gym.region import TEST_SEED_OFFSET, is_held_out


# --- se_inference_score: place a super-effective-move rate on the [0,1] inference frame ---
# The #17 headline (LLM SE-rate ≈50%, a single pass) needs to be robust. Normalizing SE-rate
# between the chart-blind floor (type_blind, 0) and the expert (oracle, 1) puts it on the SAME
# frame as the gym-based inference_score, so the pre-registered classify_inference (#10) — its
# thresholds frozen — can turn N runs into a robust verdict without inventing new thresholds.
def test_se_inference_score_anchors() -> None:
    """oracle's SE-rate normalizes to 1.0, type_blind's to 0.0, a mid value lands strictly
    between, and a non-discriminating band (span <= 0) yields 0.0."""
    assert se_inference_score(1.0, 1.0, 0.27) == 1.0          # oracle anchor
    assert se_inference_score(0.27, 1.0, 0.27) == 0.0         # chart-blind anchor
    mid = se_inference_score(0.50, 1.0, 0.27)                 # LLM ≈50% on the corrected band
    assert 0.0 < mid < 1.0
    assert se_inference_score(1.0, 0.27, 0.27) == 0.0         # span <= 0 -> 0.0
    assert se_inference_score(2.0, 1.0, 0.0) == 1.0           # clamped to [0,1]


def test_se_inference_score_on_band() -> None:
    """On the corrected demonstrator band, the inferring proxy's normalized SE sits strictly
    between the chart-blind floor and the expert (deterministic)."""
    band = inference_baseline(_demonstrator())
    oracle_se = band.arms["oracle"].se_rate
    blind_se = band.arms["type_blind"].se_rate
    infer_score = se_inference_score(band.arms["infer"].se_rate, oracle_se, blind_se)
    assert 0.0 < infer_score < 1.0
    assert infer_score == se_inference_score(band.arms["infer"].se_rate, oracle_se, blind_se)


def test_classify_reuse_on_normalized_se_scores() -> None:
    """The frozen classify_inference (#10) is reused on normalized SE scores (same [0,1] frame):
    the expert's SE robustly reads `infers`, the chart-blind baseline `at-chart-blind-floor`."""
    band = inference_baseline(_demonstrator())
    o, b = band.arms["oracle"].se_rate, band.arms["type_blind"].se_rate
    oracle_runs = [se_inference_score(o, o, b)] * 3
    blind_runs = [se_inference_score(b, o, b)] * 3
    assert classify_inference(oracle_runs).verdict == "infers"
    assert classify_inference(blind_runs).verdict == "at-chart-blind-floor"


# --- inference baseline: the 4-arm scripted band a re-measurement is read against ---
# After matchup-validity (#15) corrected the held-out world distribution, the scripted
# arms must be re-characterized so an LLM's score is interpretable against a valid band.
# Config = the inference demonstrator (grid5, types3, boss 140/6/18) used by the runner.
def _demonstrator() -> SealedEvalSet:
    return SealedEvalSet(
        master_seed=20260627, n_worlds=8, num_types=3,
        grid_size=5, boss_hp=140, boss_atk=6, boss_def=18,
    )


def test_inference_baseline_band_is_monotone() -> None:
    """The super-effective-rate band is ordered oracle >= infer >= type_blind >= probe,
    with the chart-knowing expert at the 1.0 ceiling — so an inferring agent is cleanly
    separable from a chart-blind one (the eval's discrimination power, attrition-proof).
    """
    base = inference_baseline(_demonstrator())
    assert isinstance(base, InferenceBaseline)
    se = [base.arms[a].se_rate for a in ("oracle", "infer", "type_blind", "probe")]
    assert se == sorted(se, reverse=True), f"SE-rate band not monotone: {se}"
    assert base.arms["oracle"].se_rate == 1.0
    assert base.arms["infer"].se_rate > base.arms["type_blind"].se_rate  # inference shows


def test_inference_baseline_is_deterministic() -> None:
    """Same sealed set -> identical band (scripted arms are deterministic)."""
    assert inference_baseline(_demonstrator()) == inference_baseline(_demonstrator())


def test_inference_baseline_inference_score_anchors() -> None:
    """inference_score normalizes gym-clears between the chart-blind floor (0) and expert (1):
    oracle anchors at 1.0, type_blind at 0.0.

    Honest finding pinned here: gym-clears *saturate* on this inference-gated config — the
    inferring arm matches the oracle (within-episode learning + attrition clears every winnable
    gym), so its gym-based inference_score also reads 1.0 and gym-clears do NOT discriminate
    inference from expertise (the #12 attrition confound). The attrition-proof ``se_rate`` band
    is the real discriminator: the inferring arm reads far above the chart-blind floor.
    """
    base = inference_baseline(_demonstrator())
    assert base.arms["oracle"].inference_score == 1.0
    assert base.arms["type_blind"].inference_score == 0.0
    # gym-clears saturate -> not a discriminator here; se_rate is.
    assert base.arms["infer"].se_rate > base.arms["type_blind"].se_rate


# --- AC1: sealed held-out block (private, deterministic, regenerable) ---------
def test_eval_seeds_are_all_held_out() -> None:
    s = SealedEvalSet(master_seed=7, n_worlds=12)
    seeds = s._eval_seeds()
    assert len(seeds) == 12
    assert all(is_held_out(x) for x in seeds)  # every world is in the test region (>=1M)


def test_eval_seeds_deterministic_same_master() -> None:
    a = SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds()
    b = SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds()
    assert a == b  # same master_seed -> same sealed block (reproducible)


def test_eval_seeds_regenerate_different_master() -> None:
    a = set(SealedEvalSet(master_seed=7, n_worlds=12)._eval_seeds())
    b = set(SealedEvalSet(master_seed=8, n_worlds=12)._eval_seeds())
    assert a != b  # a different master_seed yields a fresh, different block


def test_sealed_defaults_difficulty_levers_backward_compat() -> None:
    # Defaults equal the CritterEnv defaults, so the sealed env is byte-identical to before.
    s = SealedEvalSet(master_seed=7, n_worlds=2)
    assert s.patch_radius == 2 and s.num_gyms == 3
    env = s.env_factory()()
    assert env.patch_radius == 2 and env.num_gyms == 3


def test_sealed_env_honors_difficulty_levers() -> None:
    # A sealed eval carries patch_radius/num_gyms into its env (faithful to a tuned tier).
    s = SealedEvalSet(master_seed=7, n_worlds=2, grid_size=16, patch_radius=1, num_gyms=5)
    env = s.env_factory()()
    assert env.patch_radius == 1 and env.num_gyms == 5


def test_sealed_rejects_invalid_levers() -> None:
    import pytest
    with pytest.raises(ValueError):
        SealedEvalSet(master_seed=7, patch_radius=-1)
    with pytest.raises(ValueError):
        SealedEvalSet(master_seed=7, num_gyms=0)


# --- AC2: contamination guard (the moat mechanic) ----------------------------
def test_verify_sealed_clean_train_ok() -> None:
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    cert = verify_sealed(declared_train_seeds=range(0, 5000), sealed=s)
    assert cert.ok is True
    assert cert.overlap == 0
    assert cert.all_eval_held_out is True
    assert cert.n_eval == 8


def test_verify_sealed_catches_leak() -> None:
    # A submitter who (dishonestly or accidentally) trained on the sealed eval seeds.
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    leaked = list(range(0, 100)) + list(s._eval_seeds())  # includes the sealed block
    cert = verify_sealed(declared_train_seeds=leaked, sealed=s)
    assert cert.ok is False
    assert cert.overlap == 8  # all 8 sealed seeds detected in the declared train set


def test_verify_sealed_rejects_out_of_region_train() -> None:
    # Declaring "train" seeds in the held-out region is itself illegal (train must be <1M).
    s = SealedEvalSet(master_seed=1, n_worlds=8)
    cert = verify_sealed(declared_train_seeds=[0, 1, TEST_SEED_OFFSET + 999], sealed=s)
    assert cert.ok is False


# --- AC3 + AC4: RLVR-verified scoring + submission interface ------------------
def test_score_agent_oracle_beats_random_and_rates_bounded() -> None:
    s = SealedEvalSet(master_seed=3, n_worlds=8)

    oracle_card = score_agent(reference_arm("oracle"), s)  # EnvPolicy reference
    random_card = score_agent(_RandomAgent(seed=0), s)

    assert isinstance(oracle_card, Scorecard)
    assert oracle_card.n_worlds == 8
    # oracle is a strong reference; it should out-clear a random agent on the sealed worlds.
    assert oracle_card.mean_gyms_cleared > random_card.mean_gyms_cleared
    # RLVR rates are proper fractions; frac_of_oracle is non-negative.
    for card in (oracle_card, random_card):
        assert 0.0 <= card.cleared_rate <= 1.0
        assert 0.0 <= card.caught_rate <= 1.0
        assert 0.0 <= card.evolved_rate <= 1.0
        assert card.frac_of_oracle >= 0.0
    # The sealed certificate travels with the scorecard.
    assert card.n_worlds == 8


def test_score_agent_obs_only_interface() -> None:
    """An obs-only `Agent` (act(obs)->int) is accepted — same interface an LLM agent uses."""
    s = SealedEvalSet(master_seed=5, n_worlds=6)
    card = score_agent(_RandomAgent(seed=1), s)
    assert card.n_worlds == 6
    assert card.frac_of_oracle >= 0.0


# --- inference-telemetry: super-effective-move rate (direct inference signal) ---------
class _WaitAgent:
    """An agent that always Waits (5) — never moves, so it never reaches a gym / battles."""

    def act(self, obs: object) -> int:
        return 5


def test_telemetry_oracle_exploits_chart_blind_is_lower() -> None:
    """AC3: the expert exploits the hidden chart (high SE-rate); the chart-blind arm is lower."""
    s = SealedEvalSet(master_seed=3, n_worlds=6, num_types=3,
                      grid_size=5, boss_hp=120, boss_atk=12, boss_def=12, max_steps=40)
    oracle = score_inference_telemetry(reference_arm("oracle"), s)
    blind = score_inference_telemetry(reference_arm("type_blind"), s)
    assert isinstance(oracle, InferenceTelemetry)
    assert oracle.n_battle_moves > 0                       # battles happened
    assert oracle.super_effective_rate >= 0.5              # expert exploits the chart
    assert oracle.super_effective_rate >= blind.super_effective_rate  # vs chart-blind


def test_telemetry_rate_in_unit_interval_and_deterministic() -> None:
    """AC3: rate ∈ [0,1] and deterministic for a deterministic submission + seeds."""
    s = SealedEvalSet(master_seed=5, n_worlds=4, num_types=3, grid_size=5, max_steps=40)
    a = score_inference_telemetry(_RandomAgent(seed=1), s)
    b = score_inference_telemetry(_RandomAgent(seed=1), s)
    assert 0.0 <= a.super_effective_rate <= 1.0
    assert a == b                                          # same seed-set + agent -> identical


def test_telemetry_zero_battle_moves_guarded() -> None:
    """AC1: an agent that never battles -> 0 moves -> rate 0.0 (no div-by-zero)."""
    s = SealedEvalSet(master_seed=2, n_worlds=2, num_types=3, grid_size=5, max_steps=20)
    tel = score_inference_telemetry(_WaitAgent(), s)
    assert tel.n_battle_moves == 0
    assert tel.super_effective_rate == 0.0


def test_telemetry_is_read_only_score_agent_unchanged() -> None:
    """AC2: running telemetry does not perturb score_agent numerics (env read-only)."""
    s = SealedEvalSet(master_seed=3, n_worlds=8)
    before = score_agent(reference_arm("oracle"), s)
    score_inference_telemetry(reference_arm("oracle"), s)  # must not mutate anything shared
    after = score_agent(reference_arm("oracle"), s)
    assert (before.mean_gyms_cleared, before.inference_score) == (
        after.mean_gyms_cleared, after.inference_score
    )


class _RandomAgent:
    """A trivial obs-only submission: act(obs) -> action (Agent Protocol)."""

    def __init__(self, seed: int) -> None:
        import numpy as np

        self._rng = np.random.default_rng(seed)

    def act(self, obs: object) -> int:
        return int(self._rng.integers(0, 6))


# --- stateful-llm-agent: optional per-episode reset() hook -------------------
class _ResetCountingAgent:
    """A stateful submission that counts reset() calls and the steps since the last reset."""

    def __init__(self) -> None:
        self.resets = 0
        self.max_run = 0
        self._run = 0

    def reset(self) -> None:
        self.resets += 1
        self._run = 0

    def act(self, obs: object) -> int:
        self._run += 1
        self.max_run = max(self.max_run, self._run)
        return 5  # Wait


def test_score_agent_calls_reset_once_per_episode() -> None:
    """A submission's optional reset() fires exactly once per sealed world (memory isolation)."""
    s = SealedEvalSet(master_seed=9, n_worlds=5, max_steps=6)
    agent = _ResetCountingAgent()
    score_agent(agent, s)
    assert agent.resets == 5            # one reset per world, not per step
    assert agent.max_run <= 6           # each episode is independently capped


def test_score_agent_stateless_submission_unaffected() -> None:
    """A submission WITHOUT reset() runs exactly as before (byte-identical regression gate)."""
    s = SealedEvalSet(master_seed=3, n_worlds=8)
    before = score_agent(_RandomAgent(seed=0), s)
    after = score_agent(_RandomAgent(seed=0), s)
    assert (before.mean_gyms_cleared, before.cleared_rate, before.frac_of_oracle) == (
        after.mean_gyms_cleared, after.cleared_rate, after.frac_of_oracle
    )


# --- llm-eval-run: max_steps cost cap on SealedEvalSet -----------------------
def test_sealed_max_steps_caps_episode_length() -> None:
    """A small `max_steps` caps the episode (cost control for per-step LLM eval)."""
    sealed = SealedEvalSet(master_seed=2, n_worlds=2, max_steps=8)
    env = sealed.env_factory()()
    env.reset(seed=sealed._eval_seeds()[0])
    steps, done = 0, False
    while not done and steps < 1000:
        _o, _r, term, trunc, _i = env.step(5)  # Wait
        steps += 1
        done = bool(term or trunc)
    assert steps <= 8  # truncated at the cap


def test_sealed_default_max_steps_unchanged() -> None:
    """The default (max_steps=200) leaves the env behavior byte-identical."""
    sealed = SealedEvalSet(master_seed=2, n_worlds=2)  # no max_steps -> 200
    env = sealed.env_factory()()
    assert env.max_steps == 200


# --- inference-score-metric: config knobs + inference_score KPI --------------
def test_sealed_world_battle_knobs_reach_env() -> None:
    """AC1: grid_size / boss knobs flow through env_factory to the CritterEnv."""
    sealed = SealedEvalSet(master_seed=4, n_worlds=2, num_types=3,
                           grid_size=5, boss_hp=140, boss_atk=6, boss_def=18)
    env = sealed.env_factory()()
    assert env.grid_size == 5
    assert (env.boss_hp, env.boss_atk, env.boss_def) == (140, 6, 18)


def test_sealed_default_knobs_are_env_defaults() -> None:
    """AC1: defaults match CritterEnv defaults => existing sealed sets are byte-identical."""
    env = SealedEvalSet(master_seed=4, n_worlds=2).env_factory()()
    assert env.grid_size == 10
    assert (env.boss_hp, env.boss_atk, env.boss_def) == (120, 12, 12)


def test_inference_score_oracle_is_one_blind_is_zero() -> None:
    """AC2/AC3: the expert (oracle) scores 1.0, the chart-blind baseline scores 0.0."""
    # An inference-gated band: small navigable grid + a boss that kills before a blind agent
    # can brute-force it (oracle 1.67 vs type_blind 0.33 here, so the gap is real).
    s = SealedEvalSet(master_seed=3, n_worlds=6, num_types=3,
                      grid_size=5, boss_hp=120, boss_atk=12, boss_def=12, max_steps=40)
    oracle_card = score_agent(reference_arm("oracle"), s)
    assert oracle_card.oracle_gyms > oracle_card.type_blind_gyms  # band discriminates
    assert oracle_card.inference_score == 1.0
    assert score_agent(reference_arm("type_blind"), s).inference_score == 0.0


def test_inference_score_in_unit_interval() -> None:
    """AC3: any submission's inference score is clamped to [0, 1]."""
    s = SealedEvalSet(master_seed=5, n_worlds=6)
    score = score_agent(_RandomAgent(seed=2), s).inference_score
    assert 0.0 <= score <= 1.0


def test_inference_score_zero_when_band_does_not_discriminate() -> None:
    """AC3: when oracle <= type_blind (no inference gap), the score is 0.0 (denominator guard).

    A weak boss on a tiny grid is winnable even without the type chart, so oracle == type_blind."""
    s = SealedEvalSet(master_seed=6, n_worlds=3, num_types=3,
                      grid_size=5, boss_hp=70, boss_atk=4, boss_def=8)
    card = score_agent(reference_arm("oracle"), s)
    assert card.oracle_gyms <= card.type_blind_gyms  # band does not discriminate
    assert card.inference_score == 0.0


# --- claude-cli-provider: score_agent runs the submission ONCE per seed --------
def test_score_agent_single_pass_no_double_run() -> None:
    """score_agent must query the submission exactly one episode per seed (not twice —
    the old `_caught_rate` re-run doubled per-step LLM calls)."""
    class _Counter:
        def __init__(self) -> None:
            self.calls = 0

        def act(self, obs: object) -> int:
            self.calls += 1
            return 5  # Wait — keeps episodes at the max_steps cap

    n_worlds, cap = 2, 6
    c = _Counter()
    score_agent(c, SealedEvalSet(master_seed=9, n_worlds=n_worlds, max_steps=cap))
    # one pass = n_worlds episodes of <= cap steps; the old double-run would be ~2x this.
    assert c.calls <= n_worlds * cap
    assert c.calls > 0
