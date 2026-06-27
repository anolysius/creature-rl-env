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
from critter_gym.llm_eval import (
    LLMAgent,
    StatefulLLMAgent,
    parse_action,
    render_obs,
)


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


class _RecordingStub:
    """A stub `complete` that returns a fixed reply and records every prompt it received."""

    def __init__(self, reply: str = "wait") -> None:
        self.reply = reply
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.reply


# --- StatefulLLMAgent: AC1 protocol + optional reset hook -------------------
def test_stateful_agent_satisfies_protocol_and_has_reset() -> None:
    agent = StatefulLLMAgent(_StubLLM("wait"))
    assert isinstance(agent, Agent)  # same act(obs)->int Protocol as LLMAgent
    assert isinstance(agent.act(_sample_obs(0)), int)
    assert callable(agent.reset)  # optional per-episode hook score_agent will call


# --- AC2: history accumulates within an episode and the window bounds it -----
def test_stateful_history_accumulates_and_window_is_bounded() -> None:
    agent = StatefulLLMAgent(_StubLLM("0"), window=3)
    obs = _sample_obs(0)
    for _ in range(2):
        agent.act(obs)
    assert len(agent._history) == 2          # grows one per step
    for _ in range(5):
        agent.act(obs)
    assert len(agent._history) == 3          # capped at window (oldest dropped)


def test_stateful_window_zero_is_effectively_memoryless() -> None:
    agent = StatefulLLMAgent(_RecordingStub("5"), window=0)
    obs = _sample_obs(1)
    for _ in range(3):
        agent.act(obs)
    assert agent._history == []              # nothing retained
    # no prompt ever carried a history block
    assert all("Recent history" not in p for p in agent._complete.prompts)  # type: ignore[attr-defined]


# --- AC2/AC3: the prompt actually carries past actions, reset clears them ----
def test_stateful_prompt_includes_recent_history() -> None:
    stub = _RecordingStub("2")  # always "move east"
    agent = StatefulLLMAgent(stub, window=8)
    obs = _sample_obs(0)
    agent.act(obs)                           # 1st call: no history yet
    agent.act(obs)                           # 2nd call: history of step 1 present
    assert "Recent history" not in stub.prompts[0]
    assert "Recent history" in stub.prompts[1]
    assert "action 2" in stub.prompts[1]     # the recorded past action


def test_stateful_reset_clears_history_and_isolates() -> None:
    stub = _RecordingStub("1")
    agent = StatefulLLMAgent(stub, window=8)
    obs = _sample_obs(0)
    agent.act(obs)
    agent.act(obs)
    assert len(agent._history) == 2
    agent.reset()
    assert agent._history == []              # AC3: memory cleared between worlds
    # the next act after reset starts clean — no leakage from the prior episode
    agent.act(obs)
    assert "Recent history" not in stub.prompts[-1]


def test_stateful_invalid_window_raises() -> None:
    import pytest

    with pytest.raises(ValueError):
        StatefulLLMAgent(_StubLLM("wait"), window=-1)


# --- AC1/AC3: end-to-end on a sealed set, reset called per world -------------
def test_stateful_agent_scores_end_to_end_on_sealed_set() -> None:
    sealed = SealedEvalSet(master_seed=11, n_worlds=4)
    stub = _StubLLM("Action: 0")
    card = score_agent(StatefulLLMAgent(stub, window=4), sealed)
    assert isinstance(card, Scorecard)
    assert card.n_worlds == 4
    assert stub.calls > 0
    assert 0.0 <= card.cleared_rate <= 1.0


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


def test_claude_cli_complete_exists_and_errors_on_missing_binary() -> None:
    """`claude_cli_complete` builds a subscription-backed complete() via the local `claude`
    CLI; a non-existent binary raises a clear FileNotFoundError (so misconfig is obvious)."""
    from critter_gym import llm_eval

    assert hasattr(llm_eval, "claude_cli_complete")
    import pytest

    with pytest.raises(FileNotFoundError):
        llm_eval.claude_cli_complete(binary="definitely-not-a-real-binary-xyz")
