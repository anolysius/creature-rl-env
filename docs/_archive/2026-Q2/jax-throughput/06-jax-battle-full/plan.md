---
slug: jax-battle-full
initiative: jax-throughput
status: active
started: 2026-06-24
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - src/critter_gym/jax_battle_full.py
  - tests/test_jax_battle_full_parity.py
  - scripts/bench_throughput.py
  - docs/explanation/jax-throughput.md
  - DESIGN.md
  - docs/CHANGELOG.md
  - docs/_active/jax-throughput/INITIATIVE.md
extracted_to: []
supersedes: []
---

# jax-battle-full — non-commit full battle JAX 포트 + parity

> 작성일: 2026-06-24 | 상태: 계획 | 마일스톤: **M4** (jax-throughput; 핫패스 배틀의 남은 절반)

## 한 문단 요약 (수식 없이)

지금까지 JAX로 옮긴 배틀은 "챔피언 1마리 commit"(보스전) 버전뿐입니다. 일반 배틀(파티 3마리, 교체·회복아이템·기절 시 자동 교체·전멸 패배)은 아직 numpy로만 돕니다. 이번 작업은 그 **일반 배틀을 JAX로 옮기고, 원본과 한 글자도 안 틀리는지(parity)** 확인합니다. 이로써 배틀 엔진의 두 경로(commit/일반)가 모두 JAX 벡터화됩니다. 기존 것은 안 건드립니다(새 파일).

## 목표

핫패스 배틀의 남은 절반 — **non-commit full battle**(`Battle(commit_mode=False)`: 3마리 파티 + SWITCH + ITEM(potion) + 기절 force-switch + party-wipe 종료)을 functional JAX로 포트. `jax_battle.py`(commit 챔피언)의 패턴을 미러. **numpy `Battle(commit_mode=False)` 대비 parity 0 mismatch**(재현성 북극성 #3)가 게이트. vmap throughput 측정(정직 framing).

**범위**: env 사용 형태(party_a=starter 3마리 vs party_b=boss 1마리) 기준 standalone 배틀 step 포트(`jax_battle.py`처럼). full-env 통합은 아님(jax_env는 commit-only 유지). **한계효용 정직 명시**: gym-boss 실경로는 commit-mode(이미 포트)라 본 포트는 *env 기본(non-commit) 경로 커버 + M4 배틀 완전성*이지 load-bearing 경로 교체 아님.

## 선행 조건

- `jax_battle.py`(commit, parity 0) 패턴 + `battle.py`(numpy non-commit 메커닉) 재사용.
- numpy 메커닉(battle.py): turn++ → Phase1(switch: 대상 alive면 active 변경 / item: index0=potion이면 active heal[max_hp 클램프]·재고-- , 그 외 no-op) → Phase2(MOVE만, active speed desc·tie A first, 기절 attacker/defender skip, damage=max(1,floor(pow·atk/def·eff)), take_damage 0클램프) → Phase3(non-commit: active 기절 시 next_alive로 force-switch) → terminal(party_wiped=전원 기절; 양측 동시면 A-wiped→B승; turn>=max_turns truncate).
- boss=1마리 → action_b=MOVE 0(scripted greedy, 단일 move). player action=MOVE(move_idx)/SWITCH(idx)/ITEM(idx). **한 턴 = player action 1개**(switch/item/move 중 하나).
- **branch**: G1 후 `feature/jax-battle-full`. main 직접 금지.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/jax_battle_full.py` | **신규** | 중-상 | `FullBattleState`(party_a_hp (P,)·active_a·items_a·boss_hp·turn·done·winner) + `FullBattleParams`(party_a 스탯 배열 (P,)·max_hp (P,)·boss 스칼라·eff·max_turns·potion_heal) + `full_battle_step(state, act_kind, act_idx, params)`(1턴, branch-free where/cond) + `params_from_parties`/`initial_state` numpy bridge. `import jax` 모듈(코어 numpy-only, `__init__` 미import). |
| `tests/test_jax_battle_full_parity.py` | **신규** | 중 | `importorskip("jax")`: numpy `Battle(commit_mode=False)`(party_a=starter 3 vs boss 1) 대비 parity — action 시퀀스 배터리(전부 attack / switch / item(heal) / force-switch[active 기절→next] / party-wipe / truncation) + random 시퀀스(고정 seed) + jit/vmap. 매 턴 party_a_hp·active·boss_hp·done·winner·turn 일치. |
| `scripts/bench_throughput.py` | 추가 | 저 | full-battle vmap 행(numpy vs jax vmap), 정직 framing. |
| `docs/explanation/jax-throughput.md` | 갱신 | 저 | §5 open questions #1(jax-battle-full ✅) + 코드 포인터. |
| `DESIGN.md` | 갱신 | 저 | §4 R 1줄. |
| `docs/CHANGELOG.md` · `INITIATIVE.md` | append | 저 | task-end. |

### 영향 범위 (import 그래프)

`jax_battle_full` → `battle`(Side enum·상수)·`types`·numpy party 읽기. **역방향 의존 0**(jax_env/jax_battle/jax_train 무변경). `__init__` 미import → core CI numpy-only 불변. 기존 310 tests 무회귀(신규 importorskip).

## Step별 계획

> **G1 freeze 전 PILOT 필수** — #41(commit)서 pilot이 hp 클램프 버그를 잡았듯, non-commit은 switch/item/force-switch/동시-기절 동점 등 미묘차 多. freeze 전 parity 배터리 0 mismatch 실측(게이트).

1. **state/params + bridge** — numpy party → 배열 pytree.
2. **full_battle_step** — Phase1/2/3 + terminal을 branch-free로(active gather=dynamic index, next_alive=first hp>0, party-wipe=all hp<=0). commit 로직(active vs boss) 재사용 + switch/item/force-switch/party-wipe 추가.
3. **parity(pilot 핵심)** — 배터리 + random 시퀀스서 numpy 대비 0 mismatch. mismatch 시 수정(비협상).
4. **bench + 문서**.

## 검증 방법

- **CI(numpy-only)**: 기존 310 tests green. 신규 importorskip.
- **로컬 [jax]**: parity 배터리 0 mismatch + jit/vmap + bench.
- **canonical**: `mypy src`·`ruff check .`·`pytest -q`·`python -m build` clean.

## 리스크 / Pilot (freeze 전)

| # | 리스크 | Pilot | 분기 |
|---|---|---|---|
| R1 | **parity mismatch** — switch/item/force-switch/동시-기절 동점/speed-tie/heal 클램프 미묘차. | parity 배터리 실측. | 0 mismatch → 진행 / mismatch → 수정(비협상 게이트). |
| R2 | **동적 party 인덱싱 jit 실패** — active gather·next_alive가 vmap/jit서. | jit/vmap smoke. | 에러 시 where 기반 수정. |
| R3 | **speed-order 상호작용** — 빠른 쪽이 느린 쪽 기절시키면 느린 쪽 move skip(numpy 동작) 미러 실패. | tie+속도차 시드 parity. | numpy 정확 미러. |

**사전약정 결정규칙 (freeze):**
- **parity 게이트 (R1/R3)**: action 배터리(attack/switch/item/force-switch/party-wipe/truncation) + random 시퀀스(고정 seed) 전부 **0 mismatch**(party_a_hp·active_a·boss_hp·done·winner·turn). 미충족=수정(비협상).
- **speed (bench)**: vmap full-battle steps/s `>` numpy steps/s 성립 시만 "빠르다"(측정값 보고, vmap·CPU·single-run 라벨).

**정직성 사전약정 (박제):**
- parity 0 mismatch가 게이트(가짜 속도 차단). 속도 이득=vmap 한정.
- **한계효용 정직**: gym-boss 실경로는 commit-mode(이미 포트). 본 포트=env 기본(non-commit) 경로 커버 + M4 배틀 완전성. full-env 통합(non-commit jax_env)은 별도 후속.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1** — `src/critter_gym/jax_battle_full.py` 신규: `FullBattleState`/`FullBattleParams` + `full_battle_step`(non-commit 1턴: switch/item/move(speed order)/force-switch/party-wipe, branch-free) + `params_from_parties`/`initial_state` numpy bridge. `import jax` 모듈, 코어 numpy-only(`__init__` 미import).
- **AC2** — `tests/test_jax_battle_full_parity.py`(importorskip): numpy `Battle(commit_mode=False)`(starter 3 vs boss 1) 대비 **parity 0 mismatch** — action 배터리(attack/switch/item-heal/force-switch/party-wipe/truncation) + random 시퀀스(고정 seed). 매 턴 party_a_hp·active_a·boss_hp·done·winner·turn 일치. + jit/vmap smoke.
- **AC3** — `scripts/bench_throughput.py` full-battle vmap 행(numpy vs jax). 정직 framing("빠르다"=부등식 성립 시).
- **AC4** — core CI numpy-only 불변: 310 tests 무회귀(jax_battle_full importorskip 격리, `__init__` 미import). canonical clean.
- **AC5** — **freeze 전 pilot**으로 R1(parity)·R2(jit)·R3(speed-order) 측정. parity mismatch는 비협상 수정. pilot 결과·확정 report 박제.
- **AC6** — 측정/정직 보고: parity 0 mismatch 박제 + 속도=vmap·CPU·single-run 라벨 + **한계효용 정직**(commit이 load-bearing 경로·full-env 통합 별도) 명시.
- **AC7** — 문서: jax-throughput.md(§5 #1 ✅ + 코드 포인터) + DESIGN §4 + CHANGELOG + INITIATIVE. broken-link 0.

## 후속

- **non-commit full-env 통합** — jax_env에 non-commit 배틀 분기(현 commit-only). 별도.
- **커밋 단위**(feature/jax-battle-full): ① state/params/step + parity 테스트 → ② bench + 문서.
