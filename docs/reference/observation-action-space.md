# Reference: observation & action space

> Verified against `src/critter_gym/envs/critter_env.py`. 한국어: [observation-action-space.ko.md](observation-action-space.ko.md)

The action space is **`Discrete(6)`** and is reinterpreted by mode (overworld vs battle). The
observation is a `Dict` space; the same 13 keys are present in every env family (a harmonized
contract), so a single policy net can train across families.

## Action space — `Discrete(6)`

| Action | Overworld | Battle |
|---|---|---|
| `0` | move North | use attack move 0 |
| `1` | move South | use attack move 1 |
| `2` | move East | use attack move 2 |
| `3` | move West | use attack move 3 |
| `4` | Catch the creature on your tile | Switch to the next party member |
| `5` | Wait (no-op) | Pass / item |

In battle, moves `0–3` each have a **different hidden type**; which one is super-effective must
be **inferred from the damage dealt** (it is never revealed in the observation). The `in_battle`
obs flag tells you which interpretation is live.

## Observation space — `Dict`

| Key | Space | Meaning |
|---|---|---|
| `agent_pos` | `Box(0, grid_size-1, (2,), int64)` | agent row, col |
| `local_patch` | `Box(0, 2, (5,5), int8)` | egocentric view; tile codes `0`=empty `1`=creature `2`=gym |
| `caught` | `Box(0, num_creatures, (1,), int64)` | creatures caught so far |
| `gyms_defeated` | `Box(0, num_gyms, (1,), int64)` | gyms cleared so far |
| `evolved` | `Box(0, max_party, (1,), int64)` | party members evolved |
| `in_battle` | `Box(0, 1, (1,), int8)` | `1` during a gym-boss battle |
| `player_hp` | `Box(0, hp_max, (1,), int64)` | active creature hp (battle only; `0`-masked on overworld) |
| `player_type` | `Box(0, num_types-1, (1,), int64)` | active creature type (battle only) |
| `player_level` | `Box(0, level_max, (1,), int64)` | active creature level (battle only) |
| `enemy_hp` | `Box(0, hp_max, (1,), int64)` | enemy hp (battle only) |
| `enemy_type` | `Box(0, num_types-1, (1,), int64)` | enemy type (battle only) |
| `player_charge` | `Box(0, max_charge, (1,), int64)` | duel charge (family C; `0` elsewhere) |
| `enemy_charge` | `Box(0, max_charge, (1,), int64)` | duel charge (family C; `0` elsewhere) |

**Overworld masking:** the `player_*` / `enemy_*` battle fields are `0`-masked outside battle
(they read `0`, which means "not in battle" — *not* "no creature": your starter party always
exists). The text renderer (`critter_gym.llm_eval.render_obs`) reflects this honestly.

## Rewards — RLVR (verifiable boolean subgoals)

No dense shaping. Reward is `+1.0` on each verifiable subgoal completion:
- catch a creature (standing on its tile, action `4`),
- defeat a gym boss.

Episode **terminates** when every gym is defeated; **truncates** at the step budget
(`max_steps`). Movement, waiting, and catching on an empty/gym tile give `0.0`.

## Registered environments

`from critter_gym.registration import register_envs; register_envs()` then `gym.make(<id>)`.

| id | kwargs (vs the default) | what it is |
|---|---|---|
| `CritterGym-v0` | — | fixed M1 world (family A baseline) |
| `CritterGym-procgen-v0` | `vary=True, num_types=12, num_gyms=8, max_steps=400` | procedural region + per-seed hidden type chart; **train/test seed split** |
| `CritterGym-commit-v0` | procgen + `super_mult=3.0, boss_hp=140, boss_atk=18, commit_battles=True` | team-commit boss economy (makes inferring the chart load-bearing) |
| `CritterGym-forage-v0` | family B, procgen kwargs | contact-collect collection mechanic (genre generalization) |
| `CritterGym-duel-v0` | family C, procgen kwargs | type-agnostic stamina/commit duel battle |
| `CritterGym-muster-v0` | family D, `num_creatures=12, boss_hp=300, boss_def=24, max_steps=600` | collection-gated power (muster a party before you can win) |

## Train / test seed split (the moat property)

`reset(seed)` reproduces a region **exactly**. Seeds are split by `region.TEST_SEED_OFFSET`
(= 1,000,000): train seeds `< offset`, held-out (test) seeds `>= offset`. A held-out seed
generates a **new map *and* a new hidden type chart** — so a policy cannot have memorized it.
Use `critter_gym.generalization.heldout_seeds(n)` to draw held-out seeds, and
`critter_gym.eval_harness` for the sealed, contamination-guarded eval.
