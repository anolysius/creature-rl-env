---
slug: genre-learned-transfer
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - scripts/genre_learned_transfer.py
  - tests/test_genre_learned_transfer.py
  - DESIGN.md
extracted_to: []
supersedes: []
---

# 장르 일반화 — 학습정책의 held-out-family 전이 (B, moat 층2)

> 작성일: 2026-06-23 | 상태: 계획

## 목표

비교분석 갭 register 1순위 + DESIGN §3.1.1 (B)의 핵심 미싱피스: **학습 정책이 unseen family로 전이하는가**.
지금까지 (B)는 *scripted* 정책 대조(C/D skill-structural)였고, 진짜 (B) 주장엔 **학습 정책의 held-out-family
일반화**가 필요(competitive-analysis·DESIGN 명시). 난이도 task(#25)의 genre 버전: **train families에 PPO 학습 →
held-out family로 전이 gap 측정**.

**obs 제약(확인됨)**: 단일 PPO 넷은 동일 obs 필요. critter/forage/muster=동일 11키, **duel만 charge 2키 추가**.
→ 이번 실험은 **train {critter, forage} → held-out {muster}**(공유 obs)로 한정. duel 포함은 obs 조화 필요(future, 정직 표기).

**정직 예상**: muster는 A/B에 없는 *수집-강화* 스킬 요구 → A/B 학습 정책이 D로 잘 전이 *안 할* 가능성 큼(gap 큼).
그래도 **honest 결과** — "학습 정책의 genre 전이는 어렵다(=B는 미해결)"가 정직한 (B) 측정. acceptance는 *전이 측정 +
정직 보고*(전이 성공 입증 아님). scripted gap≈0이 trivial이듯, 학습 정책이 진짜 측정.

**EC 매핑**: M3 신뢰성 + (B) 학습 genre 전이 첫 측정(moat 층2 방향). 비교분석 갭 register "family+학습정책" 착수.

## 선행 조건

- `critter_gym.env_family`(families A/B/D 공유 obs 확인), `genre_generalization`/`generalization`(측정 재사용)
- `scripts/difficulty_generalization.py`(#25): PPO + `_SeededReset` + held-in/held-out 분리 패턴 — genre 버전으로 응용
- families A/B/D obs 동일(11키) — 확인 완료. duel(13키)은 제외(obs 조화 future)

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/genre_learned_transfer.py` (신규, `[rl]`) | train families {critter,forage}에 PPO 학습(에피소드마다 train family 랜덤) → held-in(train families, held-in seeds) vs **held-out family {muster}** 전이 측정. obs 공유 family만 | 신규, `[rl]` |
| `tests/test_genre_learned_transfer.py` (신규) | `importorskip` smoke(tiny budget) → 전이 리포트 유한 + train/held-out family 분리 + obs 호환 가드 | 신규 |
| `DESIGN.md` (§3.1.1) | (B) 학습정책 held-out-family 전이 첫 측정 + obs 제약(duel 제외) + 결과 신호 정직 명시 | 저 |

## Step별 계획

1. **Red** — `test_genre_learned_transfer.py`: 스크립트 `train_and_transfer` import + tiny PPO → 전이 리포트(train-family mean, held-out-family mean, gap) 유한; obs 비호환 family(duel) 거부/제외 가드.
2. **Green** — `scripts/genre_learned_transfer.py`: 멀티-family 학습 래퍼(reset마다 train family 택1, 동일 obs) + PPO 학습 + `generalization.evaluate`(또는 genre 측정)로 held-in train-family vs held-out muster family 평가. held-in eval seed는 학습 seed와 disjoint.
3. **실측 + 보고** — modest budget으로 학습→전이 gap 측정. 결과(전이 성공/실패 무관)를 report+DESIGN에 *신호*로 정직 기록.
4. **무회귀** — 전체 테스트(183 + smoke)·mypy·ruff·build.

## 검증 방법

- `pytest -q` — smoke(importorskip) 포함 무회귀(183 불변).
- train family ≠ held-out family(family-level split) + held-in eval seed ∩ 학습 seed = ∅.
- obs 비호환(duel) 제외/가드 — 동일 obs family만 단일 넷.
- 실측 gap은 *신호*(단일run·N·비CI 정직), std 병기.
- DESIGN §3.1.1: 학습 genre 전이 첫 측정 + obs 제약 + 결과 정직.
- core CI numpy-only(PPO `[rl]` 뒤), mypy/ruff/build clean.

## 리스크

1. **전이 실패를 "실패"로 오독** → 정직 프레이밍: 학습 genre 전이가 어렵다 = (B) 미해결의 *정직한 측정*(주장 아님). 전이 성공 freeze 아님.
2. **obs 불일치(duel)** → 동일 obs family만(critter/forage/muster), duel 제외 명시(future obs 조화).
3. **단일run·작은 N·저예산** → 신호 표기, std 병기.
4. **train-family 1개뿐이면 genre 아님** → train ≥2 family(critter+forage), held-out 별도 family(muster).

## Acceptance Criteria (G1 통과 시 freeze)

> *학습 genre 전이 측정 + 정직 보고*로 freeze (전이 성공 입증 아님).

- **AC1** — `scripts/genre_learned_transfer.py`(`[rl]`): train families {critter,forage}(≥2)에 PPO 학습(reset마다 family 택1, 동일 obs) → held-in(train families) vs **held-out family {muster}** 전이 측정. obs 공유 family만.
- **AC2** — `tests/test_genre_learned_transfer.py`: `importorskip` smoke(tiny budget) → 전이 리포트 유한 산출 + family-level split(train≠held-out) + held-in eval seed가 학습 seed와 disjoint.
- **AC3** — obs 호환 가드: 동일 obs family만 단일 넷(duel 제외 명시). 비호환 family 혼입 시 명확 거부/스킵.
- **AC4** — 실측 산출: PPO 학습→held-in train-family vs held-out muster-family gap 수치 + std를 report에 기록. 전이 거동을 정직 서술(전이 약하면=‌(B) 미해결 신호, 그대로 보고).
- **AC5** — **정직 보고**: 학습정책 genre 전이 첫 측정(scripted 아님). 단일run·N·저예산·비CI = 신호. (B)는 여전히 토대/미해결(전이 1쌍=증명 아님). DESIGN §3.1.1 갱신(obs 제약 포함).
- **AC6** — 무회귀: 전체 테스트 회귀 0(183 + smoke importorskip), core CI numpy-only(PPO `[rl]`), mypy/ruff/build clean, honesty 가드 무회귀.
