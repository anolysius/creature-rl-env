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
