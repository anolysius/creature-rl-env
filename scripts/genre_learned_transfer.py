#!/usr/bin/env python3
"""Does a *learned* policy transfer to an UNSEEN env family? — genre transfer ([rl]).

This is the missing piece for a real DESIGN §3.1.1 (B) genre-generalization claim: prior
(B) work compared *scripted* policies (skill-structural contrasts on families C/D), but a
credible claim needs a **learned** policy that generalizes to an env family it never trained
on. Here we train PPO on **train families** (random family per episode) and measure transfer
to a **held-out family**.

Obs constraint: a single PPO net needs one observation space. As of the obs-harmonization
task every family shares ONE harmonized obs space (``env_family.HARMONIZED_OBS_KEYS`` — the
charge keys are 0-masked on non-duel families, real on ``duel``), so ``assert_obs_compatible``
now accepts all four families and one net *can* train across them including duel. This default
default ``train_and_transfer`` run measures ``{critter, forage} → muster`` (the first
learned-transfer measurement). ``--loo`` / :func:`train_and_transfer_loo` then widens the
train distribution: a leave-one-out over all four families (incl. duel) on the SAME gap
metric, so "does a wider train set narrow the unseen-family gap?" is read against the #26
baseline on one axis (genre-transfer-policy task).

Honest scope: one train-set → one held-out family is **not** a genre-generalization proof —
it is the *first learned-policy transfer measurement*. We *report* the gap (with std); a weak
transfer (a large gap) is an honest result — "learned genre transfer is hard / (B) is still
open" — not a failure. Single run, modest N → a signal. Nothing here is a pass/fail threshold.

Usage:
    pip install -e ".[rl]"
    python scripts/genre_learned_transfer.py --timesteps 60000
"""

from __future__ import annotations

import argparse
import sys
import warnings
from dataclasses import dataclass

import gymnasium as gym
import numpy as np

from critter_gym.env_family import REQUIRED_OBS_KEYS, make_family
from critter_gym.generalization import evaluate, split_train_pool
from critter_gym.region import heldout_seeds

TRAIN_FAMILIES = ["critter", "forage"]
HELDOUT_FAMILY = "muster"
N_TRAIN = 64
N_HELDIN = 16
N_HELDOUT = 16


def assert_obs_compatible(families: list[str]) -> None:
    """Raise if the families don't share one observation space (needed for a single net).

    A family-agnostic learned policy needs identical obs keys across every family it sees.
    Since the obs-harmonization task all families expose ``HARMONIZED_OBS_KEYS`` (duel's
    charge keys are 0-masked elsewhere), so all four — including duel — are now accepted;
    this guard still fails loudly if a future family forks the obs space.
    """
    key_sets = {f: frozenset(make_family(f).observation_space.spaces) for f in families}
    shared = set.intersection(*(set(k) for k in key_sets.values())) if key_sets else set()
    if not REQUIRED_OBS_KEYS.issubset(shared):
        raise ValueError("families must all expose REQUIRED_OBS_KEYS")
    for f, ks in key_sets.items():
        if set(ks) != set(next(iter(key_sets.values()))):
            raise ValueError(
                f"family {f!r} has a different obs space {sorted(set(ks) ^ shared)}; "
                "a single learned net needs obs-identical families (duel is excluded)"
            )


@dataclass(frozen=True)
class TransferReport:
    """A learned policy's mean on its train families (held-in) vs an unseen family."""

    train_families: tuple[str, ...]
    heldout_family: str
    heldin_mean: float
    heldin_std: float
    heldout_mean: float
    heldout_std: float

    @property
    def gap(self) -> float:
        """Env-level transfer gap (train families − unseen family). Reported, not thresholded."""
        return self.heldin_mean - self.heldout_mean


class _MultiFamilyEnv(gym.Env):
    """Training env that cycles through ``families`` (one per reset) over a seed pool.

    All families must be obs-identical (checked by the caller). Each reset picks the next
    (family, seed) so PPO trains on a mix of train families without ever seeing the held-out one.
    """

    def __init__(self, families: list[str], seeds: tuple[int, ...]) -> None:
        super().__init__()
        self._families = list(families)
        self._seeds = tuple(int(s) for s in seeds)
        probe = make_family(self._families[0])
        self.observation_space = probe.observation_space
        self.action_space = probe.action_space
        self._env = probe
        self._i = 0

    def reset(self, *, seed=None, options=None):  # type: ignore[no-untyped-def]
        fam = self._families[self._i % len(self._families)]
        s = self._seeds[self._i % len(self._seeds)]
        self._i += 1
        self._env = make_family(fam)  # type: ignore[assignment]
        return self._env.reset(seed=s, options=options)

    def step(self, action):  # type: ignore[no-untyped-def]
        return self._env.step(action)


def _family_factory(name: str):
    return lambda: make_family(name)


# (a') policy/obs-representation knobs (transfer-skill-policy). The bare PPO feeds raw obs —
# but `player_hp`/`enemy_hp` (bound 10000) and `player_level` (100) are huge vs the small
# categorical keys (in_battle 0/1, local_patch 0-2, types). The pilot found that a *whole-obs*
# VecNormalize HURTS (it corrupts the categorical keys), so we instead scale ONLY these large
# continuous keys by their fixed space bound → [0,1]. Deterministic (no running stats), so
# eval reproducibility is trivial — the same divisor is reapplied at eval time.
_LARGE_OBS_KEYS: tuple[str, ...] = ("player_hp", "enemy_hp", "player_level")


def _obs_scales(env: object) -> dict[str, float]:
    """Per-key divisor = the obs-space upper bound, for the large continuous keys only."""
    space = env.observation_space  # type: ignore[attr-defined]
    return {k: float(np.asarray(space[k].high).max()) for k in _LARGE_OBS_KEYS}


def _scale_obs(obs: dict, scales: dict[str, float]) -> dict:
    out = dict(obs)
    for k, s in scales.items():
        out[k] = (np.asarray(obs[k], dtype=np.float32) / s)
    return out


class _ScaleObs(gym.ObservationWrapper):
    """Deterministically scale the large continuous obs keys to ~[0,1]; leave the rest."""

    def __init__(self, env: gym.Env) -> None:
        super().__init__(env)
        from gymnasium import spaces

        self._scales = _obs_scales(env)
        sp = dict(env.observation_space.spaces)  # type: ignore[attr-defined]
        for k in self._scales:
            sp[k] = spaces.Box(0.0, 1.0, shape=sp[k].shape, dtype=np.float32)
        self.observation_space = spaces.Dict(sp)

    def observation(self, obs: dict) -> dict:
        return _scale_obs(obs, self._scales)


def train_and_transfer(
    train_families: list[str] = TRAIN_FAMILIES,
    heldout_family: str = HELDOUT_FAMILY,
    timesteps: int = 60_000,
    *,
    n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
    seed: int = 0,
    net_arch: list[int] | None = None,
    scale_obs: bool = False,
) -> TransferReport:
    """Train PPO on ``train_families`` and measure transfer to the unseen ``heldout_family``.

    Importable so a CI smoke test can use a tiny budget. Raises ImportError if ``[rl]`` is
    missing (callers gate with importorskip). Held-in eval seeds are carved disjoint from the
    learning seeds; the held-out *family* is never trained on (family-level split).

    (a') knobs (transfer-skill-policy), default off = the bare baseline (backward compatible):
    ``net_arch`` sets a larger PPO net (e.g. ``[256, 256]``); ``scale_obs`` applies the
    deterministic large-key obs scaling (:class:`_ScaleObs`). Both are reproducible.
    """
    assert_obs_compatible([*train_families, heldout_family])
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    warnings.filterwarnings("ignore")
    learn_seeds, heldin = split_train_pool(range(N_TRAIN), n_eval=n_heldin)
    heldout = heldout_seeds(n_heldout)
    scales = _obs_scales(make_family(train_families[0])) if scale_obs else {}

    def make_train_env() -> gym.Env:
        env: gym.Env = _MultiFamilyEnv(train_families, learn_seeds)
        return _ScaleObs(env) if scale_obs else env

    policy_kwargs = {"net_arch": list(net_arch)} if net_arch else None
    model = PPO("MultiInputPolicy", DummyVecEnv([make_train_env]),
                verbose=0, n_steps=512, seed=seed, policy_kwargs=policy_kwargs)
    model.learn(timesteps, progress_bar=False)

    def policy(obs: dict) -> int:
        if scales:
            obs = _scale_obs(obs, scales)
        return int(model.predict(obs, deterministic=True)[0])

    # Held-in: mean over train families on held-in seeds (disjoint from learning seeds).
    heldin_returns: list[float] = []
    for fam in train_families:
        heldin_returns.extend(evaluate(_family_factory(fam), policy, heldin).returns)
    out = evaluate(_family_factory(heldout_family), policy, heldout)

    import numpy as np

    return TransferReport(
        train_families=tuple(train_families),
        heldout_family=heldout_family,
        heldin_mean=float(np.mean(heldin_returns)) if heldin_returns else 0.0,
        heldin_std=float(np.std(heldin_returns)) if heldin_returns else 0.0,
        heldout_mean=out.mean,
        heldout_std=out.std,
    )


# #26 baseline (genre-learned-transfer): train {critter, forage} → held-out muster, on the
# SAME gap metric (held_in_mean − held_out_family_mean). Reported alongside the widened-train
# folds so "does a wider train distribution narrow the unseen-family gap?" is read on one axis.
BASELINE_26 = ("train{critter,forage} → muster (2-family, #26)", 2.94, 0.38, 2.56)

ALL_FAMILIES = ["critter", "forage", "duel", "muster"]


def train_and_transfer_loo(
    families: list[str] = ALL_FAMILIES,
    timesteps: int = 60_000,
    *,
    n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
    seed: int = 0,
    net_arch: list[int] | None = None,
    scale_obs: bool = False,
) -> list[TransferReport]:
    """Leave-one-out widened-train transfer over ``families`` — one fold per held-out family.

    Each fold trains a single PPO net on the other N−1 families (a *wider* train distribution
    than #26's two families, and one that — post obs-harmonization — can include ``duel``) and
    measures transfer to the held-out family. Every fold reports the SAME gap metric as #26
    (``held_in_mean − held_out_family_mean``), so the folds and the #26 baseline are directly
    comparable on one axis: does widening the train distribution narrow the unseen-family gap?

    Honest scope: still a single run at modest N/budget — a *signal*, not a proof. A narrower
    gap is encouraging (B moving toward a claim); a gap that stays wide is the honest
    "(B) is still open even with a wider train set" result. Nothing here is a pass threshold.
    """
    assert_obs_compatible(families)
    reports: list[TransferReport] = []
    for held in families:
        train = [f for f in families if f != held]
        reports.append(
            train_and_transfer(
                train, held, timesteps=timesteps,
                n_heldin=n_heldin, n_heldout=n_heldout, seed=seed,
                net_arch=net_arch, scale_obs=scale_obs,
            )
        )
    return reports


@dataclass(frozen=True)
class MultiRunFoldReport:
    """One LOO fold aggregated across ``n_runs`` independent training seeds.

    The single-run gap (held-in − held-out family) is a point estimate; running the fold over
    several seeds and reporting mean ± **std across runs** tells us whether the transfer signal
    is stable or just run-to-run noise (transfer-rigor task). The gap metric is unchanged from
    #26/#27 — only its run-variance is now quantified.
    """

    heldout_family: str
    train_families: tuple[str, ...]
    n_runs: int
    heldin_mean: float
    heldin_std: float
    heldout_mean: float
    heldout_std: float
    gap_mean: float
    gap_std: float


def train_and_transfer_loo_multirun(
    families: list[str] = ALL_FAMILIES,
    timesteps: int = 60_000,
    *,
    n_runs: int = 3,
    n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
    base_seed: int = 0,
    net_arch: list[int] | None = None,
    scale_obs: bool = False,
) -> list[MultiRunFoldReport]:
    """Multi-run widened-train LOO — each fold repeated over ``n_runs`` seeds, aggregated.

    For every held-out family we run :func:`train_and_transfer_loo`'s fold ``n_runs`` times
    (seeds ``base_seed + i``) and report the per-fold held-in / held-out / gap as mean ± **std
    across runs**. This robustifies #27's single-run signal: a narrow gap that holds within the
    run-to-run std is a stronger signal; a gap whose sign flips across runs is noise.

    Honest scope: still one config, modest N/budget, deterministic bosses — run-variance is
    quantified, but this is not a proof. Read gap_mean WITH gap_std and the absolute columns.
    """
    assert_obs_compatible(families)
    out: list[MultiRunFoldReport] = []
    for held in families:
        train = tuple(f for f in families if f != held)
        runs = [
            train_and_transfer(
                list(train), held, timesteps=timesteps,
                n_heldin=n_heldin, n_heldout=n_heldout, seed=base_seed + i,
                net_arch=net_arch, scale_obs=scale_obs,
            )
            for i in range(n_runs)
        ]
        hin = [r.heldin_mean for r in runs]
        hout = [r.heldout_mean for r in runs]
        gaps = [r.gap for r in runs]
        out.append(
            MultiRunFoldReport(
                heldout_family=held, train_families=train, n_runs=n_runs,
                heldin_mean=float(np.mean(hin)), heldin_std=float(np.std(hin)),
                heldout_mean=float(np.mean(hout)), heldout_std=float(np.std(hout)),
                gap_mean=float(np.mean(gaps)), gap_std=float(np.std(gaps)),
            )
        )
    return out


# Held-in ceilings from prior tasks (3-family widened-train muster fold, SAME held-in metric),
# printed as baselines so "does capacity×budget recover held-in?" is read on one axis.
# #26 = 2-family single-family reference; #28 = budget-only@150k; #30 = net-only@50k.
HELD_IN_CEILINGS = (
    ("#26 ref (2-family)", 2.94),
    ("#28 budget-only @150k", 2.07),
    ("#30 net-only @50k", 1.15),
)
RECOVERY_THRESHOLD = 2.5  # pre-registered: held-in ≥ this ≈ #26 level ⇒ confound recovered.


@dataclass(frozen=True)
class SweepRow:
    """One (capacity, budget) config's widened held-in on the anchor fold, over ``n_runs`` seeds."""

    label: str
    net_arch: tuple[int, ...] | None
    timesteps: int
    n_runs: int
    heldin_mean: float
    heldin_std: float
    heldout_mean: float
    heldout_std: float
    gap_mean: float
    gap_std: float


def held_in_sweep(
    configs: list[dict],
    held_out: str = HELDOUT_FAMILY,
    families: list[str] = ALL_FAMILIES,
    *,
    n_runs: int = 3,
    n_heldin: int = N_HELDIN,
    n_heldout: int = N_HELDOUT,
    base_seed: int = 0,
) -> list[SweepRow]:
    """Multi-run widened held-in on the anchor ``held_out`` fold for each (net, budget) config.

    The pilot found that *budget* (not capacity) drives held-in recovery, so this sweep varies both
    over the same fold to robustly locate the held-in ceiling against ``RECOVERY_THRESHOLD``. Each
    config repeats over ``n_runs`` seeds; held-in/held-out/gap are mean ± std-across-runs.
    """
    train = [f for f in families if f != held_out]
    assert_obs_compatible([*train, held_out])
    rows: list[SweepRow] = []
    for cfg in configs:
        net = cfg.get("net_arch")
        ts = int(cfg["timesteps"])
        runs = [
            train_and_transfer(
                train, held_out, timesteps=ts, n_heldin=n_heldin, n_heldout=n_heldout,
                seed=base_seed + i, net_arch=net, scale_obs=bool(cfg.get("scale_obs", False)),
            )
            for i in range(n_runs)
        ]
        hin = [r.heldin_mean for r in runs]
        hout = [r.heldout_mean for r in runs]
        gaps = [r.gap for r in runs]
        rows.append(
            SweepRow(
                label=str(cfg["label"]),
                net_arch=tuple(net) if net else None,
                timesteps=ts, n_runs=n_runs,
                heldin_mean=float(np.mean(hin)), heldin_std=float(np.std(hin)),
                heldout_mean=float(np.mean(hout)), heldout_std=float(np.std(hout)),
                gap_mean=float(np.mean(gaps)), gap_std=float(np.std(gaps)),
            )
        )
    return rows


def charge_trace(family: str, seed: int = 0, steps: int = 200) -> list[int]:
    """Per-step max(player_charge, enemy_charge) over a scripted rollout — numpy-only.

    Used to *prove* the zero-shot duel block (duel-fewshot-adapt): across the train families the
    charge keys stay 0 the whole rollout (degenerate → unlearnable), while duel drives them > 0.
    """
    from critter_gym.genre_generalization import nav_toward_gyms

    env = make_family(family)
    obs, _ = env.reset(seed=seed)  # type: ignore[attr-defined]
    trace = [0]
    for _ in range(steps):
        obs, _, term, trunc, _ = env.step(nav_toward_gyms(obs))  # type: ignore[attr-defined]
        trace.append(max(int(obs["player_charge"][0]), int(obs["enemy_charge"][0])))
        if term or trunc:
            obs, _ = env.reset(seed=seed)  # type: ignore[attr-defined]
    return trace


@dataclass(frozen=True)
class FewShotPoint:
    """duel held-out score after ``adapt_budget`` steps of fine-tuning, over ``n_runs`` seeds."""

    adapt_budget: int
    n_runs: int
    duel_mean: float
    duel_std: float


def fewshot_adapt_curve(
    train_families: list[str],
    target: str = "duel",
    base_timesteps: int = 150_000,
    adapt_budgets: list[int] | None = None,
    *,
    n_runs: int = 3,
    n_heldout: int = N_HELDOUT,
    base_seed: int = 0,
) -> list[FewShotPoint]:
    """Few-shot adaptation curve: train a base policy on ``train_families``, then fine-tune on the
    held-out ``target`` for each adapt budget, scoring ``target`` held-out at each step.

    ``adapt_budgets`` must start at 0 (= zero-shot, the #32 baseline). Budgets are *cumulative*
    fine-tuning on the target family; the held-out eval seeds are disjoint from the fine-tune
    (learn) seeds, so this measures few-shot adaptation, not memorisation. Zero-shot transfer to
    ``duel`` is mechanism-blocked (charge degenerate in train, see :func:`charge_trace`); this
    asks the separate question of whether a *little* adaptation reaches it.
    """
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv

    warnings.filterwarnings("ignore")
    budgets = adapt_budgets if adapt_budgets is not None else [0, 25_000, 50_000, 100_000]
    learn_seeds, _ = split_train_pool(range(N_TRAIN), n_eval=8)
    heldout = heldout_seeds(n_heldout)
    per_budget: dict[int, list[float]] = {b: [] for b in budgets}

    for i in range(n_runs):
        model = PPO(
            "MultiInputPolicy",
            DummyVecEnv([lambda: _MultiFamilyEnv(train_families, learn_seeds)]),
            verbose=0, n_steps=512, seed=base_seed + i,
        )
        model.learn(base_timesteps, progress_bar=False)

        def policy(obs: dict, _m: object = model) -> int:
            return int(_m.predict(obs, deterministic=True)[0])  # type: ignore[attr-defined]

        prev = 0
        for b in budgets:
            if b > prev:  # cumulative fine-tuning on the target family
                model.set_env(DummyVecEnv([lambda: _MultiFamilyEnv([target], learn_seeds)]))
                model.learn(b - prev, progress_bar=False)
                prev = b
            per_budget[b].append(evaluate(_family_factory(target), policy, heldout).mean)

    return [
        FewShotPoint(
            adapt_budget=b, n_runs=n_runs,
            duel_mean=float(np.mean(per_budget[b])), duel_std=float(np.std(per_budget[b])),
        )
        for b in budgets
    ]


def budget_ladder_configs(budgets: list[int]) -> list[dict]:
    """Baseline-net configs at each budget — the budget ladder (transfer-budget-recovery).

    Capacity (a bigger net) was ruled out as a lever in transfer-capacity-budget (it underfits),
    so the ladder fixes ``net_arch=None`` and varies only the PPO budget to find where held-in
    recovery (≥ RECOVERY_THRESHOLD) plateaus.
    """
    return [
        {"label": f"baseline-net @{b:,}", "net_arch": None, "timesteps": int(b)}
        for b in budgets
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timesteps", type=int, default=60_000)
    parser.add_argument(
        "--loo", action="store_true",
        help="widened-train leave-one-out over all 4 families (incl. duel), vs the #26 baseline",
    )
    parser.add_argument(
        "--runs", type=int, default=1,
        help="repeat the LOO over N seeds and report per-fold mean ± std across runs "
             "(transfer-rigor; implies --loo). N=1 is the single-run --loo table.",
    )
    parser.add_argument(
        "--improved", action="store_true",
        help="(a') policy/obs improvements: bigger net (net_arch=[256,256]) + deterministic "
             "large-key obs scaling (transfer-skill-policy). Run with and without to compare "
             "widened held-in. NOTE: whole-obs VecNormalize was pilot-rejected (it hurt).",
    )
    parser.add_argument(
        "--sweep", action="store_true",
        help="(transfer-capacity-budget) multi-run capacity×budget sweep on the muster anchor "
             "fold vs the prior-task held-in ceilings + pre-registered recovery threshold.",
    )
    parser.add_argument("--runs-n", type=int, default=5, help="seeds per sweep config (--sweep)")
    parser.add_argument(
        "--budgets", type=str, default="",
        help="(transfer-budget-recovery) comma-separated budgets for a baseline-net budget "
             "ladder on the muster fold (e.g. 250000,400000,500000); capacity ruled out in #31.",
    )
    parser.add_argument(
        "--fewshot", action="store_true",
        help="(duel-fewshot-adapt) train on {critter,forage,muster}, then few-shot fine-tune on "
             "held-out duel over an adapt-budget ladder; report the duel adaptation curve.",
    )
    args = parser.parse_args()

    if args.fewshot:
        try:
            curve = fewshot_adapt_curve(
                ["critter", "forage", "muster"], "duel", n_runs=args.runs_n,
            )
        except ImportError:
            print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
            return 2
        print(
            f"few-shot adaptation to held-out duel | base=train{{critter,forage,muster}} | "
            f"runs={args.runs_n}\n"
        )
        print("Zero-shot duel is mechanism-blocked: charge (the duel RPS feature) is degenerate "
              "(≡0) across train families, so it is unlearnable zero-shot (see charge_trace).\n")
        print("| adapt budget (fine-tune on duel) | duel held-out (±run-std) |")
        print("|---|---|")
        for p in curve:
            tag = " (zero-shot)" if p.adapt_budget == 0 else ""
            print(f"| {p.adapt_budget:,}{tag} | {p.duel_mean:.3f} ±{p.duel_std:.3f} |")
        z0 = curve[0]
        bar = z0.duel_mean + z0.duel_std
        small = [p for p in curve if 0 < p.adapt_budget <= 50_000 and p.duel_mean > bar]
        big = [p for p in curve if p.adapt_budget > 50_000 and p.duel_mean > bar]
        if small:
            verdict = (f"ADAPTS: ≤50k fine-tune lifts duel above zero-shot z0+σ0 "
                       f"({z0.duel_mean:.2f}+{z0.duel_std:.2f}) — few-shot reaches duel fast.")
        elif big:
            verdict = (f"SLOW: only >50k fine-tune lifts duel above z0+σ0 "
                       f"({z0.duel_mean:.2f}+{z0.duel_std:.2f}).")
        else:
            verdict = (f"NO: even max fine-tune stays within z0+σ0 "
                       f"({z0.duel_mean:.2f}+{z0.duel_std:.2f}) — duel resists even few-shot.")
        print(f"\nPre-registered verdict (vs this run's zero-shot z0+σ0): {verdict}\n"
              f"⚠ Zero-shot ≠ few-shot (different claims). held-out eval seeds disjoint from "
              f"fine-tune seeds. Single config, deterministic bosses — a signal, not a proof. "
              f"See DESIGN §3.1.1.")
        return 0
    improved_kw = (
        {"net_arch": [256, 256], "scale_obs": True} if args.improved else {}
    )

    if args.budgets:
        budgets = [int(b) for b in args.budgets.split(",") if b.strip()]
        try:
            rows = held_in_sweep(budget_ladder_configs(budgets), n_runs=args.runs_n)
        except ImportError:
            print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
            return 2
        print(
            f"budget ladder (baseline-net, capacity ruled out) | muster anchor fold | "
            f"runs={args.runs_n}\n"
        )
        print("Held-in ceilings from prior tasks (same metric):")
        for name, val in HELD_IN_CEILINGS:
            print(f"  {name:28s} held-in {val:.2f}")
        print("  #31 budget-only @250k        held-in 2.44")
        print(f"  pre-registered recovery threshold: held-in ≥ {RECOVERY_THRESHOLD}\n")
        print("| config | held-in (±run-std) | held-out (±run-std) | gap (±run-std) |")
        print("|---|---|---|---|")
        for r in rows:
            print(
                f"| {r.label} | {r.heldin_mean:.3f} ±{r.heldin_std:.3f} "
                f"| {r.heldout_mean:.3f} ±{r.heldout_std:.3f} "
                f"| {r.gap_mean:+.3f} ±{r.gap_std:.3f} |"
            )
        best = max(rows, key=lambda r: r.heldin_mean)
        if best.heldin_mean >= RECOVERY_THRESHOLD:
            verdict = (f"RECOVERY: best held-in {best.heldin_mean:.2f} ≥ {RECOVERY_THRESHOLD} "
                       f"({best.label}) — re-measure the full-LOO confound-reduced gap.")
        elif best.heldin_mean > 2.44 + best.heldin_std:
            verdict = (f"APPROACHING: best held-in {best.heldin_mean:.2f} (>2.44 #31, "
                       f"<{RECOVERY_THRESHOLD}) — budget still helping, no full recovery yet.")
        else:
            verdict = (f"PLATEAU: best held-in {best.heldin_mean:.2f} ≤ ~2.44 within run-std — "
                       f"more budget does NOT recover held-in; the budget lever has flattened.")
        print(f"\nPre-registered verdict (read WITH run-std): {verdict}\n"
              f"⚠ Single anchor fold, deterministic bosses — a signal, not a proof. DESIGN §3.1.1.")
        return 0

    if args.sweep:
        configs = [
            {"label": "baseline-net @150k (budget-only, #28)",
             "net_arch": None, "timesteps": 150_000},
            {"label": "baseline-net @250k (more budget)",
             "net_arch": None, "timesteps": 250_000},
            {"label": "big-net[256,256] @250k (capacity+budget)",
             "net_arch": [256, 256], "timesteps": 250_000},
        ]
        try:
            rows = held_in_sweep(configs, n_runs=args.runs_n)
        except ImportError:
            print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
            return 2
        print(
            f"capacity×budget sweep | muster anchor fold (train{{critter,forage,duel}}) | "
            f"runs={args.runs_n}\n"
        )
        print("Held-in ceilings from prior tasks (same metric):")
        for name, val in HELD_IN_CEILINGS:
            print(f"  {name:28s} held-in {val:.2f}")
        print(f"  pre-registered recovery threshold: held-in ≥ {RECOVERY_THRESHOLD}\n")
        print("| config | held-in (±run-std) | held-out (±run-std) | gap (±run-std) |")
        print("|---|---|---|---|")
        for r in rows:
            print(
                f"| {r.label} | {r.heldin_mean:.3f} ±{r.heldin_std:.3f} "
                f"| {r.heldout_mean:.3f} ±{r.heldout_std:.3f} "
                f"| {r.gap_mean:+.3f} ±{r.gap_std:.3f} |"
            )
        best = max(rows, key=lambda r: r.heldin_mean)
        ceil_budget = 2.07  # #28 budget-only @150k
        if best.heldin_mean >= RECOVERY_THRESHOLD:
            verdict = (f"RECOVERY: best held-in {best.heldin_mean:.2f} ≥ {RECOVERY_THRESHOLD} "
                       f"({best.label}) — confound looks removable; re-measure the gap.")
        elif best.heldin_mean > ceil_budget + best.heldin_std:
            verdict = (f"PARTIAL: best held-in {best.heldin_mean:.2f} (>{ceil_budget} budget-only "
                       f"ceiling, <{RECOVERY_THRESHOLD}) — budget helps but no full recovery.")
        else:
            verdict = (f"BOUNDARY CLOSED: best held-in {best.heldin_mean:.2f} ≤ ~{ceil_budget} "
                       f"within run-std — capacity+budget does NOT recover held-in.")
        print(f"\nPre-registered verdict (read WITH run-std): {verdict}\n"
              f"⚠ Single config, deterministic bosses — a signal, not a proof. See DESIGN §3.1.1.")
        return 0

    if args.runs > 1:
        try:
            mfolds = train_and_transfer_loo_multirun(
                timesteps=args.timesteps, n_runs=args.runs, **improved_kw
            )
        except ImportError:
            print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
            return 2
        cfg = "IMPROVED (net256 + obs-scale)" if args.improved else "baseline (bare PPO)"
        print(
            f"multi-run widened-train LOO | PPO timesteps={args.timesteps:,} | "
            f"runs={args.runs} (seeds 0..{args.runs - 1}) | config={cfg}\n"
        )
        print("Per-fold mean ± std ACROSS RUNS. Same gap metric as #26/#27 (held-in − held-out).\n")
        print(
            "| train → held-out family | held-in (±run-std) "
            "| held-out (±run-std) | gap (±run-std) |"
        )
        print("|---|---|---|---|")
        label, b_in, b_out, b_gap = BASELINE_26
        print(f"| {label} | {b_in:.3f} | {b_out:.3f} | {b_gap:+.3f} (single run) |")
        for f in mfolds:
            train_lbl = "{" + ",".join(f.train_families) + "}"
            print(
                f"| train{train_lbl} → {f.heldout_family} (3-family) "
                f"| {f.heldin_mean:.3f} ±{f.heldin_std:.3f} "
                f"| {f.heldout_mean:.3f} ±{f.heldout_std:.3f} "
                f"| {f.gap_mean:+.3f} ±{f.gap_std:.3f} |"
            )
        print(
            f"\nReported, not pass/fail. gap_mean WITH gap_std: a narrow gap that holds within "
            f"its run-std is a stronger signal than #27's single run; a gap whose sign flips "
            f"across runs is noise.\n"
            f"⚠ Honest caveats: (1) read gap WITH the absolute held-in column — if held-in did "
            f"NOT rise vs #27 (~1.1–2.0) at higher budget, the generalist-mediocrity confound "
            f"STANDS (absolute skill is bottlenecked by policy/obs/env, not compute), so a "
            f"narrow/negative gap is not proof of strong transfer. (2) Single config, "
            f"N={N_HELDIN}/{N_HELDOUT}, deterministic bosses — run-variance is quantified, not a "
            f"proof. See DESIGN §3.1.1."
        )
        return 0

    if args.loo:
        try:
            folds = train_and_transfer_loo(timesteps=args.timesteps, **improved_kw)
        except ImportError:
            print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
            return 2
        print(f"widened-train LOO genre transfer | PPO timesteps={args.timesteps:,}\n")
        print("Same gap metric as #26 (held-in − held-out family). Lower gap = better transfer.\n")
        print("| train → held-out family | held-in (±std) | held-out (±std) | transfer gap |")
        print("|---|---|---|---|")
        label, b_in, b_out, b_gap = BASELINE_26
        print(f"| {label} | {b_in:.3f} | {b_out:.3f} | {b_gap:+.3f} |")
        for f in folds:
            train_lbl = "{" + ",".join(f.train_families) + "}"
            print(
                f"| train{train_lbl} → {f.heldout_family} (3-family) "
                f"| {f.heldin_mean:.3f} ±{f.heldin_std:.3f} "
                f"| {f.heldout_mean:.3f} ±{f.heldout_std:.3f} | {f.gap:+.3f} |"
            )
        print(
            f"\nReported, not pass/fail. Compare each 3-family fold's gap to the #26 "
            f"2-family baseline (+{b_gap:.2f}) on the SAME axis: a *narrower* gap is a signal "
            f"that a wider train distribution helps unseen-family transfer; a gap that stays "
            f"wide is the honest '(B) still open even with a wider train set' result.\n"
            f"⚠ Honest caveats: (1) the widened-train held-in means also DROP vs #26 "
            f"(generalist-mediocrity — one net, same budget, 3 families), so a narrower (or "
            f"negative) gap is partly 'uniformly mediocre across families', NOT proof of strong "
            f"transfer. A negative gap (held-out > held-in) most likely means low absolute skill "
            f"plus an easier held-out family, not super-transfer. (2) Single run, "
            f"N={N_HELDIN}/{N_HELDOUT}, low budget, deterministic bosses — a signal, not a proof. "
            f"Read gaps WITH the absolute held-in/held-out columns. See DESIGN §3.1.1."
        )
        return 0
    try:
        rep = train_and_transfer(timesteps=args.timesteps)
    except ImportError:
        print('This experiment needs the [rl] extra:  pip install -e ".[rl]"', file=sys.stderr)
        return 2

    print(f"learned genre transfer | PPO timesteps={args.timesteps:,}\n")
    print(f"train families {rep.train_families} → held-out family '{rep.heldout_family}'\n")
    print("| set | mean (±std) |")
    print("|---|---|")
    print(f"| held-in (train families) | {rep.heldin_mean:.3f} ±{rep.heldin_std:.3f} |")
    print(f"| held-out (unseen family) | {rep.heldout_mean:.3f} ±{rep.heldout_std:.3f} |")
    print(f"\nenv-level transfer gap (held-in − held-out family) = {rep.gap:+.3f}")
    print(
        "\nReported, not pass/fail. This is the FIRST learned-policy genre-transfer "
        "measurement; one train-set → one held-out family is NOT a genre proof. A large gap "
        "means the learned policy did not transfer to the unseen family's mechanic — an "
        f"honest '(B) is still open' signal. Single run, N={N_HELDIN}/{N_HELDOUT}, low budget, "
        "duel excluded (obs harmonization future). See DESIGN §3.1.1."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
