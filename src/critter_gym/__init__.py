"""CritterGym — a procedurally-generated creature-collection RL environment.

Importing this package registers the Gymnasium environment ids, so
``gymnasium.make("CritterGym-v0")`` works after ``import critter_gym``.
"""

from critter_gym.baselines import greedy_policy, random_policy
from critter_gym.battle import (
    Battle,
    BattleAction,
    BattleState,
    Side,
    play_scripted,
    scripted_opponent,
)
from critter_gym.creatures import Creature, Move
from critter_gym.envs.critter_env import CritterEnv
from critter_gym.registration import register_envs
from critter_gym.types import ElementType, TypeChart

register_envs()

__all__ = [
    "Battle",
    "BattleAction",
    "BattleState",
    "Creature",
    "CritterEnv",
    "ElementType",
    "Move",
    "Side",
    "TypeChart",
    "greedy_policy",
    "play_scripted",
    "random_policy",
    "register_envs",
    "scripted_opponent",
]
__version__ = "0.0.1"
