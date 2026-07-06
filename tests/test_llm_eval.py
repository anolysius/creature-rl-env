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
    DEFAULT_SYSTEM,
    BattleMemoryLLMAgent,
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


# --- render_obs legibility (render-obs-legibility) ---------------------------
def _make_obs(*, in_battle=0, patch=None, player=(0, 0, 0), enemy=(0, 0), pos=(5, 5)):
    """Build a minimal synthetic observation for render_obs unit tests."""
    if patch is None:
        patch = np.zeros((5, 5), dtype=np.int8)
    return {
        "agent_pos": np.array(pos, dtype=np.int64),
        "local_patch": np.asarray(patch, dtype=np.int8),
        "caught": np.array([0], dtype=np.int64),
        "gyms_defeated": np.array([0], dtype=np.int64),
        "evolved": np.array([0], dtype=np.int64),
        "in_battle": np.array([in_battle], dtype=np.int8),
        "player_hp": np.array([player[0]], dtype=np.int64),
        "player_type": np.array([player[1]], dtype=np.int64),
        "player_level": np.array([player[2]], dtype=np.int64),
        "enemy_hp": np.array([enemy[0]], dtype=np.int64),
        "enemy_type": np.array([enemy[1]], dtype=np.int64),
        "player_charge": np.array([0], dtype=np.int64),
        "enemy_charge": np.array([0], dtype=np.int64),
    }


def test_render_overworld_does_not_mislead_with_zero_hp() -> None:
    # AC1: outside battle, player_* are 0-masked — must NOT print "Your creature: hp 0"
    # (the LLM read that as "I have no creature"). Show the truth instead.
    text = render_obs(_make_obs(in_battle=0, player=(0, 0, 0)))
    assert "Your creature: hp 0" not in text
    assert "starter party" in text.lower()


def test_render_battle_shows_player_and_enemy_stats() -> None:
    # AC2: during battle the active creatures' real stats ARE shown.
    text = render_obs(_make_obs(in_battle=1, player=(12, 3, 4), enemy=(9, 1)))
    assert "Your creature: hp 12" in text
    assert "Enemy: hp 9" in text


def test_render_gym_salience_and_on_gym_flag() -> None:
    # AC3: a visible gym is called out with direction; being ON a gym is flagged.
    from critter_gym.envs.critter_env import _PATCH_GYM

    patch = np.zeros((5, 5), dtype=np.int8)
    patch[0, 2] = _PATCH_GYM  # gym 2 tiles north of center (env code, not a bare literal)
    text = render_obs(_make_obs(in_battle=0, patch=patch)).lower()
    assert "gym (g) is visible" in text and "2 north" in text

    on_gym = np.zeros((5, 5), dtype=np.int8)
    on_gym[2, 2] = _PATCH_GYM  # standing on a gym
    text2 = render_obs(_make_obs(in_battle=0, patch=on_gym)).lower()
    assert "on a gym" in text2 and "boss battle" in text2


def test_render_creature_salience() -> None:
    # AC3: a visible wild creature is called out; one on your tile prompts Catch.
    from critter_gym.envs.critter_env import _PATCH_CREATURE

    patch = np.zeros((5, 5), dtype=np.int8)
    patch[2, 4] = _PATCH_CREATURE  # creature 2 tiles east (env code, not a bare literal)
    text = render_obs(_make_obs(in_battle=0, patch=patch)).lower()
    assert "wild creature (c) is visible" in text and "2 east" in text

    on_c = np.zeros((5, 5), dtype=np.int8)
    on_c[2, 2] = _PATCH_CREATURE
    text2 = render_obs(_make_obs(in_battle=0, patch=on_c)).lower()
    assert "on your tile" in text2 and "catch" in text2


def test_render_obs_glyphs_match_env_patch_codes() -> None:
    # SSOT guard (render-obs-tile-codes): render_obs MUST use the env's actual local_patch codes.
    # The bug it pins: glyphs/salience assumed gym=3, creature=2, but the env emits
    # _PATCH_CREATURE=1, _PATCH_GYM=2 — so the LLM saw gyms as "C" creatures and creatures as
    # "#" walls, and never a real "G". Import the env constants so this can never drift again.
    from critter_gym.envs.critter_env import _PATCH_CREATURE, _PATCH_GYM

    def _glyph_rows(text: str) -> list[str]:
        return [ln for ln in text.splitlines()
                if ln.startswith("  ") and set(ln.strip().split()) <= set(".#CG") and ln.strip()]

    # A gym (env code _PATCH_GYM) two tiles north → rendered "G" + announced as a gym.
    patch = np.zeros((5, 5), dtype=np.int8)
    patch[0, 2] = _PATCH_GYM
    text = render_obs(_make_obs(in_battle=0, patch=patch))
    assert any("G" in r for r in _glyph_rows(text))          # a literal G in the map grid
    low = text.lower()
    assert "gym (g) is visible" in low and "2 north" in low
    assert "wild creature" not in low                         # the gym must NOT read as a creature

    # A creature (env code _PATCH_CREATURE) two tiles east → rendered "C" + announced as creature.
    patch2 = np.zeros((5, 5), dtype=np.int8)
    patch2[2, 4] = _PATCH_CREATURE
    text2 = render_obs(_make_obs(in_battle=0, patch=patch2))
    assert any("C" in r for r in _glyph_rows(text2))
    assert "wild creature (c) is visible" in text2.lower() and "2 east" in text2.lower()

    # Centre flags use the right codes: standing ON a gym vs ON a creature.
    on_gym = np.zeros((5, 5), dtype=np.int8)
    on_gym[2, 2] = _PATCH_GYM
    assert "on a gym" in render_obs(_make_obs(in_battle=0, patch=on_gym)).lower()
    on_c = np.zeros((5, 5), dtype=np.int8)
    on_c[2, 2] = _PATCH_CREATURE
    assert "on your tile" in render_obs(_make_obs(in_battle=0, patch=on_c)).lower()


def test_render_obs_real_env_patch_renders_gym_or_creature_glyph() -> None:
    # Cross-check against a REAL CritterEnv obs (the synthetic tests above missed the bug because
    # they used the renderer's own wrong codes). Find a reset whose 5x5 patch contains a gym or a
    # creature, and assert the rendered grid shows the matching glyph (G/C), never a stray '#'.
    from critter_gym.envs.critter_env import _PATCH_CREATURE, _PATCH_GYM

    for seed in range(1_000_000, 1_000_040):
        obs = _sample_obs(seed)
        patch = np.asarray(obs["local_patch"])
        codes = {int(x) for x in patch.flatten()}
        if _PATCH_GYM in codes or _PATCH_CREATURE in codes:
            text = render_obs(obs)
            grid = "\n".join(ln for ln in text.splitlines() if ln.startswith("  "))
            assert "#" not in grid          # the wall glyph must never appear (no wall code exists)
            if _PATCH_GYM in codes:
                assert "G" in grid          # a real gym renders as G, not as C/#
            if _PATCH_CREATURE in codes:
                assert "C" in grid
            return
    raise AssertionError("no gym/creature appeared in any sampled patch — widen the seed range")


def test_render_obs_still_deterministic_and_has_core_fields() -> None:
    # AC4: determinism + core fields preserved after the legibility changes.
    obs = _sample_obs(1)
    assert render_obs(obs) == render_obs(obs)
    low = render_obs(obs).lower()
    assert "position" in low and "in battle" in low and "gym" in low
    for i in range(6):
        assert str(i) in low


def test_default_system_explains_party_goal_and_catch() -> None:
    # AC5: the system prompt tells the LLM it has a party, the gym goal, and the catch flow.
    s = DEFAULT_SYSTEM.lower()
    assert "starter party" in s
    assert "gym" in s
    assert "catch" in s


# --- battle legibility (battle-legibility) -----------------------------------
def test_default_system_explains_battle_strategy() -> None:
    # AC1: the system prompt explains the battle mechanic — moves have different hidden types,
    # try-and-remember, switch, retry — WITHOUT revealing which move is super-effective.
    s = DEFAULT_SYSTEM.lower()
    assert "different hidden type" in s          # moves 0-3 differ by hidden type
    assert "switch" in s                          # party switch is available
    assert "super-effective" in s                 # the concept is named (not the answer)
    assert "again" in s or "re-enter" in s        # retry after a loss


def test_render_battle_has_tactical_hint_and_keeps_stats() -> None:
    # AC2: battle render nudges move-variety / enemy-hp observation / switch, and still shows stats.
    text = render_obs(_make_obs(in_battle=1, player=(12, 3, 4), enemy=(9, 1)))
    assert "Your creature: hp 12" in text and "Enemy: hp 9" in text   # stats preserved
    low = text.lower()
    assert "moves 0-3" in low and "hidden type" in low                # try-different-moves hint
    assert "switch" in low


def test_overworld_render_has_no_battle_tactical_hint() -> None:
    # AC4: the battle tip must NOT leak onto the overworld (context-appropriate rendering).
    text = render_obs(_make_obs(in_battle=0)).lower()
    assert "moves 0-3" not in text


def test_default_system_clarifies_catch_is_creature_only() -> None:
    # AC3: Catch works only on a creature (C) tile, not a gym — stops the catch-loop waste.
    s = DEFAULT_SYSTEM.lower()
    assert "on their tile" in s
    assert "gym" in s and "catch does nothing on a gym" in s


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


# --- BattleMemoryLLMAgent (agentic-battle-memory) ---------------------------
# A "thicker" agentic memory: the StatefulLLMAgent forgets per-move battle outcomes (its digest
# is position+gyms only), so it discards the very damage-feedback signal hidden-chart inference
# needs. This agent records the RAW damage each attack move dealt per enemy type and surfaces it
# as facts — WITHOUT recommending an answer move (that would do the inference for the LLM and
# invalidate the measurement).


def _battle_obs(enemy_hp: int, enemy_type: int):
    """A minimal in-battle synthetic obs (enemy = (hp, type))."""
    return _make_obs(in_battle=1, enemy=(enemy_hp, enemy_type), player=(20, 0, 1))


def test_battle_memory_satisfies_protocol_and_has_reset() -> None:
    # AC1: satisfies the #1 Agent Protocol (act + optional reset).
    agent = BattleMemoryLLMAgent(_StubLLM("wait"))
    assert isinstance(agent, Agent)
    assert isinstance(agent.act(_sample_obs(0)), int)
    assert callable(agent.reset)


def test_battle_memory_records_observed_move_damage() -> None:
    # AC2: a move's dealt damage (enemy hp drop, same enemy) is attributed to the move chosen.
    agent = BattleMemoryLLMAgent(_StubLLM("1"))  # always picks attack move 1
    agent.act(_battle_obs(enemy_hp=50, enemy_type=3))   # choose move 1 vs enemy type 3
    agent.act(_battle_obs(enemy_hp=10, enemy_type=3))   # enemy hp 50 -> 10: move 1 dealt 40
    assert agent._battle_table[3][1] == 40


def test_battle_memory_overwrites_with_latest_single_value() -> None:
    # AC2: (enemy_type, move) keeps a single latest value (bounded), not a growing list.
    agent = BattleMemoryLLMAgent(_StubLLM("0"))  # always attack move 0
    agent.act(_battle_obs(enemy_hp=50, enemy_type=2))
    agent.act(_battle_obs(enemy_hp=30, enemy_type=2))   # move 0 dealt 20
    agent.act(_battle_obs(enemy_hp=25, enemy_type=2))   # move 0 dealt 5 (overwrites 20)
    assert agent._battle_table[2][0] == 5
    assert isinstance(agent._battle_table[2][0], int)   # single int, not a list


def test_battle_memory_table_is_bounded_per_enemy_type() -> None:
    # AC2: each enemy-type row holds at most 4 entries (moves 0-3), a single int each — bounded,
    # never a growing list, no matter how many battle turns are observed.
    import itertools

    moves = itertools.cycle("0123")

    class _CycleStub:
        def __call__(self, prompt: str) -> str:
            return next(moves)

    agent = BattleMemoryLLMAgent(_CycleStub())
    hp = 100
    for _ in range(40):  # 40 turns vs the same enemy type, cycling all four attack moves
        agent.act(_battle_obs(enemy_hp=hp, enemy_type=3))
        hp = max(1, hp - 3)
    row = agent._battle_table[3]
    assert len(row) <= 4                                  # only moves 0-3 are ever keyed
    assert all(isinstance(v, int) for v in row.values())  # one int per move, not a list


def test_battle_memory_surfaces_raw_damage_in_prompt() -> None:
    # AC2: the observed damage is surfaced to the LLM as a fact in a later battle turn.
    stub = _RecordingStub("1")
    agent = BattleMemoryLLMAgent(stub)
    agent.act(_battle_obs(enemy_hp=50, enemy_type=3))
    agent.act(_battle_obs(enemy_hp=10, enemy_type=3))
    low = stub.prompts[-1].lower()
    assert "enemy type 3" in low
    assert "move 1 dealt 40" in low


def test_battle_memory_no_answer_leak_in_notes() -> None:
    # AC3 (measurement integrity): the notes surface RAW facts only — never the hidden chart,
    # a recommended move, or "super-effective". The LLM must do the inference itself.
    agent = BattleMemoryLLMAgent(_StubLLM("1"))
    agent.act(_battle_obs(enemy_hp=50, enemy_type=3))
    agent.act(_battle_obs(enemy_hp=10, enemy_type=3))
    notes = agent._battle_notes_block(_battle_obs(enemy_hp=10, enemy_type=3)).lower()
    assert "dealt" in notes  # it does carry the observed facts
    for banned in ("best", "recommend", "should", "super-effective", "strongest", "use move"):
        assert banned not in notes


def test_battle_memory_docstring_states_honest_boundary() -> None:
    # AC8: the class docstring pins the honesty boundary (mechanism, not a measured result).
    doc = (BattleMemoryLLMAgent.__doc__ or "").lower()
    assert "mechanism" in doc
    assert "not a measured" in doc or "not a result" in doc


def test_battle_memory_no_attribution_on_enemy_change_or_non_attack() -> None:
    # AC2: don't attribute across an enemy change (faint/new enemy) or after a non-attack action.
    agent = BattleMemoryLLMAgent(_StubLLM("1"))
    agent.act(_battle_obs(enemy_hp=50, enemy_type=3))
    agent.act(_battle_obs(enemy_hp=40, enemy_type=5))   # enemy TYPE changed -> no attribution
    assert 3 not in agent._battle_table or 1 not in agent._battle_table.get(3, {})

    switch = BattleMemoryLLMAgent(_StubLLM("switch"))   # parse_action -> 4 (not an attack move)
    switch.act(_battle_obs(enemy_hp=50, enemy_type=3))
    switch.act(_battle_obs(enemy_hp=40, enemy_type=3))
    assert switch._battle_table == {}                   # action 4 deals no move damage


def test_battle_memory_reset_clears_table() -> None:
    # AC4: reset() clears the battle table between sealed worlds (no cross-world leakage).
    agent = BattleMemoryLLMAgent(_StubLLM("1"))
    agent.act(_battle_obs(enemy_hp=50, enemy_type=3))
    agent.act(_battle_obs(enemy_hp=10, enemy_type=3))
    assert agent._battle_table
    agent.reset()
    assert agent._battle_table == {}
    assert agent._battle_notes_block(_battle_obs(enemy_hp=10, enemy_type=3)) == ""


def test_battle_memory_scores_end_to_end_and_arms_are_byte_identical() -> None:
    # AC1 + AC5: scores on a sealed set, and the scripted reference arms are submission-
    # independent (adding this adapter cannot move oracle / type_blind numbers).
    sealed = SealedEvalSet(master_seed=11, n_worlds=4)
    card = score_agent(BattleMemoryLLMAgent(_StubLLM("Action: 0")), sealed)
    assert isinstance(card, Scorecard)
    assert card.n_worlds == 4
    baseline = score_agent(LLMAgent(_StubLLM("Action: 0")), sealed)
    assert card.oracle_gyms == baseline.oracle_gyms
    assert card.type_blind_gyms == baseline.type_blind_gyms


def test_claude_cli_complete_exists_and_errors_on_missing_binary() -> None:
    """`claude_cli_complete` builds a subscription-backed complete() via the local `claude`
    CLI; a non-existent binary raises a clear FileNotFoundError (so misconfig is obvious)."""
    from critter_gym import llm_eval

    assert hasattr(llm_eval, "claude_cli_complete")
    import pytest

    with pytest.raises(FileNotFoundError):
        llm_eval.claude_cli_complete(binary="definitely-not-a-real-binary-xyz")


# -- claude_cli_complete retry-on-timeout (eval-product/cli-complete-retry) --------


def _timeout_then_ok(n_timeouts: int):
    """A fake subprocess.run: raises TimeoutExpired ``n_timeouts`` times, then succeeds."""
    import subprocess
    from types import SimpleNamespace

    calls = {"n": 0}

    def fake_run(cmd, **kwargs):
        calls["n"] += 1
        if calls["n"] <= n_timeouts:
            raise subprocess.TimeoutExpired(cmd=cmd, timeout=kwargs.get("timeout", 0))
        return SimpleNamespace(stdout="  3  \n", stderr="")

    return fake_run, calls


def test_cli_complete_retries_timeouts_then_returns(monkeypatch) -> None:
    import subprocess as _sp

    from critter_gym import llm_eval

    fake_run, calls = _timeout_then_ok(2)
    monkeypatch.setattr(_sp, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda b: "/usr/bin/claude")
    complete = llm_eval.claude_cli_complete()
    assert complete("prompt") == "3"       # 2 timeouts -> 3rd attempt returns
    assert calls["n"] == 3                 # exactly initial + 2 retries


def test_cli_complete_raises_after_retries_exhausted(monkeypatch) -> None:
    import subprocess as _sp

    import pytest

    from critter_gym import llm_eval

    fake_run, calls = _timeout_then_ok(99)
    monkeypatch.setattr(_sp, "run", fake_run)
    monkeypatch.setattr("shutil.which", lambda b: "/usr/bin/claude")
    complete = llm_eval.claude_cli_complete()
    with pytest.raises(_sp.TimeoutExpired):
        complete("prompt")                 # never silently substitutes an action
    assert calls["n"] == 3                 # all 3 attempts consumed, then raise
