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


@dataclass(frozen=True)
class EvolvedForm:
    """The stronger form a creature becomes on evolving (DESIGN.md §3.4).

    Stats are absolute (not deltas); they must exceed the base form so evolving
    is a real investment payoff.
    """

    name: str
    max_hp: int
    attack: int
    defense: int
    speed: int


@dataclass
class Creature:
    """A battle participant.

    ``types`` may hold 1–2 elements. ``hp`` defaults to ``max_hp`` at creation.
    A creature gains ``level`` from battle wins; on reaching ``evolve_level`` (and
    if it has an ``evolves_to`` form) it can evolve into stronger stats — a
    deliberate long-horizon investment, not dense reward shaping.
    """

    name: str
    types: tuple[ElementType, ...]
    max_hp: int
    attack: int
    defense: int
    speed: int
    moves: list[Move]
    hp: int = field(default=-1)
    level: int = 1
    evolve_level: int = 2
    evolves_to: EvolvedForm | None = None
    evolved: bool = False

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

    def gain_level(self) -> None:
        self.level += 1

    @property
    def can_evolve(self) -> bool:
        return (
            not self.evolved
            and self.evolves_to is not None
            and self.level >= self.evolve_level
        )

    def evolve(self) -> None:
        """Transform into the evolved form (idempotent once evolved).

        hp scales by the same fraction it was at, so evolving is not a free heal.
        """
        if not self.can_evolve or self.evolves_to is None:
            return
        form = self.evolves_to
        hp_fraction = self.hp / self.max_hp
        self.name = form.name
        self.max_hp = form.max_hp
        self.attack = form.attack
        self.defense = form.defense
        self.speed = form.speed
        self.hp = max(1, int(form.max_hp * hp_fraction))
        self.evolved = True
