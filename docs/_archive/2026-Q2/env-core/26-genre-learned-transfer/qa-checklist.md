# QA 체크리스트 — genre-learned-transfer

## 영향도
- `[rl]` 스크립트 + smoke + DESIGN. 코어 무변경(기존 generalization/env_family 재사용).

## 회귀 가드
- [x] 전체 185 passed/2 skipped (183→185, 회귀 0)
- [x] core CI numpy-only(PPO `train_and_transfer` 내부 import, `[rl]` 뒤)
- [x] smoke importorskip 게이트
- [x] mypy(22)/ruff/build clean, honesty 가드 무회귀

## 정합/엣지
- [x] family-level split: train {critter,forage} ≠ held-out {muster}
- [x] held-in eval seed ∩ learn_seeds = ∅ (`split_train_pool`)
- [x] held-out family 학습 미노출(`_MultiFamilyEnv`는 train family만 순환)
- [x] obs 호환 가드: duel(13키) 거부, critter/forage/muster(11키) accept
- [x] (known-minor, 비차단) family↔seed index 결합 → 일부 조합 편향, 신호 무영향

## 정직성
- [x] 학습(scripted 아님) 첫 genre 전이 측정 명시
- [x] gap +2.56 = "(B) 미해결" 정직 신호(실패도 증명도 아님)
- [x] 한 train-set→한 held-out family = 증명 아님, std 병기
- [x] 단일run·저예산·duel 제외 = 신호
