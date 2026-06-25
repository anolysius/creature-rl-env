"""One-command reproduction of CritterGym's headline results.

Regenerates the two result tables that back the front-facing claims (README + paper):

  1. **Throughput** — JAX vmap vs numpy on CPU (`scripts/bench_throughput.py`): the
     overworld / commit-battle / non-commit-battle / full-episode slices.
  2. **Oracle headroom** — a tuned PPO baseline vs the scripted oracle on held-out seeds
     (`scripts/ppo_baseline.py`): "hard-and-learnable" with a pre-registered classifier.

This is a *reproduction harness*, not a new measurement: it shells out to the same code
the archived task reports used, and every number is generated **live** (nothing is
hardcoded here). The honest framing each sub-bench prints — CPU / vmap-only (a single jit
env is slower than numpy) / run count / oracle = a scripted ceiling proxy / GPU unmeasured —
is preserved verbatim.

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
    print("  Honest scope: CPU / vmap-only (a single jit env is slower) / oracle = a")
    print("  scripted ceiling proxy / GPU (M4-EC3) unmeasured. All 4 families (A critter /")
    print("  B forage / C duel / D muster) vectorize at parity 0 — see")
    print("  tests/test_jax_{env,family,duel}_parity.py.")
    if a.quick:
        print("  [--quick] small sizes/budget → multipliers and headroom %% are lower than")
        print("  the full-budget headline; use --runs 5 (no --quick) for the robust read.")
    print("=" * 78)

    qa = ["--quick"] if a.quick else []
    rc1 = _run("bench_throughput.py", qa)
    rc2 = _run("ppo_baseline.py", qa + ["--runs", str(a.runs)])

    print("\n" + "=" * 78)
    if rc1 == 0 and rc2 == 0:
        print("DONE — both result tables reproduced above (numbers generated live).")
    else:
        print(f"WARNING — a sub-bench exited non-zero (throughput={rc1}, headroom={rc2}).")
    print("=" * 78)
    sys.exit(rc1 or rc2)


if __name__ == "__main__":
    main()
