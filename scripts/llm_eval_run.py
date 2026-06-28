"""Real-LLM sealed-eval runner — how hard is CritterGym for a frontier LLM? (eval-product #3)

Scores a real LLM agent (via `llm_eval.anthropic_complete`) on a SEALED held-out set with
verifiable subgoals, and reports its fraction of the scripted oracle — i.e. "a frontier LLM
reaches N% of expert on worlds it could not have trained on".

⚠️ COST + TIME: every env step is one LLM API call. An episode runs up to `--max-steps`
steps, over `--worlds` worlds, and the oracle/type_blind reference arms run too (scripted,
free). Keep `--worlds` and `--max-steps` SMALL for a first probe (the defaults: 3 × 40 = 120
LLM calls ≈ a couple minutes and cents). The runner prints the projected call count and
asks nothing — it just warns; size it yourself.

🔑 Bring your own key: this calls the Anthropic API. Set `ANTHROPIC_API_KEY` in your shell
(the SDK reads it from the environment) and `pip install anthropic`. The runner never takes
the key as an argument — do NOT paste API keys into a chat or commit them.

Honest scope: a small probe with a step cap against our scripted-oracle proxy — a signal,
not a definitive "frontier-LLM difficulty" number (single run, small sample, capped horizon).

Run: `python scripts/llm_eval_run.py [--model claude-opus-4-8] [--worlds 3] [--max-steps 40]`.

Inference-demo preset (navigable + inference-gated: a chart-blind baseline fails, an expert wins,
and the boss is weak enough that the agent survives long enough to infer the chart):
`--grid-size 5 --num-types 3 --boss-hp 140 --boss-atk 6 --boss-def 18 --stateful --max-steps 120`.
The headline is the INFERENCE SCORE — where the LLM lands between the chart-blind floor (0) and
the expert ceiling (1). It is the moat KPI: un-gameable in-context hidden-rule inference.
"""
from __future__ import annotations

import argparse

from critter_gym.eval_harness import SealedEvalSet, score_agent
from critter_gym.inference_rigor import classify_inference
from critter_gym.llm_eval import (
    LLMAgent,
    StatefulLLMAgent,
    anthropic_complete,
    claude_cli_complete,
)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--provider", choices=("anthropic", "claude-cli"), default="anthropic",
                   help="anthropic=API (needs ANTHROPIC_API_KEY, pay-per-token); "
                        "claude-cli=local Claude Code (uses your subscription, no API key)")
    p.add_argument("--model", default="claude-opus-4-8",
                   help="Anthropic model id (applies to --provider anthropic only)")
    p.add_argument("--worlds", type=int, default=3, help="sealed held-out worlds (keep small)")
    p.add_argument("--max-steps", type=int, default=40, help="episode step cap (keep small)")
    p.add_argument("--num-types", type=int, default=8, help="hidden type-chart size")
    p.add_argument("--master-seed", type=int, default=20260627, help="sealed-set secret seed")
    p.add_argument("--stateful", action="store_true",
                   help="give the LLM a per-episode memory of recent steps (fairer under "
                        "partial observability); memory is cleared between sealed worlds")
    p.add_argument("--window", type=int, default=8,
                   help="stateful only: how many recent (obs, action) steps to keep in the "
                        "prompt — larger = more recall but longer prompts (more tokens/call)")
    p.add_argument("--grid-size", type=int, default=10,
                   help="world grid size (smaller = navigable for an LLM under the 5x5 view)")
    p.add_argument("--boss-hp", type=int, default=120, help="gym-boss hp")
    p.add_argument("--boss-atk", type=int, default=12,
                   help="gym-boss attack (lower = the player survives more turns to learn)")
    p.add_argument("--boss-def", type=int, default=12, help="gym-boss defense")
    p.add_argument("--runs", type=int, default=1,
                   help="repeat the scoring N times and report a robust inference-score verdict "
                        "(mean ± std + classify_inference); N>1 multiplies LLM calls by N")
    a = p.parse_args()

    projected = a.worlds * a.max_steps
    backend = "claude-cli (subscription)" if a.provider == "claude-cli" else f"API {a.model}"
    memory = f"stateful (window {a.window})" if a.stateful else "stateless (memoryless)"
    print("== Real-LLM sealed eval — how hard is CritterGym for a frontier LLM? ==")
    print(f"   provider={a.provider}  backend={backend}  memory={memory}  worlds={a.worlds}  "
          f"max_steps={a.max_steps}  num_types={a.num_types}")
    print(f"   ⚠️  projected ~{projected} LLM calls (1 per env step) — cost/quota + time scale "
          "with worlds × max_steps. Ctrl-C now to abort if too large.")
    if a.stateful:
        print("   (stateful: prompts carry recent history, so each call uses more tokens than "
              "stateless.)")
    print("   (oracle / type_blind reference arms are scripted and free.)\n")

    if a.provider == "claude-cli":
        complete = claude_cli_complete()  # local Claude Code; uses your subscription, no key
    else:
        complete = anthropic_complete(model=a.model)  # raises a clear error if no SDK/key
    sealed = SealedEvalSet(master_seed=a.master_seed, n_worlds=a.worlds,
                           num_types=a.num_types, max_steps=a.max_steps,
                           grid_size=a.grid_size, boss_hp=a.boss_hp,
                           boss_atk=a.boss_atk, boss_def=a.boss_def)
    def fresh_agent():
        return StatefulLLMAgent(complete, window=a.window) if a.stateful else LLMAgent(complete)

    # Score `--runs` times (a fresh agent each run); scripted oracle/type_blind are
    # deterministic, so only the submission varies run-to-run.
    cards = [score_agent(fresh_agent(), sealed) for _ in range(max(1, a.runs))]
    card = cards[-1]

    pct = card.frac_of_oracle
    print("  -- 3-arm comparison on the SAME sealed never-seen worlds --")
    print(f"  oracle (chart-KNOWING expert, scripted)   gym-clears {card.oracle_gyms:.2f}")
    print(f"  type_blind (chart-BLIND baseline, scripted) gym-clears {card.type_blind_gyms:.2f}")
    print(f"  {a.model}  gym-clears {card.mean_gyms_cleared:.2f}  "
          f"({pct:.0%} of oracle)  cleared {card.cleared_rate:.0%}  caught {card.caught_rate:.0%}")

    if a.runs > 1:
        scores = [c.inference_score for c in cards]
        verdict = classify_inference(scores)
        print(f"\n  => INFERENCE SCORE: {verdict.mean:.2f} ± {verdict.std:.2f}  "
              f"({verdict.n_runs} runs)  →  {verdict.verdict.upper()}")
        print("     (infers = robustly beats the chart-blind baseline / at-chart-blind-floor = "
              "robustly does not infer / inconclusive = more runs needed)")
    else:
        print(f"\n  => INFERENCE SCORE: {card.inference_score:.2f}  "
              "(0 = no better than the chart-blind baseline / 1 = expert)")
    print("     the un-gameable KPI: in-context hidden-rule inference on a sealed, never-seen "
          "world — it cannot be memorized or contaminated.")
    print("  honest: a probe (worlds × max_steps capped), scripted-oracle proxy, one difficulty "
          "band — a signal, not a definitive number.")


if __name__ == "__main__":
    main()
