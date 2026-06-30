# How to: measure genre (env-family) transfer

> 한국어: [measure-genre-transfer.ko.md](measure-genre-transfer.ko.md)

CritterGym ships **four structurally distinct env families** that share one obs/action contract,
so you can measure whether a policy generalizes to a game *structure* it never trained on — an
env-level held-out split, one notch above seed-level generalization.

| family | id | structural axis |
|---|---|---|
| A | `CritterGym-procgen-v0` | catch → gyms → boss (the base RPG) |
| B | `CritterGym-forage-v0` | contact-collect collection mechanic |
| C | `CritterGym-duel-v0` | type-agnostic stamina/commit **battle system** |
| D | `CritterGym-muster-v0` | collection-gated power (muster a party before you can win) |

## Learned transfer to a held-out family

```bash
pip install -e ".[rl,jax]"
python scripts/genre_learned_transfer.py
```

This trains PPO on **train families** (a random family per episode) and measures transfer to a
**held-out family** it never trained on. Because all families share the harmonized observation
space (see `docs/reference/observation-action-space.md`), a single net consumes them all.

## Scripted skill-structural contrasts

```bash
python scripts/difficulty_generalization.py   # difficulty / generalization slices
```

For the scripted-policy contrasts across families (skill-structural differences) see
`critter_gym.genre_generalization`.

## Honest scope

- This is a **foundation, not a proof**: four families on three axes is a *direction* most
  benchmarks don't target, but it is **not** broad meta-RL task coverage (cf. XLand-MiniGrid).
- Transfer to the most distinct family (`duel`, a different battle system) is expected to need
  fine-tuning — that limitation is stated in `DESIGN.md` §3.1.1, not hidden.
