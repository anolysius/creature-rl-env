# QA 체크리스트 — arxiv-writeup (docs-only)

## 영향도
- docs-only: `docs/paper/critter-gym.md` + `docs/paper/README.md` 신규. 제품 코드/테스트 무변경.

## 회귀 가드
- [x] 제품 코드·테스트 무변경(diff = docs/paper/** + plan/report)
- [x] pytest 181 passed/2 skipped 불변(코드 무영향)
- [x] broken-link 0(README 참조는 기존 모듈/테스트/archive)

## 정확성 (L3 accuracy reviewer 코드 대조)
- [x] load-bearing gate ≥0.20/≥0.10 + 42 seeds = test_reasoning_gate.py 일치
- [x] family C +3.9/+0.2/4.3 = 19-battle-system-family report 일치
- [x] family D muster 1.42/rush 0.00, A muster≤rush = 21-family-d-muster report 일치
- [x] learnability gym-clear 4.19/1.81/1.06 = 20-learnability-precision report(4.188→4.19) 일치
- [x] CI-reproducible(gate) vs run-derived(means/margins/throughput/gap) 라벨 구분

## 정직성
- [x] Pokémon=메타포(비경쟁) abstract/§1/§6
- [x] (B) 토대 아닌 증명 — abstract/§5/§7/§8 일관
- [x] (A) 인스턴스 vs (B) 장르 구분 명확(held-out seed vs held-out env)
- [x] §7 limitations 전 caveat + family C 예측가능성 caveat(L3 반영)
