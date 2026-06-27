"""Agentic-LLM eval adapter — score an LLM agent on the sealed held-out harness.

The scarce, contamination-proof eval (eval-product, M5) is most valuable as an **agentic-LLM**
capability test: drop a fresh, never-seen world in front of an LLM agent, have it infer the
hidden rules and clear gyms, and score it with verifiable subgoals — on worlds it could not
have trained on. This module is the bridge from an LLM to :mod:`critter_gym.eval_harness`:

- :func:`render_obs` — the env observation as legible text (position, battle state, party /
  enemy, gyms cleared, a 5×5 ASCII local view, and a context-aware action legend).
- :func:`parse_action` — the LLM's free-text reply → an action index, robustly (a digit, a
  direction/verb keyword, or a safe ``WAIT`` fallback; always in ``[0, n_actions)``).
- :class:`LLMAgent` — wraps a provider-agnostic ``complete(prompt) -> reply`` callable into
  the #1 ``Agent`` Protocol (``act(obs) -> int``), so :func:`eval_harness.score_agent` scores
  it on a sealed set exactly like any other agent.
- :func:`anthropic_complete` — an *optional* Anthropic hookup (lazy-imported) for a real LLM.

**Honest scope.** This is the *adapter mechanism*, not a measured LLM-capability result. CI and
the demo use a deterministic *stub* LLM (no API, no key); a real measurement needs an API key
and incurs cost (a separate run). Provider-agnostic by design — the core never imports a vendor
SDK; the Anthropic helper is opt-in.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Callable

import numpy as np

# Action semantics (CritterEnv Discrete(6); battle reinterprets 0-3 as attack moves).
_ACTION_LEGEND_OVERWORLD = (
    "0=move North  1=move South  2=move East  3=move West  "
    "4=Catch the creature on your tile  5=Wait"
)
_ACTION_LEGEND_BATTLE = (
    "0-3=use an attack move  4=Switch to your next party member  5=Pass/Item"
)
# Keyword → action index (overworld semantics; checked after a plain digit).
_KEYWORDS: tuple[tuple[str, int], ...] = (
    ("north", 0), ("up", 0),
    ("south", 1), ("down", 1),
    ("east", 2), ("right", 2),
    ("west", 3), ("left", 3),
    ("catch", 4), ("switch", 4),
    ("attack", 0),  # in battle 0 is an attack move; a reasonable default verb
    ("wait", 5), ("pass", 5), ("item", 5),
)
_FALLBACK_ACTION = 5  # Wait — a safe no-op when the reply can't be parsed
# Tile codes in local_patch → a single legible glyph for the ASCII view.
_TILE_GLYPHS = {0: ".", 1: "#", 2: "C", 3: "G"}

DEFAULT_SYSTEM = (
    "You are playing CritterGym, a grid creature-collection game with a HIDDEN type chart you "
    "must infer from battles. Each turn you see your local surroundings and state. Your goal is "
    "to defeat gym bosses. Reply with the single action you choose — either its number (0-5) or "
    "a short phrase like 'move north' / 'catch' / 'attack' / 'wait'. Be decisive; reply briefly."
)


def _scalar(obs: Mapping[str, object], key: str) -> int:
    """Read a shape-(1,) (or scalar) obs field as a python int."""
    return int(np.asarray(obs[key]).flatten()[0])


def render_obs(obs: Mapping[str, object]) -> str:
    """Render one observation as legible text for an LLM (deterministic).

    Includes the agent position, battle state, gyms cleared, party/enemy stats, a 5×5 ASCII
    local view, and a context-aware action legend (overworld vs battle)."""
    pos = np.asarray(obs["agent_pos"]).flatten()
    in_battle = _scalar(obs, "in_battle")
    gyms = _scalar(obs, "gyms_defeated")
    caught = _scalar(obs, "caught")
    lines = [
        f"Position: row {int(pos[0])}, col {int(pos[1])}",
        f"In battle: {'yes' if in_battle else 'no'}    Gyms cleared: {gyms}    Caught: {caught}",
        f"Your creature: hp {_scalar(obs, 'player_hp')}, type {_scalar(obs, 'player_type')}, "
        f"level {_scalar(obs, 'player_level')}",
    ]
    if in_battle:
        lines.append(
            f"Enemy: hp {_scalar(obs, 'enemy_hp')}, type {_scalar(obs, 'enemy_type')}"
        )

    patch = np.asarray(obs["local_patch"])
    lines.append("Local view (.=floor #=wall C=creature G=gym, you are at center):")
    for row in patch:
        lines.append("  " + " ".join(_TILE_GLYPHS.get(int(t), "?") for t in row))

    lines.append("Actions: " + (_ACTION_LEGEND_BATTLE if in_battle else _ACTION_LEGEND_OVERWORLD))
    lines.append("Your action:")
    return "\n".join(lines)


def parse_action(reply: str, n_actions: int = 6) -> int:
    """Parse an LLM reply into an action index in ``[0, n_actions)`` (robust).

    Tries, in order: a leading/standalone digit, an explicit ``action N``, any digit in the
    reply, then direction/verb keywords; falls back to ``WAIT`` (5, clamped) if nothing matches.
    Out-of-range digits are clamped into range. Never raises on garbage/empty input."""
    if not reply:
        return min(_FALLBACK_ACTION, n_actions - 1)
    text = reply.strip().lower()

    # 1) an explicit "action N" / "choose N"
    m = re.search(r"\b(?:action|choose|select|option)\s*[:#]?\s*(\d+)", text)
    if m is None:
        # 2) a standalone digit token (e.g. "2", "2.", "2 - move east")
        m = re.search(r"(?<!\d)(\d+)(?!\d)", text)
    if m is not None:
        return max(0, min(int(m.group(1)), n_actions - 1))

    # 3) direction / verb keywords
    for kw, idx in _KEYWORDS:
        if kw in text:
            return idx if idx < n_actions else n_actions - 1

    # 4) safe fallback
    return min(_FALLBACK_ACTION, n_actions - 1)


class LLMAgent:
    """An LLM submission: ``act(obs) -> int`` via a ``complete(prompt) -> reply`` callable.

    Satisfies the :class:`critter_gym.eval_harness.Agent` Protocol, so a sealed-eval run scores
    it like any other agent. ``complete`` is provider-agnostic — inject a stub for tests, or
    :func:`anthropic_complete` for a real LLM."""

    def __init__(
        self, complete: Callable[[str], str], *, system: str = DEFAULT_SYSTEM,
        n_actions: int = 6,
    ) -> None:
        self._complete = complete
        self._system = system
        self._n_actions = n_actions

    def act(self, obs: object) -> int:
        prompt = f"{self._system}\n\n{render_obs(obs)}"  # type: ignore[arg-type]
        return parse_action(self._complete(prompt), self._n_actions)


def anthropic_complete(
    model: str = "claude-opus-4-8", *, max_tokens: int = 64, system: str = DEFAULT_SYSTEM,
) -> Callable[[str], str]:
    """Build a real-LLM ``complete(prompt) -> reply`` backed by the Anthropic SDK (**optional**).

    Lazy-imports ``anthropic`` (not a core dependency) and reads ``ANTHROPIC_API_KEY`` from the
    environment, so importing this module never requires the SDK. Each call is one
    ``messages.create`` (model default ``claude-opus-4-8``; thinking omitted — a one-token action
    needs none). Using a real LLM incurs API cost — this is for an opt-in measurement run, not CI.
    """
    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - exercised only without the SDK
        raise ImportError(
            "anthropic_complete needs the Anthropic SDK + an API key: "
            "`pip install anthropic` and set ANTHROPIC_API_KEY. The core adapter is "
            "provider-agnostic — inject your own complete(prompt)->reply instead."
        ) from exc

    client = anthropic.Anthropic()

    def complete(prompt: str) -> str:
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")

    return complete


def claude_cli_complete(
    binary: str = "claude", *, cwd: str | None = None, timeout: float = 120.0,
) -> Callable[[str], str]:
    """Build a ``complete(prompt) -> reply`` backed by the local **Claude Code** CLI (print mode).

    Uses whatever auth Claude Code is logged in with — **including a Pro/Max subscription** — so
    no per-token API key/billing (`claude -p "<prompt>"`). Each call runs in a neutral working
    directory so the repo's `CLAUDE.md`/context is **not** loaded into the prompt.

    Caveats: a subscription is intended for *interactive* use and has rate limits — keep eval
    runs small (a probe), not a large batch. It is also **slow** (~seconds/call: a full agent
    process starts per call), so prefer the API for big runs. Raises ``FileNotFoundError`` if the
    `claude` binary isn't on PATH.
    """
    import shutil
    import subprocess
    import tempfile

    resolved = shutil.which(binary)
    if resolved is None:
        raise FileNotFoundError(
            f"`{binary}` CLI not found on PATH. Install Claude Code, or use "
            "anthropic_complete() / inject your own complete(prompt)->reply."
        )
    work = cwd or tempfile.mkdtemp()

    def complete(prompt: str) -> str:
        result = subprocess.run(
            [resolved, "-p", prompt], cwd=work, capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout.strip()

    return complete
