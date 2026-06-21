"""CritterGym — a procedurally-generated creature-collection RL environment.

Importing this package registers the Gymnasium environment ids, so
``gymnasium.make("CritterGym-v0")`` works after ``import critter_gym``.
"""

from critter_gym.envs.critter_env import CritterEnv
from critter_gym.registration import register_envs

register_envs()

__all__ = ["CritterEnv", "register_envs"]
__version__ = "0.0.1"
