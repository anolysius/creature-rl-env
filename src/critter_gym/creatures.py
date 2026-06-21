"""Creature and move data model for battles.

Deterministic by construction — no random rolls. Stats are plain integers and
``take_damage``/``heal`` mutate ``hp`` within ``[0, max_hp]``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from critter_gym.types import ElementType


@dataclass(frozen=True)
class Move:
    """A battle move: an element type and a base power."""

    name: str
    type: ElementType
    power: int


@dataclass
class Creature:
    """A battle participant.

    ``types`` may hold 1–2 elements. ``hp`` defaults to ``max_hp`` at creation.
    """

    name: str
    types: tuple[ElementType, ...]
    max_hp: int
    attack: int
    defense: int
    speed: int
    moves: list[Move]
    hp: int = field(default=-1)

    def __post_init__(self) -> None:
        if self.hp < 0:
            self.hp = self.max_hp

    @property
    def is_fainted(self) -> bool:
        return self.hp <= 0

    def take_damage(self, amount: int) -> None:
        self.hp = max(0, self.hp - max(0, amount))

    def heal(self, amount: int) -> None:
        self.hp = min(self.max_hp, self.hp + max(0, amount))
