---
slug: multitype-boss-headroom
initiative: hard-benchmark
status: completed
ended: 2026-07-02
extracted_to:
  - docs/reference/multitype-boss.md
changelog_entry: docs/CHANGELOG.md
---

# 다중-타입 보스 헤드룸 — 다중-seed 사전약정 측정 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 추진 | hard-benchmark #5 — #4 scout 의 본측정 (사전약정, 3→5 seed 확충·임계 불변) |
| 수정/신규 | `headroom.py`(classify_depth 추가만) + 테스트 +6 + 측정 script 신규 + reference 갱신 |
| 테스트 | 620 → **626** (+6, 회귀 0) |
| lint/type | ruff All checks passed · mypy Success |
| L3 리뷰 | **2/2 APPROVE** |
| **판정 (A)** | **hard-for-memory-agent ROBUST** (다중-config, mean+std 1.25 ≪ 0.75·oracle 2.25) |
| **판정 (B)** | **inconclusive** — gap 3-run +9.0pp → 5-run **+2.4pp** 축소, scout 1-seed Δ 미생존 |

## 계획 대비 실적 (✅/⚠️/❌)

| AC | 결과 | 근거 |
|---|---|---|
| AC1 classify_depth+테스트 | ✅ | frozen 규칙 그대로(gap≤0→not-deeper 우선, winnable, gap>max std), 6 테스트(3 branch+경계), classify_headroom 무변경. |
| AC2 사전약정 freeze | ✅ | frac=0.75/k=1.0 + depth 규칙 + runs 3(→5 임계불변) — plan 고정, script 가 결과 전 규칙 출력(L3 확인: 데이터 계산보다 앞). |
| AC3 pilot | ✅ | `--quick --runs 1` 무오류, 양 config winnable, 양 판정 출력. |
| AC4 본측정 완주 | ✅ | 3-run(B inconclusive) → 사전약정 확충 경로로 5-run(임계 불변) → 최종 branch 그대로 보고(**반증 포함**). |
| AC5 회귀 0 | ✅ | 626 passed, ruff/mypy clean. |
| AC6 문서+CHANGELOG | ✅ | multitype-boss.md "Measured" 섹션(표+양 branch+정직 read), CHANGELOG 1줄(본 task-end). |

## 실측 (5 runs, 250 iters, CPU — 사전약정 그대로)

| config | oracle(winnable) | recurrent PPO | of oracle |
|---|---|---|---|
| single-type | 5.00 ✓ | 1.60±0.42 | 32%±8% |
| multi-type | 3.00 ✓ | 0.89±0.36 | 30%±12% |

- **(A) ROBUST**: 다중-타입 config 는 최강 agent(recurrent PPO)에게도 hard — mean+std 1.25 ≪ 2.25(#3 과 동일 임계). 절대 난이도 유지 + winnable.
- **(B) inconclusive**: fraction gap +2.4pp(std 8%/12% 안). **scout 의 1-seed Δ+3.4pp 는 노이즈였음** — 정규화하면 학습 agent 는 양쪽 config 에서 자기 oracle 대비 거의 같은 거리. 숨은 타입은 **천장을 낮추는 레버**(oracle 5.00→3.00, 절대 난이도↑)이지 **상대-깊이 레버로는 미입증**.
- **"multi-type 이 학습 agent 에게 더 깊다" 주장 금지** — 사전약정 verdict 가 inconclusive.

## 발견된 이슈

- **[정직성 핵심]** #17→#18(LLM SE 단일-run 50%→robust inconclusive)과 동일 패턴 재현: 1-seed 신호가 다중-seed 에서 미생존. scout→사전약정 본측정 2단 구조가 정확히 작동(측정 전에 헤드라인 안 씀). 후속: 깊이 질문은 open — 더 강하게 무는 config(타입 수↑ 등)는 **새 scout 선행** 후에만 측정 지출.
- **[프로세스]** plan-reviewer L1·L3 첫 호출 stall → verdict-first 재호출로 해소(기존 seeded proposal 이 근본 대응).

## 타입 체크 / 빌드 결과

`.venv/bin/python -m pytest` → 626 passed. ruff clean, mypy Success. pilot·본측정 exit 0.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 무엇 |
|---|---|
| `docs/reference/multitype-boss.md` | Measured 섹션 — 표·양 branch·정직 read·open 후속. scout 경고 대체. |
