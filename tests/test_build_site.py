"""The static leaderboard site (monetization-surface) renders leaderboard.py results.

`scripts/build_site.py` turns a `Leaderboard` into framework-free static HTML pages — English
and Korean — with a ranked table, a gameplay animation, a generalization-gap plot, CSS
animations, and an honest caption. These pin that the render is deterministic, bilingual,
includes each entry, carries the moat/honesty copy, and escapes values. Public deployment
stays a human gate (this only builds + is locally previewable)."""
from __future__ import annotations

import sys
from pathlib import Path

from critter_gym.leaderboard import BenchmarkSpec, Leaderboard, LeaderboardEntry

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_site  # noqa: E402


def _board() -> Leaderboard:
    spec = BenchmarkSpec(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40,
                         patch_radius=3, n_heldin=12, n_heldout=12)
    entries = (
        LeaderboardEntry(rank=1, name="scripted", heldin_mean=1.500, heldout_mean=1.200, gap=0.300),
        LeaderboardEntry(rank=2, name="random", heldin_mean=0.400, heldout_mean=0.300, gap=0.100),
    )
    return Leaderboard(spec=spec, entries=entries)


def test_render_site_includes_every_entry() -> None:
    """Each ranked baseline (rank, name, held-out mean) appears in the page."""
    html = build_site.render_site(_board(), generated_note="test")
    assert "<html" in html and "<table" in html
    for e in _board().entries:
        assert e.name in html
        assert f"{e.heldout_mean:.3f}" in html


def test_render_site_is_deterministic() -> None:
    """Same leaderboard + note + lang -> byte-identical page."""
    a = build_site.render_site(_board(), generated_note="x", lang="en")
    b = build_site.render_site(_board(), generated_note="x", lang="en")
    assert a == b
    ka = build_site.render_site(_board(), generated_note="x", lang="ko")
    kb = build_site.render_site(_board(), generated_note="x", lang="ko")
    assert ka == kb


def test_render_site_carries_moat_and_honesty_copy() -> None:
    """The English page explains the moat, references the assets, and honestly labels itself a
    prototype whose public deploy is a human gate."""
    html = build_site.render_site(_board(), generated_note="test").lower()
    assert "held-out" in html
    assert "contamination" in html or "un-gameable" in html or "cannot be memorized" in html
    assert "rlvr" in html or "verifiable" in html
    assert "gameplay.gif" in html   # the gameplay animation
    assert "gap.png" in html        # the generalization-gap plot
    assert "prototype" in html
    assert "in-process" in html


def test_render_site_escapes_values() -> None:
    """Entry names are HTML-escaped (no raw injection)."""
    spec = BenchmarkSpec(grid_size=6, num_creatures=6, num_gyms=2, max_steps=40,
                         patch_radius=3, n_heldin=12, n_heldout=12)
    board = Leaderboard(spec=spec, entries=(
        LeaderboardEntry(rank=1, name="<script>x</script>", heldin_mean=1.0,
                         heldout_mean=1.0, gap=0.0),
    ))
    html = build_site.render_site(board, generated_note="t")
    assert "<script>x</script>" not in html
    assert "&lt;script&gt;" in html


def test_render_site_korean() -> None:
    """The Korean page carries Korean copy (not just English) and the same assets."""
    html = build_site.render_site(_board(), generated_note="test", lang="ko")
    assert "리더보드" in html or "리그" in html or "순위" in html  # Korean leaderboard heading
    assert "프로토타입" in html                                    # honest 'prototype' in Korean
    assert "gameplay.gif" in html and "gap.png" in html
    for e in _board().entries:
        assert e.name in html


def test_render_site_language_toggle() -> None:
    """Each page links to the other language (index.html <-> index.ko.html)."""
    en = build_site.render_site(_board(), generated_note="t", lang="en")
    ko = build_site.render_site(_board(), generated_note="t", lang="ko")
    assert "index.ko.html" in en   # EN -> KO
    assert "index.html" in ko      # KO -> EN


def test_render_site_has_css_animation() -> None:
    """Pure-CSS animations (no framework): a @keyframes rule and an animation property."""
    html = build_site.render_site(_board(), generated_note="t")
    assert "@keyframes" in html
    assert "animation:" in html


def test_render_site_demo_caption_is_honest() -> None:
    """The gameplay caption only claims the boss was cleared when demo_cleared is True; otherwise
    it makes the weaker, still-true claim. And it labels the agent a scripted baseline (not LLM)."""
    cleared = build_site.render_site(_board(), generated_note="t", demo_cleared=True).lower()
    not_cleared = build_site.render_site(_board(), generated_note="t", demo_cleared=False).lower()
    assert "scripted" in cleared            # honest: not a trained/LLM agent
    assert "boss" in cleared                # claims the win when it happened
    assert "boss" not in not_cleared or "defeat" not in not_cleared  # no false win claim


# --- research-explaining visuals: grid legend, SE-rate band chart, held-out thumbnails ---
def test_render_site_grid_legend_uses_render_palette() -> None:
    """The grid-color legend uses render.py's actual palette (SSOT, not hardcoded guesses), so the
    swatches match what the gameplay clip shows."""
    from critter_gym.render import _AGENT, _CREATURE, _GYM_ACTIVE

    html = build_site.render_site(_board(), generated_note="t")
    for r, g, b in (_AGENT, _CREATURE, _GYM_ACTIVE):
        assert f"rgb({r},{g},{b})" in html    # legend swatch background from the real palette
    low = html.lower()
    assert "agent" in low and "creature" in low  # English labels


def test_render_site_grid_legend_korean() -> None:
    """The Korean legend labels the cells in Korean."""
    html = build_site.render_site(_board(), generated_note="t", lang="ko")
    assert "에이전트" in html and "생물" in html and "체육관" in html


def test_render_site_embeds_band_and_thumbnails() -> None:
    """The page references the SE-rate inference-band chart and the held-out world thumbnails."""
    for lang in ("en", "ko"):
        html = build_site.render_site(_board(), generated_note="t", lang=lang)
        assert "band.png" in html                       # SE-rate inference band chart
        for i in (1, 2, 3):
            assert f"world_{i}.png" in html             # held-out world thumbnails


def test_render_site_band_caption_is_honest() -> None:
    """The band caption is honest: a scripted proxy band; the frontier-LLM read is a separate paid
    probe and is NOT hardcoded as a number on the reproducible chart."""
    en = build_site.render_site(_board(), generated_note="t").lower()
    assert "scripted" in en          # scripted proxy band
    assert "14%" not in en           # the paid LLM number is not hardcoded on the page


# --- Difficulty-tiers section (site-tier-section): env_tier SSOT, no hardcoded claims ----

def test_render_site_tiers_from_env_tier_ssot() -> None:
    """The tier rows render the BUILT-IN tiers straight from env_tier (the SSOT) — the page
    can never claim more than the code does (the difficulty_note carries the measured facts
    and the 'SOTA/recurrent OPEN' caveat)."""
    import html as html_mod

    from critter_gym.env_tier import get_tier

    page = build_site.render_site(_board(), generated_note="test")
    for name in ("standard", "hard"):
        t = get_tier(name)
        assert name in page
        assert html_mod.escape(t.difficulty_note) in page  # SSOT verbatim, escaped
        assert str(t.grid_size) in page


def test_render_site_tiers_do_not_leak_custom_registrations() -> None:
    """Registering a custom tier (as tests legitimately do in-process) must NOT leak it onto
    the sales page — the section renders a fixed built-in list, not the global registry."""
    from critter_gym.env_tier import TierSpec, register_tier

    register_tier("site_leak_probe", TierSpec(
        name="site_leak_probe", grid_size=12, num_gyms=4, num_creatures=6, max_steps=260,
        patch_radius=2, num_types=4, boss_hp=140, boss_atk=13, boss_def=13,
        commit_battles=False, harder_knobs=("grid_size",),
        difficulty_note="a probe tier that must never appear on the site",
    ))
    page = build_site.render_site(_board(), generated_note="test")
    assert "site_leak_probe" not in page
    assert "must never appear on the site" not in page


def test_render_site_tiers_korean() -> None:
    """The ko page carries Korean tier labels while the difficulty_note stays the English
    SSOT verbatim (same pattern as the palette legend)."""
    import html as html_mod

    from critter_gym.env_tier import get_tier

    page = build_site.render_site(_board(), generated_note="test", lang="ko")
    assert "난이도 티어" in page
    assert html_mod.escape(get_tier("hard").difficulty_note) in page


def test_render_site_tiers_honest_caption() -> None:
    """Both languages carry the buyer-flow line and the human-gate honesty caption."""
    en = build_site.render_site(_board(), generated_note="test", lang="en")
    ko = build_site.render_site(_board(), generated_note="test", lang="ko")
    assert "signed" in en and "certificate" in en          # buyer flow: offer -> certificate
    assert "human decision" in en or "human gate" in en
    assert "서명" in ko and "인증서" in ko
    assert "사람" in ko


# --- Community leaderboard section (community-leaderboard): self-reported, seasonal ------

def _subs() -> tuple:
    from critter_gym.community import SCHEMA_VERSION, season_spec
    base = {
        "schema_version": SCHEMA_VERSION, "season": 1, "n_worlds": 16,
        "spec": season_spec(), "reproduce": "cmd", "date": "2026-07-02",
        "self_reported": True,
    }
    return (
        {**base, "model": "alpha<b>", "submitter": "ann", "heldout_mean": 2.0},
        {**base, "model": "beta", "submitter": "bob", "heldout_mean": 1.0},
    )


def test_render_site_community_ranks_and_escapes() -> None:
    page = build_site.render_site(_board(), generated_note="t", community=_subs())
    assert "Community leaderboard" in page
    assert "alpha&lt;b&gt;" in page          # values escaped
    assert page.index("alpha&lt;b&gt;") < page.index("beta")  # ranked desc by score
    assert "2.000" in page and "1.000" in page


def test_render_site_community_empty_state() -> None:
    page = build_site.render_site(_board(), generated_note="t", community=())
    assert "be the first" in page.lower()
    assert "Community leaderboard" in page


def test_render_site_community_honest_labels() -> None:
    en = build_site.render_site(_board(), generated_note="t", community=_subs())
    ko = build_site.render_site(_board(), generated_note="t", lang="ko", community=_subs())
    for page, sealed_word in ((en, "sealed"), (ko, "봉인")):
        assert "self-reported" in page or "자가 신고" in page
        assert sealed_word in page                        # funnel to the proof track
    assert "submissions open when announced" in en        # not-open-yet human gate
    assert "공지 후" in ko


def test_render_site_community_backward_compatible() -> None:
    # Old call sites (no community arg) still render — the section shows the empty state.
    page = build_site.render_site(_board(), generated_note="t")
    assert "Community leaderboard" in page
