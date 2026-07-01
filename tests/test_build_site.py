"""The static leaderboard site (monetization-surface #1) renders leaderboard.py results.

`scripts/build_site.py` turns a `Leaderboard` into a single framework-free static HTML page
(ranked table + killer-demo GIF + moat explanation + honest caption). These pin that the
render is deterministic, includes each entry, carries the moat/honesty copy, and escapes
values — so the page a reviewer/customer sees is faithful and safe. Public deployment stays a
human gate (this only builds + is locally previewable)."""
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
        assert f"{e.heldout_mean:.3f}" in html  # held-out mean rendered


def test_render_site_is_deterministic() -> None:
    """Same leaderboard + note -> byte-identical page."""
    a = build_site.render_site(_board(), generated_note="x")
    b = build_site.render_site(_board(), generated_note="x")
    assert a == b


def test_render_site_carries_moat_and_honesty_copy() -> None:
    """The page explains the moat (held-out / un-gameable / RLVR), references the killer-demo
    GIF, and honestly labels itself a prototype whose public deploy is a human gate."""
    html = build_site.render_site(_board(), generated_note="test").lower()
    assert "held-out" in html
    assert "contamination" in html or "un-gameable" in html or "cannot be memorized" in html
    assert "rlvr" in html or "verifiable" in html
    assert "killer_demo.gif" in html
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
