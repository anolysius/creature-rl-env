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
"""
from __future__ import annotations

import argparse

from critter_gym.eval_harness import SealedEvalSet, score_agent
from critter_gym.llm_eval import LLMAgent, anthropic_complete


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="claude-opus-4-8", help="Anthropic model id")
    p.add_argument("--worlds", type=int, default=3, help="sealed held-out worlds (keep small)")
    p.add_argument("--max-steps", type=int, default=40, help="episode step cap (keep small)")
    p.add_argument("--num-types", type=int, default=8, help="hidden type-chart size")
    p.add_argument("--master-seed", type=int, default=20260627, help="sealed-set secret seed")
    a = p.parse_args()

    projected = a.worlds * a.max_steps
    print("== Real-LLM sealed eval — how hard is CritterGym for a frontier LLM? ==")
    print(f"   model={a.model}  worlds={a.worlds}  max_steps={a.max_steps}  "
          f"num_types={a.num_types}")
    print(f"   ⚠️  projected ~{projected} LLM API calls (1 per env step) — cost + time scale "
          "with worlds × max_steps. Ctrl-C now to abort if too large.")
    print("   (oracle / type_blind reference arms are scripted and free.)\n")

    sealed = SealedEvalSet(master_seed=a.master_seed, n_worlds=a.worlds,
                           num_types=a.num_types, max_steps=a.max_steps)
    agent = LLMAgent(anthropic_complete(model=a.model))  # raises a clear error if no SDK/key
    card = score_agent(agent, sealed)

    pct = card.frac_of_oracle
    print(f"  oracle (scripted)   gym-clears {card.oracle_gyms:.2f}   "
          f"type_blind {card.type_blind_gyms:.2f}")
    print(f"  {a.model}  held-out gym-clears {card.mean_gyms_cleared:.2f}  "
          f"({pct:.0%} of oracle)  cleared {card.cleared_rate:.0%}  caught {card.caught_rate:.0%}")
    print(f"\n  => the frontier LLM reaches {pct:.0%} of the scripted expert on these sealed "
          "worlds (it never saw them).")
    print("  honest: a small probe (worlds × max_steps capped), single run, our scripted-oracle "
          "proxy — a signal, not a definitive number. Paste this output back to record it.")


if __name__ == "__main__":
    main()
