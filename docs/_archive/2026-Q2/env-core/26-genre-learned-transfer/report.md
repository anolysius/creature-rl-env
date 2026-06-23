---
slug: genre-learned-transfer
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - DESIGN.md#3.1.1   # (B) first learned-policy held-out-family transfer measurement
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# 장르 일반화 — 학습정책 held-out-family 전이 — 결과 보고서

## 요약

(B) 장르 일반화의 핵심 미싱피스 = **학습 정책의 unseen family 전이** 첫 측정(지금까지는 scripted 대조).
`scripts/genre_learned_transfer.py`([rl]): train families {critter, forage}에 PPO 학습(reset마다 family 택1,
공유 obs) → **held-out family {muster}** 전이. obs 제약상 동일 11키 family만(duel 13키 제외=future).

| set (PPO 50k, N=16/16) | mean (±std) |
|---|---|
| held-in (train families) | **2.938 ±2.015** |
| held-out (unseen family muster) | **0.375 ±0.696** |
| **전이 gap** | **+2.562** (std 훨씬 넘음) |

→ **학습 정책이 unseen family로 전이 안 됨** — muster의 수집-강화 메커닉을 학습 때 못 봐서 floor. = **정직한
"(B) 학습 genre 전이는 어렵다 / 미해결" 신호**(실패도 증명도 아님). 한 train-set→한 held-out family = 첫 측정,
증명 아님. 닫는 것(전이하는 정책 학습)이 M5/moat 층2 작업.

| 검증 | 결과 |
|---|---|
| 테스트 | **185 passed**/2 skipped (183→185, +2 smoke, 회귀 0) |
| mypy/ruff/build | clean (22 files) |
| `[rl]` smoke | pass(importorskip) |
| core CI | numpy-only 유지(PPO `[rl]` 뒤) |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 ≥2 train family PPO → held-out family | ✅ | `_MultiFamilyEnv`(critter+forage) → muster |
| AC2 smoke + family split + seed disjoint | ✅ | `test_*` 2종 pass, `split_train_pool` disjoint |
| AC3 obs 호환 가드(duel 제외) | ✅ | `assert_obs_compatible` ValueError(duel)/accept(muster) |
| AC4 실측 gap+std | ✅ | held-in 2.94±2.02 vs held-out 0.38±0.70, gap +2.56 |
| AC5 정직 보고(학습 첫 측정·미해결·증명 아님) | ✅ | docstring/main/DESIGN |
| AC6 무회귀+numpy-only+toolchain | ✅ | 185 passed, mypy/ruff/build clean |

전 AC ✅. acceptance를 *전이 측정+정직 보고*로 freeze(전이 성공 입증 아님).

## 변경 파일 상세

**신규**
- `scripts/genre_learned_transfer.py`(`[rl]`) — `_MultiFamilyEnv`(train family 순환) + `assert_obs_compatible`(obs 가드) + `train_and_transfer`(PPO→held-in vs held-out family) + `TransferReport`(±std).
- `tests/test_genre_learned_transfer.py` — importorskip smoke + obs 가드 테스트.

**수정**
- `DESIGN.md`(§3.1.1) — (B) 첫 학습-정책 held-out-family 전이 측정(gap +2.56, "(B) 미해결", duel 제외, M5/층2 framing).

## 발견된 이슈 (심각도)

- **(중, 정직 결과)** 학습 genre 전이가 어려움(gap +2.56) — (B)가 미해결임을 정직히 측정. 닫는 것=M5/moat 층2.
- **(낮음, L3 비차단 노트)** `_MultiFamilyEnv`가 family와 seed를 같은 index로 묶음(critter↔짝수 offset seed 등) → 학습되는 (family,seed) 조합이 일부 편향. **신호엔 무영향**(held-out family 누수 없음, 두 train family 모두 학습됨). 향후 정밀 측정 시 decouple 권장.
- **(낮음)** 단일run·저예산(50k)·N16·duel 제외 = 신호.

## 흡수처 매핑 (extracted_to)

- **DESIGN.md §3.1.1** — (B) 학습-정책 전이 첫 측정·obs 제약·미해결 신호 흡수. 스크립트는 기존 `generalization`/`env_family` 재사용(새 core 모듈 불요).

## 타입 체크 / 빌드 결과

mypy: Success (22) · ruff: clean · build: OK · pytest: 185 passed/2 skipped.
