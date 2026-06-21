#!/usr/bin/env python3
# domain: lifecycle
"""verdict_equivalence — reviewer 프롬프트 최적화의 품질 비저하 객관 게이지 (결정론 코어).

후속 프롬프트 최적화(W1 prefix 슬림화 / W2 캐시 복구 / W3 라우팅 정밀화)가
reviewer verdict 품질을 떨어뜨리지 않았음을 **주장이 아니라 증명**하기 위한 게이지.

3분리 아키텍처 (plan §설계):
  [1] 결정론 코어 (본 모듈, 단위테스트 가능)
        - load_corpus       : corpus.json 파싱
        - build_prompts     : reviewer_prompt.py / qa_verifier_prompt.py 위임으로 프롬프트 생성
        - run_decision      : aggregate-verdicts.py 파서 재사용 → 단일 decision 환원
        - ingest_results    : operator 가 적재한 jsonl → Run 리스트
        - diff_runs         : decision 분포 비교 + known-issue recall
        - gate              : PASS/FAIL 판정
        - build_report      : 사람용 markdown (raw 본문 미포함 — 커밋 안전)
  [2] agent 스폰 (operator/thin workflow — LLM, 본 모듈 밖)
  [3] 코어가 결과 ingest → 리포트 + PASS/FAIL

재사용 (수정 0):
  - _lib/reviewer_prompt.py      (build_reviewer_prompt)        — 평범 import (동일 디렉토리)
  - _lib/qa_verifier_prompt.py   (build_self_contained_prompt)  — 평범 import
  - task-evaluate/scripts/aggregate-verdicts.py (parse_verdicts_with_fallback)
      → **하이픈 파일명이라 평범한 import 불가 → importlib.util.spec_from_file_location 로 file-path 로딩**
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_LIB_DIR = Path(__file__).resolve().parent

# ─── 재사용 helper import ──────────────────────────────────────────────
# 동일 디렉토리(_lib) — sys.path 보장 후 평범 import
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))

import reviewer_prompt as _reviewer_prompt  # noqa: E402
import qa_verifier_prompt as _qa_verifier_prompt  # noqa: E402


_AGG_CACHE = None


def _get_agg():
    """aggregate-verdicts.py 를 file-path 로딩 (하이픈 파일명 → 평범 import 불가).

    lazy + 캐시 — 모듈 최상위에서 즉시 실행하지 않아 partial checkout(파서 파일 부재)
    환경에서도 import 자체는 성공. 파서가 실제 필요한 호출(run_decision) 시점에만 로딩.
    """
    global _AGG_CACHE
    if _AGG_CACHE is None:
        path = _LIB_DIR.parent / "task-evaluate" / "scripts" / "aggregate-verdicts.py"
        spec = importlib.util.spec_from_file_location("aggregate_verdicts", path)
        if spec is None or spec.loader is None:
            raise ImportError(f"aggregate-verdicts.py 로딩 실패: {path}")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _AGG_CACHE = mod
    return _AGG_CACHE

# ─── decision severity 순서 ────────────────────────────────────────────
_SEVERITY = {"APPROVE": 0, "SUGGEST": 1, "BLOCK": 2}


# ─── 데이터 모델 ───────────────────────────────────────────────────────
@dataclass
class CorpusItem:
    id: str
    reviewer: str                               # plan-reviewer | qa-verifier
    expected_min_decision: str = "APPROVE"      # known-issue 가 최소 잡아야 하는 decision
    source: Optional[str] = None                # archive plan 경로 (repo 상대)
    source_inline: Optional[str] = None         # inline plan/위반 텍스트 (합성 known-issue)
    known_issue: bool = False
    purpose: str = "L1"
    axes: List[str] = field(default_factory=list)


@dataclass
class Corpus:
    items: List[CorpusItem]
    thresholds: Dict[str, float] = field(default_factory=dict)


@dataclass
class Run:
    item_id: str
    variant: str                                # "control" | "candidate"
    decision: Optional[str]                     # APPROVE | SUGGEST | BLOCK | None(MALFORMED)
    known_issue: bool = False
    expected_min_decision: str = "APPROVE"
    run_index: int = 0


DEFAULT_THRESHOLDS = {
    "t_match_overall": 0.9,
    "t_match_known_issue": 1.0,
}


# ─── verdict → 단일 decision (aggregate-verdicts 파서 위임) ─────────────
def run_decision(verdict_text: str, agent_name: Optional[str] = None) -> Optional[str]:
    """reviewer 1회 출력 텍스트 → 단일 decision 으로 환원.

    aggregate-verdicts.py 의 parse_verdicts_with_fallback (3-tier) 재사용.
    per-axis + summary 가 섞여 있으면 severity precedence 로 가장 엄격한 것 채택
    (BLOCK > SUGGEST > APPROVE) — aggregator 의 BLOCK 우선 정책과 일치.
    파싱 0건(MALFORMED) → None.
    """
    verdicts = _get_agg().parse_verdicts_with_fallback(verdict_text, agent_name)
    if not verdicts:
        return None
    return max((v["kind"] for v in verdicts), key=lambda k: _SEVERITY[k])


# parse_verdict 별칭 (plan 명세 이름)
parse_verdict = run_decision


# ─── corpus 로드 ───────────────────────────────────────────────────────
def load_corpus(path) -> Corpus:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    raw_items = data.get("items", [])
    if not raw_items:
        raise ValueError(f"corpus 에 items 가 비어 있음: {path}")
    items = []
    for it in raw_items:
        if "id" not in it or "reviewer" not in it:
            raise ValueError(f"corpus item 에 id/reviewer 필수: {it}")
        items.append(CorpusItem(
            id=it["id"],
            reviewer=it["reviewer"],
            expected_min_decision=it.get("expected_min_decision", "APPROVE"),
            source=it.get("source"),
            source_inline=it.get("source_inline"),
            known_issue=it.get("known_issue", False),
            purpose=it.get("purpose", "L1"),
            axes=it.get("axes", []),
        ))
    thresholds = {**DEFAULT_THRESHOLDS, **data.get("thresholds", {})}
    return Corpus(items=items, thresholds=thresholds)


# ─── 프롬프트 생성 (helper 위임) ───────────────────────────────────────
def _item_plan_text(item: CorpusItem, repo_root: Optional[Path]) -> str:
    if item.source_inline is not None:
        return item.source_inline
    if item.source:
        base = repo_root or _LIB_DIR.parent.parent.parent  # repo root 추정
        return (Path(base) / item.source).read_text(encoding="utf-8")
    raise ValueError(f"item {item.id}: source 또는 source_inline 필요")


def build_prompts(item: CorpusItem, variant: str,
                  variant_overrides: Optional[Dict] = None,
                  repo_root: Optional[Path] = None) -> str:
    """item × variant 의 reviewer 프롬프트 생성 (helper 위임).

    variant_overrides: candidate 변형 적용용 (후속 W1/W2/W3 task 가 주입).
        v1 (본 task) 은 control/candidate 동일 — overrides 없으면 helper 원본.
    """
    overrides = variant_overrides or {}
    plan_text = _item_plan_text(item, repo_root)

    if item.reviewer == "qa-verifier":
        prompt = _qa_verifier_prompt.build_self_contained_prompt(
            purpose=item.purpose,
            inline_data={"plan": plan_text, **overrides.get("inline_data", {})},
            axes=item.axes or ["acceptance 정합", "scope", "회귀"],
        )
    else:
        prompt = _reviewer_prompt.build_reviewer_prompt(
            agent=item.reviewer,
            purpose=item.purpose,
            variable={"plan": plan_text, **overrides.get("variable", {})},
            axes=item.axes or ["scope", "impact", "risk", "verification", "deliverables"],
        )
    return prompt


# ─── 결과 ingest ───────────────────────────────────────────────────────
def ingest_results(path) -> List[Run]:
    """operator 가 적재한 jsonl → Run 리스트. verdict_text 는 run_decision 으로 환원.

    각 줄: {item_id, variant, run_index, verdict_text, known_issue?, expected_min_decision?}
    """
    path = Path(path)
    runs: List[Run] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        runs.append(Run(
            item_id=rec["item_id"],
            variant=rec["variant"],
            decision=run_decision(rec.get("verdict_text", ""), rec.get("agent")),
            known_issue=rec.get("known_issue", False),
            expected_min_decision=rec.get("expected_min_decision", "APPROVE"),
            run_index=rec.get("run_index", 0),
        ))
    return runs


# ─── diff (decision 분포 + known-issue recall) ─────────────────────────
def _majority_decision(decisions: List[str]) -> Optional[str]:
    """다수결 decision. 동률 시 더 엄격한 것 (보수적)."""
    valid = [d for d in decisions if d in _SEVERITY]
    if not valid:
        return None
    counts = Counter(valid)
    top = max(counts.values())
    tied = [d for d, c in counts.items() if c == top]
    return max(tied, key=lambda k: _SEVERITY[k])


def _catches(decision: Optional[str], expected_min: str) -> bool:
    """known-issue 를 잡았나 — decision severity ≥ expected_min severity."""
    if decision not in _SEVERITY:
        return False
    return _SEVERITY[decision] >= _SEVERITY[expected_min]


def diff_runs(runs: List[Run]) -> Dict:
    """control vs candidate decision 분포 비교 + known-issue recall.

    decision_match (per item): candidate 가 control 대비 **악화되지 않음**
        (candidate majority severity ≥ control majority severity).
        control BLOCK/SUGGEST → candidate APPROVE 떨굼 = 악화 = 불일치.
    known_issue_recall (per variant): known-issue item 의 run 중 expected_min 이상 잡은 비율.
    """
    # item_id → variant → [decision...]
    by_item: Dict[str, Dict[str, List[str]]] = {}
    known_issue_items = set()
    for r in runs:
        by_item.setdefault(r.item_id, {}).setdefault(r.variant, []).append(r.decision)
        if r.known_issue:
            known_issue_items.add(r.item_id)

    # ── decision-match ──
    matched_overall = 0
    counted_overall = 0
    matched_ki = 0
    counted_ki = 0
    per_item = {}
    for item_id, variants in by_item.items():
        ctrl = _majority_decision(variants.get("control", []))
        cand = _majority_decision(variants.get("candidate", []))
        if ctrl is None or cand is None:
            # 한쪽이라도 비면 비교 불가 — 집계 제외 (리포트에 표기)
            per_item[item_id] = {"control": ctrl, "candidate": cand, "comparable": False}
            continue
        not_worsened = _SEVERITY[cand] >= _SEVERITY[ctrl]
        per_item[item_id] = {
            "control": ctrl, "candidate": cand,
            "comparable": True, "matched": not_worsened,
        }
        counted_overall += 1
        matched_overall += 1 if not_worsened else 0
        if item_id in known_issue_items:
            counted_ki += 1
            matched_ki += 1 if not_worsened else 0

    # ── known-issue recall (run 단위) ──
    recall = {}
    for variant in ("control", "candidate"):
        catch = total = 0
        for r in runs:
            if r.known_issue and r.variant == variant and r.decision is not None:
                total += 1
                catch += 1 if _catches(r.decision, r.expected_min_decision) else 0
        recall[variant] = (catch / total) if total else None

    return {
        "decision_match_rate_overall": (matched_overall / counted_overall) if counted_overall else None,
        "decision_match_rate_known_issue": (matched_ki / counted_ki) if counted_ki else None,
        "known_issue_recall": recall,
        "per_item": per_item,
        "n_items": len(by_item),
        "n_known_issue_items": len(known_issue_items),
    }


# ─── gate ──────────────────────────────────────────────────────────────
def gate(diff: Dict, thresholds: Optional[Dict] = None) -> Dict:
    """PASS/FAIL 판정.

    PASS iff:
      decision_match_rate_overall      ≥ t_match_overall (0.9)
      AND decision_match_rate_known_issue == t_match_known_issue (1.0)  [known-issue 있을 때만]
      AND known_issue_recall(candidate) ≥ known_issue_recall(control)   [둘 다 측정됐을 때만]
    """
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    reasons: List[str] = []

    overall = diff.get("decision_match_rate_overall")
    if overall is None:
        reasons.append("decision_match_rate_overall 측정 불가 (comparable item 0)")
    elif overall < t["t_match_overall"]:
        reasons.append(
            f"decision_match_rate_overall {overall:.3f} < {t['t_match_overall']}"
        )

    ki = diff.get("decision_match_rate_known_issue")
    if ki is not None and ki < t["t_match_known_issue"]:
        reasons.append(
            f"decision_match_rate_known_issue {ki:.3f} < {t['t_match_known_issue']}"
        )

    recall = diff.get("known_issue_recall", {})
    rc, rk = recall.get("control"), recall.get("candidate")
    if rc is not None and rk is not None and rk < rc:
        reasons.append(
            f"known_issue_recall 악화: candidate {rk:.3f} < control {rc:.3f}"
        )

    return {
        "passed": len(reasons) == 0,
        "reasons": reasons,
        "thresholds": t,
        "metrics": {
            "decision_match_rate_overall": overall,
            "decision_match_rate_known_issue": ki,
            "known_issue_recall": recall,
        },
    }


# ─── 리포트 (커밋 안전: decision 라벨·집계만, raw 본문 0) ───────────────
def _fmt(v) -> str:
    return "—" if v is None else f"{v:.3f}"


def build_report(diff: Dict, gate_result: Dict) -> str:
    verdict = "PASS ✅" if gate_result["passed"] else "FAIL ❌"
    lines = [
        "# Verdict-Equivalence 리포트",
        "",
        f"**게이트: {verdict}**",
        "",
        "## 집계 지표",
        "",
        "| 지표 | 값 | 임계 |",
        "|---|---|---|",
        f"| decision_match_rate_overall | {_fmt(diff.get('decision_match_rate_overall'))} | ≥ {gate_result['thresholds']['t_match_overall']} |",
        f"| decision_match_rate_known_issue | {_fmt(diff.get('decision_match_rate_known_issue'))} | = {gate_result['thresholds']['t_match_known_issue']} |",
        f"| known_issue_recall (control) | {_fmt(diff.get('known_issue_recall', {}).get('control'))} | baseline |",
        f"| known_issue_recall (candidate) | {_fmt(diff.get('known_issue_recall', {}).get('candidate'))} | ≥ control |",
        "",
        f"- 비교 item 수: {diff.get('n_items')} (known-issue {diff.get('n_known_issue_items')})",
    ]
    if not gate_result["passed"]:
        lines += ["", "## FAIL 사유"] + [f"- {r}" for r in gate_result["reasons"]]

    # per-item decision 라벨만 (raw verdict 본문 미포함)
    lines += ["", "## item 별 decision (라벨만)", "",
              "| item | control | candidate | 악화? |", "|---|---|---|---|"]
    for item_id, rec in diff.get("per_item", {}).items():
        worsened = "—"
        if rec.get("comparable"):
            worsened = "❌ 악화" if not rec.get("matched") else "OK"
        lines.append(
            f"| {item_id} | {rec.get('control') or '—'} | {rec.get('candidate') or '—'} | {worsened} |"
        )
    return "\n".join(lines)


# ─── CLI ───────────────────────────────────────────────────────────────
def main() -> int:
    p = argparse.ArgumentParser(description="verdict-equivalence 게이지 (결정론 코어)")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("report", help="results.jsonl ingest → diff → gate → 리포트")
    pr.add_argument("--results", required=True)
    pr.add_argument("--corpus", default=None, help="thresholds 출처 (선택)")

    bp = sub.add_parser("build-prompts", help="corpus item 의 프롬프트 출력")
    bp.add_argument("--corpus", required=True)
    bp.add_argument("--item", required=True)
    bp.add_argument("--variant", default="control")

    args = p.parse_args()

    if args.cmd == "report":
        runs = ingest_results(args.results)
        diff = diff_runs(runs)
        thresholds = None
        if args.corpus:
            thresholds = load_corpus(args.corpus).thresholds
        result = gate(diff, thresholds)
        print(build_report(diff, result))
        return 0 if result["passed"] else 1

    if args.cmd == "build-prompts":
        corpus = load_corpus(args.corpus)
        item = next((i for i in corpus.items if i.id == args.item), None)
        if item is None:
            print(f"item 없음: {args.item}", file=sys.stderr)
            return 2
        print(build_prompts(item, args.variant))
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
