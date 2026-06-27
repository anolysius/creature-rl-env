"""Tests for the agentic-LLM eval adapter (eval-product/llm-eval-adapter).

The adapter lets an LLM agent be scored on the sealed held-out harness (#1): the env obs is
rendered to text, the LLM's reply is parsed into an action, and `eval_harness.score_agent`
does the RLVR-verified scoring on worlds the LLM never saw. These tests pin the mechanism —
deterministic rendering, robust parsing (incl. garbage → safe fallback), and that an
`LLMAgent` satisfies the #1 `Agent` Protocol and scores end-to-end with a stub LLM (no API).
"""
from __future__ import annotations

import numpy as np

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.eval_harness import Agent, Scorecard, SealedEvalSet, score_agent
from critter_gym.llm_eval import LLMAgent, parse_action, render_obs


def _sample_obs(seed: int = 0):
    env = CritterEnv(commit_battles=True, vary=True, num_types=8)
    obs, _ = env.reset(seed=seed)
    return obs


# --- AC1: deterministic, legible text rendering -----------------------------
def test_render_obs_is_deterministic() -> None:
    obs = _sample_obs(0)
    assert render_obs(obs) == render_obs(obs)  # same obs -> same string


def test_render_obs_includes_core_fields() -> None:
    text = render_obs(_sample_obs(0)).lower()
    assert "position" in text          # agent_pos
    assert "battle" in text            # in_battle
    assert "gym" in text               # gyms_defeated
    # an action legend with the six action indices
    for i in range(6):
        assert str(i) in text


# --- AC2: robust parsing (number / keyword / garbage -> fallback / clamp) ----
def test_parse_action_plain_number() -> None:
    assert parse_action("2") == 2
    assert parse_action("I will choose action 3 (move west).") == 3


def test_parse_action_keywords() -> None:
    assert parse_action("Go north") == 0
    assert parse_action("move SOUTH now") == 1
    assert parse_action("head east") == 2
    assert parse_action("west") == 3
    assert parse_action("I'll catch it") == 4
    assert parse_action("just wait") == 5


def test_parse_action_garbage_falls_back_to_wait() -> None:
    assert parse_action("") == 5
    assert parse_action("hmm not sure what to do here") == 5
    assert parse_action("\n\n???") == 5


def test_parse_action_out_of_range_is_clamped() -> None:
    a = parse_action("action 9")
    assert 0 <= a < 6


def test_parse_action_all_in_bounds() -> None:
    for reply in ["0", "5", "north", "garbage", "", "99", "-3"]:
        a = parse_action(reply, n_actions=6)
        assert isinstance(a, int) and 0 <= a < 6


# --- AC3: LLMAgent satisfies the #1 Agent Protocol + scores end-to-end -------
class _StubLLM:
    """A deterministic stand-in for an LLM `complete(prompt) -> reply` function."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.calls = 0

    def __call__(self, prompt: str) -> str:
        self.calls += 1
        return self.reply


def test_llm_agent_satisfies_agent_protocol() -> None:
    agent = LLMAgent(_StubLLM("wait"))
    assert isinstance(agent, Agent)  # the #1 runtime_checkable Agent Protocol
    assert isinstance(agent.act(_sample_obs(0)), int)


def test_llm_agent_scores_end_to_end_on_sealed_set() -> None:
    sealed = SealedEvalSet(master_seed=11, n_worlds=4)
    stub = _StubLLM("Let me go north. Action: 0")
    card = score_agent(LLMAgent(stub), sealed)
    assert isinstance(card, Scorecard)
    assert card.n_worlds == 4
    assert stub.calls > 0  # the LLM (stub) was actually queried per step
    assert 0.0 <= card.cleared_rate <= 1.0
    assert card.frac_of_oracle >= 0.0


def test_anthropic_complete_is_optional_lazy() -> None:
    """`anthropic_complete` must not import `anthropic` at module import time, and must give a
    clear error if the package/key is missing (so CI never needs the SDK)."""
    from critter_gym import llm_eval

    assert hasattr(llm_eval, "anthropic_complete")
    # Building it without the SDK installed raises a clear ImportError (not at module load).
    try:
        import anthropic  # noqa: F401
    except ImportError:
        import pytest

        with pytest.raises(ImportError):
            llm_eval.anthropic_complete()


def test_obs_render_handles_numpy_scalars() -> None:
    # in_battle etc. are shape-(1,) numpy arrays — rendering must not crash on them.
    obs = _sample_obs(2)
    obs = {k: np.asarray(v) for k, v in obs.items()}
    assert isinstance(render_obs(obs), str)
