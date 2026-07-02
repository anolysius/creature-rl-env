# Env tiers (custom / hard difficulty) — reference

The M5-EC2 *custom/hard env* sales surface. `critter_gym.env_tier` packages the difficulty knobs
scattered across `CritterEnv.__init__` into a **named, validated, reproducible tier API**: a buyer
instantiates a curated difficulty grade by name, or defines a custom tier (validated).

> **Honest scope (prototype).** The `hard` tier's difficulty is what was **measured** — a
> feedforward PPO reaches only ~11–16% of the scripted oracle on the grid16 config while the
> oracle stays winnable (~2.81 gyms). Whether it is hard for a **SOTA/recurrent** agent is
> **OPEN (unmeasured)**; the tier descriptor says so and the module never claims difficulty it
> did not measure. The validation guard is a *static sanity* check, not a proof of winnability.
> Real sale / pricing / hosting is a human gate.

## Public API (`critter_gym.env_tier`)

| Symbol | Role |
|---|---|
| `TierSpec` | Serializable tier spec: CritterEnv knobs + `harder_knobs` + `difficulty_note`. `to_json`/`from_json`. |
| `validate_tier_spec(spec)` | Guard: `ValueError` on non-positive knobs, `num_types < 2`, `num_gyms > cells`, or a horizon too short to traverse the grid (`max_steps < 2*grid_size`). |
| `register_tier(name, spec)` | Register after validating (idempotent on an identical spec; conflict on a different one). |
| `tier_names()` / `get_tier(name)` | List / fetch registered tiers (`KeyError` on unknown). |
| `make_tier_env(name, *, seed=None, **overrides)` | Build a `CritterEnv` (overrides merged + re-validated; `vary=True`). |
| `tier_env_factory(name, **overrides)` | Zero-arg factory (SealedEvalSet.env_factory convention). |
| `sealed_config(name)` | Tier knobs restricted to what `SealedEvalSet` accepts. |
| `build_sealed(name, master_seed, **overrides)` | Build a `SealedEvalSet` from a tier (tier-knob overrides re-validated — no guard bypass). |

## Curated presets

| Tier | Knobs | Difficulty |
|---|---|---|
| `standard` | grid 10, gyms 3, steps 200, view_r 2, types 3, boss 120/12/12 | Free-baseline (CritterEnv defaults). |
| `hard` | grid 16, gyms 3, steps 300, view_r 2, types 3, boss 120/12/12 | Measured: feedforward PPO ~11–16% of oracle; oracle winnable. SOTA/recurrent = OPEN. |

## Sealed-eval tie-in — dropped knobs

`SealedEvalSet.__init__` does not accept `num_gyms`, `patch_radius`, or `num_creatures`.
`sealed_config` / `build_sealed` **drop** them (`_SEALED_DROPPED`). Since `patch_radius`/`num_gyms`
are difficulty levers, a sealed eval built from a tier may be **less hard** than the full tier env
— the dropped levers are not reflected in the sealed variant. Extending `SealedEvalSet` to carry
them is a human-gated follow-up.

## Demo

```bash
python scripts/list_env_tiers.py   # list tiers + metadata, register custom (valid + rejected),
                                   # smoke-run hard, show the sealed tie-in, honest-scope caption
```
