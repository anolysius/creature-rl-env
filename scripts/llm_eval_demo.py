"""Demo: the agentic-LLM eval adapter on the sealed held-out harness (eval-product #2).

Shows the contamination-proof *agentic-LLM* eval mechanism end-to-end:
  1. The env observation is rendered to text an LLM can read (`render_obs`).
  2. An LLM agent (`LLMAgent`) replies with an action; `parse_action` turns the free text
     into a move.
  3. `eval_harness.score_agent` scores it on a SEALED held-out set with verifiable subgoals —
     worlds the agent never saw.

Here the "LLM" is a deterministic **stub** (no API, no key) so the demo is reproducible and
free. The same `LLMAgent` interface takes a real model via `anthropic_complete()` (opt-in,
incurs API cost) — see the commented block at the bottom.

Honest scope: this demonstrates the *adapter mechanism*, not a measured LLM-capability result.

Run: `python scripts/llm_eval_demo.py`.
"""
from __future__ import annotations

from critter_gym.eval_harness import SealedEvalSet, score_agent
from critter_gym.llm_eval import LLMAgent, render_obs


class StubLLM:
    """A deterministic stand-in for an LLM: a tiny rule over the rendered prompt text.

    Real LLMs reply in free text; this stub does too (so `parse_action` is exercised) — it
    'attacks' in battle and otherwise walks toward a gym if one is visible, else waits."""

    def __call__(self, prompt: str) -> str:
        p = prompt.lower()
        if "in battle: yes" in p:
            return "We're in a fight — attack! (action 0)"
        if " g " in p or p.rstrip().endswith("g") or "g\n" in p:
            return "I see a gym nearby, move east toward it."
        return "Nothing here yet, I'll wait."


def main() -> None:
    sealed = SealedEvalSet(master_seed=20260626, n_worlds=16, num_types=8)

    print("== Agentic-LLM eval on a sealed held-out set (contamination-proof, prototype) ==")
    print(f"   {sealed.n_worlds} private held-out worlds (master_seed={sealed.master_seed}); "
          "the LLM never sees these seeds.\n")

    # What the LLM actually reads each turn (one example obs):
    env = sealed.env_factory()()
    obs, _ = env.reset(seed=sealed._eval_seeds()[0])
    print("-- example of what the LLM sees (render_obs) --")
    print(render_obs(obs))
    print("-- end example --\n")

    # Score the stub-LLM agent on the sealed worlds (RLVR-verified subgoals).
    agent = LLMAgent(StubLLM())
    card = score_agent(agent, sealed)
    print(f"  stub-LLM agent     held-out gyms {card.mean_gyms_cleared:.2f}  "
          f"cleared {card.cleared_rate:.0%}  caught {card.caught_rate:.0%}  "
          f"({card.frac_of_oracle:.0%} of oracle {card.oracle_gyms:.2f})")
    print("  (a real LLM would replace StubLLM; the score is on worlds it could not train on.)")

    print("\n  honest scope: this is the adapter MECHANISM (render -> LLM -> parse -> sealed "
          "RLVR scoring), not a measured LLM-capability result. The stub is deterministic and "
          "API-free; a real measurement needs an API key and incurs cost.")

    # --- Optional: a real LLM (incurs API cost; needs `pip install anthropic` + key) ---
    #   from critter_gym.llm_eval import anthropic_complete
    #   real_agent = LLMAgent(anthropic_complete(model="claude-opus-4-8"))
    #   card = score_agent(real_agent, sealed)   # measures a real model on sealed worlds


if __name__ == "__main__":
    main()
