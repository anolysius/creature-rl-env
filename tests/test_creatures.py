"""AC2: creature/move model — damage application, faint, heal clamp."""

from __future__ import annotations

from critter_gym.creatures import Creature, Move
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
