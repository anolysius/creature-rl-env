"""One-command reproduction of CritterGym's headline results.

Regenerates the result tables that back the front-facing claims (README + paper):

  1. **Throughput** — JAX vmap vs numpy on CPU (`scripts/bench_throughput.py`): the
     overworld / commit-battle / non-commit-battle / full-episode slices.
  2. **Oracle headroom** — a tuned PPO baseline vs the scripted oracle on held-out seeds
     (`scripts/ppo_baseline.py`): "hard-and-learnable" with a pre-registered classifier.
  3. **Eval-product inference band** (paper §5) — the scripted ceiling->floor band an LLM
     submission is read against (`inference_baseline`: oracle / infer / type_blind / probe
     super-effective-move rate). Free + deterministic (no LLM). The paper's frontier-LLM read
     (§5: super-effective-move rate ~50%) is a *paid, evaluator-local* run and is **not**
     reproduced here — only the scripted band is.

This is a *reproduction harness*, not a new measurement: it shells out to (or, for the band,
imports) the same code the archived task reports used, and every number is generated **live**
(nothing is hardcoded here). The honest framing each sub-bench prints — CPU / vmap-only (a
single jit env is slower than numpy) / run count / oracle = a scripted ceiling proxy / GPU
unmeasured / the §5 LLM read is not reproduced — is preserved verbatim.

    python scripts/reproduce_results.py --quick     # fast smoke (small sizes), ~seconds
    python scripts/reproduce_results.py --runs 5     # full multi-run headroom (minutes)

The `[jax]` and `[rl]` extras are needed for the JAX throughput rows and the PPO table
respectively; without them the sub-benches print a notice and skip those rows.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent

# The inference-gated demonstrator config (paper §5 / inference-baseline.md). max_steps=40 is
# the runner default — the chart-blind floor is step-cap dependent, so band and any submission
# must be read at the same cap (#16). num_types/grid/boss match the runner's inference preset.
_DEMO_CONFIG = dict(
    master_seed=20260627, num_types=3, grid_size=5, boss_hp=140, boss_atk=6, boss_def=18,
    max_steps=40,
)


def _demo_sealed(quick: bool):  # type: ignore[no-untyped-def]
    """The sealed demonstrator set; ``--quick`` uses fewer worlds for a fast smoke."""
    from critter_gym.eval_harness import SealedEvalSet
    return SealedEvalSet(n_worlds=4 if quick else 8, **_DEMO_CONFIG)


def inference_band(quick: bool = False):  # type: ignore[no-untyped-def]
    """Regenerate the paper §5 scripted inference band (oracle/infer/type_blind/probe) on the
    demonstrator config — free and deterministic (no LLM). Returns an ``InferenceBaseline``."""
    from critter_gym.eval_harness import inference_baseline
    return inference_baseline(_demo_sealed(quick))


def _print_inference_band(quick: bool) -> None:
    """Print the §5 band the frontier-LLM probe is read against (scripted, free, deterministic)."""
    from critter_gym.eval_harness import inference_baseline
    sealed = _demo_sealed(quick)
    band = inference_baseline(sealed)
    print(f"\n$ inference_baseline(demonstrator, n_worlds={sealed.n_worlds}, "
          f"max_steps={_DEMO_CONFIG['max_steps']})")
    print("  super-effective-move rate — the §5 band an LLM submission is read against:")
    labels = {"oracle": "oracle (chart-KNOWING expert)",
              "infer": "infer (inference proxy, NOT an LLM)",
              "type_blind": "type_blind (chart-BLIND floor)",
              "probe": "probe (blind guess)"}
    for arm in ("oracle", "infer", "type_blind", "probe"):
        ab = band.arms[arm]
        print(f"    {labels[arm]:<34} {ab.se_rate:>4.0%}  ({ab.n_battle_moves} battle moves)")
    print("  honest: this scripted band is free + deterministic (reproduced here). The paper's")
    print("  frontier-LLM read (§5: super-effective-move rate ~50%) is a PAID, evaluator-local")
    print("  run — NOT reproduced by this script; see docs/reference/inference-baseline.md.")


def _run(script: str, args: list[str]) -> int:
    """Run a sibling script in this interpreter; stream its output. Returns its exit code."""
    path = _SCRIPTS / script
    print(f"\n$ python scripts/{script} {' '.join(args)}".rstrip(), flush=True)
    return subprocess.run([sys.executable, str(path), *args], check=False).returncode


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--quick", action="store_true", help="fast smoke (small sizes)")
    p.add_argument("--runs", type=int, default=1,
                   help="PPO/A2C runs for the headroom table (5 reproduces the robust read)")
    a = p.parse_args()

    print("=" * 78)
    print("CritterGym — headline results reproduction")
    print("  (1) throughput: JAX vmap vs numpy, CPU   (2) oracle headroom: PPO vs scripted")
    print("  (3) eval-product inference band (paper §5): the scripted ceiling->floor band")
    print("  Honest scope: CPU / vmap-only (a single jit env is slower) / oracle = a")
    print("  scripted ceiling proxy / GPU (M4-EC3) unmeasured. All 4 families (A critter /")
    print("  B forage / C duel / D muster) vectorize at parity 0 — see")
    print("  tests/test_jax_{env,family,duel}_parity.py. The §5 frontier-LLM read itself is a")
    print("  paid, evaluator-local run and is NOT reproduced here (only the scripted band is).")
    if a.quick:
        print("  [--quick] small sizes/budget → multipliers and headroom %% are lower than")
        print("  the full-budget headline; use --runs 5 (no --quick) for the robust read.")
    print("=" * 78)

    qa = ["--quick"] if a.quick else []
    rc1 = _run("bench_throughput.py", qa)
    rc2 = _run("ppo_baseline.py", qa + ["--runs", str(a.runs)])
    _print_inference_band(a.quick)  # (3) scripted §5 band — free + deterministic, in-process

    print("\n" + "=" * 78)
    if rc1 == 0 and rc2 == 0:
        print("DONE — all result tables reproduced above (numbers generated live).")
    else:
        print(f"WARNING — a sub-bench exited non-zero (throughput={rc1}, headroom={rc2}).")
    print("=" * 78)
    sys.exit(rc1 or rc2)


if __name__ == "__main__":
    main()
