---
slug: genre-transfer-policy
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/genre_learned_transfer.py
  - src/critter_gym/genre_generalization.py
  - tests/test_genre_learned_transfer.py
  - tests/**
  - DESIGN.md
extracted_to: []
supersedes: []
---

# 전이하는 학습 정책 — widened train distribution으로 unseen-family 전이 gap 측정

> 작성일: 2026-06-23 | 상태: 계획

## 목표

obs 조화(task 26, PR #32)로 4 family가 한 obs 공간을 공유하게 됐다. 이제 **train 분포를
넓혀(duel 포함) 학습한 정책이 unseen family로 전이하는지**를 측정한다 — #26이 측정한 전이
gap(train{A,B}→held-out{D} = **+2.56**, 전이 실패)을 기준선으로, **더 많은/다양한 family를
train 분포에 넣으면 unseen family 전이 gap이 줄어드는가**를 leave-one-out으로 측정한다.

이것은 "전이하는 학습 정책" 이니셔티브(moat 층2)의 **층2 핵심 측정**이다. (B)를 토대→주장으로
옮기려는 시도다.

### ⚠️ 정직성 불변식 (가장 중요 — freeze 규율)
- 이 task의 성공은 **"gap을 줄였다"가 아니다**. 성공 = **정직한 측정 + 보고**다.
  - gap이 줄면 → (B)가 주장으로 이동하는 **양성 신호**(증명 아님).
  - gap이 안 줄면 → "**widened train으로도 학습 genre 전이는 어렵다 = (B) 여전히 미해결**"의
    정직한 음성 신호.
  - 둘 다 valid한 결과. acceptance는 *결과값*이 아니라 *측정 머신 + 정직 보고*로 freeze.
- **freeze 전 pilot 필수** — "gap을 줄인다"는 주장형이므로, pilot로 (a) widened-train LOO가
  저예산에서 돌아가고 신호를 내는지, (b) 어떤 framing이든 정직히 보고 가능한지 확인. pilot이
  가정(예: "더 많은 family면 당연히 전이")을 falsify하면 정직 reframe(난이도 task 선례).

### 마일스톤 매핑
- M5/moat 층2(genre generalization surface). M3 공개 EC보다 먼저(기능 준비 우선 방침). G1에서
  override 재확인.

## 선행 조건
- **task 26 `obs-harmonization`(PR #32)** — 4 family 공유 obs. 이 task는 그 위에서 작동
  (현재 `feature/genre-transfer-policy`는 obs-harmonization HEAD 기준 브랜치; #32 머지 후 rebase).
- 기존: `train_and_transfer`(PPO MultiInputPolicy + `_MultiFamilyEnv`), `measure_genre_generalization_loo`,
  `split_train_pool`/`heldout_seeds`, family registry 4종.

## 작업 범위

### 핵심 설계 (L1/pilot로 정련)
1. **widened-train LOO 전이 실험**: 4 family에 대해 leave-one-out — 각 family를 held-out으로
   두고 나머지 3 family(duel 포함 가능)에 PPO 학습 → held-out family 전이 gap 측정. #26의
   2-family train(→+2.56)과 **train 분포 폭의 효과**를 대조.
2. **정직 비교 축**: (a) #26 baseline(train{A,B}→D) vs (b) widened(train{A,B,C}→D 등) gap 비교.
   "train에 family 추가가 unseen 전이 gap을 줄이는가"를 *수치로* 보고(±std, 단일run caveat).
3. (옵션, pilot 결과 따라) 메커닉-범용 정책/obs 표현 개선은 별도 후속으로 분리 가능 —
   scope creep 방지. 이 task는 **widened-train LOO 측정 + 정직 보고**가 코어.

### 수정 대상 파일 (영향도 표)
| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` | LOO 전이(`train_and_transfer_loo` 또는 multi-fold) + duel 포함 train + #26 대조 출력. `[rl]` | 중 — 실험 진입점 |
| `src/critter_gym/genre_generalization.py` | (필요 시) LOO 헬퍼 재사용/확장 점검 | 저 |
| `tests/test_genre_learned_transfer.py` | widened-train LOO smoke(importorskip) + 4 family fold 구성 | 신규 케이스 |
| `DESIGN.md` §3.1.1 | 실측 결과 정직 반영(양성/음성 어느 쪽이든) | 문서 |

### 영향 범위 (import 그래프)
- core CI는 numpy-only 유지(PPO는 `[rl]` 뒤 importorskip). 실제 학습 run은 비-CI 오프라인.

## Step별 계획
1. **(freeze 전 pilot)** widened-train LOO를 저예산(timesteps 작게, N 작게)으로 1 fold 돌려
   (a) 동작·신호 유무, (b) #26 대비 비교 가능성, (c) 정직 framing 확인. 가정 falsify 시 reframe.
2. `train_and_transfer`를 LOO/multi-fold로 확장(TDD: Red smoke 먼저). duel 포함 train 분포.
3. #26 baseline 대조 출력 + ±std + caveat(단일run/저예산/N).
4. smoke 테스트(importorskip) + 4 family fold 구성 가드.
5. **실측 run**(오프라인 [rl], 적정 예산) → 결과 기록.
6. DESIGN §3.1.1 + CHANGELOG 정직 갱신(결과가 양성이면 신호, 음성이면 "여전히 미해결").

## 검증 방법
- `python3 -m unittest`/pytest 전체 무회귀(192 유지/증가), mypy/ruff/build clean.
- `[rl]` smoke: widened-train LOO가 tiny budget에서 finite gap 산출(importorskip).
- 실측 결과는 코드 근거 + ±std + caveat 동반(날조 0). #26 +2.56과 같은 축으로 비교.

## 리스크
- **R1 결과 과대해석**: gap이 조금 줄어도 "전이 입증" 주장 금지. → acceptance를 측정+보고로 묶고
  std·단일run·저예산 caveat 의무. honesty 가드 패턴 계승.
- **R2 compute 비용**: LOO×4 fold × PPO는 무겁다. → CI는 smoke만; 실측은 적정 예산 1회(신호).
  비용 임계(rules/80 §D 200k) 모니터.
- **R3 scope creep**: "메커닉-범용 정책 설계"까지 끌어들이면 비대. → 이 task=widened-train LOO
  측정까지. 정책/obs 표현 개선은 결과 보고 후 별도 task로 분리.
- **R4 pilot falsify**: "더 많은 family면 전이된다"는 가정이 틀릴 수 있음(난이도 confound 등).
  → pilot로 사전 확인, 틀리면 정직 reframe(측정은 그대로 valid).
- **R5 #32 미머지 의존**: obs 조화가 main에 없음. → 브랜치가 #32 위에 stack; #32 머지 후 rebase.

## Acceptance Criteria (G1 통과 시 freeze)

> 성능/주장형이 아니라 **측정 머신 + 정직 보고**로 freeze. "gap을 줄였다"는 acceptance가 아니다.

- **AC1** `genre_learned_transfer`가 **widened-train LOO 전이**(각 family held-out, 나머지 train,
  duel 포함 가능)를 측정·출력. **비교 축의 정의 = 전이 gap = `held_in_mean − held_out_family_mean`
  (에피소드 리턴 단위; 기존 `TransferReport.gap`과 동일 metric)**. 즉 widened-train 각 fold의 gap을
  #26 baseline(train{A,B}→held-out{D}, **동일 gap = +2.56**)과 **같은 metric·같은 단위**로 한 표에
  나란히 보고(낮을수록 전이 잘 됨). held-in mean은 train family들의 held-in seed(학습 seed와 disjoint)
  평균, held-out mean은 미학습 family의 평균.
- **AC2** 실측 결과를 **±std + 단일run/저예산/N caveat**와 함께 보고(코드 근거, 날조 0). 결과가
  양성이든 음성이든 정직히 — gap 감소면 "신호(증명 아님)", 미감소면 "(B) 여전히 미해결".
- **AC3** `[rl]` smoke 테스트(importorskip)로 widened-train LOO + 4 family(duel 포함) fold 구성
  무회귀 검증. core CI numpy-only 유지.
- **AC4** 기존 테스트 전부 무회귀(192 유지/증가), mypy/ruff/build clean.
- **AC5** DESIGN §3.1.1 정직 갱신(이 task 결과 반영) + 마일스톤 매핑(M5/층2).
- **AC6** CHANGELOG 1줄 append.
- **AC7** (freeze 전) pilot로 실험 동작 + 정직 framing 확인. pilot이 가정 falsify 시 plan reframe
  후 재평가(새 slug 불요 — freeze 전이므로).
