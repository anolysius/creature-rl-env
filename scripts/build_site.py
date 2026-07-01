"""Build a framework-free static leaderboard website (monetization-surface prototype #1).

Renders `leaderboard.py`'s ranked results into a single static HTML page — the ranked
baseline table, the killer-demo GIF, an explanation of the moat (a contamination-proof,
regenerable, RLVR-scored sealed held-out eval), and a repo link — written to ``site/`` so it
can be hosted as-is on GitHub Pages. No npm, no framework, no build step, no network (stdlib
``html``/``json`` only).

    python scripts/build_site.py            # score the free baselines, write site/index.html
    python scripts/build_site.py --from-json board.json   # render a pre-scored leaderboard
    python -m http.server -d site           # local preview at http://localhost:8000

Honest scope: this **builds** the page and lets you **preview it locally**. Actually
publishing it (enabling GitHub Pages / making the site public) is a **human gate** — a
public-facing deployment, like the arXiv/OSS release. The page labels itself a prototype with
in-process sealing, and states where its numbers come from — no over-claim of a hosted product.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from critter_gym.leaderboard import BenchmarkSpec, Leaderboard, LeaderboardEntry

_ROOT = Path(__file__).resolve().parents[1]
_GIF_SRC = _ROOT / "docs" / "assets" / "killer_demo.gif"
_SITE_DIR = _ROOT / "site"
_REPO_URL = "https://github.com/anolysius/creature-rl-env"


def _rows_html(entries: tuple[LeaderboardEntry, ...]) -> str:
    """The ranked leaderboard table body (values HTML-escaped)."""
    out = []
    for e in entries:
        out.append(
            "      <tr>"
            f"<td>{e.rank}</td>"
            f"<td>{html.escape(e.name)}</td>"
            f"<td>{e.heldin_mean:.3f}</td>"
            f"<td>{e.heldout_mean:.3f}</td>"
            f"<td>{e.gap:.3f}</td>"
            "</tr>"
        )
    return "\n".join(out)


def render_site(leaderboard: Leaderboard, *, generated_note: str) -> str:
    """Render a ``Leaderboard`` into a single static HTML page (deterministic, framework-free).

    The page carries the ranked table, the killer-demo GIF, the moat explanation (held-out
    seed split, contamination guard, RLVR scoring), a repo link, and an honest caption
    (prototype / in-process sealing / public deploy is a human gate). All interpolated values
    are ``html.escape``-d."""
    note = html.escape(generated_note)
    spec = html.escape(json.dumps(leaderboard.spec.to_dict(), sort_keys=True))
    rows = _rows_html(leaderboard.entries)
    gif = "killer_demo.gif"  # copied next to index.html by main()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CritterGym — a contamination-proof RL benchmark</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto;
            padding: 0 1rem; line-height: 1.5; color: #1a1a1a; }}
    h1 {{ margin-bottom: 0.2rem; }}
    .sub {{ color: #555; margin-top: 0; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.6rem; text-align: right; }}
    th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    thead {{ background: #f4f4f4; }}
    img {{ max-width: 100%; border: 1px solid #eee; }}
    .note {{ color: #666; font-size: 0.9rem; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>CritterGym</h1>
  <p class="sub">A procedurally-generated creature-collection RL environment for measuring
  long-horizon agency and in-context rule inference.</p>

  <h2>Leaderboard — ranked by held-out generalization</h2>
  <p>Each baseline is scored on <strong>held-out</strong> seeds (unseen maps <em>and</em> a new
  hidden type-chart) it never trained on. The rank is by held-out mean, not in-distribution
  score — the benchmark rewards generalization to worlds the agent has never seen.</p>
  <table>
    <thead><tr><th>rank</th><th>baseline</th><th>held-in</th><th>held-out</th><th>gap</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <p class="note">Pinned spec (reproducible): <code>{spec}</code></p>

  <h2>The killer demo</h2>
  <p>The same agent, dropped into an <strong>unseen held-out seed</strong> (a new map and a new
  hidden type-chart), still defeats the gym boss:</p>
  <img src="{gif}" alt="CritterGym killer demo — an agent clearing an unseen held-out world">

  <h2>Why this eval is a moat</h2>
  <ul>
    <li><strong>Contamination-proof.</strong> Evaluation worlds are regenerated per run from a
    secret seed in a held-out region; a submitter's declared training seeds are checked against
    the eval block, so &ldquo;could not have trained on it&rdquo; is <em>verifiable</em>, not
    assumed. A fixed benchmark eventually leaks; this one <strong>cannot be memorized</strong>.</li>
    <li><strong>RLVR scoring.</strong> Scores come only from <strong>verifiable</strong> subgoals
    (gym-clears, catches, evolutions) — boolean, un-gameable, no hand-tuned reward shaping.</li>
    <li><strong>Un-gameable inference.</strong> The hidden type-chart is never in the observation,
    so a submission can only score by <em>inferring the rules in context</em> on a never-seen
    world — it cannot be looked up or memorized.</li>
  </ul>

  <p><a href="{_REPO_URL}">Source &amp; paper on GitHub &rarr;</a></p>

  <hr>
  <p class="note"><strong>Honest scope.</strong> This is a <strong>prototype</strong> launch page,
  not a hosted product. Sealing here is <strong>in-process</strong> (a hosted eval-as-a-service
  needs server-side secret seeds + a submission sandbox). Numbers are generated live by the
  scripted/free baselines via <code>scripts/build_site.py</code>; learned baselines appear only
  when the <code>[rl]</code> extra is installed. Publishing this page is a human decision.
  Generated: {note}.</p>
</body>
</html>
"""


def _free_leaderboard(spec: BenchmarkSpec) -> Leaderboard:
    """Score the free (numpy-only) baselines — random + scripted — and rank them.

    Learned baselines (PPO/recurrent) need the ``[rl]`` extra and heavy scoring; they are
    intentionally omitted from this default build (use ``--from-json`` to render a pre-scored
    leaderboard that includes them)."""
    import numpy as np

    from critter_gym.baselines import greedy_policy, random_policy
    from critter_gym.leaderboard import run_benchmark

    rng = np.random.default_rng(0)
    policies = {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=spec.grid_size),
    }
    return run_benchmark(spec, policies)


def _leaderboard_from_json(path: Path) -> Leaderboard:
    """Rebuild a ``Leaderboard`` from a ``Leaderboard.to_json()`` file (e.g. a full run that
    included the learned baselines)."""
    data = json.loads(path.read_text())
    spec = BenchmarkSpec(**data["spec"])
    entries = tuple(LeaderboardEntry(**e) for e in data["entries"])
    return Leaderboard(spec=spec, entries=entries)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-json", type=Path, default=None,
                   help="render a pre-scored Leaderboard.to_json() file instead of scoring the "
                        "free baselines (use for a full run incl. learned baselines)")
    p.add_argument("--out", type=Path, default=_SITE_DIR, help="output site directory")
    p.add_argument("--note", default="scripted/free baselines", help="a short 'generated' note")
    a = p.parse_args()

    if a.from_json is not None:
        board = _leaderboard_from_json(a.from_json)
    else:
        print("Scoring the free baselines (random + scripted) — learned baselines need [rl].")
        board = _free_leaderboard(BenchmarkSpec())

    out: Path = a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(render_site(board, generated_note=a.note))
    if _GIF_SRC.exists():
        shutil.copy2(_GIF_SRC, out / "killer_demo.gif")
    else:
        print(f"note: {_GIF_SRC} not found — the page's demo image will be broken.")

    print(f"wrote {out / 'index.html'}")
    print(f"local preview:  python -m http.server -d {out}   # then open http://localhost:8000")
    print("public deploy (GitHub Pages / making it public) is a human decision — not done here.")


if __name__ == "__main__":
    main()
