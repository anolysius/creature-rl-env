# QA 체크리스트 — difficulty-generalization

## 영향도
- `[rl]` 스크립트 + smoke 테스트 + DESIGN. 제품 코어 무변경(기존 `generalization` 재사용).

## 회귀 가드
- [x] 전체 183 passed/2 skipped (181→183, 회귀 0)
- [x] core CI numpy-only 유지(PPO는 `train_and_gap` 내부 import, `[rl]` 뒤)
- [x] smoke importorskip 게이트(sb3 없으면 skip, CI 안 깨짐)
- [x] mypy(22)/ruff/build clean, honesty 가드 무회귀

## 엣지/정합
- [x] held-in eval ∩ learn_seeds = ∅ (`split_train_pool`) — gap 부풀림 없음
- [x] held-out 영역 분리 + 누수 가드(`measure_generalization` 상속)
- [x] `_SeededReset`가 learn_seeds만 순환(held-in eval 미노출)
- [x] N_heldin/heldout 16/16 고정, `EvalResult.std` 병기

## 정직성
- [x] config=난이도 점(calibrated 사다리 주장 0; pilot falsification 명시)
- [x] 측정=학습정책 gap(scripted gap≈0 trivial 명시)
- [x] gap-within-std는 *약한 증거*("입증" 아님) — script/DESIGN hedge(L3 반영)
- [x] 단일run·저예산·N16 = 신호
