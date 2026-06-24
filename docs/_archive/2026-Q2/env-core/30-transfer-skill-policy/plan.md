---
slug: transfer-skill-policy
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/genre_learned_transfer.py
  - tests/test_genre_learned_transfer.py
  - tests/**
  - DESIGN.md
extracted_to: []
supersedes: []
---

# transfer-skill-policy — 정책/obs 표현 개선으로 widened held-in 절대성능 끌어올리기 (a')

> 작성일: 2026-06-23 | 상태: 계획

## 목표

#28(transfer-rigor)이 입증한 한계: widened-train의 좁은 전이 gap은 대체로 **held-in 절대성능
하락**(generalist-mediocrity, widened held-in 0.9~2.1 ≪ #26 2.94) 탓이고, **예산·seed로는
held-in이 안 오른다**(compute 병목 아님). 남은 유일한 직접 경로 = **(a') 정책/obs 표현 개선**.

이 task는 **개선된 학습 설정이 widened held-in 절대성능을 올리는지** 측정한다. 구체 레버(현재
PPO는 `MultiInputPolicy`+기본 net+`n_steps=512`, **obs 정규화 없음**):
- **obs 정규화** — `player_hp`/`enemy_hp` bound가 10000, `player_level` 100 등 **큰 비정규화
  스칼라**가 net 학습을 해칠 가능성 큼. `VecNormalize`(obs) 또는 명시적 스케일링으로 정규화.
- **net 용량** — `policy_kwargs=dict(net_arch=...)`로 더 큰 net(3 family를 한 net이 감당).
- (옵션) 하이퍼파라미터(lr, n_steps, n_epochs) 약간 조정.

### ⚠️ 정직성 불변식 (freeze 규율)
- 성공 = **개선 설정의 held-in 효과를 측정+정직 보고**이지 "held-in을 올렸다/gap을 줄였다"가 아니다.
  - 개선 설정이 widened held-in을 #26(≈2.9) 쪽으로 유의히 올림 → confound 제거 경로 확보(양성).
    그 위에서 gap을 재측정해 (B) 신호의 *진짜* 강도를 본다.
  - held-in이 안 오름 → "**env가 본질적으로 어렵다 / 이 레버로는 부족** → 환경/정책 더 깊은 개선이
    다음"의 정직한 음성 결과(#28의 "compute로는 한계" 연장선).
- **freeze 전 pilot 필수** — "held-in을 올린다"는 주장형. pilot로 (i) 개선 설정이 1 fold에서
  held-in을 *올리는 방향*인지(특히 obs 정규화 효과), (ii) timing, (iii) 어느 결과든 정직 보고 가능
  확인. 가정 falsify(개선해도 안 오름) 시 정직 reframe.

### 마일스톤 매핑
- M5/moat 층2. M3 공개 EC보다 먼저(기능 준비 우선). G1에서 override 재확인.

## 선행 조건
- **#28 transfer-rigor(머지됨)** — `train_and_transfer`/`_loo`/`_loo_multirun`, `--runs N`,
  `MultiRunFoldReport`, 4 family 공유 obs. 이 위에 정책/obs 개선 노브를 얹는다.

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **개선 설정 노브** — `train_and_transfer`에 정책/obs 개선을 인자/플래그로 주입:
   (a) obs 정규화(`VecNormalize` obs-only, 또는 결정론 보장되는 명시 스케일링),
   (b) `policy_kwargs`(net_arch ↑). 기존 bare 설정은 baseline으로 보존(하위호환·대조).
2. **held-in 대조 측정** — baseline 설정 vs 개선 설정의 **widened held-in**을 같은 metric으로 대조
   (#26 2.94, #28 widened ~1.7-2.0 기준선). 개선이 held-in을 올리는지 수치로.
3. **(개선이 효과 있으면) gap 재측정** — 개선 설정의 multi-run LOO gap을 #28과 같은 축으로 보고
   (confound 줄어든 상태의 전이 신호). 효과 없으면 held-in 측정 + 정직 음성 보고까지.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | 개선 설정 노브(obs 정규화/net_arch) + baseline-vs-improved held-in 대조 + (효과 시) gap 재측정. `[rl]` | 중 — 실험 진입점 |
| `tests/test_genre_learned_transfer.py` | 개선 설정 smoke(importorskip, tiny) + 결정론/형태 가드 | 신규 케이스 |
| `DESIGN.md` §3.1.1 | held-in 개선 효과(양성/음성) 정직 반영 | 문서 |

### 영향 범위 (import 그래프)
- core CI numpy-only 유지(PPO `[rl]` 뒤 importorskip). 실측 비-CI 오프라인.
- `VecNormalize` 사용 시 **재현성** 주의: seed 고정 + obs 정규화 통계는 train 중만 갱신,
  eval 시 동결(`training=False`). RLVR(보상)은 손대지 않음 — obs 표현만.

## Step별 계획
1. **(freeze 전 pilot)** obs 정규화 + 더 큰 net을 1 fold(widened→muster)에 적용해 baseline 대비
   held-in이 *오르는지* + timing 확인. obs 정규화가 큰 hp/level 스케일 문제를 푸는지 우선 검증.
   효과 없으면(가정 falsify) 정직 reframe(레버 교체 또는 음성 보고로 scope 조정).
2. 개선 설정 노브 구현(TDD: Red smoke 먼저). baseline 보존.
3. baseline-vs-improved held-in 대조 출력(+ caveat). 효과 있으면 multi-run gap 재측정.
4. smoke 테스트(importorskip, tiny) + 결정론/형태 가드.
5. **실측 run**(오프라인 [rl]) → 결과 기록.
6. DESIGN §3.1.1 + CHANGELOG 정직 갱신(held-in 개선 효과 — 양성/음성 어느 쪽이든).

## 검증 방법
- pytest 전체 무회귀(194 유지/증가), mypy/ruff/build clean.
- `[rl]` smoke: 개선 설정이 tiny budget에서 finite held-in/gap 산출(importorskip), 결정론(seed 고정).
- 실측은 코드 근거 + ±std + caveat 동반(날조 0). #26(2.94)·#28(widened held-in)과 같은 metric.

## 리스크
- **R1 obs 정규화 재현성/결정론 깨짐** — `VecNormalize` 통계가 비결정 or eval 누수. → seed 고정 +
  eval 시 `training=False`·정규화 동결 + smoke 결정론 가드. RLVR 보상 불변.
- **R2 held-in 안 오름(가정 falsify)** — 개선 레버로도 부족. → 정직 reframe: "env가 본질 어려움/더
  깊은 개선 필요"(음성도 valid, #28 연장선). pilot로 사전 확인.
- **R3 compute 비용** — 개선 설정 × multi-run × fold. → pilot timing 후 예산/run/fold 현실적 freeze,
  silent 축소 금지. 1차는 held-in 대조(1 fold)로 효과 확인 후 full LOO.
- **R4 scope creep** — 커스텀 feature extractor/CNN/대규모 HPO까지 가면 비대. 이 task=obs 정규화 +
  net_arch + 약간의 HP까지. 더 깊은 아키텍처는 별도 후속.
- **R5 결과 과대해석** — held-in이 올라도 "전이 입증" 금지. gap 재측정도 ±std·단일config caveat 유지.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **개선 효과 측정 + 정직 보고**로 freeze. "held-in을 올렸다"가 acceptance가 아니다.

- **AC1** `train_and_transfer`에 **정책/obs 개선 노브**(obs 정규화 + `net_arch`↑)를 추가하고, 기존
  bare 설정을 baseline으로 보존(하위호환). 개선 on/off가 인자/플래그로 선택 가능.
- **AC2** **baseline vs 개선 설정의 widened held-in을 대조 측정**해 보고(#26 2.94·#28 widened 기준).
  결과를 정직 framing: held-in이 유의히 오름=confound 제거 경로(양성) / 안 오름=env 본질 어려움/레버
  부족(음성, 더 깊은 개선이 다음). ±std + caveat(단일config/저예산/N) 동반, 날조 0.
- **AC3** (개선이 held-in을 올렸을 때) 개선 설정의 multi-run LOO **gap을 #28과 같은 축**으로 재측정·보고
  (confound 줄어든 전이 신호). 효과 없으면 본 AC는 "held-in 미상승으로 gap 재측정 불요"로 정직 기록.
- **AC4** `[rl]` smoke(importorskip)로 개선 설정 무회귀 + **결정론**(seed 고정, eval 시 정규화 동결).
  core CI numpy-only 유지.
- **AC5** 기존 테스트 무회귀(194 유지/증가) + mypy/ruff/build clean.
- **AC6** DESIGN §3.1.1 정직 갱신(held-in 개선 효과 — 양성/음성) + M5/층2 매핑. CHANGELOG 1줄.
- **AC7** (freeze 전) pilot로 (i) 개선 설정의 held-in 방향(특히 obs 정규화 효과), (ii) timing,
  (iii) 결정론, (iv) 어느 결과든 정직 보고 가능 확인. 가정 falsify 시 plan 조정/reframe(새 slug 불요).
