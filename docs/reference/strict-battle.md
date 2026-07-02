# Strict battle (attrition lever, opt-in) — reference

An opt-in battle-economy variant targeting the paper's §5 limitation (i): the default
damage rule `max(1, floor(power * atk / def * eff))` lets even a resisted
(effectiveness < NEUTRAL) attack chip HP, so a no-inference "attrition" policy can win
gyms. With **`strict_battle=True` a resisted hit deals 0** — symmetrically, for both the
player and the boss. Effective hits (eff ≥ NEUTRAL) keep the exact legacy formula
(min-1 clamp included). **Off (default) is byte-identical** to the historical economy —
every published number (oracle 2.81/4.69, PPO 11–16%, recurrent 43%, tiers, the paper)
stays valid unchanged.

## How it works

- `battle.Battle(strict_battle=True)` — the single numpy choke point (`Battle.damage`):
  `eff < NEUTRAL → 0`, else legacy. Multi-type bosses use the *product* effectiveness
  (`multi_effectiveness`), so `super × resisted = NEUTRAL` still damages, while
  `neutral × resisted < NEUTRAL` zeroes out.
- `CritterEnv(strict_battle=True)` plumbs the flag into every gym battle (commit and
  non-commit). `scripted_opponent` is unchanged: every current creature has exactly one
  move, so its legacy-formula argmax is invariant (revisit if multi-move creatures land).
- JAX: `JaxEnvConfig(strict_battle=True)`; the flag is a compile-time constant — `False`
  compiles to the exact prior damage expression (byte-identical jaxpr), `True` wraps the
  four gym-damage sites (commit + non-commit, player + boss). Parity 0 is gated by
  `tests/test_jax_strict_battle_parity.py` ({commit, non-commit} × {single, multi-type}).
  The standalone ports `jax_battle.py`/`jax_battle_full.py` are not on the training path
  (same boundary as the multi-type boss port).
- **No unwinnable worlds**: the matchup guarantee (vary-mode boss types are only drawn
  from types some starter move strictly super-effects; with a hidden secondary the
  product is still ≥ `super_mult × 0.5 ≥ NEUTRAL`) means every boss has a party move
  with strict damage > 0. `tests/test_strict_battle.py` sweeps 200 hard-config seeds
  (single- and multi-type) as the executable proof.
- **Mutual-zero stalemates** (both sides resisted) end via the pre-existing
  `max_turns` draw: the battle truncates with no winner and the env leaves battle.

## Scout finding (16 held-out seeds, scripted only — SIGNAL, honest falsify)

`scripts/strict_battle_scout.py` at the hard-commit grid16 and base-commit grid10
configs, strict OFF vs ON:

| probe | OFF | ON | delta |
|---|---|---|---|
| oracle − type_blind spread (grid16 commit) | 2.56 | 2.56 | +0.00 |
| oracle − type_blind spread (grid10 commit) | 1.62 | 1.62 | +0.00 |
| non-commit attrition probe (always-attack) | clears all | clears all | +0.00 |

**The lever's premise did not survive the scout, and we report that as-is:**

1. **Commit mode**: a resisted commit already loses under the legacy rule (the boss
   out-damages the min-chip long before attrition could win), so zeroing resisted hits
   flips no scripted outcome — the spread is unchanged.
2. **Non-commit mode** (where the §5-(i) confound actually lives): a zero-inference
   always-attack policy **fully clears** both configs, strict on or off. Attrition runs
   on NEUTRAL chip damage + party cycling + full-heal battle re-entry — none of which
   strict touches by design (strict only zeroes *resisted* hits).

So `strict_battle` is a correct, tested, byte-identical-off engine rule, but **it does
not close the attrition confound** at current configs, and it is **not** a
discrimination-widening (sale-tier) lever on scripted evidence. Do not present it as
either. Whether a *stronger* variant (e.g. only-super-effective damage, no re-entry
heal, or boss-economy knobs that make resisted attrition matter) should exist is a
separate design decision with its own scout.

## Boundaries (read before quoting)

- Scripted arms + one deterministic probe on one seed set; no learned agent, no robust
  threshold, CPU. The falsify is about *scripted-visible* effects at *current* configs.
- A learned/LLM agent could still be affected by strict (e.g. wasted resisted turns
  changing credit assignment) — unmeasured; a pre-registered multi-seed measurement
  would be the follow-up if anyone wants to claim that.
- Default-off byte-identity is enforced by tests (`test_strict_battle.py` AC1) and the
  full pre-existing parity/test suite.
