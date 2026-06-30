"""The paper's one-command reproduction includes the §5 eval-product inference band.

`scripts/reproduce_results.py` regenerates the headline figures; this pins the new
eval-product section (the scripted band the frontier-LLM probe is read against, #16/#17),
so a reviewer can reproduce the §5 band figures — free and deterministic (no LLM)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import reproduce_results as repro  # noqa: E402

from critter_gym.eval_harness import InferenceBaseline  # noqa: E402


def test_inference_band_is_monotone_and_deterministic() -> None:
    """The reproduced band is the §5 ceiling->floor band, regenerated deterministically:
    oracle >= infer >= type_blind >= probe on super-effective-move rate, expert at 1.0."""
    band = repro.inference_band(quick=True)
    assert isinstance(band, InferenceBaseline)
    se = [band.arms[a].se_rate for a in ("oracle", "infer", "type_blind", "probe")]
    assert se == sorted(se, reverse=True), f"band not monotone: {se}"
    assert band.arms["oracle"].se_rate == 1.0
    assert repro.inference_band(quick=True) == repro.inference_band(quick=True)  # deterministic


def test_inference_band_quick_uses_fewer_worlds() -> None:
    """--quick scales the band down (fewer sealed worlds) for a fast smoke."""
    assert repro._demo_sealed(quick=True).n_worlds < repro._demo_sealed(quick=False).n_worlds
