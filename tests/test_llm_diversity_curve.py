"""Mechanism tests for the LLM diversity-curve runner (llm-diversity-curve) — quota 0.

The real measurement spends the user's claude-cli subscription quota, so every branch of the
gated protocol (G-0 smoke -> G-1 floor-stop -> G-2 delta verdict -> G-3 conditional mid-point)
is proven here with an injected stub ``complete`` — no subprocess, no network, no ``claude``
binary. CI-deterministic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import llm_diversity_curve as ldc  # noqa: E402

# A tiny sealed config so stub episodes finish fast (the real frozen config stays in the script).
TINY_KWARGS = dict(master_seed=123, grid_size=8, num_gyms=3, num_types=8,
                   max_steps=25, boss_hp=40, boss_atk=6, boss_def=10)


def _stub_complete(reply: str = "0"):
    return lambda prompt: reply


# -- reply_unparseable (parse-failure telemetry) --------------------------------


def test_reply_unparseable_matches_parse_fallback() -> None:
    assert ldc.reply_unparseable("") is True
    assert ldc.reply_unparseable("hmm, I wonder what to do") is True
    assert ldc.reply_unparseable("2") is False           # digit
    assert ldc.reply_unparseable("Action: 3") is False   # explicit action
    assert ldc.reply_unparseable("go north") is False    # keyword


# -- CountingComplete (budget + telemetry wrapper) ------------------------------


def test_counting_complete_counts_calls_and_unparseable() -> None:
    counter = ldc.CountingComplete(_stub_complete("gibberish reply"), budget=10)
    counter("p1")
    counter("p2")
    assert counter.calls == 2
    assert counter.unparseable == 2
    assert counter.seconds >= 0.0


def test_counting_complete_enforces_hard_budget() -> None:
    counter = ldc.CountingComplete(_stub_complete("0"), budget=2)
    counter("p1")
    counter("p2")
    with pytest.raises(ldc.BudgetExceeded):
        counter("p3")


# -- decide / needs_mid_point (pre-registered gate branches) ---------------------


def test_decide_floor_saturated_stops_before_pool_max() -> None:
    verdict, _ = ldc.decide(anchor_score=0.05, max_score=None)
    assert verdict == "FLOOR-SATURATED"


def test_decide_dial_visible() -> None:
    verdict, _ = ldc.decide(anchor_score=0.60, max_score=0.30)
    assert verdict == "DIAL-VISIBLE"  # delta 0.30 >= 0.15


def test_decide_inverted() -> None:
    verdict, _ = ldc.decide(anchor_score=0.20, max_score=0.50)
    assert verdict == "INVERTED"  # delta -0.30 <= -0.15


def test_decide_flat() -> None:
    verdict, _ = ldc.decide(anchor_score=0.40, max_score=0.35)
    assert verdict == "FLAT"  # |delta| < 0.15


def test_decide_pending_when_anchor_passes_floor_but_no_max_yet() -> None:
    verdict, _ = ldc.decide(anchor_score=0.40, max_score=None)
    assert verdict == "PENDING"


def test_needs_mid_point_only_on_signal() -> None:
    assert ldc.needs_mid_point(0.60, 0.30) is True    # |0.30| >= 0.15
    assert ldc.needs_mid_point(0.20, 0.50) is True    # inverted counts too (shape check)
    assert ldc.needs_mid_point(0.40, 0.35) is False   # flat -> no extra spend


def test_gate_thresholds_are_the_frozen_ones() -> None:
    # The pre-registered constants (qa-checklist) — a regression guard against silent edits.
    assert ldc.FLOOR == 0.10
    assert ldc.MARGIN == 0.15
    assert (ldc.POOL_ANCHOR, ldc.POOL_MID, ldc.POOL_MAX) == (1, 4, 8)
    assert ldc.WORLDS == 4


# -- curve_point (pool threading + schema) ---------------------------------------


def test_curve_point_threads_pool_and_reports_schema() -> None:
    counter = ldc.CountingComplete(_stub_complete("0"), budget=10_000)
    pt = ldc.curve_point(1, counter, worlds=1, sealed_kwargs=TINY_KWARGS)
    for key in ("pool", "worlds", "mean_distinct_types", "llm_se_rate", "llm_battle_moves",
                "oracle_se", "type_blind_se", "llm_score", "band_degenerate",
                "calls_this_point"):
        assert key in pt, f"missing key {key}"
    assert pt["pool"] == 1
    assert pt["mean_distinct_types"] == 1.0  # pool=1 => every world has exactly 1 boss type
    assert 0.0 <= pt["llm_score"] <= 1.0
    assert counter.calls > 0  # the stub LLM was actually driven through the worlds


def test_curve_point_pool_changes_measured_diversity() -> None:
    counter = ldc.CountingComplete(_stub_complete("0"), budget=10_000)
    lo = ldc.curve_point(1, counter, worlds=2, sealed_kwargs=TINY_KWARGS)
    hi = ldc.curve_point(8, counter, worlds=2, sealed_kwargs=TINY_KWARGS)
    assert hi["mean_distinct_types"] > lo["mean_distinct_types"]  # the knob actually turns


# -- run_protocol (gates end-to-end + artifact) -----------------------------------


def test_run_protocol_smoke_writes_artifact_and_spends_one_world(tmp_path: Path) -> None:
    out = tmp_path / "results.json"
    res = ldc.run_protocol(_stub_complete("0"), out_path=out, smoke=True,
                           worlds=1, sealed_kwargs=TINY_KWARGS, model_label="stub")
    assert out.exists()
    data = json.loads(out.read_text())
    assert data["protocol"]["floor"] == ldc.FLOOR
    assert data["protocol"]["margin"] == ldc.MARGIN
    assert data["model_label"] == "stub"
    assert data["gates"][0]["gate"] == "G-0"
    assert res["verdict"] == "SMOKE-ONLY"


def test_run_protocol_floor_stop_spends_no_pool_max_budget(tmp_path: Path) -> None:
    # A stub that always answers "5" (wait) never lands a super-effective move -> score ~0
    # -> the G-1 floor gate must stop BEFORE any pool=8 spend. (TINY at worlds=1 has a VALID
    # anchor band: oracle 1.00 vs blind 0.00 — so this exercises the floor path, not the guard.)
    out = tmp_path / "results.json"
    res = ldc.run_protocol(_stub_complete("5"), out_path=out, smoke=False,
                           worlds=1, sealed_kwargs=TINY_KWARGS, model_label="stub")
    assert res["verdict"] == "FLOOR-SATURATED"
    pools = [p["pool"] for p in res["points"]]
    assert ldc.POOL_MAX not in pools  # no pool=8 spend after the floor stop
    assert ldc.POOL_MID not in pools


def test_run_protocol_degenerate_band_is_not_a_floor_verdict(tmp_path: Path) -> None:
    # TINY at worlds=2 deterministically yields oracle==blind (band 0.00) at pool=1 — the
    # instrument-validity guard must report DEGENERATE-BAND (raw rates), never FLOOR-SATURATED,
    # and must stop before any pool=8 spend.
    out = tmp_path / "results.json"
    res = ldc.run_protocol(_stub_complete("5"), out_path=out, smoke=False,
                           worlds=2, sealed_kwargs=TINY_KWARGS, model_label="stub")
    assert res["verdict"] == "DEGENERATE-BAND"
    assert res["points"][0]["band_degenerate"] is True
    pools = [p["pool"] for p in res["points"]]
    assert ldc.POOL_MAX not in pools and ldc.POOL_MID not in pools
