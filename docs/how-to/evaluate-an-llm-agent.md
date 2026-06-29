# How to: evaluate an LLM agent on the sealed held-out eval

> 한국어: [evaluate-an-llm-agent.ko.md](evaluate-an-llm-agent.ko.md)

CritterGym can score an **agentic LLM** on a sealed, never-seen world: drop a fresh held-out
world in front of the model, have it infer the hidden rules and clear gyms, and score it with
**verifiable subgoals** — on worlds it could not have trained on. This is the contamination-proof
eval (the moat property).

## What you need to know first (honest scope)

- This is an **in-process prototype**, not a hosted service. You run it on your machine; a
  server-side sealed eval (submit-an-agent-get-a-score) is future/funded work (M5).
- **Cost:** every env step is one LLM call. Keep `--worlds` and `--max-steps` small for a first
  probe. The runner prints the projected call count and warns before you spend.
- The result is a **signal, not a verdict** — a small probe against a scripted-oracle proxy on
  one difficulty band. Report it as-is; don't reframe a floor as "LLMs can't do it".

## Option A — the bundled runner (Claude CLI or Anthropic API)

```bash
# Uses your local Claude Code subscription (no API key, rate-limited, slower):
python scripts/llm_eval_run.py --provider claude-cli --worlds 2 --max-steps 40 --runs 3

# Or the Anthropic API (set ANTHROPIC_API_KEY; pay-per-token, faster):
python scripts/llm_eval_run.py --provider anthropic --model claude-opus-4-8 --worlds 2 --max-steps 40
```

Useful flags:

| flag | meaning |
|---|---|
| `--provider {anthropic,claude-cli}` | API (needs `ANTHROPIC_API_KEY`) vs local Claude Code subscription |
| `--worlds N` / `--max-steps M` | sealed worlds × episode step cap (keep small — `N×M` ≈ LLM calls) |
| `--runs K` | repeat K times → robust `inference_score` verdict (mean ± std, pre-registered classifier) |
| `--stateful` / `--battle-memory` | give the agent per-episode memory / a per-move battle-outcome memory |
| `--telemetry` | also report the super-effective-move rate (attrition-proof inference signal) |
| `--grid-size / --num-types / --boss-hp / --boss-atk / --boss-def` | demonstrator-config knobs |

The headline is the **`inference_score`** ∈ [0,1]: `0` = plays like a chart-blind baseline, `1` =
plays like a chart-knowing expert. It cannot be memorized or contaminated — the world is sealed.

🔑 **Never paste an API key into a chat or commit it.** The runner reads `ANTHROPIC_API_KEY` from
the environment and never takes it as an argument.

## Option B — score your own agent (any provider)

Wrap any `complete(prompt) -> reply` callable, or implement the `Agent` protocol directly:

```python
from critter_gym.eval_harness import SealedEvalSet, score_agent, verify_sealed
from critter_gym.llm_eval import LLMAgent  # or StatefulLLMAgent / BattleMemoryLLMAgent

def my_complete(prompt: str) -> str:
    ...  # call your model, return its text reply

sealed = SealedEvalSet(master_seed=20260627, n_worlds=4)   # the evaluator's secret block
card = score_agent(LLMAgent(my_complete), sealed)
print(card.inference_score, card.frac_of_oracle, card.cleared_rate)
```

An `Agent` just needs `act(obs) -> int` (and an optional `reset()` for per-world memory). See
`scripts/eval_harness_demo.py` and `scripts/llm_eval_demo.py` for runnable, key-free demos
(deterministic stub LLM — no API, no cost).

## Prove no contamination

```python
cert = verify_sealed(declared_train_seeds=my_train_seeds, sealed=sealed)
assert cert.ok   # train seeds do NOT overlap the sealed eval block, and are all in the train region
```

`verify_sealed` makes "you could not have trained on this eval" **checkable** — the trust a fixed
benchmark can't give once it leaks.
