"""LLM diversity curve — is the difficulty dial visible to an imperfect reasoner? (money-gated)

The scripted diversity-dial scout falsified calibration: the scripted ``infer`` arm learns a
matchup perfectly on first sight, so its score stays saturated no matter how much per-episode
type diversity (``boss_pool_size``) rises. The meta-finding: the scripted band can VERIFY an
eval but cannot CALIBRATE difficulty — a difficulty curve should only be visible to an
imperfect reasoner. This runner buys that missing evidence with a real LLM (claude-cli, the
user's subscription quota — an explicitly user-approved spend).

GATED, PRE-REGISTERED PROTOCOL (frozen in the plan/qa-checklist BEFORE any quota is spent):
  G-0 smoke     : 1 world at pool=1 — wiring, latency, parse-failure rate.        (<=140 calls)
  G-1 anchor    : pool=1 x 4 worlds. llm_score < FLOOR (0.10) => FLOOR-SATURATED
                  (this model/provider cannot exploit even maximal recurrence — consistent with
                  the earlier arena-inference inconclusive) => STOP, spend nothing more.
  G-2 main      : pool=8 x 4 worlds. delta = score(pool 1) - score(pool 8).
                  delta >= MARGIN (0.15) => DIAL-VISIBLE; delta <= -MARGIN => INVERTED;
                  else FLAT. Reported AS-IS either way.
  G-3 mid point : pool=4 x 4 worlds ONLY if |delta| >= MARGIN (shape check).
Budget hard-cap <= 1,820 calls (a floor stop spends <= ~700); every gate's partial result is
flushed to the JSON artifact immediately.

Scoring: `score_inference_telemetry` SE-rate normalized by the SAME pool point's FREE scripted
anchors (`se_inference_score`: 0 = chart-blind floor, 1 = chart-knowing oracle). The x-axis is
the MEASURED mean distinct boss-types per world, not the raw knob.

HONEST framing (read before quoting any number): ONE run, 4 worlds/point (the scripted curve
used 8), ONE model, ONE provider, no error bars (LLM replies are stochastic); the parse-failure
rate is reported alongside. A DIAL-VISIBLE result is a SIGNAL about THIS model in THIS setting —
not "LLMs in general". Do NOT headline.

Run: `python scripts/llm_diversity_curve.py --smoke` (G-0 only), then without --smoke for the
full gated protocol. Requires the `claude` CLI on PATH (subscription login); tests inject a stub.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from critter_gym.eval_harness import (
    SealedEvalSet,
    inference_baseline,
    score_inference_telemetry,
    se_inference_score,
)
from critter_gym.inference_curve import _mean_distinct_types
from critter_gym.llm_eval import _KEYWORDS, BattleMemoryLLMAgent, claude_cli_complete

# -- pre-registered constants (frozen in qa-checklist BEFORE data; do not edit post-hoc) -----
SEALED_KWARGS: dict[str, Any] = dict(
    master_seed=20260708, grid_size=8, num_gyms=8, num_types=12,
    max_steps=140, boss_hp=140, boss_atk=6, boss_def=18,
)  # mirrors inference_curve._DIVERSITY_SEALED (the scripted curve's config)
WORLDS = 4                      # per point (cost control; scripted curve used 8 — label honestly)
FLOOR = 0.10                    # G-1: anchor score below this => FLOOR-SATURATED, stop
MARGIN = 0.15                   # G-2: |delta| at/above this => a real gap (pre-registered)
POOL_ANCHOR, POOL_MID, POOL_MAX = 1, 4, 8
BUDGET_TOTAL = 1_820            # hard cap on LLM calls across the whole protocol
WINDOW = 8                      # BattleMemoryLLMAgent history window
# Instrument-validity guard, added AFTER G-0 smoke and BEFORE any G-1 data (documented in the
# plan): the G-0 world showed oracle_se == type_blind_se == 1.0, a DEGENERATE anchor band whose
# normalized score is meaningless (clamps to 0) and would fake a FLOOR-SATURATED stop. A point
# whose band is narrower than EPS_BAND is reported as raw SE-rates, never as a floor verdict.
EPS_BAND = 0.05


class BudgetExceeded(RuntimeError):
    """Raised when the pre-registered hard call budget would be exceeded."""


def reply_unparseable(reply: str) -> bool:
    """True iff ``parse_action`` would hit its safe WAIT fallback (no digit, no keyword).

    Mirrors the fallback conditions of :func:`critter_gym.llm_eval.parse_action` so the
    parse-failure rate can be reported without changing engine behavior."""
    if not reply:
        return True
    text = reply.strip().lower()
    if re.search(r"\b(?:action|choose|select|option)\s*[:#]?\s*(\d+)", text):
        return False
    if re.search(r"(?<!\d)(\d+)(?!\d)", text):
        return False
    return not any(kw in text for kw, _idx in _KEYWORDS)


class CountingComplete:
    """Wraps a ``complete(prompt) -> reply`` callable with budget + telemetry.

    Counts calls and wall-clock, tallies unparseable replies, and raises
    :class:`BudgetExceeded` BEFORE a call that would break the pre-registered hard cap."""

    def __init__(self, complete: Callable[[str], str], budget: int) -> None:
        self._complete = complete
        self.budget = budget
        self.calls = 0
        self.seconds = 0.0
        self.unparseable = 0

    def __call__(self, prompt: str) -> str:
        if self.calls >= self.budget:
            raise BudgetExceeded(f"pre-registered budget of {self.budget} calls exhausted")
        t0 = time.perf_counter()
        reply = self._complete(prompt)
        self.seconds += time.perf_counter() - t0
        self.calls += 1
        if reply_unparseable(reply):
            self.unparseable += 1
        return reply


def curve_point(
    pool: int, counter: CountingComplete, *, worlds: int = WORLDS,
    sealed_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """One diversity point: sealed set at ``pool`` -> free scripted anchors -> LLM telemetry.

    Returns a JSON-ready dict. The scripted anchors (oracle / type_blind SE-rates) cost no
    quota — only the LLM telemetry pass drives ``counter``."""
    kw = dict(sealed_kwargs if sealed_kwargs is not None else SEALED_KWARGS)
    sealed = SealedEvalSet(n_worlds=worlds, boss_pool_size=pool, **kw)
    band = inference_baseline(sealed)  # free numpy anchors
    oracle_se = float(band.arms["oracle"].se_rate)
    blind_se = float(band.arms["type_blind"].se_rate)

    calls_before = counter.calls
    agent = BattleMemoryLLMAgent(counter, window=WINDOW)
    tel = score_inference_telemetry(agent, sealed)
    score = se_inference_score(tel.super_effective_rate, oracle_se, blind_se)
    return {
        "pool": pool,
        "worlds": worlds,
        "mean_distinct_types": float(_mean_distinct_types(pool, sealed)),
        "llm_se_rate": float(tel.super_effective_rate),
        "llm_battle_moves": int(tel.n_battle_moves),
        "oracle_se": oracle_se,
        "type_blind_se": blind_se,
        "llm_score": float(score),
        "band_degenerate": bool(oracle_se - blind_se < EPS_BAND),
        "calls_this_point": counter.calls - calls_before,
    }


def decide(anchor_score: float, max_score: float | None) -> tuple[str, str]:
    """The pre-registered verdict from the gate scores (pure — unit-tested without quota)."""
    if anchor_score < FLOOR:
        return ("FLOOR-SATURATED",
                f"anchor pool={POOL_ANCHOR} score {anchor_score:.2f} < {FLOOR} — this model/"
                "provider cannot exploit even maximal recurrence; curve unmeasurable here "
                "(consistent with the arena-inference inconclusive). Remaining budget unspent.")
    if max_score is None:
        return ("PENDING", "anchor passed the floor; pool-max point not yet measured")
    delta = anchor_score - max_score
    if delta >= MARGIN:
        return ("DIAL-VISIBLE",
                f"delta {delta:+.2f} >= {MARGIN} — per-episode type diversity IS a difficulty "
                "dial for this imperfect reasoner (SIGNAL; this model/setting only).")
    if delta <= -MARGIN:
        return ("INVERTED", f"delta {delta:+.2f} <= -{MARGIN} — score ROSE with diversity; "
                            "reported as-is (falsify welcome).")
    return ("FLAT", f"|delta {delta:+.2f}| < {MARGIN} — no dial visible at this margin; "
                    "same conclusion as the scripted band. Reported as-is.")


def needs_mid_point(anchor_score: float, max_score: float) -> bool:
    """G-3 spend rule: buy the mid point only when the endpoints show a real gap."""
    return abs(anchor_score - max_score) >= MARGIN


def _flush(out_path: Path, results: dict[str, Any]) -> None:
    out_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")


def run_protocol(
    complete: Callable[[str], str], *, out_path: Path, smoke: bool,
    worlds: int = WORLDS, sealed_kwargs: dict[str, Any] | None = None,
    model_label: str = "claude-cli-default",
) -> dict[str, Any]:
    """Run the gated protocol, flushing the JSON artifact after every gate (partial-safe)."""
    counter = CountingComplete(complete, budget=BUDGET_TOTAL)
    results: dict[str, Any] = {
        "protocol": {
            "sealed_kwargs": dict(sealed_kwargs if sealed_kwargs is not None else SEALED_KWARGS),
            "worlds_per_point": worlds, "floor": FLOOR, "margin": MARGIN,
            "pools": {"anchor": POOL_ANCHOR, "mid": POOL_MID, "max": POOL_MAX},
            "budget_total": BUDGET_TOTAL, "agent": f"BattleMemoryLLMAgent(window={WINDOW})",
        },
        "model_label": model_label,
        "points": [], "gates": [], "verdict": None, "verdict_detail": None,
    }

    def log_gate(gate: str, point: dict[str, Any]) -> None:
        avg_s = counter.seconds / counter.calls if counter.calls else 0.0
        entry = {"gate": gate, **point, "calls_total": counter.calls,
                 "avg_seconds_per_call": round(avg_s, 2),
                 "unparseable_replies": counter.unparseable}
        results["gates"].append(entry)
        print(f"  [{gate}] pool={point['pool']} worlds={point['worlds']} "
              f"llm_score={point['llm_score']:.2f} (se {point['llm_se_rate']:.2f}, "
              f"moves {point['llm_battle_moves']}, oracle {point['oracle_se']:.2f}, "
              f"blind {point['type_blind_se']:.2f}) | calls {counter.calls}/{counter.budget} "
              f"avg {avg_s:.1f}s unparseable {counter.unparseable}")
        _flush(out_path, results)

    print("== LLM diversity curve (gated, pre-registered) — SIGNAL, not measurement ==")
    print(f"   frozen: worlds/point={worlds}, floor={FLOOR}, margin={MARGIN}, "
          f"pools {POOL_ANCHOR}/{POOL_MID}/{POOL_MAX}, budget<= {BUDGET_TOTAL} calls, "
          f"agent BattleMemory(w={WINDOW}), model={model_label}")
    print("   verdict rule (declared before data): anchor<floor => FLOOR-SATURATED stop; "
          "delta>=margin => DIAL-VISIBLE; delta<=-margin => INVERTED; else FLAT. "
          "Mid point only on |delta|>=margin.")

    # G-0 smoke: 1 world at the anchor pool — wiring/latency/parse-rate at minimal spend.
    smoke_pt = curve_point(POOL_ANCHOR, counter, worlds=1, sealed_kwargs=sealed_kwargs)
    log_gate("G-0", smoke_pt)
    if smoke:
        results["verdict"], results["verdict_detail"] = "SMOKE-ONLY", "G-0 wiring check only"
        _flush(out_path, results)
        return results

    # G-1 anchor: pool=1 (maximal recurrence — the easiest possible inference setting).
    anchor = curve_point(POOL_ANCHOR, counter, worlds=worlds, sealed_kwargs=sealed_kwargs)
    results["points"].append(anchor)
    log_gate("G-1", anchor)
    if anchor["band_degenerate"]:
        # Instrument failure, NOT a floor result: oracle==blind leaves nothing to normalize by.
        results["verdict"] = "DEGENERATE-BAND"
        results["verdict_detail"] = (
            f"anchor band oracle {anchor['oracle_se']:.2f} - blind {anchor['type_blind_se']:.2f}"
            f" < {EPS_BAND}: normalized score invalid; raw SE-rates reported; no floor verdict.")
        _flush(out_path, results)
        print(f"  verdict: DEGENERATE-BAND — {results['verdict_detail']}")
        return results
    verdict, detail = decide(anchor["llm_score"], None)
    if verdict == "FLOOR-SATURATED":
        results["verdict"], results["verdict_detail"] = verdict, detail
        _flush(out_path, results)
        print(f"  verdict: {verdict} — {detail}")
        return results

    # G-2 main: pool=8 (maximal diversity).
    maxp = curve_point(POOL_MAX, counter, worlds=worlds, sealed_kwargs=sealed_kwargs)
    results["points"].append(maxp)
    log_gate("G-2", maxp)
    if maxp["band_degenerate"]:
        results["verdict"] = "DEGENERATE-BAND"
        results["verdict_detail"] = (
            f"pool-max band oracle {maxp['oracle_se']:.2f} - blind {maxp['type_blind_se']:.2f}"
            f" < {EPS_BAND}: normalized delta invalid; raw SE-rates reported for both points.")
        _flush(out_path, results)
        print(f"  verdict: DEGENERATE-BAND — {results['verdict_detail']}")
        return results
    verdict, detail = decide(anchor["llm_score"], maxp["llm_score"])
    results["verdict"], results["verdict_detail"] = verdict, detail
    _flush(out_path, results)

    # G-3 conditional mid point: shape check only when the endpoints showed a real gap.
    if needs_mid_point(anchor["llm_score"], maxp["llm_score"]):
        mid = curve_point(POOL_MID, counter, worlds=worlds, sealed_kwargs=sealed_kwargs)
        results["points"].append(mid)
        log_gate("G-3", mid)
        _flush(out_path, results)

    print(f"  verdict: {verdict} — {detail}")
    print("  HONEST: ONE run, 4 worlds/point (scripted curve used 8), ONE model, ONE provider, "
          "no error bars (stochastic LLM); parse-failure rate above. A DIAL-VISIBLE result is a "
          "SIGNAL about THIS model in THIS setting — not 'LLMs in general'. Do NOT headline.")
    return results


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--smoke", action="store_true", help="G-0 only (1 world) — wiring check")
    p.add_argument("--worlds", type=int, default=WORLDS, help="worlds per point (frozen: 4)")
    p.add_argument("--out", type=Path,
                   default=Path("docs/_active/llm-diversity-curve/results.json"))
    p.add_argument("--model-label", default="claude-cli-default",
                   help="honest label for the JSON artifact (the CLI uses the login default)")
    p.add_argument("--timeout", type=float, default=120.0, help="per-call CLI timeout seconds")
    p.add_argument("--claude-bin", default="claude",
                   help="claude CLI binary (pass the real binary path to avoid shell shims)")
    a = p.parse_args()

    # claude_cli_complete is a FACTORY: (binary, timeout) -> complete(prompt) callable.
    complete = claude_cli_complete(a.claude_bin, timeout=a.timeout)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    run_protocol(complete, out_path=a.out, smoke=a.smoke, worlds=a.worlds,
                 model_label=a.model_label)


if __name__ == "__main__":
    main()
