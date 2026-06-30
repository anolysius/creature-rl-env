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
    "must infer from battles. You ALREADY START with a starter party of creatures (their stats "
    "are shown only during a battle, not on the overworld). Your main goal is to clear gyms: walk "
    "onto a gym tile (shown as G in your local view) to start a boss battle, then fight to defeat "
    "the boss. "
    "BATTLE STRATEGY: your attack moves 0-3 each have a different HIDDEN type, and one may be "
    "super-effective against this enemy. You must discover which by trying moves and watching how "
    "much the enemy's hp drops — the move that deals the most damage is your best counter; "
    "remember it for this enemy type. Just spamming move 0 usually loses. If your creature is a "
    "bad matchup, Switch (action 4) to another party member. If you lose a gym battle your party "
    "heals, so you can re-enter the same gym and try again using what you learned. "
    "You can also catch wild creatures (shown as C) by standing EXACTLY on their tile and choosing "
    "Catch (4); Catch does nothing on a gym (G) or empty tile. "
    "Each turn you see your local surroundings and state. Reply with the single action you choose "
    "— either its number (0-5) or a short phrase like 'move north' / 'catch' / 'attack' / 'wait'. "
    "Be decisive; reply briefly."
)


def _scalar(obs: Mapping[str, object], key: str) -> int:
    """Read a shape-(1,) (or scalar) obs field as a python int."""
    return int(np.asarray(obs[key]).flatten()[0])


def _dir_phrase(drow: int, dcol: int) -> str:
    """Describe a local-view offset (center-relative) in words. drow<0=north, dcol<0=west."""
    parts = []
    if drow < 0:
        parts.append(f"{-drow} north")
    elif drow > 0:
        parts.append(f"{drow} south")
    if dcol < 0:
        parts.append(f"{-dcol} west")
    elif dcol > 0:
        parts.append(f"{dcol} east")
    return " and ".join(parts) if parts else "on your tile"


def _nearest_in_view(patch: np.ndarray, code: int) -> tuple[int, int] | None:
    """Nearest (drow, dcol) tile with ``code`` in the patch (Manhattan), excluding center."""
    radius = patch.shape[0] // 2
    best: tuple[int, int] | None = None
    best_d: int | None = None
    for pr in range(patch.shape[0]):
        for pc in range(patch.shape[1]):
            if int(patch[pr, pc]) != code:
                continue
            dr, dc = pr - radius, pc - radius
            if dr == 0 and dc == 0:
                continue  # center handled separately (you are ON this tile)
            d = abs(dr) + abs(dc)
            if best_d is None or d < best_d:
                best_d, best = d, (dr, dc)
    return best


def render_obs(obs: Mapping[str, object]) -> str:
    """Render one observation as legible text for an LLM (deterministic).

    Includes the agent position, battle state, gyms cleared, a 5×5 ASCII local view, and a
    context-aware action legend. Creature stats are shown **only during battle** (the env
    0-masks ``player_*``/``enemy_*`` on the overworld); on the overworld we instead note that
    the starter party exists, so the LLM is never misled into thinking it has no creature.
    Visible gyms (G) / wild creatures (C) are called out with their direction so the agent can
    act on them rather than wander blindly."""
    pos = np.asarray(obs["agent_pos"]).flatten()
    in_battle = _scalar(obs, "in_battle")
    gyms = _scalar(obs, "gyms_defeated")
    caught = _scalar(obs, "caught")
    lines = [
        f"Position: row {int(pos[0])}, col {int(pos[1])}",
        f"In battle: {'yes' if in_battle else 'no'}    Gyms cleared: {gyms}    Caught: {caught}",
    ]
    if in_battle:
        # Battle: the active creatures' real stats are available — show them.
        lines.append(
            f"Your creature: hp {_scalar(obs, 'player_hp')}, type {_scalar(obs, 'player_type')}, "
            f"level {_scalar(obs, 'player_level')}"
        )
        lines.append(
            f"Enemy: hp {_scalar(obs, 'enemy_hp')}, type {_scalar(obs, 'enemy_type')}"
        )
        # Tactical hint — nudge the agent into the hidden-chart inference loop (it must still
        # discover WHICH move is super-effective itself; we only explain the mechanic).
        lines.append(
            "Tip: moves 0-3 have different hidden types — try them and watch the enemy hp drop "
            "to find the super-effective one (remember it), or Switch (4) party member."
        )
    else:
        # Overworld: player_* are 0-masked by the env — do NOT print "hp 0" (it reads as "no
        # creature"). State the truth: a starter party exists; its stats appear in battle.
        lines.append(
            "Your party: you have a starter party of creatures (their stats appear during battle)."
        )

    patch = np.asarray(obs["local_patch"])
    lines.append("Local view (.=floor #=wall C=creature G=gym, you are at center):")
    for row in patch:
        lines.append("  " + " ".join(_TILE_GLYPHS.get(int(t), "?") for t in row))

    # Salience: call out gyms/creatures in view so the agent doesn't confuse or miss them.
    radius = patch.shape[0] // 2
    center = int(patch[radius, radius])
    if not in_battle:
        if center == 3:  # _PATCH_GYM
            lines.append(
                "You are ON a gym (G) tile — moving onto it starts a boss battle; defeat the "
                "boss to clear this gym."
            )
        else:
            gym = _nearest_in_view(patch, 3)
            if gym is not None:
                lines.append(
                    f"A gym (G) is visible {_dir_phrase(*gym)} — walk onto it to start a boss "
                    "battle (your main goal)."
                )
        creature = _nearest_in_view(patch, 2)  # _PATCH_CREATURE
        if center == 2:
            lines.append("A wild creature (C) is on your tile — choose Catch (4) to catch it.")
        elif creature is not None:
            lines.append(
                f"A wild creature (C) is visible {_dir_phrase(*creature)} — stand on its tile "
                "and Catch (4)."
            )

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


_ACTION_NAMES = ("North", "South", "East", "West", "Catch", "Wait")


def _obs_summary(obs: Mapping[str, object]) -> str:
    """A compact one-line digest of an observation for the running history (not the full render).

    Keeps the history token-cheap: only the fields that change a navigation/battle decision
    (position, battle flag, gyms cleared)."""
    pos = np.asarray(obs["agent_pos"]).flatten()
    where = "in battle" if _scalar(obs, "in_battle") else f"at ({int(pos[0])},{int(pos[1])})"
    return f"{where}, gyms {_scalar(obs, 'gyms_defeated')}"


class StatefulLLMAgent:
    """An LLM submission that **remembers** its recent steps within an episode.

    The plain :class:`LLMAgent` is memoryless — each turn it sees only the current observation,
    so under partial observability (the 5×5 local view) it cannot recall a corridor it walked a
    moment ago. This agent prepends a sliding window of the last ``window`` ``(observation
    digest, action taken)`` pairs to each prompt, so the LLM can reason over where it has been.
    That makes for a *fairer* sealed-eval measurement of an agentic LLM — memory is load-bearing
    in this env, so withholding it floors any agent regardless of capability.

    Satisfies the same :class:`critter_gym.eval_harness.Agent` Protocol as :class:`LLMAgent`
    (``act(obs) -> int``) and adds the optional ``reset()`` hook: :func:`eval_harness.score_agent`
    calls it at the start of each sealed world, clearing the history so one world's transcript
    cannot leak into the next. ``window`` bounds context growth (and so per-call tokens); the
    history holds compact one-line digests, not full renders.

    Honest scope: this is the *memory mechanism*, not a measured result. CI uses a stub
    ``complete``; a real probe (subscription Claude CLI or API) is a separate user-run, and
    whatever fraction-of-oracle it yields is reported as-is — not reframed as "frontier LLMs
    can/can't solve it"."""

    def __init__(
        self, complete: Callable[[str], str], *, system: str = DEFAULT_SYSTEM,
        n_actions: int = 6, window: int = 8,
    ) -> None:
        if window < 0:
            raise ValueError("window must be >= 0")
        self._complete = complete
        self._system = system
        self._n_actions = n_actions
        self._window = int(window)
        self._history: list[tuple[str, int]] = []  # (obs digest, action) most-recent last

    def reset(self) -> None:
        """Clear the per-episode memory (called by ``score_agent`` between sealed worlds)."""
        self._history.clear()

    def _history_block(self) -> str:
        """Render the recent history as legible prompt context (empty string if none)."""
        if not self._history:
            return ""
        lines = ["Recent history (oldest first):"]
        for digest, action in self._history:
            name = _ACTION_NAMES[action] if 0 <= action < len(_ACTION_NAMES) else str(action)
            lines.append(f"  - You were {digest}; you chose action {action} ({name}).")
        return "\n".join(lines)

    def act(self, obs: object) -> int:
        obs_map: Mapping[str, object] = obs  # type: ignore[assignment]
        history = self._history_block()
        parts = [self._system]
        if history:
            parts.append(history)
        parts.append(render_obs(obs_map))
        action = parse_action(self._complete("\n\n".join(parts)), self._n_actions)
        self._remember(obs_map, action)
        return action

    def _remember(self, obs: Mapping[str, object], action: int) -> None:
        """Record this step's (obs digest, action), then bound the window (drop oldest)."""
        self._history.append((_obs_summary(obs), action))
        if len(self._history) > self._window:
            del self._history[: len(self._history) - self._window]


class BattleMemoryLLMAgent(StatefulLLMAgent):
    """A :class:`StatefulLLMAgent` that also **remembers per-move battle outcomes**.

    The hidden-chart inference this env measures is, mechanically, *try a move → watch how much
    the enemy's hp drops → remember which move hit hardest against this enemy type*. The plain
    :class:`StatefulLLMAgent` cannot support that loop: its history digest is position + gyms
    only (:func:`_obs_summary`), so it discards the very damage-feedback signal the inference
    needs — a thin-adapter artifact that floors any agent regardless of capability.

    This agent diffs consecutive in-battle observations: if the previous action was an attack
    move (0-3) and the enemy is unchanged, the enemy-hp drop is attributed to that move and
    stored per enemy type as ``{enemy_type: {move: latest observed damage}}`` — a single value
    per ``(enemy_type, move)`` (overwritten, never a growing list). Each enemy-type row holds at
    most 4 entries (the attack moves 0-3), so the table is bounded (≤ ``num_types × 4``, since
    ``enemy_type`` ∈ ``[0, num_types)``). The accumulated damage is surfaced into the prompt as
    **raw observed facts** (e.g. "vs enemy type 3: move 1 dealt 40, move 0 dealt 8"), in move
    order with **no recommended/super-effective move** — choosing how to exploit them is left to the
    LLM (recommending the answer would do the inference *for* it and invalidate the measurement).
    :meth:`reset` clears the table between sealed worlds (no cross-world leakage).

    Honest scope: this is the *memory mechanism*, **not a measured result**. CI uses a stub
    ``complete``; a real probe (subscription Claude CLI or API) is a separate user-local run, and
    whatever inference_score it yields is reported as-is — not reframed as "frontier LLMs can/
    can't solve it". De-thinning the adapter only makes a *subsequent* measurement fair; it does
    not by itself prove the chart-blind floor was an artifact.
    """

    def __init__(
        self, complete: Callable[[str], str], *, system: str = DEFAULT_SYSTEM,
        n_actions: int = 6, window: int = 8,
    ) -> None:
        super().__init__(complete, system=system, n_actions=n_actions, window=window)
        # {enemy_type: {move: latest observed damage}} — single value per (type, move), bounded.
        self._battle_table: dict[int, dict[int, int]] = {}
        # Snapshot of the PREVIOUS step as plain ints (not the obs dict) — copying the dict would
        # share its numpy arrays, so an env that reused/mutated arrays in place would make the
        # next-step hp diff read 0. Plain scalars are immune to that aliasing.
        self._prev_battle: tuple[int, int, int] | None = None  # (in_battle, enemy_type, enemy_hp)
        self._prev_action: int | None = None

    def reset(self) -> None:
        """Clear per-episode memory: history (super) + the battle-outcome table."""
        super().reset()
        self._battle_table.clear()
        self._prev_battle = None
        self._prev_action = None

    def _observe_battle_outcome(self, obs: Mapping[str, object]) -> None:
        """Attribute the last attack move's dealt damage from the enemy-hp drop (if unambiguous).

        Relies on the env invariant that a battle is vs a SINGLE boss whose faint *ends* the
        battle (``in_battle`` → 0): so within one in-battle session the enemy is fixed and its
        hp is monotonically non-increasing — an enemy-type-equal, in-battle→in-battle, ``delta``
        ≥ 0 transition is genuinely our move's damage, never a same-type replacement enemy."""
        prev, action = self._prev_battle, self._prev_action
        if prev is None or action is None or not (0 <= action <= 3):
            return  # only attack moves 0-3 deal move damage
        prev_in_battle, prev_type, prev_hp = prev
        if not prev_in_battle or not _scalar(obs, "in_battle"):
            return  # need an in-battle → in-battle transition
        if prev_type != _scalar(obs, "enemy_type"):
            return  # enemy changed (faint / new boss) — can't attribute the drop
        delta = prev_hp - _scalar(obs, "enemy_hp")
        if delta < 0:
            return  # hp went up (new/healed enemy) — not our damage
        self._battle_table.setdefault(prev_type, {})[action] = int(delta)

    def _battle_notes_block(self, obs: Mapping[str, object]) -> str:
        """Render observed damage vs the current enemy type as raw facts (empty if none/overworld).

        Moves are listed in index order (no damage ranking) and no move is recommended — the
        inference (which move to exploit) is the LLM's job, which is what the eval measures."""
        if not _scalar(obs, "in_battle"):
            return ""
        etype = _scalar(obs, "enemy_type")
        row = self._battle_table.get(etype)
        if not row:
            return ""
        facts = ", ".join(f"move {m} dealt {row[m]}" for m in sorted(row))
        return (
            "Battle notes — damage YOU have already observed against this enemy type "
            "(raw facts, decide for yourself):\n"
            f"  vs enemy type {etype}: {facts}"
        )

    def act(self, obs: object) -> int:
        obs_map: Mapping[str, object] = obs  # type: ignore[assignment]
        self._observe_battle_outcome(obs_map)  # learn from the previous move's result first
        history = self._history_block()
        notes = self._battle_notes_block(obs_map)
        parts = [self._system]
        if notes:
            parts.append(notes)
        if history:
            parts.append(history)
        parts.append(render_obs(obs_map))
        action = parse_action(self._complete("\n\n".join(parts)), self._n_actions)
        self._remember(obs_map, action)  # history window (shared with the parent)
        # Snapshot this step as plain ints for next-step damage attribution (no array aliasing).
        self._prev_battle = (
            _scalar(obs_map, "in_battle"), _scalar(obs_map, "enemy_type"),
            _scalar(obs_map, "enemy_hp"),
        )
        self._prev_action = action
        return action


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
