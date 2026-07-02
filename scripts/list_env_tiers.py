"""Demo the named difficulty-graded env tier API (monetization-surface #5).

Lists the curated tiers with their difficulty metadata, registers a custom tier (one valid,
one rejected by the guard), smoke-runs the `hard` tier for one step, and shows the sealed-eval
tie-in. Prints an honest-scope caption.

    python scripts/list_env_tiers.py

Honest scope: the `hard` tier's difficulty is what was *measured* (feedforward PPO ~11-16% of
the scripted oracle on grid16; oracle still winnable; a recurrent PPO reached ~32-43% of oracle
at a related, deeper grid16 config — hard-benchmark #3/#5). OPEN (unmeasured): recurrent agents
at this exact tier config, and SOTA-class difficulty anywhere. The sealed tie-in carries the
difficulty levers patch_radius/num_gyms (only num_creatures is dropped — see env-tiers.md).
Real sale / pricing / hosting is a human gate.
"""
from __future__ import annotations

from critter_gym.env_tier import (
    TierSpec,
    build_sealed,
    get_tier,
    make_tier_env,
    register_tier,
    sealed_config,
    tier_names,
    validate_tier_spec,
)


def _rule(title: str) -> None:
    print(f"\n{'=' * 4} {title} {'=' * max(4, 56 - len(title))}")


def main() -> None:
    _rule("1. Curated tiers + difficulty metadata")
    for name in tier_names():
        t = get_tier(name)
        harder = ", ".join(t.harder_knobs) or "(baseline)"
        print(f"\n[{t.name}]  grid={t.grid_size} gyms={t.num_gyms} steps={t.max_steps} "
              f"view_r={t.patch_radius} types={t.num_types} "
              f"boss={t.boss_hp}/{t.boss_atk}/{t.boss_def}")
        print(f"  harder knobs: {harder}")
        print(f"  difficulty: {t.difficulty_note}")

    _rule("2. Register a custom tier (valid) + reject an invalid one")
    custom = TierSpec(
        name="custom_mid", grid_size=13, num_gyms=4, num_creatures=6, max_steps=260,
        patch_radius=2, num_types=4, boss_hp=140, boss_atk=13, boss_def=13,
        commit_battles=False, harder_knobs=("grid_size", "num_gyms", "num_types"),
        difficulty_note="a custom mid tier (unmeasured difficulty — sanity-checked only)",
    )
    register_tier("custom_mid", custom)
    print(f"registered custom tier -> tiers now: {tier_names()}")

    bad = custom._replace(name="custom_broken", num_types=1)  # single-type chart = invalid
    try:
        validate_tier_spec(bad)
        print("ERROR: guard let an invalid tier through")
    except ValueError as e:
        print(f"guard rejected invalid tier (as expected): {e}")

    _rule("3. Smoke-run the hard tier (one step)")
    env = make_tier_env("hard", seed=0)
    obs, reward, terminated, truncated, _ = env.step(0)
    print(f"hard env stepped once: reward={reward}  terminated={terminated}  truncated={truncated}")

    _rule("4. Sealed-eval tie-in (faithful difficulty levers)")
    cfg = sealed_config("hard")
    print(f"sealed_config('hard') keys: {sorted(cfg)}")
    print("  carries the difficulty levers patch_radius/num_gyms (drops only num_creatures)")
    sealed = build_sealed("hard", master_seed=20260701, n_worlds=4)
    print(f"build_sealed('hard'): n_worlds={sealed.n_worlds} grid_size={sealed.grid_size} "
          f"boss_hp={sealed.boss_hp} patch_radius={sealed.patch_radius} "
          f"num_gyms={sealed.num_gyms}")

    _rule("Honest scope")
    print("hard difficulty = MEASURED (feedforward PPO ~11-16% of oracle, grid16; "
          "oracle winnable; recurrent PPO ~32-43% at a related deeper config).")
    print("OPEN (unmeasured) = recurrent at this exact tier config; SOTA-class anywhere. "
          "sealed variant carries patch_radius/num_gyms (drops only num_creatures).")
    print("Real sale / pricing / hosting = human gate — not done here.")


if __name__ == "__main__":
    main()
