# QA 체크리스트 — jax-duel-integration

## Acceptance (G1 freeze 대조)
- [x] AC1 — parity 0 mismatch (13 obs+reward+term+trunc, fixed+vary, ≥4 정책) ✅
- [x] AC2 — non-vacuity 가드 (ATTACK/CHARGE/GUARD·교착cap·evolve 자극) ✅
- [x] AC3 — family A/B/D 무회귀 + module-level byte-identical ✅
- [x] AC4 — jit + vmap smoke ✅
- [x] AC5 — G2 (mypy·ruff·pytest·build clean) ✅
- [x] AC6 — 정직 보고 (4/4 family·CPU·vmap-only·GPU 후속) ✅

## 회귀 가드
- [x] 기존 396 테스트 전부 green (415 passed = 396 + 19 신규)
- [x] family A/B/D parity 테스트 무변경 통과 (charge 필드·dispatch가 compile-time `family` 분기)
- [x] default-config module-level API(`jax_env_step`/`encode_obs`/`jax_reset`) byte-identical
- [x] `JaxEnvState` 필드 추가가 vmap/jit/pytree flatten 깨지 않음 (jit/vmap smoke green)

## 엣지 케이스 (parity 배터리 커버)
- [x] 동시 데미지로 양쪽 동시 기절 → loss (win = boss_fainted & ~player_fainted)
- [x] 40턴 교착 cap → loss (all-GUARD stalemate 정책)
- [x] charge 누적 후 큰 히트 (charge_exploit 정책)
- [x] 승리 → 레벨업 → evolve (duel_optimal 정책: win 60·evolve 24 in battery)
- [x] overworld charge=0 / battle charge>0 / battle 종료 후 0 리셋 (obs parity로 검증)
- [x] fixed(3 type) + vary(per-seed 8 type) 차트 양쪽

## 정직성 가드
- [x] parity 0 mismatch 비협상 — 달성
- [x] 속도는 측정값만 보고 (numpy 123k/s · vmap 40–83×), GPU 미측정 명시
- [x] pilot이 always-attack 0승을 포착 → 정직 reframe 없이 테스트 설계 보강(scripted-optimal)
