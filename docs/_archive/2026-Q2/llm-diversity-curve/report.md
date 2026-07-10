---
slug: llm-diversity-curve
initiative: null
status: completed
ended: 2026-07-09
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# LLM 다양성 곡선 — 결과 보고서 (DIAL-VISIBLE, 비단조 중간점 경고 동반)

## 요약 (수치 표)

scripted 밴드가 calibration 불가(infer arm saturated)임을 확인한 두 scout의 후속 — **진짜 불완전
추론자(LLM)로 `boss_pool_size` sweep을 재측정**. 사용자 승인 quota(claude-cli 구독), 사전약정
게이트 프로토콜(G-0 smoke → G-1 floor → G-2 Δ → G-3 조건부) 그대로 완주.

| 항목 | 결과 |
|---|---|
| 테스트 | **770 → 785** (+15 stub 메커니즘, 회귀 0), ruff clean, **src 무변경** |
| 지출 | **1,200콜 / 상한 1,820** (G-0 65 · G-1 257 · G-2 318 · G-3 560), 평균 5.5–9.2s/콜 |
| 파싱 실패 | **0 / 1,200** (fable-5가 액션 형식을 완벽 준수) |
| G-1 (pool=1, 재발생 최대) | **llm_score 0.68** (SE 81%, 68 moves; oracle 1.00·blind 0.39) — floor 통과 |
| G-2 (pool=8, 다양성 최대) | **llm_score 0.47** (SE 50%, 102 moves; blind 0.05) |
| G-3 (pool=4, 중간) | llm_score 1.00 ⚠️ (SE 100%, **22 moves — 표본 1/3~1/5**) |
| **사전약정 verdict** | **DIAL-VISIBLE** — Δ(양끝) = **+0.21 ≥ 0.15** |

**정직 결론(SIGNAL)**: **per-episode 타입 다양성은 이 불완전 추론자에게 실제 난이도 다이얼이다** —
양끝점에서 정규화 점수 0.68→0.47(+0.21), 원시 SE-rate도 81%→50%(정규화 인공물 아님). 같은 sweep에서
scripted infer arm은 0.96→0.92로 평평했으므로, **"난이도 곡선은 불완전 추론자에게만 보인다"는
meta-가설이 실측 확증**됨 — scripted 밴드=검증용, calibration=LLM/학습 arm 필요. 판매 티어 난이도
레버(`boss_pool_size`)의 첫 실증.

**경고 1 (비단조 중간점)**: G-3(pool=4)가 1.00으로 앵커(0.68)보다 높음 — 단 전투 move 22개뿐
(G-3는 560콜을 다 썼지만 대부분 overworld 배회 = pool별 에피소드 역학 차이)이라 단일-run 노이즈
가능성이 큼. **정확한 클레임 = "양끝점 gap 입증(endpoint rule, frozen)"이지 "매끈한 단조 곡선"이
아님.** 곡선 형태 확정은 다중 run/worlds 재측정(후속) 필요.

**경고 2 (한정)**: 단일 run · 4 worlds/point(scripted 곡선 8보다 작음) · 1 모델(fable-5, claude-cli
기본) · 1 provider · 오차막대 없음(LLM 확률적). "이 모델·이 설정"의 SIGNAL — "LLM 일반" 아님.
헤드라인 금지.

**부수 관찰**: blind floor가 pool과 함께 붕괴(0.39→0.28→0.05) — 고정-리드 커버리지가 타입 수에
희석되는 #9의 메커니즘과 정합. G-1 결과(0.68)는 아레나 inconclusive와 대조적 — overworld+체육관
설정에선 fable-5의 상성 추론 신호가 뚜렷.

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 게이트 러너 + src 무변경 | ✅ | llm_diversity_curve.py — 프로토콜·예산 카운터·규칙 선출력·JSON flush |
| AC2 stub 테스트 + 무회귀 | ✅ | 15 케이스(게이트 분기·예산·pool 스레딩·스키마·**DEGENERATE-BAND 가드**), 785 green |
| AC3 smoke 실측 보고 | ✅ | G-0: 61~65콜·7.6~9.2s/콜·파싱 실패 0 → 본측정 진입 |
| AC4 게이트 그대로 준수 | ✅ | G-1 floor 통과→G-2 Δ판정→G-3(\|Δ\|≥0.15 충족으로 집행), 마진·grid 사후 변경 0 |
| AC5 정직 라벨 + 박제 | ✅ | 본 report + `results.json`(전체 게이트·프로토콜 상수·모델 라벨) |

**프로토콜 수정 1건(투명 공개)**: G-0 smoke가 1-world 밴드 퇴화(oracle==blind=1.0 → 점수 무의미
클램프)를 드러내 **G-1 데이터 전**에 `EPS_BAND=0.05` DEGENERATE-BAND 가드 추가(거짓 FLOOR-SATURATED
방지). 계측기 유효성 게이트 — smoke의 존재 이유이며 stub 테스트로 고정. 본측정에선 미발동(G-1 밴드
0.61·G-2 0.95 정상).

## 변경 파일 상세

- `scripts/llm_diversity_curve.py` (+~280, 신규): 게이트 러너. 첫 실행에서 `claude_cli_complete`가
  팩토리(첫 인자=바이너리)임을 놓친 인자 버그 1건 — quota 지출 0에서 즉시 실패, 수정 후 프로브
  1콜로 확인. cmux shim 회피 위해 `--claude-bin` 플래그 추가(실 바이너리 경로).
- `tests/test_llm_diversity_curve.py` (+~180, 신규): stub 15 테스트(quota 0·CI-safe).
- `docs/_active/llm-diversity-curve/results.json`: 측정 아티팩트(재현 메타 포함) — archive에 동반.

## 발견된 이슈 (심각도)

- **[중/후속] 비단조 중간점**: pool=4가 1.00(22 moves) — 단일-run 노이즈 vs 진짜 비단조 미구분.
  곡선 형태 확정은 다중 run 재측정(quota·사람 게이트) 후속.
- **[낮음/관찰] pool별 overworld 역학 차이**: G-3가 560콜(상한)을 쓰고도 전투 22 move — pool이
  에피소드의 전투 밀도를 바꿈. telemetry 표본 크기를 pool마다 다르게 만듦(위 노이즈의 원인).

## 흡수처 매핑 (extracted_to)

**흡수 없음(빈 배열)** — 결과는 SIGNAL(단일 run), reference로 굳힐 단계 아님(다중 run 재측정 선행).
INITIATIVE 없음(단발). **후속 후보**(사람 게이트): (a) 다중 run/worlds로 곡선 형태 확정, (b) Fable5
커뮤니티 리더보드 정식 측정(≤1,600콜, 보류 중), (c) 사이트/문서에 "다이얼 실증" 반영은 재측정 후.

## 타입 체크 / 빌드 결과

- `pytest`: 785 passed, 0 regression. `ruff`: clean. mypy: 대상 무변경(src 무변경).
