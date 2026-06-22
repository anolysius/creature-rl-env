---
slug: reasoning-load-bearing
initiative: env-core
status: completed
ended: 2026-06-22
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC-reliability]
extracted_to:
  - DESIGN.md   # §3.1.1 — "infer-the-meta load-bearing?" open problem → scripted-arm 실증 (learnability follow-up)
changelog_entry: docs/CHANGELOG.md
supersedes: []
---

# Report — reasoning-load-bearing · M3 신뢰성 + DESIGN §3.1.1 해소

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md) (AC1–AC6)

## 요약 — 정직한 성공 (typechart-depth 의 open problem 을 해소)

`typechart-depth`(archive 15)가 pilot 로 *불가 입증*→descope 했던 **"infer-the-meta 를 provably load-bearing"**
을, **team-commit 보스 경제** 로 *scripted-arm 실증*했다. freeze 전 achievability pilot 통과 후 진입(§4 함정 회피).

| arm (42 고정 held-out 시드, product 엔진 `commit_mode`) | 평균 |
|---|---|
| oracle (완벽한 차트 지식, 상한) | 1.000 |
| type_blind (타입 무시, 항상 크리처 0) | 0.521 |
| probe (commit 하 probing 불가 → 추측) | 0.473 |
| infer (보스타입 재출현을 cross-battle 기억·재사용) | 0.836 |

- **Gate 0** `oracle − type_blind = 0.479 ≥ 0.20` — 타입지식이 *결정적* (지난 실패의 진짜 원인 해소).
- **Gate 1** `infer − probe = 0.363 ≥ 0.10` — *추론*이 *probing* 을 이김 = load-bearing.

지난 실패의 근본 원인을 코드로 확정: faint 시 **force-switch 순회**(`battle.py` Phase 3)가 다중-크리처 파티로
super 크리처를 *공짜로* brute-force → type_blind 가 1.0(타입지식 무의미). team-commit 이 이 순회 + 배틀내
switching 을 차단해 (a) brute-force 제거(Gate 0 해금) + (b) probing 구조적 불가 → cross-battle 추론만이 싼 길.

## 계획 대비 실적 (AC1–AC6)

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | `Battle(commit_mode=True)`: switch no-op + faint=즉시패배(force-switch off). M1 불변(기본 off) | ✅ 단위 3건 + `test_battle` 42 passed(force-switch 회귀 포함) |
| AC2 | super_mult·boss strength 를 env/registration config 노출(상수 X) + winnability | ✅ `TypeChart.super_mult`/`gym_boss(hp/atk/df)`/env params/`CritterGym-commit-v0`; 테스트 5건 |
| AC3 | `test_reasoning_gate.py` 42 고정시드 Gate0≥0.2 ∧ Gate1≥0.1, 4 arm product API | ✅ 0.479 / 0.363; 4 테스트 통과; pilot(0.48/0.36) 재현 |
| AC4 | M1 완전 무회귀 + check_env(fixed/procgen/commit) + 누수 0 | ✅ 42 passed + check_env ×3 OK; baseline 128→140(신규12만, skip 동일) |
| AC5 | DESIGN §3.1.1 정직 갱신(scripted 실증/learnability follow-up) + honesty 가드 | ✅ DESIGN 재작성 + 가드 재정의(`test_source_does_not_overclaim_learned_inference`) |
| AC6 | toolchain canonical clean | ✅ mypy(16) clean · ruff clean · pytest 140 passed/2 skipped · build OK |

## 변경 파일 상세

| 파일 | 내용 |
|---|---|
| `battle.py` | `commit_mode` 플래그 — Phase1 switch skip / Phase3 force-switch skip / `_update_terminal` active-faint=패배 |
| `types.py` | `TypeChart.super_mult` 필드(난이도 knob) + `generate_typechart` 스레딩; docstring 정직 갱신 |
| `region.py` | `generate_region(super_mult=)` → chart 전달; docstring 정직 갱신 |
| `party.py` | `gym_boss(hp/atk/df/spd)` 보스 strength 파라미터화(M1 기본값 유지) |
| `critter_env.py` | env params `super_mult/boss_hp/atk/def/commit_battles`(M1 기본) + region/battle wiring |
| `registration.py` | `CritterGym-commit-v0` 등록(pilot-검증 config: num_types12/super_mult3/boss140·18/commit) |
| `DESIGN.md` | §3.1.1 open problem → scripted-arm 실증 + learnability follow-up 정직 분리 |
| `tests/test_reasoning_gate.py` (신규) | 4-arm 게이트(42 고정시드, product API, Gate0/Gate1 + 평균 출력) |
| `tests/test_battle.py` | commit_mode 3건(switch noop / faint=loss / default 무회귀) |
| `tests/test_meta_difficulty.py` | super_mult 2 + env knob 3 + honesty 가드 재정의 |

## 발견된 이슈 (심각도)

- **(중) scope_paths 누락** — 구현 중 AC2 가 `types.py`/`region.py`/`party.py` 를 건드리는데 frozen scope_paths
  에 빠져 task-start-guard 가 BLOCK. acceptance 변경 아닌 **범위 보정**으로 3 파일 추가 후 진행(정당). 가드가
  정확히 작동한 사례.
- **(낮) L3 plan-reviewer verdict 미생성** — 9파일/262줄 diff 에서 maxTurns=5 소진→verdict 라인 전 종료 2회.
  남긴 유일 우려(registration honesty 토큰)는 결정론 확인으로 해소. retro 큐 `l3-reviewer-maxturns` 적재.
  사용자 결정(가)으로 L3 통과 처리(qa-verifier APPROVE + plan-reviewer 무차단).
- **(낮·정직성) env 의 agent 챔피언-선택 UX 는 deferred** — env commit 모드에서 챔피언=active_a(크리처 0).
  load-bearing *증명*은 scripted 게이트(AC3)가 챔피언을 명시 선택해 수행. 학습 정책이 enemy_type 관측으로
  챔피언을 *추론·선택*하게 하는 액션 UX 는 follow-up(아래).

## 흡수처 매핑 (extracted_to)

- **`DESIGN.md` §3.1.1** — 살아있는 설계 narrative. "infer-the-meta load-bearing?" 단락을 *open problem*
  에서 *team-commit 으로 scripted-arm 실증*(수치 포함) + *learnability 는 follow-up* 으로 정직 갱신. 이 task 의
  유일한 evergreen 결정 (rl-env evergreen 디렉토리·ADR 디렉토리 부재 — typechart-depth 선례 동일).

## 후속 (follow-up)

1. **learnability 측정** — PPO 등 *학습* 정책을 `CritterGym-commit-v0` 에서 학습 → infer-arm 수준 일반화
   달성 여부(현재 미측정; DESIGN §3.1.1 명시). M3 신뢰성/EC4 writeup 의 자연스러운 다음.
2. **env 챔피언-선택 액션** — commit 모드에서 agent 가 enemy_type 관측 기반으로 챔피언을 commit 하는 액션 UX
   (turn-0 commit window). 학습 실험의 전제.
3. (retro) `l3-reviewer-maxturns` — plan-reviewer maxTurns/verdict-first 패턴.

## 툴체인 결과
- `pytest` → **140 passed, 2 skipped**(128 baseline + 신규 12; skip 동일)
- `mypy src` → Success(16 files) · `ruff check .` → clean · `python -m build` → OK
- `check_env`(fixed + procgen-v0 + commit-v0) 통과 · M1 결정론·FIXED_CHART·누수0 무회귀
