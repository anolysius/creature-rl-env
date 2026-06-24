---
slug: transfer-skill-policy
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - docs/explanation/genre-generalization.md   # (B) 스레드 학술 narrative 박제(initiative-level 흡수)
changelog_entry: docs/CHANGELOG.md (env-core, transfer-skill-policy)
---

# transfer-skill-policy (a') — 정책/obs 개선의 held-in 효과 — 결과 보고서 (정직한 음성)

## 요약 — baseline vs improved widened held-in (50k × 5 run, N16)

| fold | baseline held-in (±std) | improved held-in (±std) | Δ |
|---|---|---|---|
| critter | 0.863 ±0.392 | 0.654 ±0.223 | −0.21 |
| forage | 0.917 ±0.186 | 0.675 ±0.155 | −0.24 |
| duel | 1.738 ±0.204 | 1.096 ±0.594 | −0.64 |
| muster | 1.733 ±0.502 | 1.150 ±0.381 | −0.58 |

(improved = `net_arch=[256,256]` + 결정론적 대형키 obs 스케일. #26 single-family held-in 2.94 기준.)

## 정직한 결과 (음성)

- **개선 설정이 widened held-in을 올리지 못함 — 4 fold 전부에서 *낮춤*** (delta 대부분 run-std 초과 = robust).
- 원인: net256 + 입력 스케일 변경은 50k 소예산에서 **underfit**(큰 net은 더 많은 데이터 필요).
- **pilot 기여**: whole-obs `VecNormalize`가 범주형 obs(in_battle/local_patch/type)를 망쳐 *해롭다*는 것을
  pilot이 robust하게 밝힘(held-in 0.139) → 제외하고 선택 스케일로 정련(AC7 사전등록 분기). 그러나 정련된
  설정조차 held-in을 못 올림.
- **종합 verdict**: **compute(#28)도, 이 정책/obs 레버(이 task)도 widened held-in을 #26(2.9) 쪽으로 못 올린다.**
  → generalist-mediocrity confound는 **stubborn하게 잔존**. (B) genre-transfer는 여전히 *신호*. confound 제거엔
  더 깊은 작업(커스텀 아키텍처/커리큘럼/용량+예산, 또는 "이 스케일서 env가 본질적으로 어렵다" 수용)이 필요 —
  값싼 레버로는 안 됨. 이 task가 그 두 값싼 경로(compute, 단순 정책/obs)를 **정직하게 닫았다**.

## 계획 대비 실적 (✅)

| AC | 상태 | 근거 |
|---|---|---|
| AC1 개선 노브(net_arch+scale_obs)+bare baseline 보존 | ✅ | `train_and_transfer(..., net_arch=, scale_obs=)`+`_ScaleObs`+`--improved`, 기본 off=baseline |
| AC2 baseline vs 개선 held-in 대조 + 정직 framing(음성) | ✅ | 위 표, 4 fold 전부 improved≤baseline robust, "env 본질 어려움/레버 부족" 음성 보고 |
| AC3 (조건부) held-in 올랐을 때만 gap 재측정 | ✅ | held-in 미상승 → **gap 재측정 불요** 정직 기록(조건 충족 안 됨) |
| AC4 [rl] smoke + 결정론(seed 고정·스케일 결정론) | ✅ | `test_improved_policy_config_smoke_and_deterministic`(같은 seed→동일 결과 assert) |
| AC5 무회귀 + 툴체인 | ✅ | 194→195 passed, mypy 22/ruff/build clean, core numpy-only |
| AC6 DESIGN §3.1.1 정직 갱신(음성)+M5+CHANGELOG | ✅ | transfer-skill-policy 음성 verdict 단락 추가 |
| AC7 freeze 전 pilot(held-in 방향/timing/결정론) | ✅ | pilot: vecnorm-whole 해로움 배제·net/스케일은 단일seed 노이즈→multi-run 필요 확정; timing ~14-30s/fold |

## 변경 파일 상세
**수정**
- `scripts/genre_learned_transfer.py` — `_LARGE_OBS_KEYS`/`_obs_scales`/`_scale_obs`/`_ScaleObs`(결정론 스케일) + `train_and_transfer`/`_loo`/`_loo_multirun`에 `net_arch`/`scale_obs` 노브 + `--improved` CLI(config 라벨). `import numpy as np` 이미 모듈화.
- `tests/test_genre_learned_transfer.py` — `test_improved_policy_config_smoke_and_deterministic`(개선설정 동작+결정론+baseline 하위호환).
- `DESIGN.md` §3.1.1 — 정책/obs 개선 음성 결과 반영(vecnorm 배제·held-in 못 올림·confound stubborn).

## 발견된 이슈 (심각도)
- (방법론) whole-obs 정규화는 범주형 obs를 가진 환경에서 해로움 — 대형 연속 키만 선택 스케일해야. pilot이 사전 차단.
- (음성 결과) 값싼 레버(compute·단순 정책/obs)로는 widened held-in 회복 불가 입증 → 다음은 더 비싼/깊은 접근.

## 정직한 한계 / 다음 task
- 단일 config·N16·결정론 보스·50k = 신호. 더 큰 예산+큰 net 조합은 미탐(이번 50k 한정).
- 다음 후보(더 깊은 접근, 비용↑): (a) 큰 net을 **충분한 예산**으로(net+budget 동시 스케일) held-in 회복 시도,
  (b) 메커닉-범용 obs 인코딩(family 식별자/구조 피처), (c) 커리큘럼(easy family→hard), (d) 5~6 family 확장.
  또는 (e) 현 결과로 (B)를 "신호+정직 한계"로 패키징하고 다른 갭(난이도/JAX)으로 전환.

## 타입 체크 / 빌드 결과
- pytest 195 passed, 2 skipped · mypy 22 files clean · ruff clean · build OK.
