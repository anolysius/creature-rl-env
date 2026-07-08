"""Inference-difficulty curve — how hard is in-context rule inference vs. the hidden chart size?

The sealed inference eval reads one point: on a fixed ``num_types`` config, an idealized
first-sight inferrer (the scripted ``infer`` arm) plays super-effective some fraction of the
time. This module turns that point into a *curve*: sweep ``num_types`` and, for each, run the
scripted 4-arm band (:func:`eval_harness.inference_baseline`) and record where the infer arm
sits between the chart-blind floor and the chart-knowing oracle.

The mechanism: a bigger hidden chart means more distinct matchups, so within a fixed number of
gyms the first-sight inferrer has seen fewer of them — it should exploit the chart less often
as ``num_types`` grows. A clean monotone falloff means ``num_types`` is a *calibrated
inference-difficulty dial*; a flat curve falsifies that. Scripted-only, deterministic — a scout,
not a learned/LLM curve (that is money-gated follow-up work).
"""

from __future__ import annotations

from typing import Any, NamedTuple

from critter_gym.eval_harness import SealedEvalSet, inference_baseline, se_inference_score

# A config tuned so battles last long enough to infer (high boss hp, low atk, high def — the
# demonstrator economy) with enough gyms per world to expose several matchups. ``num_types`` is
# the swept knob, so it is *not* fixed here.
_CURVE_SEALED: dict[str, Any] = dict(
    master_seed=20260708, n_worlds=8, grid_size=8, num_gyms=5, max_steps=120,
    boss_hp=140, boss_atk=6, boss_def=18,
)
_ARMS = ("oracle", "infer", "type_blind", "probe")


class CurvePoint(NamedTuple):
    """One (``num_types``) point on the inference-difficulty curve (all scripted, deterministic)."""

    num_types: int
    oracle_se: float        # chart-KNOWING expert's super-effective-move rate (the ceiling)
    infer_se: float         # first-sight inferrer's SE-rate (the curve of interest)
    type_blind_se: float    # chart-BLIND floor
    probe_se: float         # blind-guess anchor
    infer_score: float      # infer_se normalized to [0,1] (0 = blind floor, 1 = oracle)
    oracle_gyms: float      # mean gyms the oracle clears (winnability check)
    winnable: bool          # oracle clears >= half the gyms → the task stays solvable in principle


def _point(num_types: int, sealed_kwargs: dict[str, Any]) -> CurvePoint:
    sealed = SealedEvalSet(num_types=num_types, **sealed_kwargs)
    band = inference_baseline(sealed)
    se = {a: band.arms[a].se_rate for a in _ARMS}
    infer_score = se_inference_score(se["infer"], se["oracle"], se["type_blind"])
    return CurvePoint(
        num_types=num_types,
        oracle_se=se["oracle"], infer_se=se["infer"],
        type_blind_se=se["type_blind"], probe_se=se["probe"],
        infer_score=infer_score,
        oracle_gyms=band.oracle_gyms,
        winnable=band.oracle_gyms >= 0.5 * sealed.num_gyms,
    )


def inference_difficulty_curve(
    num_types_grid: tuple[int, ...], *, sealed_kwargs: dict[str, Any] | None = None,
) -> tuple[CurvePoint, ...]:
    """The scripted inference-difficulty curve over ``num_types_grid``.

    For each ``num_types`` runs the 4-arm scripted band and records the arms' super-effective-move
    rates, the infer arm's normalized inference score, and a winnability flag. Deterministic (fixed
    master seed); ``sealed_kwargs`` overrides the tuned default config (``num_types`` is always the
    swept knob and must not appear in it)."""
    kw = dict(_CURVE_SEALED if sealed_kwargs is None else sealed_kwargs)
    kw.pop("num_types", None)  # num_types is the swept axis, never fixed
    return tuple(_point(n, kw) for n in num_types_grid)


# The diversity-dial config: a FIXED gym budget + a large type pool, so sweeping ``boss_pool_size``
# varies per-episode boss-type *diversity* (and thus revisits) cleanly. num_types is large enough
# to draw a diverse pool; num_gyms is held fixed so more diversity means fewer revisits.
_DIVERSITY_SEALED: dict[str, Any] = dict(
    master_seed=20260708, n_worlds=8, grid_size=8, num_gyms=8, num_types=12, max_steps=140,
    boss_hp=140, boss_atk=6, boss_def=18,
)


class DiversityPoint(NamedTuple):
    """One (``boss_pool_size``) point on the type-diversity dial (all scripted, deterministic)."""

    pool_size: int
    mean_distinct_types: float  # measured mean distinct boss-types per world (the real x-axis)
    oracle_se: float
    infer_se: float
    type_blind_se: float
    probe_se: float
    infer_score: float
    oracle_gyms: float
    winnable: bool


def _mean_distinct_types(pool_size: int, sealed: SealedEvalSet) -> float:
    """Mean distinct boss-types per world on the sealed block — the diversity actually realized."""
    from critter_gym.region import generate_region
    n = 0.0
    for seed in sealed._eval_seeds():
        region = generate_region(
            seed, sealed.grid_size, 5, sealed.num_gyms, vary=True, num_types=sealed.num_types,
            min_gyms=sealed.num_gyms, boss_pool_size=pool_size)
        n += len({t for (_, t) in region.gyms})
    return n / sealed.n_worlds


def diversity_curve(
    pool_grid: tuple[int, ...], *, sealed_kwargs: dict[str, Any] | None = None,
) -> tuple[DiversityPoint, ...]:
    """The scripted inference-difficulty curve over ``boss_pool_size`` (per-episode type diversity).

    At a fixed gym budget, a bigger pool means more distinct boss types recur (fewer revisits), so a
    first-sight inferrer should exploit the chart less. Each point records the 4-arm band, the infer
    arm's normalized inference score, and the *measured* mean distinct-types per world (the real
    x-axis — confirms the knob raised diversity). Deterministic."""
    kw = dict(_DIVERSITY_SEALED if sealed_kwargs is None else sealed_kwargs)
    kw.pop("boss_pool_size", None)  # boss_pool_size is the swept axis
    out = []
    for pool in pool_grid:
        sealed = SealedEvalSet(boss_pool_size=pool, **kw)
        band = inference_baseline(sealed)
        se = {a: band.arms[a].se_rate for a in _ARMS}
        out.append(DiversityPoint(
            pool_size=pool,
            mean_distinct_types=_mean_distinct_types(pool, sealed),
            oracle_se=se["oracle"], infer_se=se["infer"],
            type_blind_se=se["type_blind"], probe_se=se["probe"],
            infer_score=se_inference_score(se["infer"], se["oracle"], se["type_blind"]),
            oracle_gyms=band.oracle_gyms,
            winnable=band.oracle_gyms >= 0.5 * sealed.num_gyms,
        ))
    return tuple(out)
