"""AC2: creature/move model — damage application, faint, heal clamp."""

from __future__ import annotations

from critter_gym.creatures import Creature, EvolvedForm, Move
from critter_gym.types import ElementType


def _make() -> Creature:
    return Creature(
        name="Emberling",
        types=(ElementType.FIRE,),
        max_hp=30,
        attack=12,
        defense=10,
        speed=8,
        moves=[Move("ember", ElementType.FIRE, 40)],
    )


def _evolvable() -> Creature:
    c = _make()
    c.evolve_level = 2
    c.evolves_to = EvolvedForm("Emberon", max_hp=60, attack=20, defense=14, speed=10)
    return c


def test_hp_defaults_to_max() -> None:
    c = _make()
    assert c.hp == c.max_hp == 30
    assert not c.is_fainted


def test_take_damage_and_faint() -> None:
    c = _make()
    c.take_damage(10)
    assert c.hp == 20
    c.take_damage(100)  # overkill clamps to 0
    assert c.hp == 0
    assert c.is_fainted


def test_heal_clamps_to_max() -> None:
    c = _make()
    c.take_damage(25)
    assert c.hp == 5
    c.heal(50)
    assert c.hp == c.max_hp  # clamped, not 55


def test_negative_amounts_are_ignored() -> None:
    c = _make()
    c.take_damage(-5)
    assert c.hp == 30
    c.heal(-5)
    assert c.hp == 30


# --- evolution (AC1/AC3/AC5) --------------------------------------------------

def test_level_gates_evolution() -> None:
    c = _evolvable()
    assert c.level == 1 and not c.can_evolve  # below threshold
    c.gain_level()
    assert c.level == 2 and c.can_evolve  # threshold reached


def test_evolve_boosts_stats_and_renames() -> None:
    c = _evolvable()
    base_hp, base_atk = c.max_hp, c.attack
    c.gain_level()
    c.evolve()
    assert c.evolved and c.name == "Emberon"
    assert c.max_hp > base_hp and c.attack > base_atk  # AC5: stronger
    assert not c.can_evolve  # no re-evolution


def test_evolve_below_threshold_is_noop() -> None:
    c = _evolvable()  # level 1
    c.evolve()
    assert not c.evolved and c.name == "Emberling"


def test_no_evolution_without_a_form() -> None:
    c = _make()  # evolves_to is None
    for _ in range(10):
        c.gain_level()
    assert not c.can_evolve
    c.evolve()
    assert not c.evolved


def test_evolve_scales_hp_not_a_free_heal() -> None:
    c = _evolvable()
    c.take_damage(15)  # 30 -> 15 (half)
    c.gain_level()
    c.evolve()  # max_hp 30 -> 60; half of 60 = 30
    assert c.hp == 30 and c.hp < c.max_hp
