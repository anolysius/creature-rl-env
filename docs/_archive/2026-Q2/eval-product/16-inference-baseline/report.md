---
slug: inference-baseline
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to:
  - docs/reference/inference-baseline.md
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# 보정 분포 위 inference baseline 확정 — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 변경 파일 | `eval_harness.py`(+inference_baseline/_arm_band/ArmBaseline/InferenceBaseline), `llm_eval_run.py`(--telemetry full band), `test_eval_harness.py`(+3), `docs/reference/inference-baseline.md`(신규) |
| 테스트 | 517 → **520 passed** (+3), 2 skipped, 회귀 0 |
| 타입/린트/빌드 | mypy 31 clean · ruff clean · build OK |
| 보정 band SE-rate (demo n8) | oracle **100%** > infer **90%** ≫ type_blind **7%** > probe **0%** |
| gym-clears | oracle 2.12 == **infer 2.12** (saturate) > type_blind 1.25 > probe 0.00 |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1** — `inference_baseline(sealed)` 4-arm 결정론 band. 3 신규 테스트(단조·결정론·앵커) PASS.
- ✅ **AC2** — 러너 `--telemetry` full 4-arm band(`inference_baseline` 경유). score_agent/score_inference_telemetry 본문 무변경 → 채점 byte-identical.
- ✅ **AC3** — 520 passed, 회귀 0, mypy/ruff/build clean.
- ✅ **AC4** — `docs/reference/inference-baseline.md`: 보정 band(2 config×2 n) + 고정 재측정 명령 + 정직 경고.

## 변경 파일 상세

### 수정 — `src/critter_gym/eval_harness.py` (+101 lines)
- 신규 `inference_baseline(sealed) -> InferenceBaseline` + `_arm_band`(per-world 격리 단일패스) + `ArmBaseline`/`InferenceBaseline` NamedTuple. 4 scripted arm(oracle/infer/type_blind/probe)의 gym_clears·se_rate·inference_score 반환. inference_score span 공식은 `score_agent` 재사용.
- **기존 score_agent/score_inference_telemetry 본문 무변경**(추가 함수만).

### 수정 — `scripts/llm_eval_run.py` (+14/−9)
- `--telemetry` 가 `inference_baseline` 로 full 4-arm band(oracle/infer/type_blind/probe + submission) 출력(기존 oracle/type_blind 2-arm → 4-arm). display-only. 미사용 `reference_arm` import 제거.

### 신규 — `tests/test_eval_harness.py` (+48), `docs/reference/inference-baseline.md`
- band 단조·결정론·inference_score 앵커 테스트. reference 문서.

## 발견된 이슈 (Green 측정 정직 보정)

- **[중] infer SE 39% → 90% (artifact 정정)** — plan 의 탐색 표는 `score_inference_telemetry`(reference arm reset 안 함=persist-across-seeds)로 infer SE 39%를 적었으나, 이는 **세계 간 stale 메모리 아티팩트**(이전 world 의 틀린 차트 기억으로 오-commit). 올바른 의미론(**per-world 격리**, learnability `_arm_means`·score_agent 내부 동작과 일치)으로 재측정 → infer SE **90%**. 헬퍼를 per-world 격리로 일관 구현.
- **[중] gym-clears saturate** — per-world 격리 시 infer gym-clears == oracle(2.12). 전투 `damage=max(1)` attrition 으로 *에피소드 내 학습 + 소모전*이 winnable gym 을 다 깸 → gym 기반 inference_score 가 둘 다 1.0 → **gym-clears 는 추론/전문가 변별 불가**(#12 confound 재확인). 결론: **SE-rate 가 변별자**. 테스트 앵커가 이를 박제(infer.se_rate > type_blind.se_rate 만 단정, infer inference_score strictly-between 단정 안 함).

## 흡수처 매핑 (extracted_to)

- `docs/reference/inference-baseline.md` — 보정 분포 band + 고정 재측정 프로토콜 + 정직 경계. evergreen reference(살아있는 사실표). cross-task 의존 없음(archive invariant 충족).

## 정직 경계 (AC4)

- band 는 **scripted proxy** — infer arm 은 추론 *에이전트 proxy* 이지 LLM 아님.
- single config·scripted-oracle proxy·작은 N → *신호*이지 LLM 능력 *verdict* 아님.
- 이전 LLM 수치(#11/#13/#14)는 옛 매치업-broken 분포 → 본 분포와 비교 금지. 재측정은 본 분포 위에서.
- 유료 LLM 실측은 평가자 로컬(구독/키=사용자). 전투 모델 재설계(attrition)는 사람 게이트.

## 타입 체크 / 빌드 결과
- mypy: Success, 31 files. ruff: clean. build: wheel+sdist OK. pytest: 520 passed, 2 skipped.

## 의존
- #15 `matchup-validity`(PR #84) 위 stacked(feature/inference-baseline off fix/matchup-validity). 서로 다른 파일 → 충돌 0. PR base=fix/matchup-validity → #84 머지 시 자동 main 리타깃.
