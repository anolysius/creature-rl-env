# QA 체크리스트 — v1-results-packaging

## Acceptance (G1 freeze 대조)
- [x] AC1 — `reproduce_results.py --quick` 두 표 + honest framing ✅
- [x] AC2 — README 두 헤드라인 + Release status 1.0.0-rc + 잔여 게이트 ✅
- [x] AC3 — paper JAX throughput + PPO headroom 통합 + conclusion 정정 + source map ✅
- [x] AC4 — version 1.0.0rc1 + build 아티팩트 ✅
- [x] AC5 — 무회귀(pytest exit=0) + 정직성(fabricate 0) ✅
- [x] AC6 — 공개 행위 안 함 (사람 게이트 직전 정지) ✅

## 회귀 가드
- [x] src/critter_gym 무변경 (docs/scripts/meta만) → pytest 415 무회귀
- [x] mypy(28)/ruff clean (신규 script 포함)
- [x] build → critter_gym-1.0.0rc1 (version bump 정상)
- [x] reproduce_results.py가 기존 bench/ppo_baseline 공개 API만 호출(신규 측정 로직 0)

## 정직성 가드 (front-facing 최우선)
- [x] vmap 속도: CPU·vmap-only·single jit slower 명시
- [x] 4/4 family: parity 0 근거(test 파일) 명시
- [x] PPO headroom: 21–28% of oracle·5-run robust·oracle=scripted proxy·작은net·이 예산 명시
- [x] 1.0.0-rc: GPU/arXiv/OSS 잔여 게이트 명시, "공개=사람 결정"
- [x] 수치 라이브 재생성(하드코딩 0) → fabricate 불가
- [x] paper source map으로 모든 정량 주장 추적가능

## 공개 게이트 (사람 전용 — 본 task가 건드리지 않음)
- [ ] git tag v1.0.0 push — **사람**
- [ ] OSS 공개 리스팅 — **사람**
- [ ] arXiv 제출 — **사람**
- [ ] GPU throughput 측정 (M4-EC3) — 후속 task
