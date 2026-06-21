---
slug: scaffolding
initiative: env-core
status: done
started: 2026-06-21
ended: 2026-06-21
mode: standard
result: passed
---

# Report — Phase 1 스캐폴딩 (최소 Gymnasium env + 패키지 레이아웃)

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약
CritterGym 제품 코드 첫 줄. `src/critter_gym/` (src-layout) 패키지 + hatchling 빌드 + ruff/mypy/pytest
툴체인을 세우고, 10×10 catch-only `CritterEnv` (Gymnasium API, seeded 결정론, RLVR boolean subgoal
리워드) 를 구현·등록했다. Acceptance 8/8 통과, 모든 정적·동적 검사 green.

## 산출물
| 파일 | 내용 |
|---|---|
| `pyproject.toml` | 패키지 메타 + deps(gymnasium≥0.29, numpy) + dev(ruff/mypy/pytest/build) + tool 설정 |
| `src/critter_gym/__init__.py` | 패키지 진입 — import 시 `register_envs()` 호출, `__version__` |
| `src/critter_gym/registration.py` | `register("CritterGym-v0", ...)` (idempotent) |
| `src/critter_gym/envs/critter_env.py` | `CritterEnv` — 구조적 obs(Dict), Discrete(6) 액션, catch-only RLVR 리워드 |
| `src/critter_gym/envs/__init__.py` | env export |
| `tests/test_env.py` | API/결정론/리워드/종료/가드 — 10 케이스 |
| `tests/test_registration.py` | `gymnasium.make` 라운드트립 — 2 케이스 |

## Acceptance 결과 (G1 freeze ↔ 실측, 1:1)
- ✅ AC1 설치 — `pip install -e ".[dev]"` clean venv 성공
- ✅ AC2 등록 — `gymnasium.make("CritterGym-v0")` → `CritterEnv`
- ✅ AC3 Gymnasium API — `reset`→(obs,info), `step`→5-튜플, obs∈space (test PASS)
- ✅ AC4 결정론 — 동일 seed reset 2회 `array_equal` (test PASS)
- ✅ AC5 RLVR 리워드 — creature 칸 CATCH→+1 ∧ subgoal 증가, 빈 칸·이동→0, dense shaping 없음 (3 test PASS)
- ✅ AC6 종료 — caught≥C→terminated, budget 초과→truncated (2 test PASS)
- ✅ AC7 툴체인 green — ruff ∧ mypy ∧ pytest(12) ∧ `python -m build` (sdist+wheel) 전부 PASS
- ✅ AC8 커플링 확정 (HARNESS-PORT-MANIFEST §(c)):
  - **#1** ruff 를 포매터/린터로 채택 — pyproject `[tool.ruff]` + dev-deps 등록.
  - **#2** `run-tdd.py` `COMMANDS`(mypy src / ruff check .) 가 본 src-layout 에서 `all_passed=true`.
  - **#3** `active_plan_scope._TARGET_PREFIXES=("src/",)` 정합 — frozen plan 이 `src/**` 편집을
    허용(가드 발화). 제품 코드가 `src/` 에 있어 가드가 실제로 보호함을 확인.
  - **#4** `path-criticality.json` critical glob(`src/critter_gym/{envs,...}/**`, `registration.py`,
    `pyproject.toml`) 이 실제 산출 파일과 매칭 → mode=standard 판정 정합.

## 설계 메모 (후속 task 인계)
- **obs**: `Dict{agent_pos, local_patch(5×5 binary), caught}` — 구조적/심볼릭(DESIGN §3.2). procgen·party·
  type meta 확장 시 키 추가로 성장.
- **action**: `Discrete(6)` = MOVE{N,S,E,W}+CATCH+NOOP (DESIGN §3.3 의 최소 부분집합). 상수+델타 딕셔너리 분리.
- **리워드**: catch 성공 시에만 +1 (RLVR). 이동/실패 CATCH/NOOP = 0 (shaping 없음). `info["subgoals"]`
  로 subgoal chain 확장 지점 확보.
- **결정론**: `super().reset(seed)` → `self.np_random` 단일 경유. train/test seed split 기반 마련.
- `action_space` 에 `# type: ignore[assignment]` 1건 — gymnasium `Discrete`(Space[np.int64]) ↔ ActType
  int invariant 충돌(알려진 quirk). 주석으로 사유 명시.

## L3 리뷰 반영
- @plan-reviewer SUGGEST(correctness): `num_creatures ≥ grid_size²` 시 reset agent-pos 탐색 무한 루프 가능
  → `__init__` 에 `ValueError` 가드 + 테스트(`test_too_many_creatures_rejected`) 추가.
- @qa-verifier: APPROVE (AC 8/8 정합).

## 후속 seed
- `env-core/subgoal-chain` — evolve / gym boss 등 verifiable subgoal 체인 (DESIGN §3.5).
- `env-core/procgen-typechart` — 시드별 내부정합 type 매트릭스 (DESIGN §3.1, infer-the-meta).
- 벡터화/JAX 핫패스 포팅 (DESIGN §4, throughput gate) — perf vertical.
- ruff 가 `.claude/`(하네스, process-owner 소유) 를 exclude — 하네스 자체 린트는 별도 task.
