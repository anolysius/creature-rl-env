"""Build a framework-free static leaderboard website (monetization-surface prototype).

Renders `leaderboard.py`'s ranked results into static HTML pages — English (``index.html``)
and Korean (``index.ko.html``) — each with a ranked baseline table, a **gameplay animation**
(a scripted baseline agent playing an unseen held-out world), **inline-SVG** generalization-gap
and inference-band charts (theme-aware, from the measured numbers), a design-token light/dark
theme, an explanation of the moat, and an honest caption. Written to ``site/`` so it can be
hosted as-is on GitHub Pages. No npm, no framework, no build step, no network at serve time
(stdlib ``html``/``json``; the charts are inline SVG, only the raster clips are pre-generated).

    python scripts/build_site.py            # score free baselines, build assets, write both pages
    python scripts/build_site.py --no-assets   # skip (re)generating gameplay.gif / thumbnails
    python -m http.server -d site           # local preview at http://localhost:8000

The raster assets (``gameplay.gif`` + world thumbnails) need the ``[render]`` extra (``imageio``);
it is imported lazily and, if missing, that asset is skipped and any committed file is reused —
the build still succeeds. The charts are pure inline SVG and need no extras.

Honest scope: this **builds** the pages and lets you **preview them locally**. Publishing them
(enabling GitHub Pages / making the site public) is a **human gate** — a public-facing deploy.
The pages label themselves prototypes with in-process sealing; the gameplay clip is a *scripted*
baseline (not a trained or LLM agent); numbers come from the free baselines. No hosted-product
over-claim.
"""

from __future__ import annotations

import argparse
import functools
import html
import json
import shutil
from pathlib import Path

from critter_gym.env_tier import get_tier
from critter_gym.leaderboard import BenchmarkSpec, Leaderboard, LeaderboardEntry
from critter_gym.render import _AGENT, _BG, _CREATURE, _GYM_ACTIVE, _GYM_DEFEATED

_ROOT = Path(__file__).resolve().parents[1]
_GIF_FALLBACK = _ROOT / "docs" / "assets" / "killer_demo.gif"
_SITE_DIR = _ROOT / "site"
_REPO_URL = "https://github.com/anolysius/creature-rl-env"
_GAMEPLAY_GIF = "gameplay.gif"
_WORLD_PNG = "world_{}.png"

# Bilingual copy (en / ko). Same structure both languages so render_site is language-agnostic.
_COPY: dict[str, dict[str, str]] = {
    "en": {
        "lang_name": "English",
        "title": "CritterGym — a contamination-proof RL benchmark",
        "theme_label": "Toggle light / dark theme",
        "gap_in": "held-in", "gap_out": "held-out",
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
        "legend_h": "What the colors mean",
        "lg_agent": "the agent (you)", "lg_creature": "a catchable creature",
        "lg_gym_active": "an undefeated gym (a checkpoint to clear)",
        "lg_gym_defeated": "a cleared gym", "lg_empty": "empty tile",
        "band_h": "Can it infer the hidden rules? (the moat KPI)",
        "band_p": "On an inference-gated sealed config, we measure how often each arm plays a "
                  "<em>super-effective</em> move — i.e. exploits the hidden type-chart. A "
                  "chart-<strong>knowing</strong> expert (oracle) reads ~100%; a scripted "
                  "<strong>inferrer</strong> reads high; a chart-<strong>blind</strong> baseline "
                  "reads near zero. The clean separation is what makes the eval measure "
                  "in-context inference — un-memorizable, un-gameable.",
        "band_alt": "Super-effective-move rate by arm: oracle / infer / type_blind / probe",
        "band_note": "This is the free <em>scripted</em> band (reproducible). A frontier LLM was "
                     "probed separately (a paid, evaluator-local run) and read low — near the "
                     "chart-blind floor, inconclusive; that number is not shown on this "
                     "reproducible chart.",
        "worlds_h": "Every eval is a fresh, unseen world",
        "worlds_p": "Each held-out seed regenerates a different map <em>and</em> a different "
                    "hidden type-chart — so a submission can never have trained on the world it "
                    "is scored on. Three held-out worlds:",
        "worlds_alt": "A held-out world (a fresh map the agent has never seen)",
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
        "tiers_h": "Difficulty tiers",
        "tiers_p": "Curated difficulty grades from the tier API "
                   "(<code>critter_gym.env_tier</code> — the notes below are rendered "
                   "<strong>verbatim from the code</strong>, so this page can never claim more "
                   "than the code does). In the <strong>prototype</strong> buyer flow (a "
                   "demonstrated artifact, not a live service), a buyer picks a tier, gets a "
                   "<strong>signed, secret-free manifest</strong> for its sealed eval, submits, "
                   "and receives a signed contamination-proof <strong>certificate</strong> "
                   "bound to that tier.",
        "tiers_th_tier": "tier", "tiers_th_world": "world", "tiers_th_harder": "harder knobs",
        "tiers_th_note": "difficulty (measured facts, verbatim from code)",
        "tiers_baseline": "(baseline)",
        "tiers_honest": "<strong>Honest scope.</strong> Tiers and the signed-certificate flow "
                        "are <strong>prototype artifacts</strong> (custom tiers are validated, "
                        "not measured). Real sale, pricing and hosting stay a human decision.",
        "comm_h": "Community leaderboard (self-reported)",
        "comm_p": "Race your own model on the <strong>seasonal public exam set</strong>: every "
                  "season issues a fresh, openly-derived block of held-out worlds (procedural "
                  "generation means the exam can always be re-issued — a fixed benchmark "
                  "can't). Run locally, submit a small JSON, appear here. The metric is "
                  "<strong>mean gym-clears</strong> on the season block.",
        "comm_th_rank": "rank", "comm_th_model": "model", "comm_th_by": "submitter",
        "comm_th_score": "gym-clears (mean)", "comm_th_worlds": "worlds", "comm_th_date": "date",
        "comm_season": "Season",
        "comm_how_h": "How to get on the board",
        "comm_step1": "<strong>Get the season's exam set</strong> — the same public held-out "
                      "worlds for everyone: <code>season_seeds(1, 16)</code> and the pinned "
                      "<code>season_spec()</code>.",
        "comm_step2": "<strong>Run your model</strong> on those worlds and record the mean "
                      "gym-clears. One command does it end-to-end: "
                      "<code>community_submit.py --demo</code> (a scripted policy) or "
                      "<code>--llm</code> (an LLM agent).",
        "comm_step3": "<strong>Write a small JSON</strong> (copy the example) and check it "
                      "locally — the same check CI runs: "
                      "<code>community_submit.py --validate your-file.json</code>.",
        "comm_step4": "<strong>Open a PR</strong> adding your file to "
                      "<code>community/submissions/</code>. Once it's merged, you're on the board.",
        "comm_guide_path": "docs/how-to/submit-your-model.md",
        "comm_guide": "Full step-by-step guide &rarr;",
        "comm_subs": "Browse submissions &rarr;",
        "comm_empty": "No submissions yet — be the first! See the how-to guide in the repo "
                      "(<code>docs/how-to/submit-your-model.md</code>).",
        "comm_honest": "<strong>Honest scope.</strong> These scores are "
                       "<strong>self-reported</strong> (honor system): every submission must "
                       "carry a reproduce command, but the numbers are not verified by us. "
                       "<strong>Verified, contamination-proof</strong> results are the sealed "
                       "track (signed certificates). This is a <strong>prototype</strong> — "
                       "submissions open when announced (a human decision).",
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
        "title": "CritterGym — 오염 불가능(contamination-proof) RL 벤치마크",
        "theme_label": "라이트 / 다크 테마 전환",
        "gap_in": "held-in", "gap_out": "held-out",
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
        "legend_h": "색깔의 의미",
        "lg_agent": "에이전트(플레이어)", "lg_creature": "잡을 수 있는 생물",
        "lg_gym_active": "안 깬 체육관(격파할 보스)",
        "lg_gym_defeated": "깬 체육관", "lg_empty": "빈 칸",
        "band_h": "숨은 규칙을 추론할 수 있나? (moat 핵심 지표)",
        "band_p": "추론이 필요한 sealed config 에서, 각 arm 이 <em>super-effective</em> 무브를 "
                  "얼마나 자주 쓰는지 — 즉 숨은 타입표를 얼마나 exploit 하는지 — 측정합니다. "
                  "차트를 <strong>아는</strong> 전문가(oracle)는 ~100%, 규칙기반 "
                  "<strong>추론자</strong>(infer)는 높게, 차트를 <strong>모르는</strong> "
                  "baseline 은 0 근처를 읽습니다. 이 깨끗한 분리가 eval 이 맥락 내 추론을 잰다는 "
                  "증거입니다 — "
                  "못 외우고, 못 속입니다.",
        "band_alt": "arm 별 super-effective-move 율: oracle / infer / type_blind / probe",
        "band_note": "이건 무료 <em>규칙기반(scripted)</em> band(재현 가능)입니다. 프런티어 LLM 은 "
                     "별도(유료·평가자 로컬)로 probe 했고 낮게 — chart-blind floor 근처, "
                     "inconclusive — 읽었습니다. 그 수치는 이 재현 가능한 차트에 표시하지 "
                     "않습니다.",
        "worlds_h": "매 평가는 처음 보는 새 세계",
        "worlds_p": "각 held-out 시드는 서로 다른 맵 <em>과</em> 서로 다른 숨은 타입표를 "
                    "재생성합니다 — 그래서 제출물은 채점되는 세계로 절대 학습했을 수 없습니다. "
                    "held-out 세계 3개:",
        "worlds_alt": "held-out 세계(에이전트가 한 번도 못 본 새 맵)",
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
        "tiers_h": "난이도 티어",
        "tiers_p": "티어 API(<code>critter_gym.env_tier</code>)의 curated 난이도 등급입니다 — "
                   "아래 설명은 <strong>코드에서 원문 그대로</strong> 렌더되므로 이 페이지는 "
                   "코드보다 더 세게 주장할 수 없습니다. <strong>프로토타입</strong> 구매자 "
                   "흐름(시연된 artifact 이지 운영 서비스가 아님)에서는, 구매자가 티어를 고르고 "
                   "그 봉인 eval 의 <strong>서명된(비밀 미노출) 매니페스트</strong>를 받아 "
                   "제출하면, 그 티어에 묶인 서명된 오염-불가 <strong>인증서</strong>를 받습니다.",
        "tiers_th_tier": "티어", "tiers_th_world": "세계", "tiers_th_harder": "난이도 손잡이",
        "tiers_th_note": "난이도 (측정된 사실, 코드 원문)",
        "tiers_baseline": "(기본)",
        "tiers_honest": "<strong>정직한 범위.</strong> 티어와 서명-인증서 흐름은 "
                        "<strong>프로토타입 artifact</strong>입니다(커스텀 티어는 검증만 되고 "
                        "측정되지 않음). 실제 판매·가격·hosting 은 사람의 결정입니다.",
        "comm_h": "커뮤니티 리더보드 (자가 신고)",
        "comm_p": "<strong>시즌제 공개 시험지</strong>에서 자기 모델로 경쟁하세요: 시즌마다 "
                  "공개 유도식으로 새 held-out 세계 블록이 발급됩니다(절차생성이라 시험지를 "
                  "언제든 다시 발급 가능 — 고정 벤치마크는 불가). 로컬에서 돌리고, 작은 JSON 을 "
                  "제출하면, 여기 랭크됩니다. 지표는 시즌 블록에서의 <strong>평균 체육관 "
                  "클리어</strong>입니다.",
        "comm_th_rank": "순위", "comm_th_model": "모델", "comm_th_by": "제출자",
        "comm_th_score": "체육관 클리어(평균)", "comm_th_worlds": "세계 수", "comm_th_date": "날짜",
        "comm_season": "시즌",
        "comm_how_h": "리더보드에 올리는 법",
        "comm_step1": "<strong>시즌 시험지를 받으세요</strong> — 모두에게 같은 공개 held-out "
                      "세계: <code>season_seeds(1, 16)</code> 와 고정 "
                      "<code>season_spec()</code>.",
        "comm_step2": "<strong>모델을 실행</strong>해 그 세계들에서 평균 체육관 클리어를 "
                      "기록하세요. 한 명령이 끝까지 해줍니다: "
                      "<code>community_submit.py --demo</code>(규칙기반 정책) 또는 "
                      "<code>--llm</code>(LLM 에이전트).",
        "comm_step3": "<strong>작은 JSON 을 작성</strong>하고(예시를 복사) 로컬에서 확인하세요 "
                      "— CI 가 돌리는 것과 같은 검사: "
                      "<code>community_submit.py --validate your-file.json</code>.",
        "comm_step4": "<strong>PR 을 여세요</strong> — 파일을 "
                      "<code>community/submissions/</code> 에 추가. 머지되면 리더보드에 오릅니다.",
        "comm_guide_path": "docs/how-to/submit-your-model.ko.md",
        "comm_guide": "전체 단계별 가이드 &rarr;",
        "comm_subs": "제출 폴더 보기 &rarr;",
        "comm_empty": "아직 제출이 없습니다 — 첫 번째가 되어보세요! repo 의 가이드를 참고하세요"
                      "(<code>docs/how-to/submit-your-model.ko.md</code>).",
        "comm_honest": "<strong>정직한 범위.</strong> 이 점수들은 <strong>자가 신고</strong>"
                       "(honor system)입니다: 모든 제출에 재현 명령이 필수지만, 수치를 우리가 "
                       "검증하지는 않습니다. <strong>검증된 오염-불가</strong> 결과는 봉인 "
                       "트랙(서명 인증서)입니다. 이건 <strong>프로토타입</strong>이며 — 제출 "
                       "접수는 공지 후 열립니다(사람의 결정).",
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


_LEGEND_ITEMS = (
    (_AGENT, "lg_agent"),
    (_CREATURE, "lg_creature"),
    (_GYM_ACTIVE, "lg_gym_active"),
    (_GYM_DEFEATED, "lg_gym_defeated"),
    (_BG, "lg_empty"),
)


def _legend_html(c: dict[str, str]) -> str:
    """Grid-color legend swatches, coloured from render.py's palette (SSOT)."""
    out = []
    for (r, g, b), key in _LEGEND_ITEMS:
        out.append(f'      <li><span class="sw" style="background:rgb({r},{g},{b})"></span>'
                   f'{html.escape(c[key])}</li>')
    return "\n".join(out)


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


# The tiers section renders THIS fixed built-in list, never the global registry — tests (and
# buyers) legitimately register custom tiers in-process, and those must not leak onto the page.
_SITE_TIERS = ("standard", "hard")


def _tiers_html(c: dict[str, str]) -> str:
    """The difficulty-tier rows, straight from the env_tier SSOT (values HTML-escaped).

    Only the built-in tiers (`_SITE_TIERS`) are rendered. The `difficulty_note` is the code's
    own honest description (measured facts + the 'SOTA/recurrent OPEN' caveat), escaped and
    rendered verbatim — the page cannot claim more than the code does (no hardcoded numbers)."""
    out = []
    for name in _SITE_TIERS:
        t = get_tier(name)
        view = 2 * t.patch_radius + 1
        world = f"{t.grid_size}&times;{t.grid_size}, {view}&times;{view} view, " \
                f"{t.num_gyms} gyms, {t.max_steps} steps"
        harder = html.escape(", ".join(t.harder_knobs)) if t.harder_knobs \
            else c["tiers_baseline"]
        out.append(
            "      <tr>"
            f"<td><strong>{html.escape(t.name)}</strong></td>"
            f"<td>{world}</td>"
            f"<td>{harder}</td>"
            f"<td class=\"note-cell\">{html.escape(t.difficulty_note)}</td>"
            "</tr>"
        )
    return "\n".join(out)


def _howto_html(c: dict[str, str]) -> str:
    """The 'how to get on the board' block: a 4-step numbered recipe (condensed from the
    submit-your-model how-to) plus links to the full guide (per language) and the submissions
    folder. Step copy carries its own HTML (code snippets) — trusted, not escaped; the two
    hrefs are built from the fixed repo URL + a per-language guide path."""
    steps = "".join(f"      <li>{c[f'comm_step{i}']}</li>\n" for i in range(1, 5))
    guide_href = f"{_REPO_URL}/blob/main/{c['comm_guide_path']}"
    subs_href = f"{_REPO_URL}/tree/main/community/submissions"
    return (
        f"    <h3>{c['comm_how_h']}</h3>\n"
        f"    <ol class=\"steps\">\n{steps}    </ol>\n"
        f"    <p><a class=\"repo-link\" href=\"{guide_href}\">{c['comm_guide']}</a>\n"
        f"      &nbsp; <a href=\"{subs_href}\">{c['comm_subs']}</a></p>"
    )


def _community_html(c: dict[str, str], submissions: tuple[dict, ...]) -> str:
    """The community-track body: per-season ranked tables (values HTML-escaped), or the
    be-the-first empty state. Submissions are assumed validated + ranked (load_submissions)."""
    if not submissions:
        return f"    <p>{c['comm_empty']}</p>"
    out: list[str] = []
    season = None
    for sub in submissions:
        if sub["season"] != season:
            if season is not None:
                out.append("      </tbody>\n    </table>\n    </div>")
            season = sub["season"]
            rank = 0
            out.append(
                f"    <h3>{c['comm_season']} {int(season)}</h3>\n"
                "    <div class=\"table-wrap\">\n    <table>\n"
                f"      <thead><tr><th>{c['comm_th_rank']}</th><th>{c['comm_th_model']}</th>"
                f"<th>{c['comm_th_by']}</th><th>{c['comm_th_score']}</th>"
                f"<th>{c['comm_th_worlds']}</th><th>{c['comm_th_date']}</th></tr></thead>\n"
                "      <tbody>"
            )
        rank += 1
        out.append(
            "      <tr>"
            f"<td>{rank}</td>"
            f"<td>{html.escape(str(sub['model']))}</td>"
            f"<td>{html.escape(str(sub['submitter']))}</td>"
            f"<td>{float(sub['heldout_mean']):.3f}</td>"
            f"<td>{int(sub['n_worlds'])}</td>"
            f"<td>{html.escape(str(sub['date']))}</td>"
            "</tr>"
        )
    out.append("      </tbody>\n    </table>\n    </div>")
    return "\n".join(out)


# The inference-gated demonstrator sealed config (paper §5 / inference-baseline.md).
_DEMO_SEALED = dict(master_seed=20260627, n_worlds=8, num_types=3, grid_size=5,
                    boss_hp=140, boss_atk=6, boss_def=18, max_steps=40)
_BAND_ARMS = ("oracle", "infer", "type_blind", "probe")


@functools.lru_cache(maxsize=1)
def _band_rates() -> tuple[tuple[str, float], ...]:
    """The scripted inference band (SE-rate per arm) on the demonstrator sealed set — numpy-only,
    deterministic, cached. Falls back to an empty tuple if the eval can't run (kept graceful)."""
    try:
        from critter_gym.eval_harness import SealedEvalSet, inference_baseline
        band = inference_baseline(SealedEvalSet(**_DEMO_SEALED))
        return tuple((a, float(band.arms[a].se_rate)) for a in _BAND_ARMS)
    except Exception:  # noqa: BLE001 — chart degrades gracefully if the eval can't run
        return ()


def _bar_svg(rows: tuple[tuple[str, float, str, str], ...], *, title: str) -> str:
    """A horizontal bar chart as inline, theme-aware SVG (fills reference CSS vars, text uses ink
    tokens). ``rows`` = (label, value_0to1, fill_css_var, value_label). Direct value labels satisfy
    the low-contrast fill (dataviz: labels are the secondary encoding); native <title> = hover."""
    n = len(rows)
    if n == 0:
        return ""
    row_h, gap, pad_l, pad_r, top = 34, 10, 154, 52, 8
    bar_w = 680 - pad_l - pad_r
    height = top + n * row_h + (n - 1) * gap + 8
    out = [f'<svg class="chart" viewBox="0 0 680 {height}" role="img" '
           f'aria-label="{html.escape(title)}" preserveAspectRatio="xMinYMin meet">']
    for i, (label, val, fill, vlabel) in enumerate(rows):
        y = top + i * (row_h + gap)
        w = max(2.0, min(1.0, val) * bar_w)
        lab = html.escape(label)
        out.append(f'  <title>{lab}: {html.escape(vlabel)}</title>')
        out.append(f'  <text x="{pad_l - 10}" y="{y + row_h * 0.62}" '
                   f'class="c-lab" text-anchor="end">{lab}</text>')
        out.append(f'  <rect x="{pad_l}" y="{y + 6}" width="{bar_w}" height="{row_h - 12}" '
                   f'rx="5" class="c-track"/>')
        out.append(f'  <rect x="{pad_l}" y="{y + 6}" width="{w:.1f}" height="{row_h - 12}" '
                   f'rx="5" fill="var({fill})"><title>{lab}: {html.escape(vlabel)}</title></rect>')
        out.append(f'  <text x="{pad_l + w + 8:.1f}" y="{y + row_h * 0.62}" '
                   f'class="c-val">{html.escape(vlabel)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def _band_svg() -> str:
    """SE-rate inference band: one accent bar per scripted arm (ceiling→floor), % direct labels."""
    rates = _band_rates()
    if not rates:
        return ""
    rows = tuple((arm, rate, "--series-1", f"{rate:.0%}") for arm, rate in rates)
    return _bar_svg(rows, title="Super-effective-move rate by scripted arm")


def _gap_svg(leaderboard: Leaderboard, c: dict[str, str]) -> str:
    """Generalization-gap chart: per baseline, a held-in and a held-out bar (2-series categorical,
    blue/aqua). Close bars = a small gap = real generalization. Values normalized to num_gyms."""
    entries = leaderboard.entries
    if not entries:
        return ""
    ceiling = max(1.0, float(leaderboard.spec.num_gyms))
    rows = []
    for e in entries:
        rows.append((f"{e.name} · {c['gap_in']}", e.heldin_mean / ceiling,
                     "--series-1", f"{e.heldin_mean:.2f}"))
        rows.append((f"{e.name} · {c['gap_out']}", e.heldout_mean / ceiling,
                     "--series-2", f"{e.heldout_mean:.2f}"))
    svg = _bar_svg(tuple(rows), title="Held-in vs held-out mean per baseline")
    sw1, sw2 = '<i class="sw" style="background:var(--series-1)"></i>', \
        '<i class="sw" style="background:var(--series-2)"></i>'
    legend = (
        '<div class="c-legend">'
        f'<span>{sw1}{html.escape(c["gap_in"])}</span>'
        f'<span>{sw2}{html.escape(c["gap_out"])}</span>'
        "</div>")
    return svg + "\n" + legend


def render_site(
    leaderboard: Leaderboard, *, generated_note: str, lang: str = "en", demo_cleared: bool = True,
    community: tuple = (),
) -> str:
    """Render a ``Leaderboard`` into a single static HTML page in ``lang`` (``en``/``ko``).

    Deterministic and framework-free (pure CSS animations). Carries the ranked table, the
    gameplay animation (``gameplay.gif``), inline-SVG generalization-gap + inference-band
    charts, the moat
    explanation, a language toggle, a repo link, and an honest caption. ``demo_cleared`` picks
    the honest gameplay caption (only claims the boss was defeated when it actually was). All
    interpolated values are ``html.escape``-d."""
    c = _COPY[lang]
    note = html.escape(generated_note)
    spec = html.escape(json.dumps(leaderboard.spec.to_dict(), sort_keys=True))
    rows = _rows_html(leaderboard.entries)
    legend = _legend_html(c)
    tiers = _tiers_html(c)
    comm = _community_html(c, tuple(community))
    howto = _howto_html(c)
    gap_svg = _gap_svg(leaderboard, c)
    band_svg = _band_svg()
    demo_caption = c["demo_cleared"] if demo_cleared else c["demo_uncleared"]
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(c['title'])}</title>
  <style>
    :root {{
      --surface-0: #ffffff; --surface-1: #fcfcfb; --surface-2: #f3f4f6;
      --border: #e5e6ea; --ink-1: #0b0b0b; --ink-2: #52514e; --ink-3: #8a8a80;
      --accent: #2a78d6; --series-1: #2a78d6; --series-2: #1baf7a; --track: #eceef1;
      --radius: 12px; --shadow: 0 8px 30px rgba(20,30,60,0.10); --maxw: 880px;
      --sp: 1rem;
    }}
    /* Dark theme: same tokens, dark steps (validated against the dark surface). Auto by
       system preference unless the user forced light; always on when data-theme=dark. */
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) {{
        --surface-0: #121211; --surface-1: #1a1a19; --surface-2: #232322;
        --border: #33332f; --ink-1: #ffffff; --ink-2: #c3c2b7; --ink-3: #8a8a80;
        --accent: #6da7ec; --series-1: #3987e5; --series-2: #199e70; --track: #2b2b28;
        --shadow: 0 8px 30px rgba(0,0,0,0.45);
      }}
    }}
    :root[data-theme="dark"] {{
      --surface-0: #121211; --surface-1: #1a1a19; --surface-2: #232322;
      --border: #33332f; --ink-1: #ffffff; --ink-2: #c3c2b7; --ink-3: #8a8a80;
      --accent: #6da7ec; --series-1: #3987e5; --series-2: #199e70; --track: #2b2b28;
      --shadow: 0 8px 30px rgba(0,0,0,0.45);
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{ font-family: system-ui, -apple-system, "Segoe UI", sans-serif; max-width: var(--maxw);
            margin: 0 auto; padding: 0 1rem 4rem; line-height: 1.6; color: var(--ink-1);
            background: var(--surface-0); -webkit-font-smoothing: antialiased;
            transition: background 0.3s ease, color 0.3s ease; }}
    @keyframes fadeInUp {{ from {{ opacity: 0; transform: translateY(16px); }}
                          to {{ opacity: 1; transform: translateY(0); }} }}
    @keyframes gradientShift {{ 0% {{ background-position: 0% 50%; }}
                               50% {{ background-position: 100% 50%; }}
                               100% {{ background-position: 0% 50%; }} }}
    @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    .topbar {{ display: flex; justify-content: flex-end; align-items: center; gap: 0.5rem;
               padding: 0.7rem 0; font-size: 0.9rem; }}
    .topbar a {{ text-decoration: none; }}
    .theme-btn {{ font: inherit; cursor: pointer; border: 1px solid var(--border);
                  background: var(--surface-1); color: var(--ink-2); border-radius: 999px;
                  width: 2rem; height: 2rem; line-height: 1; font-size: 1rem;
                  transition: background 0.2s ease, transform 0.2s ease; }}
    .theme-btn:hover {{ background: var(--surface-2); transform: rotate(20deg); }}
    .hero {{ margin: 0 -1rem 2rem; padding: 3rem 1.6rem 2.4rem; color: #fff; border-radius: 0;
             background: linear-gradient(120deg, #2a78d6, #6d5bd6, #1baf7a);
             background-size: 200% 200%; animation: gradientShift 14s ease infinite; }}
    .hero h1 {{ margin: 0; font-size: clamp(2rem, 6vw, 2.8rem); letter-spacing: -0.02em;
                font-weight: 800; }}
    .hero p {{ margin: 0.5rem 0 0; opacity: 0.96; max-width: 46rem; font-size: 1.05rem; }}
    section {{ animation: fadeInUp 0.7s ease both; margin-top: 2.4rem; }}
    section:nth-of-type(2) {{ animation-delay: 0.06s; }}
    section:nth-of-type(3) {{ animation-delay: 0.12s; }}
    h2 {{ font-size: 1.5rem; letter-spacing: -0.01em; margin: 0 0 0.4rem;
          padding-bottom: 0.4rem; border-bottom: 2px solid var(--border); }}
    h3 {{ font-size: 1.05rem; margin: 1.4rem 0 0.5rem; color: var(--ink-2); }}
    p {{ margin: 0.5rem 0 1rem; color: var(--ink-2); }}
    p strong, li strong {{ color: var(--ink-1); }}
    .card {{ background: var(--surface-1); border: 1px solid var(--border);
             border-radius: var(--radius); padding: 1.2rem 1.3rem; box-shadow: var(--shadow); }}
    .table-wrap {{ overflow-x: auto; border-radius: var(--radius); }}
    table {{ border-collapse: collapse; width: 100%; margin: 0.6rem 0 0.4rem;
             font-variant-numeric: tabular-nums; }}
    th, td {{ padding: 0.55rem 0.8rem; text-align: right;
              border-bottom: 1px solid var(--border); }}
    th:nth-child(2), td:nth-child(2) {{ text-align: left; }}
    thead th {{ background: var(--surface-2); color: var(--ink-2); font-size: 0.82rem;
                text-transform: uppercase; letter-spacing: 0.03em;
                border-bottom: 2px solid var(--border); }}
    tbody tr {{ transition: background 0.15s ease; }}
    tbody tr:hover {{ background: var(--surface-2); }}
    tbody tr:first-child td {{ font-weight: 600; }}
    .note-cell {{ text-align: left; font-size: 0.86rem; min-width: 22rem; color: var(--ink-2); }}
    .chart {{ width: 100%; max-width: 640px; height: auto;
              margin: 0.8rem 0 0.3rem; display: block; }}
    .c-track {{ fill: var(--track); }}
    .c-lab {{ fill: var(--ink-2); font-size: 13px; }}
    .c-val {{ fill: var(--ink-1); font-size: 13px; font-weight: 600; }}
    .c-legend {{ display: flex; gap: 1.3rem; font-size: 0.85rem; color: var(--ink-2);
                 margin: 0.1rem 0 0.6rem; }}
    .c-legend span {{ display: flex; align-items: center; gap: 0.45rem; }}
    .c-legend .sw {{ width: 0.85rem; height: 0.85rem; border-radius: 3px;
                     margin: 0; border: none; }}
    img.pixel {{ image-rendering: pixelated; width: 340px; max-width: 100%;
                 box-shadow: var(--shadow); border-radius: var(--radius);
                 border: 1px solid var(--border); }}
    ul.legend {{ list-style: none; padding: 0; display: flex; flex-wrap: wrap;
                 gap: 0.5rem 1.4rem; }}
    ul.legend li {{ display: flex; align-items: center; color: var(--ink-2); font-size: 0.92rem; }}
    .sw {{ display: inline-block; width: 1rem; height: 1rem; border-radius: 4px;
           margin-right: 0.5rem; border: 1px solid var(--border); }}
    .worlds {{ display: flex; flex-wrap: wrap; gap: 0.9rem; }}
    img.pixel.sm {{ width: 210px; }}
    ol.steps {{ counter-reset: step; list-style: none; padding: 0; display: grid; gap: 0.7rem;
                margin: 0.6rem 0 1rem; }}
    ol.steps li {{ counter-increment: step; position: relative; background: var(--surface-1);
                   border: 1px solid var(--border); border-radius: var(--radius);
                   padding: 0.85rem 1rem 0.85rem 3rem; color: var(--ink-2); }}
    ol.steps li::before {{ content: counter(step); position: absolute; left: 0.85rem; top: 0.8rem;
                           width: 1.5rem; height: 1.5rem; border-radius: 999px; font-size: 0.85rem;
                           font-weight: 700; color: #fff; background: var(--accent);
                           display: flex; align-items: center; justify-content: center; }}
    ul.moat {{ list-style: none; padding: 0; display: grid; gap: 0.8rem; }}
    ul.moat li {{ background: var(--surface-1); border: 1px solid var(--border);
                  border-left: 3px solid var(--accent); border-radius: var(--radius);
                  padding: 0.9rem 1.1rem; color: var(--ink-2); }}
    a {{ color: var(--accent); }}
    .repo-link {{ display: inline-block; margin-top: 0.6rem; font-weight: 600;
                  padding: 0.55rem 1.1rem; border-radius: 999px; text-decoration: none;
                  background: var(--accent); color: #fff; transition: transform 0.2s ease; }}
    .repo-link:hover {{ transform: translateY(-2px); }}
    .note {{ color: var(--ink-3); font-size: 0.9rem; }}
    code {{ background: var(--surface-2); padding: 0.12rem 0.35rem; border-radius: 4px;
            font-size: 0.88em; }}
    hr {{ border: none; border-top: 1px solid var(--border); margin: 2.5rem 0 1.2rem; }}
  </style>
</head>
<body>
  <div class="topbar">
    <a href="{c['other_href']}">{c['other_label']} &rarr;</a>
    <button class="theme-btn" type="button" onclick="__toggleTheme()"
            aria-label="{html.escape(c['theme_label'])}"
            title="{html.escape(c['theme_label'])}">&#9680;</button>
  </div>
  <div class="hero">
    <h1>CritterGym</h1>
    <p>{c['subtitle']}</p>
  </div>

  <section>
    <h2>{c['board_h']}</h2>
    <p>{c['board_p']}</p>
    <div class="table-wrap card">
    <table>
      <thead><tr><th>{c['th_rank']}</th><th>{c['th_base']}</th><th>{c['th_in']}</th>
      <th>{c['th_out']}</th><th>{c['th_gap']}</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    </div>
    <p class="note">{c['spec_label']} <code>{spec}</code></p>
  </section>

  <section>
    <h2>{c['gap_h']}</h2>
    <p>{c['gap_p']}</p>
    <div class="card">
{gap_svg}
    </div>
  </section>

  <section>
    <h2>{c['demo_h']}</h2>
    <p>{demo_caption}</p>
    <img class="pixel" src="{_GAMEPLAY_GIF}" alt="{c['demo_alt']}">
    <h3>{c['legend_h']}</h3>
    <ul class="legend">
{legend}
    </ul>
  </section>

  <section>
    <h2>{c['band_h']}</h2>
    <p>{c['band_p']}</p>
    <div class="card">
{band_svg}
    </div>
    <p class="note">{c['band_note']}</p>
  </section>

  <section>
    <h2>{c['worlds_h']}</h2>
    <p>{c['worlds_p']}</p>
    <div class="worlds">
      <img class="pixel sm" src="{_WORLD_PNG.format(1)}" alt="{c['worlds_alt']}">
      <img class="pixel sm" src="{_WORLD_PNG.format(2)}" alt="{c['worlds_alt']}">
      <img class="pixel sm" src="{_WORLD_PNG.format(3)}" alt="{c['worlds_alt']}">
    </div>
  </section>

  <section>
    <h2>{c['moat_h']}</h2>
    <ul class="moat"><li>{c['moat_1']}</li><li>{c['moat_2']}</li><li>{c['moat_3']}</li></ul>
    <p><a class="repo-link" href="{_REPO_URL}">{c['repo']}</a></p>
  </section>

  <section>
    <h2>{c['tiers_h']}</h2>
    <p>{c['tiers_p']}</p>
    <div class="table-wrap card">
    <table>
      <thead><tr><th>{c['tiers_th_tier']}</th><th>{c['tiers_th_world']}</th>
      <th>{c['tiers_th_harder']}</th><th>{c['tiers_th_note']}</th></tr></thead>
      <tbody>
{tiers}
      </tbody>
    </table>
    </div>
    <p class="note">{c['tiers_honest']}</p>
  </section>

  <section>
    <h2>{c['comm_h']}</h2>
    <p>{c['comm_p']}</p>
{howto}
{comm}
    <p class="note">{c['comm_honest']}</p>
  </section>

  <hr>
  <p class="note">{c['honest']} Generated: {note}.</p>
  <script>
  (function() {{
    var root = document.documentElement, key = "crittergym-theme";
    try {{ var s = localStorage.getItem(key); if (s) root.setAttribute("data-theme", s); }}
    catch (e) {{}}
    window.__toggleTheme = function() {{
      var cur = root.getAttribute("data-theme")
        || (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      var next = cur === "dark" ? "light" : "dark";
      root.setAttribute("data-theme", next);
      try {{ localStorage.setItem(key, next); }} catch (e) {{}}
    }};
  }})();
  </script>
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

    Uses a single :func:`score_baselines` pass for the ranked leaderboard (the generalization-gap
    and inference-band charts are now inline SVG rendered from these numbers — no matplotlib).
    Records a gameplay GIF (``gameplay.gif``) of the scripted agent on the first held-out seed it
    actually *clears* (so the "defeats the boss" caption is true; falls back to an uncleared clip +
    honest caption otherwise). Raster encoders (imageio, the ``[render]`` extra) are imported
    lazily; if missing, that asset is skipped and any committed file is reused. Returns the
    leaderboard and whether the gameplay clip cleared the boss."""
    from critter_gym.leaderboard import Leaderboard as _LB
    from critter_gym.scoreboard import score_baselines

    env_factory = spec.env_factory()
    heldin = spec.heldin_eval_seeds()
    heldout = spec.heldout_eval_seeds()
    table = score_baselines(env_factory, _free_policies(spec), heldin, heldout)
    board = _LB.from_score_table(spec, table)

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

    _build_world_thumbnails(out)
    return board, cleared


def _build_world_thumbnails(out: Path) -> None:
    """Render the reset frame of three *different* held-out seeds — each a fresh, unseen world
    (a new map and a new hidden type-chart) — so 'every eval is a new world' is visible."""
    try:
        import imageio.v2 as imageio

        from critter_gym.envs.critter_env import CritterEnv
        from critter_gym.region import heldout_seeds
        seeds = heldout_seeds(3)  # three distinct held-out (test-region) seeds
        for i, seed in enumerate(seeds, start=1):
            env = CritterEnv(grid_size=8, num_creatures=5, num_gyms=3, max_steps=120,
                             patch_radius=3, vary=True, render_mode="rgb_array")
            env.reset(seed=int(seed))
            frame = env.render()
            imageio.imwrite(str(out / _WORLD_PNG.format(i)), frame)
    except Exception as exc:  # noqa: BLE001 — optional [viz]; keep committed asset
        print(f"note: skipped world thumbnails ({type(exc).__name__}); reusing committed assets.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-json", type=Path, default=None,
                   help="render a pre-scored Leaderboard.to_json() file (skips scoring/assets)")
    p.add_argument("--no-assets", action="store_true",
                   help="skip (re)generating the gameplay.gif / world thumbnails")
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
        print("Scoring the free baselines and generating assets (gameplay.gif, thumbnails)...")
        board, demo_cleared = build_assets(out, BenchmarkSpec())

    # Community submissions (validated + ranked); rejected files are reported, not silently
    # dropped. The scores are self-reported (honor system) — the page labels this permanently.
    from critter_gym.community import load_submissions

    community, rejected = load_submissions(_ROOT / "community" / "submissions")
    for fname, errors in rejected:
        print(f"community submission rejected: {fname}: {'; '.join(errors)}")

    for lang in ("en", "ko"):
        name = "index.html" if lang == "en" else "index.ko.html"
        (out / name).write_text(
            render_site(board, generated_note=a.note, lang=lang, demo_cleared=demo_cleared,
                        community=tuple(community)))
        print(f"wrote {out / name}")

    print(f"local preview:  python -m http.server -d {out}   # then open http://localhost:8000")
    print("public deploy (GitHub Pages / making it public) is a human decision — not done here.")


if __name__ == "__main__":
    main()
