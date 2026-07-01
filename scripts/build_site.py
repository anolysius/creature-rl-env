"""Build a framework-free static leaderboard website (monetization-surface prototype).

Renders `leaderboard.py`'s ranked results into static HTML pages — English (``index.html``)
and Korean (``index.ko.html``) — each with a ranked baseline table, a **gameplay animation**
(a scripted baseline agent playing an unseen held-out world), a **generalization-gap plot**,
pure-CSS animations, an explanation of the moat, and an honest caption. Written to ``site/`` so
it can be hosted as-is on GitHub Pages. No npm, no framework, no build step, no network at serve
time (stdlib ``html``/``json``; the assets are pre-generated).

    python scripts/build_site.py            # score free baselines, build assets, write both pages
    python scripts/build_site.py --no-assets   # skip (re)generating gameplay.gif / gap.png
    python -m http.server -d site           # local preview at http://localhost:8000

Asset generation needs the ``[viz]`` extras (``imageio`` for the GIF, ``matplotlib`` for the
plot); they are imported lazily and, if missing, asset generation is skipped and any committed
assets are reused — the build still succeeds.

Honest scope: this **builds** the pages and lets you **preview them locally**. Publishing them
(enabling GitHub Pages / making the site public) is a **human gate** — a public-facing deploy.
The pages label themselves prototypes with in-process sealing; the gameplay clip is a *scripted*
baseline (not a trained or LLM agent); numbers come from the free baselines. No hosted-product
over-claim.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path

from critter_gym.leaderboard import BenchmarkSpec, Leaderboard, LeaderboardEntry

_ROOT = Path(__file__).resolve().parents[1]
_GIF_FALLBACK = _ROOT / "docs" / "assets" / "killer_demo.gif"
_SITE_DIR = _ROOT / "site"
_REPO_URL = "https://github.com/anolysius/creature-rl-env"
_GAMEPLAY_GIF = "gameplay.gif"
_GAP_PNG = "gap.png"

# Bilingual copy (en / ko). Same structure both languages so render_site is language-agnostic.
_COPY: dict[str, dict[str, str]] = {
    "en": {
        "lang_name": "English",
        "other_href": "index.ko.html",
        "other_label": "한국어",
        "subtitle": "A procedurally-generated creature-collection RL environment for measuring "
                    "long-horizon agency and in-context rule inference.",
        "board_h": "Leaderboard — ranked by held-out generalization",
        "board_p": "Each baseline is scored on <strong>held-out</strong> seeds (unseen maps "
                   "<em>and</em> a new hidden type-chart) it never trained on. The rank is by "
                   "held-out mean — the benchmark rewards generalization to worlds never seen.",
        "th_rank": "rank", "th_base": "baseline", "th_in": "held-in",
        "th_out": "held-out", "th_gap": "gap",
        "spec_label": "Pinned spec (reproducible):",
        "gap_h": "How well does it generalize?",
        "gap_p": "Held-in vs held-out mean per baseline — a small gap means the score is real "
                 "generalization, not memorization of seen worlds.",
        "gap_alt": "Generalization-gap plot: held-in vs held-out mean per baseline",
        "demo_h": "The gameplay",
        "demo_cleared": "A <strong>scripted baseline</strong> agent, dropped into an "
                        "<strong>unseen held-out world</strong> (a new map and a new hidden "
                        "type-chart), navigates the map, battles at the gyms, and defeats the "
                        "boss — no training on this world:",
        "demo_uncleared": "A <strong>scripted baseline</strong> agent, dropped into an "
                          "<strong>unseen held-out world</strong> (a new map and a new hidden "
                          "type-chart), navigates the map and battles through the gyms — no "
                          "training on this world:",
        "demo_alt": "Gameplay: a scripted agent playing an unseen held-out world",
        "moat_h": "Why this eval is a moat",
        "moat_1": "<strong>Contamination-proof.</strong> Evaluation worlds are regenerated per "
                  "run from a secret seed in a held-out region; a submitter's declared training "
                  "seeds are checked against the eval block, so &ldquo;could not have trained on "
                  "it&rdquo; is <em>verifiable</em>. A fixed benchmark eventually leaks; this one "
                  "<strong>cannot be memorized</strong>.",
        "moat_2": "<strong>RLVR scoring.</strong> Scores come only from "
                  "<strong>verifiable</strong> subgoals (gym-clears, catches, evolutions) — "
                  "boolean, un-gameable, no hand-tuned reward shaping.",
        "moat_3": "<strong>Un-gameable inference.</strong> The hidden type-chart is never in the "
                  "observation, so a submission can only score by <em>inferring the rules in "
                  "context</em> on a never-seen world — it cannot be looked up or memorized.",
        "repo": "Source &amp; paper on GitHub &rarr;",
        "honest": "<strong>Honest scope.</strong> This is a <strong>prototype</strong> launch "
                  "page, not a hosted product. Sealing here is <strong>in-process</strong> (a "
                  "hosted eval-as-a-service needs server-side secret seeds + a submission "
                  "sandbox). The gameplay clip is a <em>scripted</em> baseline (not a trained or "
                  "LLM agent); leaderboard numbers are the free baselines via "
                  "<code>scripts/build_site.py</code>. Publishing this page is a human decision.",
    },
    "ko": {
        "lang_name": "한국어",
        "other_href": "index.html",
        "other_label": "English",
        "subtitle": "장기 호라이즌 행위성과 맥락 내 규칙 추론을 측정하는 절차생성 "
                    "creature-collection 강화학습 환경.",
        "board_h": "리더보드 — held-out 일반화 순위",
        "board_p": "각 baseline 은 학습한 적 없는 <strong>held-out</strong> 시드(처음 보는 맵 "
                   "<em>과</em> 새로운 숨은 타입표)에서 채점됩니다. 순위는 held-out 평균 기준 — "
                   "이 벤치마크는 처음 보는 세계로의 일반화를 보상합니다.",
        "th_rank": "순위", "th_base": "baseline", "th_in": "held-in",
        "th_out": "held-out", "th_gap": "격차",
        "spec_label": "고정 spec (재현 가능):",
        "gap_h": "얼마나 일반화하나?",
        "gap_p": "baseline 별 held-in vs held-out 평균 — 격차가 작을수록 점수가 (본 세계 암기가 "
                 "아니라) 진짜 일반화라는 뜻입니다.",
        "gap_alt": "일반화 격차 플롯: baseline 별 held-in vs held-out 평균",
        "demo_h": "게임플레이",
        "demo_cleared": "<strong>규칙기반(scripted) baseline</strong> 에이전트가 <strong>처음 보는 "
                        "held-out 세계</strong>(새 맵 + 새 숨은 타입표)에 놓여 맵을 탐색하고, "
                        "체육관에서 전투하며, 보스를 격파합니다 — 이 세계로 학습한 적 없음:",
        "demo_uncleared": "<strong>규칙기반(scripted) baseline</strong> 에이전트가 "
                          "<strong>처음 보는 held-out 세계</strong>(새 맵 + 새 숨은 타입표)에 놓여 "
                          "맵을 탐색하고 체육관을 헤쳐 나갑니다 — 이 세계로 학습한 적 없음:",
        "demo_alt": "게임플레이: 처음 보는 held-out 세계를 플레이하는 scripted 에이전트",
        "moat_h": "왜 이 eval 이 해자(moat)인가",
        "moat_1": "<strong>오염 불가.</strong> 평가 세계는 매 실행마다 held-out 구역의 비밀 "
                  "시드에서 재생성되고, 제출자가 선언한 학습 시드가 eval 블록과 겹치는지 "
                  "검사되므로 "
                  "&ldquo;테스트로 학습할 수 없었다&rdquo;가 <em>검증 가능</em>합니다. 고정 "
                  "벤치마크는 언젠가 유출되지만, 이건 <strong>외울 수 없습니다</strong>.",
        "moat_2": "<strong>RLVR 채점.</strong> 점수는 오직 <strong>검증 가능한</strong> "
                  "subgoal(체육관 클리어·포획·진화)에서만 나옵니다 — 불리언, 게이밍 불가, "
                  "손튜닝 보상 없음.",
        "moat_3": "<strong>게이밍 불가 추론.</strong> 숨은 타입표는 관측에 절대 들어가지 않으므로, "
                  "제출물은 처음 보는 세계에서 <em>맥락 내에서 규칙을 추론</em>해야만 점수를 "
                  "얻습니다 — 조회하거나 외울 수 없습니다.",
        "repo": "GitHub 소스 &amp; 논문 &rarr;",
        "honest": "<strong>정직한 범위.</strong> 이건 <strong>프로토타입</strong> 런치 페이지이지 "
                  "hosted 제품이 아닙니다. 여기서 봉인은 <strong>in-process</strong>입니다"
                  "(hosted eval 서비스는 서버측 비밀 시드 + 제출 샌드박스가 필요). 게임플레이 "
                  "클립은 <em>규칙기반(scripted)</em> baseline(학습/LLM 에이전트 아님)이며, "
                  "리더보드 수치는 <code>scripts/build_site.py</code> 의 무료 baseline 입니다. "
                  "이 페이지의 공개는 "
                  "사람의 결정입니다.",
    },
}


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


def render_site(
    leaderboard: Leaderboard, *, generated_note: str, lang: str = "en", demo_cleared: bool = True,
) -> str:
    """Render a ``Leaderboard`` into a single static HTML page in ``lang`` (``en``/``ko``).

    Deterministic and framework-free (pure CSS animations). Carries the ranked table, the
    gameplay animation (``gameplay.gif``), the generalization-gap plot (``gap.png``), the moat
    explanation, a language toggle, a repo link, and an honest caption. ``demo_cleared`` picks
    the honest gameplay caption (only claims the boss was defeated when it actually was). All
    interpolated values are ``html.escape``-d."""
    c = _COPY[lang]
    note = html.escape(generated_note)
    spec = html.escape(json.dumps(leaderboard.spec.to_dict(), sort_keys=True))
    rows = _rows_html(leaderboard.entries)
    demo_caption = c["demo_cleared"] if demo_cleared else c["demo_uncleared"]
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CritterGym — a contamination-proof RL benchmark</title>
  <style>
    :root {{ --accent: #5b7cfa; }}
    * {{ box-sizing: border-box; }}
    body {{ font-family: system-ui, -apple-system, sans-serif; max-width: 860px;
            margin: 0 auto; padding: 0 1rem 3rem; line-height: 1.55; color: #1a1a1a; }}
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(16px); }}
                          to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes gradientShift {{ 0% {{ background-position: 0% 50%; }}
                               50% {{ background-position: 100% 50%; }}
                               100% {{ background-position: 0% 50%; }} }}
    .hero {{ margin: 0 -1rem 1.5rem; padding: 2.6rem 1.5rem 2rem; color: #fff;
             background: linear-gradient(120deg, #5b7cfa, #8b5cf6, #22c55e);
             background-size: 200% 200%; animation: gradientShift 12s ease infinite; }}
    .hero h1 {{ margin: 0; font-size: 2.4rem; letter-spacing: -0.02em; }}
    .hero p {{ margin: 0.4rem 0 0; opacity: 0.95; max-width: 46rem; }}
    .langbar {{ text-align: right; padding: 0.6rem 0; font-size: 0.9rem; }}
    section {{ animation: fadeInUp 0.7s ease both; }}
    section:nth-of-type(2) {{ animation-delay: 0.08s; }}
    section:nth-of-type(3) {{ animation-delay: 0.16s; }}
    h2 {{ margin-top: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #e2e2e2; padding: 0.45rem 0.7rem; text-align: right; }}
    th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    thead {{ background: #f4f5ff; }}
    tbody tr {{ transition: background 0.15s ease; }}
    tbody tr:hover {{ background: #f4f5ff; }}
    img.asset {{ max-width: 100%; border: 1px solid #eee; border-radius: 6px; }}
    img.pixel {{ image-rendering: pixelated; width: 320px; max-width: 100%;
                 box-shadow: 0 6px 24px rgba(91,124,250,0.25); border-radius: 8px; }}
    a {{ color: var(--accent); }}
    .note {{ color: #666; font-size: 0.9rem; }}
    code {{ background: #f4f4f4; padding: 0.1rem 0.3rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <div class="langbar"><a href="{c['other_href']}">{c['other_label']} &rarr;</a></div>
  <div class="hero">
    <h1>CritterGym</h1>
    <p>{c['subtitle']}</p>
  </div>

  <section>
    <h2>{c['board_h']}</h2>
    <p>{c['board_p']}</p>
    <table>
      <thead><tr><th>{c['th_rank']}</th><th>{c['th_base']}</th><th>{c['th_in']}</th>
      <th>{c['th_out']}</th><th>{c['th_gap']}</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    <p class="note">{c['spec_label']} <code>{spec}</code></p>
  </section>

  <section>
    <h2>{c['gap_h']}</h2>
    <p>{c['gap_p']}</p>
    <img class="asset" src="{_GAP_PNG}" alt="{c['gap_alt']}">
  </section>

  <section>
    <h2>{c['demo_h']}</h2>
    <p>{demo_caption}</p>
    <img class="pixel" src="{_GAMEPLAY_GIF}" alt="{c['demo_alt']}">
  </section>

  <section>
    <h2>{c['moat_h']}</h2>
    <ul><li>{c['moat_1']}</li><li>{c['moat_2']}</li><li>{c['moat_3']}</li></ul>
    <p><a href="{_REPO_URL}">{c['repo']}</a></p>
  </section>

  <hr>
  <p class="note">{c['honest']} Generated: {note}.</p>
</body>
</html>
"""


def _free_policies(spec: BenchmarkSpec):  # type: ignore[no-untyped-def]
    import numpy as np

    from critter_gym.baselines import greedy_policy, random_policy

    rng = np.random.default_rng(0)
    return {
        "random": lambda o: random_policy(o, rng),
        "scripted": lambda o: greedy_policy(o, grid_size=spec.grid_size),
    }


def _leaderboard_from_json(path: Path) -> Leaderboard:
    """Rebuild a ``Leaderboard`` from a ``Leaderboard.to_json()`` file."""
    data = json.loads(path.read_text())
    spec = BenchmarkSpec(**data["spec"])
    entries = tuple(LeaderboardEntry(**e) for e in data["entries"])
    return Leaderboard(spec=spec, entries=entries)


def build_assets(out: Path, spec: BenchmarkSpec) -> tuple[Leaderboard, bool]:
    """Score the free baselines once and (best-effort) generate the site's visual assets.

    Uses a single :func:`score_baselines` pass for both the ranked leaderboard and the
    generalization-gap plot (``gap.png``, via matplotlib). Records a gameplay GIF
    (``gameplay.gif``) of the scripted agent on the first held-out seed it actually *clears*
    (so the "defeats the boss" caption is true; falls back to an uncleared clip + honest caption
    otherwise). Asset encoders (imageio/matplotlib, the ``[viz]`` extras) are imported lazily; if
    missing, that asset is skipped and any committed file is reused. Returns the leaderboard and
    whether the gameplay clip cleared the boss."""
    from critter_gym.leaderboard import Leaderboard as _LB
    from critter_gym.scoreboard import score_baselines

    env_factory = spec.env_factory()
    heldin = spec.heldin_eval_seeds()
    heldout = spec.heldout_eval_seeds()
    table = score_baselines(env_factory, _free_policies(spec), heldin, heldout)
    board = _LB.from_score_table(spec, table)

    # generalization-gap plot (matplotlib, lazy)
    try:
        from critter_gym.viz import plot_generalization_gap
        fig = plot_generalization_gap(table)
        fig.savefig(out / _GAP_PNG, dpi=100, bbox_inches="tight")
    except Exception as exc:  # noqa: BLE001 — optional [viz]; keep committed asset
        print(f"note: skipped {_GAP_PNG} ({type(exc).__name__}: {exc}); reusing committed asset.")

    # gameplay GIF (imageio via demo.save_demo, lazy) — prefer a held-out seed it clears
    cleared = False
    try:
        from critter_gym.baselines import greedy_policy
        from critter_gym.demo import record_episode, save_demo
        from critter_gym.envs.critter_env import CritterEnv

        def render_env() -> CritterEnv:
            return CritterEnv(grid_size=8, num_creatures=5, num_gyms=3, max_steps=120,
                              patch_radius=3, vary=True, render_mode="rgb_array")

        rec = None
        for seed in heldout[:12]:
            r = record_episode(
                render_env(), lambda o: greedy_policy(o, grid_size=8), seed=int(seed))
            if rec is None:
                rec = r  # keep the first as a fallback
            if r.boss_defeated:
                rec, cleared = r, True
                break
        if rec is not None:
            save_demo(rec, str(out / _GAMEPLAY_GIF), fps=6)
    except Exception as exc:  # noqa: BLE001 — optional [viz]; keep committed asset
        print(f"note: skipped {_GAMEPLAY_GIF} ({type(exc).__name__}); reusing committed asset.")
        if not (out / _GAMEPLAY_GIF).exists() and _GIF_FALLBACK.exists():
            shutil.copy2(_GIF_FALLBACK, out / _GAMEPLAY_GIF)

    return board, cleared


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-json", type=Path, default=None,
                   help="render a pre-scored Leaderboard.to_json() file (skips scoring/assets)")
    p.add_argument("--no-assets", action="store_true",
                   help="skip (re)generating gameplay.gif / gap.png")
    p.add_argument("--out", type=Path, default=_SITE_DIR, help="output site directory")
    p.add_argument("--note", default="scripted/free baselines", help="a short 'generated' note")
    a = p.parse_args()

    out: Path = a.out
    out.mkdir(parents=True, exist_ok=True)

    demo_cleared = True
    if a.from_json is not None:
        board = _leaderboard_from_json(a.from_json)
    elif a.no_assets:
        from critter_gym.scoreboard import score_baselines
        spec = BenchmarkSpec()
        board = Leaderboard.from_score_table(
            spec, score_baselines(spec.env_factory(), _free_policies(spec),
                                  spec.heldin_eval_seeds(), spec.heldout_eval_seeds()))
    else:
        print("Scoring the free baselines and generating assets (gameplay.gif, gap.png)...")
        board, demo_cleared = build_assets(out, BenchmarkSpec())

    for lang in ("en", "ko"):
        name = "index.html" if lang == "en" else "index.ko.html"
        (out / name).write_text(
            render_site(board, generated_note=a.note, lang=lang, demo_cleared=demo_cleared))
        print(f"wrote {out / name}")

    print(f"local preview:  python -m http.server -d {out}   # then open http://localhost:8000")
    print("public deploy (GitHub Pages / making it public) is a human decision — not done here.")


if __name__ == "__main__":
    main()
