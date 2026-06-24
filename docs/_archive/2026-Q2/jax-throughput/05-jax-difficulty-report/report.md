---
slug: jax-difficulty-report
initiative: jax-throughput
status: completed
ended: 2026-06-24
extracted_to:
  - docs/explanation/jax-throughput.md   # §4 "Update (jax-difficulty-report / R5)" 블록 + references
  - DESIGN.md                            # §4 M4 follow-on R5 문장
changelog_entry: docs/CHANGELOG.md (jax-throughput 섹션)
---

# jax-difficulty-report (R5) — 결과 보고서

## 한 문단 요약 (수식 없이)

지난번 빠른 JAX 엔진은 "도장 3개"로 고정돼 있어, 변별이 또렷한 "도장 8개" 설정을 못 돌렸습니다. 이번에 엔진을 **설정 가능**하게(도장 수·격자·보스 스탯) 바꿔 8-도장 설정도 돌리게 했고, **원본과 한 글자도 안 틀리는지(parity)** 확인했습니다 — 결과: **단 하나도 안 틀림**. 그 위에서 학습을 돌리니 옛 방식보다 **~63배 빨랐습니다.** 기본 설정(도장 3개)은 그대로라 기존 것은 안 깨졌습니다(기존 테스트 전부 통과). 즉 "변별 잘 되는 어려운 설정"과 "빠른 엔진"을 하나로 합쳤습니다.

## 요약 (수치)

| 측정 | 결과 |
|---|---|
| 고-gym(8) parity (jax vs CritterEnv) | **0 mismatch** (obs 13키[patch 11×11]+reward+term+trunc, random+gym-clearing, fixed+held-out) |
| default config 무회귀 | byte-identical (기존 parity 3종 + test_default_config_unchanged green) |
| 고-gym 학습 throughput | **~196k env-steps/s vmap** vs sb3 ~3.1k = **~63× FASTER** |
| 고-gym 학습 곡선 | 상승(jit/vmap OK) |
| 테스트 | 294 → **310** (+16 importorskip parity, 회귀 0) |
| canonical | mypy(26)/ruff/build clean |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 config factory | ✅ | `JaxEnvConfig`+`make_jax_env(cfg)`(static-shape 클로저). module-level fns=default 인스턴스 보존. |
| AC2 jax_train config-aware | ✅ | `EnvSpec`/`default_env_spec`/`difficulty_env_spec`, obs_dim 동적(_obs_dim), make_rollout(env). 고-gym tracer OK. |
| AC3 고-gym parity 테스트 | ✅ | `test_jax_difficulty_parity.py` 16 — 0 mismatch + jit/vmap + default 불변 + train smoke. |
| AC4 데모 | ✅ | `jax_rl_demo --difficulty` — 고-gym vmap vs sb3(matched config), ~63× FASTER(부등식 성립). |
| AC5 CI 불변 | ✅ | 310 passed/2 skipped(회귀 0), 기존 parity 3종 green, 신규 importorskip, canonical clean. |
| AC6 pilot | ✅ | freeze 전 R1(parity 0)·R2(무회귀)·R3(tracer)·R4(63×) 측정 → 사전약정 분기. parity 비협상 충족. |
| AC7 정직 보고 | ✅ | parity 0 박제 + 속도 vmap·CPU·single-run·"고-gym 발산으로 배율↓" + "family A commit·고-gym 한정, scripted arms numpy 유지·GPU/tuned PPO 후속" 명시. |
| AC8 문서 | ✅ | jax-throughput.md(R5)+DESIGN §4+INITIATIVE+CHANGELOG. broken-link 0. |

## 변경 파일 상세

**수정**
- `src/critter_gym/jax_env.py` — `JaxEnvConfig`(grid·patch_radius·max_steps·max_gyms·boss_*) + `make_jax_env(cfg)` factory(reset/step/encode/make_step 클로저, 로직 verbatim·상수만 cfg화). module-level `jax_env_step`/`jax_reset`/`encode_obs`/`make_env_step`=`make_jax_env(DEFAULT_CONFIG)` 인스턴스로 보존(import 무변경).
- `src/critter_gym/jax_train.py` — `EnvSpec`+`default_env_spec`/`difficulty_env_spec`, `build_region_bank(seeds, spec)`, `_obs_dim`(동적), `make_rollout(init, env)`, `train`/`evaluate`에 `spec` 인자(기본=default world, 무회귀).
- `scripts/jax_rl_demo.py` — `--difficulty` flag(고-gym spec 학습 + matched sb3 baseline), ep_return 스케일=config.max_steps(정정).

**신규**: `tests/test_jax_difficulty_parity.py` (16, importorskip).
**문서**: jax-throughput.md(R5 update + refs)·DESIGN §4·INITIATIVE·CHANGELOG.

## 발견된 이슈 / 정직한 한계

- **obs_dim이 patch 크기에 의존** — 고-gym config는 patch_radius=5(11×11)라 default(5×5)와 obs_dim 다름 → train이 env에서 동적 도출(하드코딩 38 제거 경로). 발견·반영.
- **고-gym 배율(~63×) < default(~170×)** — 8-gym·긴 에피소드가 제어흐름 발산 심해 vmap 효율↓(정직 보고).
- **범위 경계**: family A commit·고-gym 재포트지 difficulty *전체* JAX화 아님 — scripted resolution arms(oracle/blind)는 env 내부 peek이라 numpy 유지. GPU·tuned PPO·다른 family 후속.
- 학습 곡선·속도 = CPU·single-run 신호. 회귀 가드: default config byte-identical(기존 parity 3종).

## 흡수처 (extracted_to)

| 정보 | 흡수처 |
|---|---|
| config화 + 고-gym parity + ~63× 가속 narrative | jax-throughput.md §4 "Update (R5)" |
| M4 follow-on 진행 | DESIGN §4 |
| JaxEnvConfig/make_jax_env/EnvSpec 코드 포인터 | jax-throughput.md references |

ADR 가치: 없음(기존 jax-throughput narrative + 코드로 충분).

## 검증 결과
mypy clean(26)·ruff clean·pytest 310 passed/2 skipped(294→310, 회귀 0)·build OK. L3 2/2 APPROVED(plan-reviewer 코드 정합성 + qa-verifier AC 8/8).
