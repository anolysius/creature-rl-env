"""JAX functional port of the full CritterGym episode — M4 (throughput) env integration.

Composes the overworld port (`jax_overworld`) and the commit-mode champion battle
(`jax_battle`) into a single **full-episode** env step that an RL loop can `vmap` over
thousands of environments at once. Exposes `jax_env_step(state, action) -> (state, obs,
reward, terminated, truncated)`, mirroring `CritterEnv(commit_battles=True)` (family A,
`CritterGym-commit-v0`).

**Config (jax-difficulty-report, R5).** The env's shape/economy constants (grid size,
patch radius, step budget, **max gym count**, boss stats) are a :class:`JaxEnvConfig`
closed over by :func:`make_jax_env` — so the higher-gym *dynamic-range* difficulty config
(`difficulty-dynamic-range`) can be vmap-trained on JAX, not just the default 3-gym world.
Because JAX needs static shapes, the config is a compile-time constant captured by the
factory's closures (not a traced argument). The module-level `jax_env_step` / `jax_reset`
/ `encode_obs` / `make_env_step` are the **default-config** instances (grid 10, 3 gyms,
boss 120/12/12) — preserved so existing imports, parity tests and the benchmark are
unchanged.

**Scope:** all four families via `JaxEnvConfig.family` — critter (A), forage (B), muster (D),
and **duel (C)** — and either battle economy via `JaxEnvConfig.commit`. The step dispatches by
mode (`jax.lax.cond`): the overworld branch moves / catches (family-specific collection) /
enters a gym battle (heals the party, and in commit mode opens the champion-select commit
window). The battle branch is selected by `family`/`commit` (compile-time constants):
**duel** resolves one type-agnostic RPS/stamina turn (ATTACK/CHARGE/GUARD, simultaneous
damage, charge accumulation, 40-turn stalemate cap — see `duel_battle_branch`); else
**commit** cycles the champion during the commit window then resolves one commit-mode turn;
**non-commit** (mirrors `CritterEnv(commit_battles=False)`, the env's default —
`jax-noncommit-env-integration`) resolves one full-battle turn (SWITCH / speed-ordered moves /
force-switch / party-wipe). On a win the active marks the gym defeated, levels up and
conditionally evolves. Termination = all (real) gyms defeated; truncation = `max_steps`.

**Parity contract:** for the same seed + same action sequence, this reproduces
`CritterEnv(commit_battles=True)` exactly — every observation key (incl. the egocentric
`local_patch`), reward, terminated, truncated. Verified in `tests/test_jax_env_parity.py`
(default config) and `tests/test_jax_difficulty_parity.py` (the high-gym config). Procgen
(`generate_region`) stays numpy; `jax_reset` bridges a `Region` into the state.

Requires the `[jax]` extra; core + CI stay numpy-only.
"""

from __future__ import annotations

from typing import Callable, NamedTuple

import jax
import jax.numpy as jnp
import numpy as np

from critter_gym.party import starter_party
from critter_gym.region import Region
from critter_gym.types import ElementType, TypeChart

# --- fixed enums / party (not config-dependent) ---
_PARTY = 3
_CATCH = 4  # action enum: MOVE_N/S/E/W=0-3, CATCH=4, NOOP=5
_PATCH_CREATURE, _PATCH_GYM = 1, 2
_MODE_OVERWORLD, _MODE_BATTLE = 0, 1

# family enum: 0 critter (action-collect), 1 forage (contact-collect), 2 muster
# (action-collect + caught buffs party attack), 3 duel (jax-duel-integration — type-agnostic
# RPS/stamina battle; overworld reuses critter CATCH-collect).
_FAM_CRITTER, _FAM_FORAGE, _FAM_MUSTER, _FAM_DUEL = 0, 1, 2, 3
_MUSTER_ATK = 12.0  # muster_env.MUSTER_ATK — attack added to every party member per catch

# duel (C) battle constants (mirror duel_env.py).
_DUEL_ATTACK, _DUEL_CHARGE, _DUEL_GUARD = 0, 1, 2
_DUEL_MAX_CHARGE = 2  # duel_env.MAX_CHARGE
_DUEL_TURN_CAP = 40  # duel_env._DUEL_TURN_CAP — a stalled duel (mutual guard/charge) = loss

_TYPES = list(ElementType)
_NUM_TYPES = len(_TYPES)
_TYPE_TO_INT = {t: i for i, t in enumerate(_TYPES)}

_MOVE_DELTAS = jnp.array(
    [[-1, 0], [1, 0], [0, 1], [0, -1], [0, 0], [0, 0]], dtype=jnp.int32
)


class JaxEnvConfig(NamedTuple):
    """Shape/economy constants captured (statically) by :func:`make_jax_env`.

    Defaults reproduce ``CritterEnv``'s commit-mode family-A defaults, so the
    default-config env is bit-for-bit the prior behavior. ``num_types`` / ``super_mult``
    are *not* here — they flow through the per-seed ``Region.chart`` at reset.

    ``commit`` picks the battle economy: ``True`` (default) = commit-mode champion
    (mirrors ``CritterEnv(commit_battles=True)``); ``False`` = **non-commit full battle**
    (party + SWITCH + force-switch + party-wipe, mirrors ``CritterEnv(commit_battles=False)``
    — the env's *default* battle). ``potions`` / ``battle_max_turns`` are the non-commit
    battle's potion stock and per-battle turn cap (dead constants in commit mode).
    """

    grid: int = 10
    patch_radius: int = 2
    max_steps: int = 200
    max_gyms: int = 3
    boss_hp: int = 120
    boss_atk: int = 12
    boss_def: int = 12
    boss_spd: int = 8
    boss_move_power: float = 30.0
    commit: bool = True
    potions: int = 2
    battle_max_turns: int = 200
    family: int = _FAM_CRITTER


DEFAULT_CONFIG = JaxEnvConfig()
DEFAULT_NONCOMMIT_CONFIG = JaxEnvConfig(commit=False)


def _party_stat_tables() -> tuple[jax.Array, jax.Array]:
    """(base, evolved) stat tables for the fixed starter party: (PARTY, 7) each.

    Columns: max_hp, attack, defense, speed, move_power, move_type_idx, def_type_idx.
    """
    base, evo = [], []
    for c in starter_party():
        mt, dt = _TYPE_TO_INT[c.moves[0].type], _TYPE_TO_INT[c.types[0]]
        base.append((c.max_hp, c.attack, c.defense, c.speed, c.moves[0].power, mt, dt))
        f = c.evolves_to
        assert f is not None
        evo.append((f.max_hp, f.attack, f.defense, f.speed, c.moves[0].power, mt, dt))
    return jnp.asarray(np.array(base, np.float32)), jnp.asarray(np.array(evo, np.float32))


_BASE_STATS, _EVO_STATS = _party_stat_tables()


class JaxEnvState(NamedTuple):
    """Full-episode env state pytree (jit/vmap-friendly). Family A, commit or non-commit.

    Per-episode constants (set at reset, immutable except ``gym_defeated``): ``gym_pos``,
    ``gym_type``, ``gym_active`` (real-gym mask — ``vary`` charts have 1..max_gyms gyms),
    ``eff`` (the seed's type-effectiveness matrix). The rest is mutable episode state.
    Array shapes that depend on the config (gym arrays' leading dim = ``max_gyms``;
    ``creature_mask`` is ``grid×grid``) are fixed per :func:`make_jax_env` instance.
    """

    agent_pos: jax.Array  # (2,) int32
    creature_mask: jax.Array  # (GRID, GRID) bool
    gym_pos: jax.Array  # (MAX_GYMS, 2) int32 (unused slots = -1)
    gym_type: jax.Array  # (MAX_GYMS,) int32
    gym_active: jax.Array  # (MAX_GYMS,) bool — real gyms for this seed
    gym_defeated: jax.Array  # (MAX_GYMS,) bool
    eff: jax.Array  # (NUM_TYPES, NUM_TYPES) float32
    mode: jax.Array  # () int32 — 0 overworld / 1 battle
    commit_window: jax.Array  # () bool
    active: jax.Array  # () int32 — committed champion idx
    party_hp: jax.Array  # (PARTY,) float32
    party_level: jax.Array  # (PARTY,) int32
    party_evolved: jax.Array  # (PARTY,) bool
    boss_hp: jax.Array  # () float32
    battle_gym: jax.Array  # () int32 — gym idx currently fought
    caught: jax.Array  # () int32
    evolved: jax.Array  # () int32
    steps: jax.Array  # () int32
    items: jax.Array  # () int32 — potion stock (non-commit; dead in commit mode)
    battle_turn: jax.Array  # () int32 — turns in the current battle (non-commit trunc cap)
    party_atk_boost: jax.Array  # (PARTY,) float32 — muster attack buff (catch +12; evolve resets)
    player_charge: jax.Array  # () int32 — duel: player charge 0..MAX (always 0 on non-duel)
    enemy_charge: jax.Array  # () int32 — duel: boss charge 0..MAX (always 0 on non-duel)


def _eff_matrix(chart: TypeChart) -> jax.Array:
    rows = [[chart.effectiveness(a, d) for d in _TYPES] for a in _TYPES]
    return jnp.asarray(rows, dtype=jnp.float32)


def _stat(s: JaxEnvState, idx: jax.Array, col: int) -> jax.Array:
    """Current stat[col] for party member ``idx`` (evolved-aware)."""
    return jnp.where(s.party_evolved[idx], _EVO_STATS[idx, col], _BASE_STATS[idx, col])


def _damage(power: jax.Array, atk: jax.Array, df: jax.Array, eff: jax.Array) -> jax.Array:
    return jnp.maximum(1.0, jnp.floor(power * atk / df * eff))


class JaxEnv(NamedTuple):
    """A config-bound JAX env: pure ``reset`` / ``step`` / ``encode_obs`` + ``make_step``."""

    config: JaxEnvConfig
    reset: Callable[[Region], JaxEnvState]
    step: Callable[
        [JaxEnvState, jax.Array],
        tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array],
    ]
    encode_obs: Callable[[JaxEnvState], dict[str, jax.Array]]
    make_step: Callable[..., Callable]


def make_jax_env(config: JaxEnvConfig = DEFAULT_CONFIG) -> JaxEnv:
    """Build a config-bound JAX env. ``config`` is captured statically by the closures
    (JAX needs static shapes), so a higher ``max_gyms`` / different ``grid`` works under
    ``jit``/``vmap`` exactly like the default. Logic is identical to the default port —
    only the baked constants change."""
    grid = config.grid
    patch_radius = config.patch_radius
    patch_side = 2 * patch_radius + 1
    max_steps = config.max_steps
    max_gyms = config.max_gyms
    boss_hp_f = float(config.boss_hp)
    boss_atk_f = float(config.boss_atk)
    boss_def_f = float(config.boss_def)
    boss_spd = config.boss_spd
    boss_move_power = config.boss_move_power
    commit = config.commit
    potions = config.potions
    battle_max_turns = config.battle_max_turns
    family = config.family

    def reset(region: Region) -> JaxEnvState:
        cm = np.zeros((grid, grid), dtype=bool)
        for r, c in region.creatures:
            cm[r, c] = True
        gym_pos = np.full((max_gyms, 2), -1, dtype=np.int32)
        gym_type = np.zeros((max_gyms,), dtype=np.int32)
        gym_active = np.zeros((max_gyms,), dtype=bool)
        for i, ((r, c), t) in enumerate(region.gyms):
            gym_pos[i] = (r, c)
            gym_type[i] = _TYPE_TO_INT[t]
            gym_active[i] = True
        return JaxEnvState(
            agent_pos=jnp.asarray(region.agent_start, dtype=jnp.int32),
            creature_mask=jnp.asarray(cm),
            gym_pos=jnp.asarray(gym_pos),
            gym_type=jnp.asarray(gym_type),
            gym_active=jnp.asarray(gym_active),
            gym_defeated=jnp.zeros((max_gyms,), dtype=bool),
            eff=_eff_matrix(region.chart),
            mode=jnp.asarray(_MODE_OVERWORLD, dtype=jnp.int32),
            commit_window=jnp.asarray(False),
            active=jnp.asarray(0, dtype=jnp.int32),
            party_hp=_BASE_STATS[:, 0],
            party_level=jnp.ones((_PARTY,), dtype=jnp.int32),
            party_evolved=jnp.zeros((_PARTY,), dtype=bool),
            boss_hp=jnp.asarray(0.0, dtype=jnp.float32),
            battle_gym=jnp.asarray(-1, dtype=jnp.int32),
            caught=jnp.asarray(0, dtype=jnp.int32),
            evolved=jnp.asarray(0, dtype=jnp.int32),
            steps=jnp.asarray(0, dtype=jnp.int32),
            items=jnp.asarray(0, dtype=jnp.int32),
            battle_turn=jnp.asarray(0, dtype=jnp.int32),
            party_atk_boost=jnp.zeros((_PARTY,), dtype=jnp.float32),
            player_charge=jnp.asarray(0, dtype=jnp.int32),
            enemy_charge=jnp.asarray(0, dtype=jnp.int32),
        )

    def overworld_branch(s: JaxEnvState, action: jax.Array) -> tuple[JaxEnvState, jax.Array]:
        is_move = action < 4
        delta = _MOVE_DELTAS[action]
        nr = jnp.clip(s.agent_pos[0] + delta[0], 0, grid - 1)
        nc = jnp.clip(s.agent_pos[1] + delta[1], 0, grid - 1)
        new_pos = jnp.where(is_move, jnp.array([nr, nc], dtype=jnp.int32), s.agent_pos)

        # -- collection (family-specific; `family` is a compile-time constant) --
        if family == _FAM_FORAGE:
            # contact-collect: stepping onto a creature tile collects it; CATCH is inert.
            # A collected step does not also enter a gym (numpy ForageEnv returns early).
            got = is_move & s.creature_mask[new_pos[0], new_pos[1]]
            cm = s.creature_mask.at[new_pos[0], new_pos[1]].set(
                jnp.where(got, False, s.creature_mask[new_pos[0], new_pos[1]])
            )
        else:
            # critter / muster: explicit CATCH on the *current* tile.
            r0, c0 = s.agent_pos[0], s.agent_pos[1]
            got = (action == _CATCH) & s.creature_mask[r0, c0]
            cm = s.creature_mask.at[r0, c0].set(jnp.where(got, False, s.creature_mask[r0, c0]))
        reward = jnp.where(got, 1.0, 0.0)

        on_gym = jnp.asarray(False)
        gym_idx = jnp.asarray(-1, dtype=jnp.int32)
        for i in range(max_gyms):
            hit = (
                is_move
                & (new_pos[0] == s.gym_pos[i, 0])
                & (new_pos[1] == s.gym_pos[i, 1])
                & s.gym_active[i]
                & (~s.gym_defeated[i])
            )
            on_gym = on_gym | hit
            gym_idx = jnp.where(hit, i, gym_idx)
        if family == _FAM_FORAGE:
            on_gym = on_gym & (~got)  # a contact-collect step skips the gym check

        # muster: each catch buffs every party member's attack (+_MUSTER_ATK).
        if family == _FAM_MUSTER:
            new_boost = s.party_atk_boost + got.astype(jnp.float32) * _MUSTER_ATK
        else:
            new_boost = s.party_atk_boost

        healed = jnp.where(s.party_evolved, _EVO_STATS[:, 0], _BASE_STATS[:, 0])
        s = s._replace(
            agent_pos=new_pos,
            creature_mask=cm,
            caught=s.caught + got.astype(jnp.int32),
            party_atk_boost=new_boost,
            mode=jnp.where(on_gym, _MODE_BATTLE, _MODE_OVERWORLD).astype(jnp.int32),
            # commit mode opens the champion-select window on entry; non-commit never does.
            commit_window=on_gym & commit,
            battle_gym=jnp.where(on_gym, gym_idx, s.battle_gym).astype(jnp.int32),
            party_hp=jnp.where(on_gym, healed, s.party_hp),
            boss_hp=jnp.where(on_gym, jnp.float32(boss_hp_f), s.boss_hp),
            active=jnp.where(on_gym, 0, s.active).astype(jnp.int32),
            # non-commit battle bookkeeping (reset on entry; dead in commit mode).
            items=jnp.where(on_gym, jnp.int32(potions), s.items),
            battle_turn=jnp.where(on_gym, jnp.int32(0), s.battle_turn),
            # duel: charges reset on battle entry (dead for non-duel families = stay 0).
            player_charge=jnp.where(on_gym, jnp.int32(0), s.player_charge),
            enemy_charge=jnp.where(on_gym, jnp.int32(0), s.enemy_charge),
        )
        return s, reward

    def attack_of(s: JaxEnvState, idx: jax.Array) -> jax.Array:
        """Party member ``idx``'s attack, incl. the muster buff (0 for other families)."""
        base = _stat(s, idx, 1)
        if family == _FAM_MUSTER:
            return base + s.party_atk_boost[idx]
        return base

    def reset_boost_on_evolve(
        s: JaxEnvState, act: jax.Array, can_evolve: jax.Array
    ) -> jax.Array:
        """Mirror numpy `evolve()` (`attack = form.attack`): a muster buff is wiped on
        evolution. No-op for non-muster families (boost stays 0)."""
        if family == _FAM_MUSTER:
            return s.party_atk_boost.at[act].set(
                jnp.where(can_evolve, 0.0, s.party_atk_boost[act])
            )
        return s.party_atk_boost

    def battle_branch(s: JaxEnvState, action: jax.Array) -> tuple[JaxEnvState, jax.Array]:
        def cycle(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
            cur = s.active
            nxt = cur
            found = jnp.asarray(False)
            for off in range(1, _PARTY + 1):
                i = (cur + off) % _PARTY
                alive = s.party_hp[i] > 0
                take = alive & (~found)
                nxt = jnp.where(take, i, nxt).astype(jnp.int32)
                found = found | alive
            return s._replace(active=nxt), jnp.float32(0.0)

        def fight(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
            act = s.active
            btype = s.gym_type[s.battle_gym]
            c_mt = _stat(s, act, 5).astype(jnp.int32)
            c_dt = _stat(s, act, 6).astype(jnp.int32)
            champ_dmg = jnp.where(
                action < 4,
                _damage(_stat(s, act, 4), attack_of(s, act), jnp.float32(boss_def_f),
                        s.eff[c_mt, btype]),
                0.0,
            )
            boss_dmg = _damage(
                jnp.float32(boss_move_power), jnp.float32(boss_atk_f), _stat(s, act, 2),
                s.eff[btype, c_dt],
            )
            champ_first = _stat(s, act, 3) >= boss_spd
            ch, bh = s.party_hp[act], s.boss_hp

            def champ_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
                nb = jnp.maximum(0.0, bh - champ_dmg)
                nc = jnp.where(nb > 0, jnp.maximum(0.0, ch - boss_dmg), ch)
                return nc, nb

            def boss_first_fn(_: None) -> tuple[jax.Array, jax.Array]:
                nc = jnp.maximum(0.0, ch - boss_dmg)
                nb = jnp.where(nc > 0, jnp.maximum(0.0, bh - champ_dmg), bh)
                return nc, nb

            nc, nb = jax.lax.cond(champ_first, champ_first_fn, boss_first_fn, operand=None)
            champ_fainted = nc <= 0
            boss_fainted = nb <= 0
            win = boss_fainted & (~champ_fainted)
            done_battle = champ_fainted | boss_fainted

            gym = s.battle_gym
            new_level = s.party_level[act] + jnp.where(win, 1, 0)
            can_evolve = win & (~s.party_evolved[act]) & (new_level >= 2)
            reward = jnp.where(win, 1.0, 0.0) + jnp.where(can_evolve, 1.0, 0.0)
            s = s._replace(
                commit_window=jnp.asarray(False),
                party_hp=s.party_hp.at[act].set(nc),
                boss_hp=nb,
                gym_defeated=s.gym_defeated.at[gym].set(
                    jnp.where(win, True, s.gym_defeated[gym])
                ),
                party_level=s.party_level.at[act].set(new_level),
                party_evolved=s.party_evolved.at[act].set(
                    jnp.where(can_evolve, True, s.party_evolved[act])
                ),
                party_atk_boost=reset_boost_on_evolve(s, act, can_evolve),
                evolved=s.evolved + can_evolve.astype(jnp.int32),
                mode=jnp.where(done_battle, _MODE_OVERWORLD, _MODE_BATTLE).astype(jnp.int32),
            )
            return s, reward

        do_cycle = s.commit_window & (action == 4)
        return jax.lax.cond(do_cycle, cycle, fight, s)

    def noncommit_battle_branch(
        s: JaxEnvState, action: jax.Array
    ) -> tuple[JaxEnvState, jax.Array]:
        """One non-commit battle turn, mirroring ``CritterEnv._step_battle`` (commit off).

        Action map (``CritterEnv._to_battle_action``): ``<4`` → MOVE(0), ``4`` → SWITCH to
        the next-alive party member (cyclic from active), ``5`` → ITEM(99) = a wasted turn
        (potions are never usable via the env's action space, so ``items`` is inert — kept
        only for an exact mirror). The single boss always MOVEs (``scripted_opponent`` only
        ever returns a MOVE). Resolves like ``Battle.step`` (commit_mode=False): Phase 1
        switch, Phase 2 speed-ordered moves (faint skip, tie → A), Phase 3 force-switch a
        fainted active to the first alive bench member, then party-wipe / max-turns. On a
        win the (post-force-switch) active clears the gym, levels up and conditionally
        evolves — identical economy to the commit ``fight`` path.
        """
        turn = s.battle_turn + jnp.int32(1)
        is_move = action < 4
        is_switch = action == 4

        # -- Phase 1: SWITCH to the next-alive member, cyclic from the active --
        cur = s.active
        nxt = cur
        found = jnp.asarray(False)
        for off in range(1, _PARTY + 1):
            i = (cur + off) % _PARTY
            alive = s.party_hp[i] > 0
            take = alive & (~found)
            nxt = jnp.where(take, i, nxt).astype(jnp.int32)
            found = found | alive
        # numpy _switch no-ops an illegal/fainted target; nxt is alive unless none are.
        active = jnp.where(is_switch & (s.party_hp[nxt] > 0), nxt, cur).astype(jnp.int32)

        # -- Phase 2: moves. Boss always MOVEs; player MOVEs only on an ACT_MOVE turn. --
        a_hp = s.party_hp[active]
        a_atk, a_def = attack_of(s, active), _stat(s, active, 2)
        a_spd, a_pow = _stat(s, active, 3), _stat(s, active, 4)
        a_mt = _stat(s, active, 5).astype(jnp.int32)
        a_dt = _stat(s, active, 6).astype(jnp.int32)
        btype = s.gym_type[s.battle_gym]
        player_dmg = _damage(a_pow, a_atk, jnp.float32(boss_def_f), s.eff[a_mt, btype])
        boss_dmg = _damage(
            jnp.float32(boss_move_power), jnp.float32(boss_atk_f), a_def, s.eff[btype, a_dt]
        )
        player_first = a_spd >= boss_spd
        nb_pf = jnp.maximum(0.0, s.boss_hp - player_dmg)
        na_pf = jnp.where(nb_pf > 0, jnp.maximum(0.0, a_hp - boss_dmg), a_hp)
        na_bf = jnp.maximum(0.0, a_hp - boss_dmg)
        nb_bf = jnp.where(na_bf > 0, jnp.maximum(0.0, s.boss_hp - player_dmg), s.boss_hp)
        na_move = jnp.where(player_first, na_pf, na_bf)
        nb_move = jnp.where(player_first, nb_pf, nb_bf)
        # switch / item turn: the player does not attack; only the boss strikes the active.
        na = jnp.where(is_move, na_move, jnp.maximum(0.0, a_hp - boss_dmg))
        nb = jnp.where(is_move, nb_move, s.boss_hp)
        party_hp = s.party_hp.at[active].set(na)
        boss_hp = nb

        # -- Phase 3: force-switch a fainted active to the FIRST alive member (party order) --
        alive_mask = party_hp > 0
        any_alive = jnp.any(alive_mask)
        first_alive = jnp.argmax(alive_mask.astype(jnp.int32)).astype(jnp.int32)
        active = jnp.where((na <= 0) & any_alive, first_alive, active).astype(jnp.int32)

        # -- terminal: party-wipe (both wiped → A loses) / boss dead / max-turns trunc --
        a_wiped = ~jnp.any(party_hp > 0)
        b_wiped = boss_hp <= 0
        faint_done = a_wiped | b_wiped
        trunc_battle = (~faint_done) & (turn >= battle_max_turns)
        battle_done = faint_done | trunc_battle
        win = b_wiped & (~a_wiped)

        gym = s.battle_gym
        new_level = s.party_level[active] + jnp.where(win, 1, 0)
        can_evolve = win & (~s.party_evolved[active]) & (new_level >= 2)
        reward = jnp.where(win, 1.0, 0.0) + jnp.where(can_evolve, 1.0, 0.0)
        s = s._replace(
            party_hp=party_hp,
            boss_hp=boss_hp,
            active=active,
            battle_turn=turn,
            gym_defeated=s.gym_defeated.at[gym].set(
                jnp.where(win, True, s.gym_defeated[gym])
            ),
            party_level=s.party_level.at[active].set(new_level),
            party_evolved=s.party_evolved.at[active].set(
                jnp.where(can_evolve, True, s.party_evolved[active])
            ),
            party_atk_boost=reset_boost_on_evolve(s, active, can_evolve),
            evolved=s.evolved + can_evolve.astype(jnp.int32),
            mode=jnp.where(battle_done, _MODE_OVERWORLD, _MODE_BATTLE).astype(jnp.int32),
        )
        return s, reward

    def duel_battle_branch(
        s: JaxEnvState, action: jax.Array
    ) -> tuple[JaxEnvState, jax.Array]:
        """One duel (family C) battle turn, mirroring ``DuelEnv._step_battle``.

        Type-AGNOSTIC RPS/stamina (no type chart, no defense): ``0=ATTACK / 1=CHARGE /
        2=GUARD`` (any other action → GUARD). The single active is ``party[0]`` (no
        switching). The boss is deterministic (``_enemy_duel_action``): ATTACK if its
        charge ≥ 1 else CHARGE — it never GUARDs. Resolution applies **both** damages
        *simultaneously* every turn (numpy calls ``take_damage`` on both unconditionally —
        there is NO speed order and no faint-skip, unlike the type-matchup battle): ATTACK
        deals ``floor(attack × (1 + charge))`` (0 if the opponent GUARDs), then resets that
        side's charge; CHARGE bumps charge (≤ MAX); GUARD does nothing. The damage is raw
        stat-based — distinct from the min-1-clamped, type/defense-scaled :func:`_damage`.
        Terminal = boss faint ∨ active faint ∨ ``battle_turn ≥ _DUEL_TURN_CAP`` (a stall =
        loss). ``battle_turn`` (reset to 0 on entry) is the duel turn counter — the
        non-commit branch is never reached for a duel config, so it is exclusively the duel
        turn. On a win (boss fainted & active alive) the active clears the gym, levels up
        and conditionally evolves — identical economy to the ``fight`` path.
        """
        turn = s.battle_turn + jnp.int32(1)
        act = s.active  # always 0 in a duel (no switching)
        p_act = jnp.where(action <= _DUEL_GUARD, action, jnp.int32(_DUEL_GUARD))
        # boss: ATTACK if charged, else CHARGE (never GUARD).
        e_act = jnp.where(
            s.enemy_charge >= 1, jnp.int32(_DUEL_ATTACK), jnp.int32(_DUEL_CHARGE)
        )

        p_atk = _stat(s, act, 1)  # creature attack (evolved-aware); no muster buff in duel
        p_is_attack = p_act == _DUEL_ATTACK
        p_is_charge = p_act == _DUEL_CHARGE
        p_is_guard = p_act == _DUEL_GUARD
        e_is_attack = e_act == _DUEL_ATTACK

        # player → boss: ATTACK only (boss never GUARDs, so no negation term needed).
        p_dmg = jnp.where(
            p_is_attack,
            jnp.floor(p_atk * (1.0 + s.player_charge.astype(jnp.float32))),
            0.0,
        )
        # boss → player: ATTACK, negated if the player GUARDs.
        e_dmg = jnp.where(
            e_is_attack & (~p_is_guard),
            jnp.floor(jnp.float32(boss_atk_f) * (1.0 + s.enemy_charge.astype(jnp.float32))),
            0.0,
        )
        # charge updates: ATTACK → 0, CHARGE → min(MAX, +1), GUARD → unchanged.
        new_pcharge = jnp.where(
            p_is_attack,
            0,
            jnp.where(
                p_is_charge,
                jnp.minimum(_DUEL_MAX_CHARGE, s.player_charge + 1),
                s.player_charge,
            ),
        ).astype(jnp.int32)
        new_echarge = jnp.where(
            e_is_attack,
            0,
            jnp.minimum(_DUEL_MAX_CHARGE, s.enemy_charge + 1),  # boss only ATTACK/CHARGE
        ).astype(jnp.int32)

        # simultaneous damage (numpy: max(0, hp - max(0, dmg)) on both, unconditionally).
        ch = s.party_hp[act]
        nb = jnp.maximum(0.0, s.boss_hp - jnp.maximum(0.0, p_dmg))
        nc = jnp.maximum(0.0, ch - jnp.maximum(0.0, e_dmg))

        boss_fainted = nb <= 0
        player_fainted = nc <= 0
        win = boss_fainted & (~player_fainted)
        faint_done = boss_fainted | player_fainted
        trunc_battle = (~faint_done) & (turn >= _DUEL_TURN_CAP)
        battle_done = faint_done | trunc_battle

        gym = s.battle_gym
        new_level = s.party_level[act] + jnp.where(win, 1, 0)
        can_evolve = win & (~s.party_evolved[act]) & (new_level >= 2)
        reward = jnp.where(win, 1.0, 0.0) + jnp.where(can_evolve, 1.0, 0.0)
        s = s._replace(
            party_hp=s.party_hp.at[act].set(nc),
            boss_hp=nb,
            battle_turn=turn,
            gym_defeated=s.gym_defeated.at[gym].set(
                jnp.where(win, True, s.gym_defeated[gym])
            ),
            party_level=s.party_level.at[act].set(new_level),
            party_evolved=s.party_evolved.at[act].set(
                jnp.where(can_evolve, True, s.party_evolved[act])
            ),
            evolved=s.evolved + can_evolve.astype(jnp.int32),
            mode=jnp.where(battle_done, _MODE_OVERWORLD, _MODE_BATTLE).astype(jnp.int32),
            # numpy resets both charges to 0 when the duel ends.
            player_charge=jnp.where(battle_done, jnp.int32(0), new_pcharge),
            enemy_charge=jnp.where(battle_done, jnp.int32(0), new_echarge),
        )
        return s, reward

    def encode_obs(state: JaxEnvState) -> dict[str, jax.Array]:
        gridv = state.creature_mask.astype(jnp.int8) * _PATCH_CREATURE
        for i in range(max_gyms):
            show = state.gym_active[i] & (~state.gym_defeated[i])
            gr, gc = state.gym_pos[i, 0], state.gym_pos[i, 1]
            valid = show & (gr >= 0) & (gc >= 0)
            gr_s, gc_s = jnp.maximum(gr, 0), jnp.maximum(gc, 0)
            gridv = gridv.at[gr_s, gc_s].set(
                jnp.where(valid, jnp.int8(_PATCH_GYM), gridv[gr_s, gc_s])
            )
        padded = jnp.pad(gridv, patch_radius)
        patch = jax.lax.dynamic_slice(
            padded, (state.agent_pos[0], state.agent_pos[1]), (patch_side, patch_side),
        )

        in_battle = state.mode == _MODE_BATTLE
        act = state.active
        p_hp = jnp.where(in_battle, state.party_hp[act], 0.0).astype(jnp.int32)
        p_ty = jnp.where(in_battle, _stat(state, act, 6).astype(jnp.int32), 0)
        p_lvl = jnp.where(in_battle, state.party_level[act], 0)
        e_hp = jnp.where(in_battle, state.boss_hp, 0.0).astype(jnp.int32)
        e_ty = jnp.where(in_battle, state.gym_type[state.battle_gym], 0)
        defeated = jnp.sum((state.gym_defeated & state.gym_active).astype(jnp.int32))

        return {
            "agent_pos": state.agent_pos,
            "local_patch": patch,
            "caught": state.caught[jnp.newaxis],
            "gyms_defeated": defeated[jnp.newaxis],
            "evolved": state.evolved[jnp.newaxis],
            "in_battle": in_battle.astype(jnp.int8)[jnp.newaxis],
            "player_hp": p_hp[jnp.newaxis],
            "player_type": p_ty[jnp.newaxis],
            "player_level": p_lvl[jnp.newaxis],
            "enemy_hp": e_hp[jnp.newaxis],
            "enemy_type": e_ty[jnp.newaxis],
            # duel exposes real charge state (playable from obs); non-duel families keep
            # the harmonized charge keys 0-masked (byte-identical to the prior behavior).
            "player_charge": (
                state.player_charge[jnp.newaxis]
                if family == _FAM_DUEL
                else jnp.zeros((1,), dtype=jnp.int32)
            ),
            "enemy_charge": (
                state.enemy_charge[jnp.newaxis]
                if family == _FAM_DUEL
                else jnp.zeros((1,), dtype=jnp.int32)
            ),
        }

    def step(
        state: JaxEnvState, action: jax.Array
    ) -> tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array]:
        action = jnp.asarray(action, dtype=jnp.int32)
        steps = state.steps + jnp.int32(1)

        def ow(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
            return overworld_branch(s, action)

        def bt(s: JaxEnvState) -> tuple[JaxEnvState, jax.Array]:
            # family / commit are compile-time constants → pick the battle economy statically.
            if family == _FAM_DUEL:
                return duel_battle_branch(s, action)
            return battle_branch(s, action) if commit else noncommit_battle_branch(s, action)

        state, reward = jax.lax.cond(state.mode == _MODE_OVERWORLD, ow, bt, state)
        state = state._replace(steps=steps)
        terminated = jnp.all(jnp.where(state.gym_active, state.gym_defeated, True))
        truncated = steps >= max_steps
        return state, encode_obs(state), reward, terminated, truncated

    def make_step(jit: bool = True) -> Callable:
        return jax.jit(step) if jit else step

    return JaxEnv(config=config, reset=reset, step=step, encode_obs=encode_obs,
                  make_step=make_step)


# --- default-config instances (backward-compatible module-level API) ---
_DEFAULT_ENV = make_jax_env(DEFAULT_CONFIG)


def jax_reset(region: Region) -> JaxEnvState:
    """Bridge a numpy :class:`~critter_gym.region.Region` into a fresh episode state
    (default config). For other configs use ``make_jax_env(cfg).reset``."""
    return _DEFAULT_ENV.reset(region)


def jax_env_step(
    state: JaxEnvState, action: jax.Array
) -> tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array]:
    """One full-episode env step → (state, obs, reward, terminated, truncated) — default
    config. Mirrors ``CritterEnv(commit_battles=True).step`` for family A."""
    return _DEFAULT_ENV.step(state, action)


def encode_obs(state: JaxEnvState) -> dict[str, jax.Array]:
    """The 13-key observation (default config), matching ``CritterEnv._obs``."""
    return _DEFAULT_ENV.encode_obs(state)


def make_env_step(jit: bool = True) -> Callable[
    [JaxEnvState, jax.Array],
    tuple[JaxEnvState, dict[str, jax.Array], jax.Array, jax.Array, jax.Array],
]:
    """A ready full-episode env step (default config), ``jit`` by default. ``vmap`` it."""
    return _DEFAULT_ENV.make_step(jit)
