# CritterGym AI 하네스 도입 — Master Plan

> 단계 어휘 (L1·G1·L2·G2·L3) 매핑: [rules/80-task-lifecycle.md](../../../.claude/rules/80-task-lifecycle.md#단계-어휘-stage-vocabulary-ssot)
> 작성일: 2026-04-18 | 개정: 2026-04-24 (Phase 3 완료)
> 상태: Phase 0·1·2·3 완료 / Phase 4·5·6 대기
> 담당: park

---

## SSOT 원칙

**환경 코어 명세(env spec)가 CritterGym 코드베이스의 단일 출처(Single Source of Truth)**.

```
critter-rl-env/
├── crittergym/          # 환경/spaces/wrappers/render/agents — RL 코어 코드
├── docs/                # 설계 기록·가이드·레시피 — AI 컨텍스트 소스
└── .claude/             # rules/hooks/skills/agents/context — 하네스
```

- **명세 SSOT**: Gymnasium API 계약 (`reset()` / `step()` 5-tuple, `observation_space` / `action_space` 일관성, 결정적 시드)
- **코드 반영본**: `crittergym/` 의 실제 env/wrapper 구현체 (명세를 코드로 구현)
- **무결성 룰**: 구현체의 모든 동작은 명세와 일치해야 함. API 계약 변경은 명세에 먼저 반영 후 구현 동기화.
- **하네스 역할**: `.claude/` 가 이 SSOT 를 강제 (비결정적 reset 금지, step 반환 5-tuple 검증, vectorize 안전성 권장)

---

## 진행 순서 원칙

하네스는 **강제 게이트**이므로 강제할 기준이 먼저 존재해야 함. 따라서:

1. **Phase 1 — 명세를 코드 계약으로 반영** (Gymnasium API 계약 정렬 + 결정성 보장 도입)
2. **Phase 2 — 기존 코드의 비결정/비벡터화 패턴을 안전한 형태로 마이그레이션**
3. **Phase 3 — 하네스 설치**: 이 시점에는 SSOT 가 지켜진 상태라 hooks/skills 가 유의미한 검증을 수행

이 순서는 "인과가 뒤집힌 하네스 → SSOT → 마이그레이션" 을 방지.

---

## 목표

CritterGym RL 환경 코드베이스(`critter-rl-env`)에 **env 계약 하네스 + Task 라이프사이클 + 결정성 안전장치**를 통합한 Claude Code 하네스를 도입한다.

**최종 상태**:
- Claude Code가 RL 환경 계약 규칙을 자동으로 강제 (Hook + Rules + Skills)
- 작업 lifecycle(plan → 구현 → verify 루프)이 `/task-*` 슬래시 커맨드로 표준화
- 결정성·재현성 안전장치가 적용 (시드·reset·step 계약)
- pass-criteria 와 lifecycle 문서가 on-demand 로드

**가치**:
- 계약 위반(비결정적 reset, 잘못된 step 반환 형태 등) 자동 차단/경고
- 작업 시작 시 PRD, 완료 시 결과 리포트 + QA 체크리스트 자동 생성
- TDD + 벡터화 벤치 기반 자동 검증 루프
- 명세 우회 변경 / 재현성 깨짐 사고를 구조적으로 방지

---

## 현재 상태

### 자산 (이미 있는 것)
- `critter-rl-env/.claude/`
  - `commands/` — task-start, task-end
  - `settings.json`, `settings.local.json`
- 루트 `CLAUDE.md` — 패키지 구조, env 계약, 모듈 아키텍처
- 사용자 메모리

### 갭 (도입 후 갖춰질 것)
- ❌ `.claude/rules/` — 경로 매칭 자동 규칙
- ❌ `.claude/hooks/` — 결정적 가드레일 (Python 훅)
- ❌ `.claude/skills/` — 도메인 슬래시 커맨드
- ❌ `.claude/skills/task-verify`, `task-loop` — 검증 루프
- ❌ `.claude/agents/` — 서브에이전트 (plan-reviewer + qa-verifier)
- ❌ `.claude/context/` — pass-criteria, lifecycle 레퍼런스
- ❌ Pass criteria 정의 — task-verify가 사용할 통과 기준 미설계

### 파생 작업 (2026-04-18 추가)
계약 훅 활성화의 전제 조건인 **벡터화 백엔드 정렬**을 조사한 결과, 일부 env 가 순수 NumPy 루프에 묶여 있어 JAX 타깃 벡터화로 옮기기 전에는 perf 훅이 의미 있는 검증을 못 하는 것으로 나타나 **선결 작업이 파생**됨. 별도 서브플랜으로 분기:

- ✅ **Phase A 완료 (2026-04-18)**: 핵심 env step 루프를 배열 연산 형태로 1차 정리, 시드 경로 단일화
- 🟡 **Phase B 대기**: JAX 호환 패치 + vmap 적용 (2-3일)
- ⚪ Phase C/D: 벤치 파이프라인 단순화, 레거시 루프 정리

상세: jax-vectorization 서브플랜 (계획 단계)

---

## 선결 조건

| 조건 | 이유 | 상태 | 담당 |
|---|---|---|---|
| env 계약 명세 정리 | 훅이 검사할 대상이 코드에 있어야 함 | 🟡 JAX 벡터화 전제 (서브플랜 Phase B 후) | park |
| 결정성/시드 경로 확보 | SSOT가 비면 훅 무력 | ✅ **확인** (단일 RNG 경로) | — |
| `python3` 환경 확인 | 모든 훅이 Python | ✅ 3.9.6 확인 | — |
| `ripgrep (rg)` 설치 | 스킬에서 사용 | ✅ 14.1.1 확인 | — |
| 벤치/프로파일 도구 동작 확인 | task-verify 루프에서 사용 | ✅ 환경 확인됨 | — |
| **JAX 벡터화** | perf 훅의 un-vectorized loop 감지 로직이 배열 백엔드 가정 | ✅ **완료** (2026-04-20, 서브플랜 Phase A~F) | — |
| **env 코어 소유권 확보** | 계약 패치 권한 필요 | ✅ **완료** (2026-04-18) — `crittergym/` 내부 | — |

**주의**: 명세 정렬(Phase 1)은 env 계약 변경과 재현성 회귀 검증을 포함하므로 `experiment/env-contract` 같은 feature 브랜치 위에서 진행 권장.

---

## 작업 범위

### 하네스 레이어 모델 (가로 × 세로)

```
                [ 🔵 Process Layer (horizontal) ]
                task-start, task-end, task-evaluate,
                task-verify, task-loop,
                @plan-reviewer, @qa-verifier,
                rules/0X-forbidden, rules/80-task-lifecycle,
                hooks/harness-*, git-policy-guard
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
[ 🟢 rl-env Vertical ] [ 🟡 render ]   [ 🟠 Future ]
env/spaces/wrappers    viewer/render    agents- / perf-
계약 검증 훅           결정성 검증      baseline eval / 벡터화
context, pass-criteria
```

- **🔵 Process layer (horizontal)**: 도메인 무관. **모든 작업** (rl-env·render·agents 등) 의 lifecycle 관리. Phase 4 가 구축
- **🟢 rl-env vertical**: 환경/spaces/wrappers 도메인 (Phase 1·2·3 완료)
- **🟡 render vertical**: 렌더링/뷰어 결정성 안전장치 (Phase 4c 에서 추가)
- **🟠 Future verticals**: agents(baseline eval), perf(JAX/벡터화) — `prefix-` 컨벤션 + `domain:` frontmatter 로 추가

별도 하네스 분리 없음. 단일 `.claude/` 안에서 prefix + frontmatter 로 layer 구분.

### 디렉토리 구조 (Phase 4 완료 시)

```
critter-rl-env/
├── CLAUDE.md                          # Top Rules + Task Lifecycle 섹션
├── .claude/                           # 단일 하네스 (Phase 3 tracked)
│   ├── settings.json                  # team-shared (allow + deny + hooks + env)
│   ├── settings.local.json            # gitignored (개인 누적 allow)
│   ├── projects/                      # gitignored (개인 세션)
│   ├── rules/
│   │   ├── 00-forbidden, 80-task-lifecycle  # 🔵 horizontal
│   │   ├── 85-git-policy                     # 🔵 horizontal
│   │   └── 9X (rl-env / render)              # 🟢🟡 vertical
│   ├── hooks/
│   │   ├── harness-*.py, git-policy-guard.py # 🔵 horizontal
│   │   ├── agent-worktree-*.py               # 🔵 horizontal
│   │   └── (도메인 계약 훅)                  # 🟢🟡
│   ├── skills/
│   │   ├── task-start, task-end, task-evaluate, task-verify, task-loop  # 🔵
│   │   └── (도메인 skill)                    # 🟢🟡
│   ├── agents/
│   │   └── plan-reviewer, qa-verifier        # 🔵 horizontal
│   ├── context/
│   │   ├── lifecycle/                        # 🔵 process docs (pass-criteria 등)
│   │   └── (도메인 context)                  # 🟢🟡
│   └── data/                                 # SSOT JSON (필요 시)
└── docs/
    └── harness/
        ├── explanation/master-plan.md   # 본 문서
        ├── explanation/process-diagram.md  # 작업 프로세스 청사진
        ├── phases/                      # Phase 별 plan/report
        ├── checklists/                  # Phase 별 QA
        └── decisions/                   # ADR
```

---

## Phase 요약

| Phase | 내용 | 기간 | 상태 | 주요 산출물 |
|---|---|---|---|---|
| 0 | 사전 준비 (백업·환경) | 0.5일 | ✅ 완료 (2026-04-23) | 백업 파일, 환경 확인 완료 |
| **1** | **env 계약 정렬** — Gymnasium API 계약 정렬 + 결정성/시드 단일화 | 1~1.5일 | ✅ 완료 (2026-04-24) | reset/step 계약 정렬, 단일 RNG 경로 |
| **2** | **결정성/벡터화 마이그레이션** — 기존 코드의 비결정 reset·un-vectorized loop 를 안전 형태로 일괄 정리 | 2~3일 | ✅ 완료 (2026-04-24) | 412 files 스캔, 비결정 패턴 정리, defer 46, whitelist 3 |
| **3** | **하네스 도입** — `.claude/` 설치 (rules/hooks/skills/agents/context) + Top Rule 추가 | 1.5일 | ✅ 완료 (2026-04-24) | `.claude/` 설치, 영문 slug 통일, CLAUDE.md Top Rule, settings.json strict=0 |
| **3 보강** | **retroactive `domain:` frontmatter** — 기존 rules + agents + skills + hooks 에 `domain:` 필드 추가 | 30분 | ✅ 완료 (2026-04-25) | frontmatter 갱신, Phase 4d rules/80 강제 준비 |
| **4a** | **Task lifecycle 기반** — Skill 변환 + plan-reviewer/qa-verifier agent + multi-agent verdict aggregator | 1일 | ⚪ 대기 | `/task-start`, `/task-end` Skill, `@plan-reviewer`, `@qa-verifier` |
| **4b** | **TDD 검증 루프** — `/task-verify`, `/task-loop`, pass-criteria | 1일 | ⚪ 대기 | TDD micro/macro loop 동작 |
| **4c** | **render + L2 hook 통합** — 결정성 가드 hook + render rules + CLAUDE.md 슬림화 | 0.5일 | ⚪ 대기 | 비결정 렌더 차단, render 계약 rule |
| **4d** | **Multi-reviewer L3** — `@qa-verifier (+ 도메인 reviewer)` 병렬 합의, rules/80-task-lifecycle | 0.5일 | ⚪ 대기 | L3 합의 로직, rules/80 |
| 5 | 운용 + strict 전환 | 1주 | ⚪ 대기 | warning→strict, false-positive 튜닝, 운용 리포트 |

**Critical path**: 0 → 1 → 2 → 3 → 4a → 4b → 4c → 4d → 5

**참고**:
- 다이어그램 [process-diagram.md](./process-diagram.md) 가 Phase 4 청사진. 3 loop (L1 계획·L2 TDD·L3 리뷰) + 2 gate (DoR·DoD) 가 Phase 4a~4d 에서 단계적으로 구현
- 레이어 아키텍처 [layer-architecture.md](./layer-architecture.md) — 단일 `.claude/` 안의 horizontal/vertical 모델 + future vertical 추가 플레이북
- 시나리오·비용 [cross-vertical-scenarios.md](./cross-vertical-scenarios.md) — E2E 다중 vertical 작업 동작 + 토큰 절감 12 전략 + 비용 한계선

---

## Phase별 계획

### Phase 0 — 사전 준비 (0.5일)

**목표**: 안전한 설치를 위한 백업 + 환경 확인

- [ ] `.claude.backup-2026-04-23` 생성
- [ ] `CLAUDE.md.backup` 생성
- [ ] 환경 확인: `python3 --version`, `which rg`, `python -m crittergym --version`
- [ ] 본 master-plan.md 리뷰 / 승인

**완료 기준**: 백업 파일 존재, 환경 의존성 모두 OK

---

### Phase 1 — env 계약 정렬 (1~1.5일)

**목표**: Gymnasium API 계약(reset/step 시그니처, space 일관성, 결정적 시드)을 실제 `crittergym/` 코어에 정렬. 이후 Phase 2 마이그레이션 target 을 확보.

#### Step 1.1: Gap 분석 (1시간)
현재 env 구현체 vs Gymnasium 표준 계약 전수 diff:
- `reset(seed=...)` 가 `(obs, info)` 반환하는지, 시드를 실제로 RNG 에 주입하는지 목록화
- `step()` 가 `(obs, reward, terminated, truncated, info)` 5-tuple 반환하는지 확인
- `observation_space` / `action_space` 가 실제 반환값과 dtype·shape 일치하는지 카테고리별 커버리지 확인

출력: `docs/_archive/2026-Q2/env-core/02-contract-alignment/contract-gap-analysis.md` — gap 목록 + 반영 전략 결정

#### Step 1.2: 시드/결정성 단일화 규칙 (30분)
산발적 `np.random` 전역 호출 → 단일 `self.np_random` 경로:
| 기존 패턴 | 정렬 후 | 이유 |
|---|---|---|
| `np.random.randint(...)` | `self.np_random.integers(...)` | seed 재현성 보장 |
| 모듈 전역 RNG | env 인스턴스 RNG | 병렬 env 간 시드 격리 |
| 미시드 reset | `reset(seed=...)` 경유 | Gymnasium 계약 준수 |

출력: `docs/harness/decisions/001-determinism-seeding.md`

#### Step 1.3: reset/step 계약 정렬 (반나절)
Step 1.1 gap 리스트 기반으로 누락된 계약 요소 보강. 기존 동작과 불일치하는 경우 **명세 우선** — 단 baseline 에이전트 성능에 영향 주면 리뷰 후 결정.
- `reset` 5-tuple/2-tuple 시그니처 정정
- `terminated` vs `truncated` 분리 (구 `done` 단일 플래그 제거)
- 테스트 실행 후 `pytest crittergym/tests/contract` 성공

#### Step 1.4: space 일관성 검증 레이어 등록 (반나절)
환경 클래스마다 `observation_space.contains(obs)` 자가검증 헬퍼 등록:
```python
def _assert_obs(self, obs):
    assert self.observation_space.contains(obs), "obs out of space"
# ...
```
- 정의만 — 전체 코드 적용(Phase 2 로 미룸)
- 모든 등록 env 가 contract 테스트 커버

#### Step 1.5: 명세 물리 위치 결정 (30분)
옵션:
- **A**: 계약을 docstring + contract 테스트로 **코드 내 명세**로 유지 (단일 진실) — 권장
- **B**: 별도 `SPEC.md` 로 prose 명세 병존 — 이중 관리 부담

A 기준으로 진행하되 결정사항을 `docs/harness/decisions/002-spec-placement.md` 에 기록.

#### Step 1.6: 재현성 회귀 검증 (1-2시간)
- 고정 시드로 rollout 2회 실행 → 동일 trajectory 확인
- 주요 env(기본 grid, 절차생성 맵, 멀티에이전트) 재현성 검증
- 계약 변경이 기존 baseline eval 점수를 깨지 않는지 확인

**완료 기준**:
- [ ] 모든 env 가 Gymnasium reset/step 계약 100% 준수
- [ ] 모든 RNG 사용처가 인스턴스 시드 경로 경유
- [ ] `pytest crittergym/tests` 성공
- [ ] 재현성 회귀 0건
- [ ] Step 1.1 gap 리스트가 모두 해소 or 명시적 defer

**리스크**:
| 리스크 | 대응 |
|---|---|
| 전역 RNG 를 직접 쓰는 코드가 다수 | 인스턴스 RNG alias 임시 유지 (deprecated 표기), Phase 2 에서 정리 |
| 동작 불일치 발견 시 원본 판단 | 명세(계약) 우선, 의심스러우면 메인테이너 컨펌 |
| `done` → `terminated/truncated` 분리가 baseline 코드 깨뜨림 | shim wrapper 임시 제공 |

---

### Phase 2 — 결정성/벡터화 마이그레이션 (2~3일)

**목표**: 기존 코드베이스에서 **비결정 패턴 + un-vectorized loop** 를 안전한 형태로 대체. "하네스가 감시할 상태" 를 청결하게 만든다.

#### Step 2.1: 스캔 (1시간)
계약 가드 로직 또는 단순 `grep` 로 스캔:
- **비결정 reset**: 시드 미주입 `reset()`, 전역 `np.random.*`
- **un-vectorized loop**: env step 내 Python `for` 루프 over agents/cells (벡터화 가능 패턴)
- **잘못된 step 반환**: 4-tuple `done` 반환, info dict 누락

출력: `docs/_archive/2026-Q2/env-core/03-determinism-migration/scan.md` — 카테고리별 count + 파일 경로

#### Step 2.2: 자동 변환 도구 준비 (반나절)
안전 변환을 별도 독립 스크립트로 먼저 추출:
- `scripts/migrate-rng.py` — 전역 RNG → 인스턴스 RNG safe replacement
- dry-run 모드 + diff 출력
- 화이트리스트(변환 제외 경로/패턴) 지원

#### Step 2.3: 일괄 변환 — 1차 안전 범위 (1일)
- env 코어 파일 (`crittergym/envs/**`)
- RNG 직관 변환 (`np.random.randint` → `self.np_random.integers`)
- 1 카테고리씩 (rng → reset → step-return) 커밋 분리
- 각 커밋 후 재현성 체크

#### Step 2.4: 일괄 변환 — 2차 wrapper/agent (반나절~1일)
- wrapper 와 baseline agent 의 시드 전파
- 조건부 분기 (벡터화 vs 스칼라 경로) 는 수동 리뷰 대상
- 자동 변환 후 각 env rollout 실측

#### Step 2.5: 수동 리뷰 케이스 (반나절)
- 의도적 비결정 (예: 외부 시뮬레이터 stochasticity, 명시적 noise injection) 는 화이트리스트 등록
- 화이트리스트: `.claude/data/determinism-whitelist.json` (Phase 3 설치 시 이관)

#### Step 2.6: 재현성 전수 검증 (1시간)
- 주요 10~15개 env (이전 작업에서 실측한 리스트 재사용)
- 고정 시드 trajectory diff
- 스트릭트 실패 시 Step 2.3/2.4 재검토

**완료 기준**:
- [ ] 비결정 reset 0건 (화이트리스트 제외)
- [ ] un-vectorized hot loop 0건 (화이트리스트 제외)
- [ ] 계약 검사 통과 (하네스 설치 전 수동 실행)
- [ ] 재현성 회귀 0건
- [ ] 화이트리스트 JSON 작성됨

**리스크**:
| 리스크 | 대응 |
|---|---|
| 자동 변환 false positive | dry-run + 1 카테고리씩, 커밋 분리 |
| 벡터화 변환이 1:1 아님 (semantics 의존) | 수동 리뷰로 분기 |
| 외부 시뮬레이터 비결정 대량 발생 | 화이트리스트 + 문서화 |
| 변환 후 테스트 실패 | 카테고리별 커밋으로 revert 단순화 |

---

### Phase 3 — 하네스 도입 (1.5일)

**목표**: `.claude/` 하네스(rules/hooks/skills/agents/context) 설치 + Top Rule 추가. Phase 1·2 로 정비된 SSOT 상태를 하네스가 지속적으로 강제하는 게이트 설치.

**선결**: Phase 1 완료 (계약 정렬), Phase 2 완료 (코드 청결)

#### Step 3.1: 하네스 골격 설치 (30분)
```bash
DST=".claude"
for d in rules hooks skills agents context data; do
  mkdir -p "$DST/$d"
done
```

#### Step 3.2: 설계 문서 → `.claude/context/` 통합 (1시간)
`docs/` 의 설계 문서를 `.claude/context/` 에 매핑:

| docs 원본 | `.claude/context/` 대상 |
|---|---|
| 환경 원칙 노트 | `.claude/context/principles/` |
| 구현 가이드 | `.claude/context/patterns/` |
| 레시피 | `.claude/context/recipes/` |
| env/wrapper 모듈 노트 | `.claude/context/modules/` |
| 설계 기록 | `docs/decisions/` (ADR) |

중복되는 경우 버전 비교 후 최신본 유지.

#### Step 3.3: 계약 레퍼런스를 `.claude/context/contracts/` 에 배치 (30분)
- Gymnasium API 계약 요약 → `.claude/context/contracts/gym-api.md`
- 결정성/시드, space 일관성, render 계약도 각 `.md` 로 정리
- 각 파일 상단에 "SSOT: contract 테스트 + docstring" 명시

#### Step 3.4: rules/ 경로 패치 (30분)
| 파일 | 기존 paths | 수정 후 |
|---|---|---|
| (env 계약 rule) | `**` | `crittergym/envs/**`, `crittergym/wrappers/**` |
| (render rule) | `**` | `crittergym/render/**` |
| (perf rule, future) | 필요 시 경로 추가 | `crittergym/**` (hot path) |

#### Step 3.5: SSOT 데이터 설치 + 갱신 (1시간)
- `determinism-whitelist.json` → `.claude/data/` (Phase 2 산출물 이관, 값 검증)
- `protected-paths.json`: 이 레포 경로로 조정 (contract 테스트 경로 등)
- 기타 도메인 데이터: 필요 시점에 생성

#### Step 3.6: `settings.json` 머지 (30분)
- 기존 `.claude/settings.json` 을 `settings.json.backup` 으로 보존
- 아래 섹션을 머지:
  - `permissions.allow` — `Bash(python3 .claude/hooks/*.py:*)` 등
  - `permissions.deny` — 보호 경로 Write, `Bash(rm -rf:*)` 등
  - `env` — `HARNESS_HOOKS_DEBUG=0`, `HARNESS_HOOKS_STRICT=0` (시작은 warning)
  - `hooks` — 이벤트 훅 통째로 머지

#### Step 3.7: CLAUDE.md 머지 + **Top Rule 추가** (1.5시간)
- 기존 CLAUDE.md 섹션 유지: Project Overview, Development Commands, Architecture, Important Patterns, Environment Variables, Testing
- **Top Rule 추가** (SSOT 원칙 + 계약 강제):
  ```markdown
  ## RL 환경 Top Rules (요약)
  1. 환경 계약 SSOT = Gymnasium API + contract 테스트. env 변경 시 반드시 계약 준수.
  2. reset 은 `(obs, info)`, step 은 `(obs, reward, terminated, truncated, info)`.
     계약 위반은 빌드 실패 범주 (hook 감지).
  3. 비결정 reset·전역 RNG 금지. 인스턴스 시드(`self.np_random`) 사용.
  4. env/wrapper 수정 전 해당 모듈의 계약 노트 확인.
  5. 새 결정 사항은 `docs/decisions/` 에 ADR 로 기록.
  ```
- Task Lifecycle 섹션은 Phase 4 에서 활성화

#### Step 3.8: 동작 확인 (30분)
- `python3 .claude/hooks/_lib/rules_loader.py` 실행 무에러
- 새 Claude Code 세션에서 도메인 skill 호출 — 정상 응답
- 계약 auditor 서브에이전트 스폰 — Phase 2 청결 상태 재확인 (0건 이어야 함)

**완료 기준**:
- [ ] `.claude/{rules,hooks,skills,agents,context,data}/` 모두 존재, 내용 설치 완료
- [ ] `.claude/context/contracts/` 에 계약 레퍼런스 반영
- [ ] CLAUDE.md 에 SSOT Top Rule 추가됨
- [ ] 슬래시 커맨드·서브에이전트 호출 시 에러 없음
- [ ] 계약 검사 Phase 2 청결 상태 재확인 0건
- [ ] `HARNESS_HOOKS_STRICT=0` (warning 모드 시작)

**리스크**:
| 리스크 | 대응 |
|---|---|
| 기존 `.claude/settings.json` 의 다른 설정과 충돌 | 백업 후 수동 머지, 충돌 발생 시 기존 우선 |
| 훅이 모든 Edit에 트리거되어 느려짐 | matcher 적용 확인 (Write/Edit만), strict=0 으로 시작 |
| 설계 문서 간 중복·상충 | Step 3.2 에서 수동 리뷰, 최신본 우선 |

---

### ~~Phase 5 — render 3계층 안전장치~~ (Phase 4c 로 흡수됨)

> **이 phase 는 2026-04-25 재편 시 Phase 4c 로 흡수.** render 결정성 hook 은 L2 의 acceptance 일부 (pass-criteria 의 `render_warning_0`) — 별도 phase 로 둘 가치가 부족.

---

### Phase 4 — Task 라이프사이클 통합 (3일)

> 청사진: [process-diagram.md](./process-diagram.md) — 3 loop (L1·L2·L3) + 2 gate (DoR·DoD)
> 4a → 4b → 4c → 4d 순차 진행. 모든 산출물은 **horizontal layer** (도메인 무관).

**목표**: 다이어그램 기준 RFC + ATDD + Multi-Reviewer PR 프로세스를 결정적 슬래시 커맨드 체인으로 구현. rl-env 외 future vertical (render, agents, perf) 도 같은 layer 재사용.

---

#### Phase 4a — Lifecycle 기반 (1일)

**범위**: Skill 변환 + horizontal agents 신규 + multi-agent verdict aggregator

##### Step 4a.1: task-start, task-end → Skill 변환 (반나절)
- `.claude/commands/task-{start,end}.md` → `.claude/skills/task-{start,end}/SKILL.md`
  - Frontmatter: `name`, `description` (when_to_load 키워드 — "계획", "작업 시작", "리포트", "완료"), `allowed-tools`, `domain: lifecycle`
  - 기존 `commands/` 파일은 stub 으로 (Skill 호출 redirect) 또는 삭제

##### Step 4a.2: `agents/plan-reviewer.md` 신규 (1시간) 🆕
- 모델: Sonnet (계획 평가는 추론 깊이 필요)
- 격리 컨텍스트, 메인에 verdict 만 반환 (`APPROVE | SUGGEST: <list> | BLOCK: <reason>`)
- 평가 축: 범위 명확성, 영향도 분석 충분성, 리스크 식별, 검증 방법 적정성, 산출물 명시 여부
- `domain: lifecycle` (모든 작업에 사용)

##### Step 4a.3: `agents/qa-verifier.md` 신규 (1시간) 🆕
- 모델: Haiku (격리 + 저렴, 상시)
- DoD/DoR 검증 전담, plan ↔ 결과 정합성 비교
- `domain: lifecycle`

##### Step 4a.4: `skills/task-evaluate/` 신규 (1시간) 🆕 — **L1 평가 진입점**
- 사용자 호출: `/task-evaluate` 또는 `/task-start` 내부 자동
- 동작: `@plan-reviewer` (+ 도메인 auditor 가 추가됐다면 함께) **병렬 스폰** → verdict aggregator → 사용자에게 종합 결과
- aggregator 로직:
  - 모두 APPROVE → L1 종료, G1 진입
  - 1개 이상 BLOCK → 계획 보완 → L1 재진입
  - SUGGEST 만 → 사용자 컷오프 가능

##### Step 4a.5: 통합 동작 확인 (30분)
- 더미 plan.md 작성 → `/task-evaluate` → 병렬 verdict 출력 확인
- L1 loop 5회 이내 종료 가능성 검증

**4a 완료 기준**:
- [ ] `/task-start`, `/task-end` Skill 동작
- [ ] `@plan-reviewer`, `@qa-verifier` 스폰 가능
- [ ] `/task-evaluate` 가 ≥2 agent 병렬 호출 + verdict aggregate
- [ ] `domain: lifecycle` frontmatter 일관 적용

> **현재 기본 reviewer 세트**: `@plan-reviewer` + `@qa-verifier` 두 개만 기본 동봉. 도메인 전용 auditor (`@rl-env-auditor`, `@perf-auditor` 등) 는 vertical 추가 시 옵션. routing 확장점은 layer-architecture 참조.

---

#### Phase 4b — TDD 검증 루프 (1일)

**범위**: G1 통과 → QA criteria → L2 TDD micro/macro → G2 DoD

##### Step 4b.1: `pass-criteria.md` 설계 (1시간)
`.claude/context/lifecycle/pass-criteria.md`:
```yaml
default_passes:
  type_check:    mypy crittergym
  lint:          ruff check
  unit_tests:    pytest
  contract:      pytest crittergym/tests/contract   # selective
  reproducibility: 고정 시드 rollout 2회 동일 trajectory
  contract_hooks: env-contract-check + determinism-guard warning 0건 (strict 시 차단)
plan_overrides:
  # plan.md frontmatter 의 passes: 가 default 를 override
```
**G1 통과 시점에 plan.md 의 acceptance criteria 와 함께 qa-checklist.md 초안 자동 생성** — ATDD 정석.

##### Step 4b.2: `skills/task-verify/` 신규 (반나절) — **L2-inner check + G2**
- Input: plan.md + qa-checklist.md
- 단계: 수집 → 분류 (TDD/Bench/Manual) → 실행 → 자동수정 (whitelist) → 갱신
- 출력: `pass | partial | fail` + iteration log
- 자동수정 whitelist: 전역 RNG→인스턴스 RNG, unused import, `done`→`terminated/truncated` shim (Phase 2 mapping 재사용)
- `scripts/run-tdd.py`, `scripts/run-bench.py` (벡터화 벤치 wrapper)

##### Step 4b.3: `skills/task-loop/` 신규 (1시간) — **L2-outer**
- `/task-verify` 자율 N회 반복
- 종료 조건:
  - `all_passed` — 모든 acceptance pass
  - `max_iterations=5` — 컷오프
  - `no_progress` — 동일 fail 2회 연속 (사용자 에스컬레이션)
  - `critical_blocker` — type-check/contract 테스트 실패는 즉시 중단

##### Step 4b.4: TDD 가드와 task-loop 협업 (1시간)
- 매 PostToolUse 마다 test 우선 작성 강제 (TDD 가드)
- task-loop 내부의 매 iteration 마다 가드 verdict 확인 후 진행

##### Step 4b.5: G2 게이트 명세화 (30분)
- `/task-verify` 결과 = `pass` 일 때만 G2 통과 (자동)
- `partial` 또는 `fail` → L2 재진입
- `max_iterations` 도달 → 사용자 에스컬레이션

**4b 완료 기준**:
- [ ] `/task-verify` 1회 호출 시 TDD + bench + 자동수정 + 리포트 갱신
- [ ] `/task-loop` 자율 5회 반복 + 4종 종료 조건 동작
- [ ] G2 통과 자동 판정

---

#### Phase 4c — render + L2 hook 통합 (0.5일, 기존 Phase 5 흡수)

**범위**: render 결정성 가드를 L2 의 acceptance 일부로 통합

##### Step 4c.1: render 결정성 hook 신규 (30분) 🆕
- PostToolUse(Write|Edit) — `crittergym/render/**` 에서 시드 미주입 난수·시간 의존 렌더 감지
- `domain: render` (vertical)

##### Step 4c.2: settings.json deny 강화 (15분)
- 보호 경로 (contract 테스트 baseline 등) Write 차단 검증

##### Step 4c.3: render 계약 rule 신규 (30분)
- 적용 paths: `crittergym/render/**`
- 내용: 결정적 렌더 원칙, `rgb_array` 모드 재현성, 프레임 dtype 계약
- `domain: render`

##### Step 4c.4: CLAUDE.md render 섹션 슬림화 (15분)
```markdown
## Render
결정적 렌더만. 시드 미주입 난수·wall-clock 의존 금지 (Hook 감지). 계약: render 계약 rule 참조.
```

##### Step 4c.5: pass-criteria 통합 (15분)
`pass-criteria.md` 의 `contract_hooks` 항목에 render-guard warning 0 포함:
```yaml
hooks:
  contract_warning_0: env-contract-check + determinism-guard
  render_warning_0:   render-determinism-guard
  # 모두 strict 시 차단으로 격상 (Phase 5)
```

##### Step 4c.6: 검증 (15분)
- 모의 테스트: `Edit crittergym/render/viewer.py` 에 wall-clock 의존 추가 → 경고

**4c 완료 기준**:
- [ ] 비결정 렌더 패턴 감지
- [ ] render 계약 rule 존재 + path 매칭
- [ ] CLAUDE.md render 섹션 1-2줄로 축소
- [ ] L2 acceptance 에 render hook 통합

---

#### Phase 4d — Multi-reviewer L3 + rules/80 (0.5일)

**범위**: L3 코드 리뷰 합의 로직 + lifecycle 운용 원칙 규칙화

##### Step 4d.1: `skills/task-review/` 신규 (1시간) 🆕 — **L3 진입점**
- 동작: `@qa-verifier` (+ 도메인 reviewer 가 추가됐다면 함께) **병렬 스폰**
- verdict aggregator: 2+ 모두 `APPROVE` 시만 통과
- BLOCK/SUGGEST → 회귀 개선 후 재진입
- > 기본 동봉은 `@qa-verifier` 1개. 도메인 reviewer (`@rl-env-auditor` 등) 는 vertical 추가 시 함께 병렬 스폰.

##### Step 4d.2: `rules/80-task-lifecycle.md` 신규 (1시간) — **운용 원칙 강제**
적용 paths: 무조건 (모든 작업)

내용:
- **단방향 전진**: G1·G2 통과 후 plan 수정 시 새 task slug 강제
- **병렬 평가**: L1·L3 의 평가 agent 호출은 단일 메시지에 ≥2개 (순차 호출 BLOCK)
- **acceptance 사전 정의**: G1 통과 후 qa-checklist 신규 항목 추가는 BLOCK
- **iteration cap**: L1 ≤ 사용자 컷오프, L2-outer ≤ 5, L3 ≤ 사용자 컷오프
- **no-progress 감지**: 동일 fail 2회 연속 → 사용자 에스컬레이션
- **plan/report 누락 작업 경고**: 큰 변경(N 파일 이상) 시 plan 없으면 SUGGEST

##### Step 4d.3: CLAUDE.md Task Lifecycle 섹션 활성화 (30분)
```markdown
## Task Lifecycle
다이어그램: `docs/harness/explanation/process-diagram.md`

흐름:
1. /task-start — plan.md
2. /task-evaluate — L1 평가 (≥2 agent 병렬) → DoR
3. (G1) — qa-checklist 자동 생성 + acceptance 확정
4. TDD 구현 (task-loop) — L2 자율
5. /task-verify — L2 종료 검증 (G2)
6. /task-review — L3 리뷰 (≥2 agent 병렬)
7. /task-end — report.md
8. 커밋 + 푸쉬
```

##### Step 4d.4: 풀 사이클 E2E (1시간)
- 더미 작업: "예시 wrapper 에 reward clipping 옵션 추가"
- 1~8 순차 실행 → 모든 게이트·loop 동작 확인

**4d 완료 기준**:
- [ ] `/task-review` 가 ≥2 reviewer 병렬 + 합의 판정
- [ ] `rules/80` 가 lifecycle 위반 시 warning 출력
- [ ] CLAUDE.md Task Lifecycle 섹션이 다이어그램 reference 포함
- [ ] 풀 사이클 1회 통과

---

**Phase 4 전체 리스크**:
| 리스크 | 대응 |
|---|---|
| 토큰 비용 (여러 agent × 매 작업) | Haiku 격리 (qa-verifier), Sonnet 만 plan-reviewer, max_iterations 컷 |
| 벤치 세션 누수 | 매 iteration 격리 프로세스, 결과만 회수 |
| 자동수정 의도 외 변경 | whitelist (rng, unused import) 만, 그 외 사용자 승인 |
| 교착 (같은 fail 반복) | no_progress 감지 → 즉시 사용자 에스컬레이션 |
| L1 평가 agent 가 false positive | verdict aggregator 가 SUGGEST 만 있을 때 사용자 컷오프 허용 |
| domain frontmatter 누락 시 wrong agent 호출 | rules/80 가 frontmatter 강제 검증 |

---

### ~~Phase 4 — SSOT 데이터 채우기~~ (흡수됨)

> **이 phase 는 2026-04-23 재편 시 Phase 1·2·3 으로 분해·흡수됨**
>
> - tokens 반입 류 작업은 RL 환경에 해당 없음 → 계약 정렬(Phase 1)·결정성 마이그(Phase 2)·하네스 설치(Phase 3)로 분해
> - whitelist / protected-paths 데이터 → **Phase 3 Step 3.5** (하네스 설치 시 경로 조정)

---

### Phase 5 — 운용 + strict 전환 (1주 운용, 기존 Phase 6)

**목표**: Phase 4 통합 직후 1주 warning 모드 운용 후 strict 활성화. multi-agent · multi-loop 의 토큰·UX 비용 튜닝.

#### Step 5.1: warning 모드 운용 (1주)
- `HARNESS_HOOKS_STRICT=0` — 위반 경고만 출력
- 팀 피드백: false positive 빈도, 적응 난이도, agent 호출 토큰 비용

**메트릭 수집** (session-report hook 이 매 Stop event 시 출력):
```yaml
session_metrics:
  total_tokens: int                    # 작업당 토큰 합계 (200k 임계값)
  agent_calls:                          # vertical 별 호출 수
    plan-reviewer: int
    qa-verifier: int
    rl-env-*: int (if added)
    perf-*: int (future)
    render-*: int
  hook_fires:                           # vertical 별 발화 횟수
    rl-env-*: int
    render-*: int
    harness-*: int
  iterations:
    L1: int                             # 평균 / 최대
    L2-outer: int
    L3: int
  no_progress_count: int                # rules/80 강제 에스컬레이션
  threshold_violations:                 # 비용 폭주 신호 카운트
    tokens_200k_plus: int
    agent_10_plus_per_step: int
    L2_max_5_reached: int
```

→ 1주 후 메트릭 분석으로 false positive 빈번 vertical hook matcher 좁힘 + 모델 분배 (Sonnet/Haiku) 재조정 근거 자료.

#### Step 5.2: 튜닝 (반나절)
- false positive 룰 조정 (env 계약 rule, render rule 등)
- 너무 시끄러운 훅 matcher 좁힘
- multi-agent 호출 비용 높으면 Haiku 격리 강화 또는 cap 조정

#### Step 5.3: strict 모드 활성화
- `HARNESS_HOOKS_STRICT=1` — 위반 시 도구 호출 차단
- env-contract-check, determinism-guard 는 처음부터 strict 가능
- L2 의 hook warning 0 조건이 차단으로 격상

#### Step 5.4: 후속 작업
- contract 테스트를 CI 게이트에 통합 (Phase 4 외 별도 gate)
- 회귀 trajectory 스냅샷 테스트 도입 검토
- **향후 vertical 추가 로드맵** — [layer-architecture.md §Vertical 추가 플레이북](./layer-architecture.md#vertical-추가-플레이북) 의 9-step 절차 참조
  - 🟠 agents (baseline 에이전트 / eval 하네스)
  - 🟣 perf (JAX 벡터화 / steps-per-second / 메모리)
  - 🔴 render (rgb_array 재현성 / 프레임 계약) — 4c 에서 기초 도입, 확장 가능
- vertical 추가 시 본 Phase 의 process layer 재사용 — 추가 비용 minimal

**완료 기준**: 1주 운용 보고서, strict=1 활성화, multi-agent 비용 메트릭 안정화, 팀 합의

---

## 일정 요약

| Phase | 내용 | 작업량 | 의존 | 상태 |
|---|---|---|---|---|
| 0 | 사전 준비 | 0.5일 | — | ✅ 완료 |
| 1 | env 계약 정렬 | 1~1.5일 | 0 | ✅ 완료 |
| 2 | 결정성/벡터화 마이그레이션 | 2~3일 | 1 | ✅ 완료 |
| 3 | 하네스 도입 | 1.5일 | 2 | ✅ 완료 |
| **4a** | Lifecycle 기반 (Skill 변환 + agents + verdict aggregator) | 1일 | 3 | ✅ 완료 (2026-04-25) |
| **4b** | TDD 검증 루프 (verify/loop + pass-criteria) | 1일 | 4a | ✅ 완료 (2026-04-26) |
| **4c** | render + L2 hook 통합 (render-guard + render rule) | 0.5일 | 4b | ✅ 완료 (2026-04-26) |
| **4d** | Multi-reviewer L3 + rules/80 | 0.5일 | 4c | ✅ 완료 (2026-04-26) |
| **4e** | 계약 명세 역할 명확화 + drift 감지 (Phase 5 진입 전 정리) | 0.3일 | 4d | ✅ 완료 (2026-04-26) |
| **4f** | 품질 기준 확장 — 벤치·중복·화이트리스트 (Phase 5 진입 전 보강) | 0.4일 | 4e | ✅ 완료 (2026-04-26) |
| 5 | 운용 + strict 전환 | 1주 | 4f | ⚪ 대기 |

**총 예상**: 핵심 도입 9-10일 + 운용 1주 = **약 3주**

**Critical path**: Phase 0 → 1 → 2 → 3 → 4a → 4b → 4c → 4d → 5

**의의**: SSOT 정렬(1·2) → 하네스 설치(3) → Lifecycle 통합(4a-d, 다이어그램 청사진) → 운용(5). Phase 4 는 horizontal layer 라 향후 모든 vertical (rl-env, render, agents, perf) 에 재사용.

---

## 검증 방법

### Phase별 자동 검증
- Phase 1: contract 테스트 성공 + 재현성 회귀 0건 + 계약 완전 정렬
- Phase 2: 계약 검사 수동 실행 시 비결정 reset 0건, un-vectorized hot loop 0건 (화이트리스트 제외)
- Phase 3: `python3 .claude/hooks/_lib/rules_loader.py` 무에러, 도메인 skill 정상 응답, 계약 auditor 스폰 후 0건 확인
- Phase 4: `/task-verify`, `/task-loop` E2E 시나리오 1개 통과
- Phase 5: 모의 비결정 렌더 편집 시도 → 경고/차단 확인
- Phase 6: 1주 운용 후 false positive < 5%

### 종합 검증
- `mypy crittergym` 통과
- `ruff check` 통과
- 임의 env/wrapper 변경 → `/task-start` → 구현 → `/task-end` → `/task-verify` 풀 사이클 동작
- 1주 후 Stop 훅의 세션 리포트에 의미 있는 메트릭 누적

---

## 리스크와 대응 (전체)

| 리스크 | 영향 | 대응 |
|---|---|---|
| 계약 명세 정리 지연 | Phase 4 블록, 하네스 효용 저하 | dry-run으로 우선 운용, 메인테이너와 주간 동기화 |
| 팀이 하네스 적응 못 함 | 활용도 저하 | strict=0로 시작, 1주 운용 + 피드백 |
| Hook이 false positive 다수 | 작업 흐름 방해 | warning 모드 1주, 튜닝 후 strict |
| 벤치 비용 | task-verify 루프 시 토큰 폭발 | qa-verifier 격리 + max_iterations |
| 기존 .claude/settings.json 충돌 | 다른 설정 손실 | 머지 전 백업, diff 리뷰 |
| **Phase 1 계약 불일치** | 계약 변경이 재현성/baseline 회귀 유발 | Step 1.6 재현성 회귀 검증 필수, 문제 시 Phase 1 Step 1.1 gap 재검토 |
| **Phase 2 자동 변환 false positive** | 대량 회귀 가능 | dry-run + 카테고리 분할 커밋 + env별 rollout 실측 |

---

## 의사결정 필요 사항

1. **task-start/end 설치 전략**: Skill로 변환 vs commands에 그대로 두기 → **권장: Skill 변환** (Phase 4)
2. **strict 모드 전환 시점**: 1주 vs 2주 → **권장: 1주 (WARN 빈도 보고 결정)**
3. **명세 물리 배치 (Phase 1 Step 1.5)**: contract 테스트+docstring 단일 유지 vs 별도 SPEC.md 병존 → **권장: 단일 유지**
4. **통합 브랜치 모델**: 이 solo OSS 프로젝트는 기본적으로 `feature/fix/...` → `main` (trunk). `qa/*` one-way sink 는 옵션 패턴 (rules/85) → **권장: main trunk 직접, qa sink 불필요**
5. **Phase 2 재현성 허용 범위**: trajectory 완전 일치 vs 허용 오차 범위 → **권장: 고정 시드 완전 일치 + 부동소수 엣지 케이스 수동 검토**
6. **experiment 브랜치 vs 별도 브랜치**: Phase 1·2 는 코드 대규모 변경 → **권장: `experiment/env-contract` 위에서 진행**

---

## 다음 단계

1. 본 master-plan.md 리뷰 / 승인 (오늘)
2. Phase 0 시작 — 백업 + 환경 확인
3. Phase 1 착수 — `/task-start "Harness Phase 1: env 계약 정렬"` 으로 plan.md 생성 후 실행
4. Phase 1 완료 후 Phase 2 — 결정성 마이그레이션 (대규모, 커밋 카테고리별 분할)
5. Phase 2 완료 후 Phase 3 — `.claude/` 설치 + 설계 문서 통합 + Top Rule

---

## 참고 문서

- 하네스 설계 narrative: 본 `docs/harness/explanation/` (master-plan, layer-architecture, process-diagram, cross-vertical-scenarios)
- 본 레포 기존: `CLAUDE.md`, `.claude/settings.json`, `.claude/commands/task-*.md`

---

## Mode Tiering — 작업 영향도 기반 lifecycle 분기 (rules/80 §F, harness-mode-tiering 2026-05-01)

### 설계 의도

작업 영향도가 다른데 동일 lifecycle 적용 시 **process 비용이 산출물 비용을 역전**하는 영역 발생:
- 1-3 file 의 docs/test/comment 만 변경 → standard 9 step + ≥2 reviewer 가 과함
- 50+ file cross-vertical 마이그 → standard L2-outer cap=5 가 부족 + 모든 vertical reviewer 의무

→ **3 mode 자동 분기** 도입 (criticality + file count 기반 deterministic):

| Mode | 적용 조건 | 핵심 차이 | 절감 추정 |
|---|---|---|---|
| 🟢 quick-fix | 1-3 file + criticality=low | single reviewer / minimal plan / minimal entry | task당 ~70% (vs standard) |
| 🟡 standard | default | 9 step 전부 (기존 정책) | baseline |
| 🔴 heavy | 50+ file 또는 domains 3+ | L2 cap 5→8 + paths routing 의무 | -20% (vs naive standard) |

### CHANGELOG 강제 (audit minimum floor)

mode 무관 entry 1줄 의무 — quick-fix 도 lifecycle 우회 X. 사유: 6개월 후 "왜/언제/어떤 변경" 추적 가능 floor 보장.

### Tradeoff

| 측면 | mode tiering 도입 | 기존 단일 lifecycle |
|---|---|---|
| 토큰 비용 | ~25% 절감 (전체 평균) | baseline |
| 회귀 위험 | criticality 기반 → 회귀 위험 영역엔 standard/heavy 강제 (자동 분류) | 모든 task standard — over-process |
| 사용자 인지 부담 | mode 자동 감지 + frontmatter 기록 — 추가 입력 0 | 단일 흐름 — 분기 없음 |
| audit trail | mode 무관 CHANGELOG 강제 | 동일 |
| backward compat | mode 부재 = standard | 무관 |

### 후속 evolution

- task `harness-prompt-cache-optimization` (✅ 완료 2026-05-01) — reviewer prompt 의 fixed prefix cache hit (rules/80 §G)
- task `rules80-v2-finalize` (scheduled 2026-05-12) — mode tiering + prompt cache 의 실측 효과 결산

---

## Prompt Cache — reviewer prompt 의 fixed prefix cache hit (rules/80 §G, harness-prompt-cache-optimization 2026-05-01)

### 설계 의도

mode tiering (§F) 도입 후 task당 reviewer 호출이 4-6회 (standard) ~ 8-12회 (heavy) 로
다수 발생. 같은 reviewer (plan-reviewer / qa-verifier / 도메인 auditor) 가 매 호출마다
**가이드 / 원칙 / 형식 제약** 등 동일 정보를 prompt 에 inline 으로 작성하면
Anthropic prompt cache 가 hit 되지 않음 — fixed prefix 매번 미세하게 다르기 때문.

→ helper (`_lib/reviewer_prompt.py`) 를 강제하여 **fixed prefix + variable 분리**
표준화. fixed prefix 가 매 호출 동일하면 자동 cache hit (1024+ token 임계 충족 시).

### 3-layer 구조

```
[Layer 1] SHARED_GUIDELINES (모든 reviewer 공통)
    ↓ lifecycle 9-step / aggregator 4 decision / mode tiering / prompt cache /
      verdict 형식 / MALFORMED 처리 / 모델 격리 / domain frontmatter /
      hook 우선 / 비용 임계
[Layer 2] Agent-specific fixed prefix (agent + purpose 별)
    ↓ plan-reviewer L1: 5축 표준 + 추가 축
    ↓ qa-verifier L1/L3: plan↔결과 정합성 표준
    ↓ (도메인 auditor 추가 시) rl-env-auditor L1: 계약 + 결정성 + 벡터화
[Layer 3] Variable section (이번 task 고유)
    plan path / diff stat / inline 검증 결과 / 이번 task axes
```

### 정량 효과

| Reviewer | fixed prefix size (chars / ~tokens) | 호출당 cache hit 절감 |
|---|---|---|
| plan-reviewer L1 | 4749 / ~1187 | ~30% |
| qa-verifier L1/L3 | 4659 / ~1164 | ~30% |
| (옵션) rl-env-auditor L1 | 5995 / ~1498 | ~30% |

mode 별 task당 절감:
- standard (~5 reviewer 호출) → ~10-15% 추가 (mode tiering 25% + prompt cache 누적 = ~35-40%)
- heavy (~10 reviewer 호출) → ~15-20% 추가 (mode tiering 20% + prompt cache 누적 = ~35-40%)

### Tradeoff

| 측면 | 도입 후 | 도입 전 |
|---|---|---|
| 토큰 비용 | -10-15% (mode tiering 누적 -35-40%) | baseline |
| prompt verbosity | fixed prefix 5-6k chars (cache hit 후 cost 0) | minimal prompt (cache miss) |
| DRY 원칙 | fixed prefix 가 SSOT — agent 변경 시 한 곳만 | 매 호출 inline 중복 |
| 변경 cost | SHARED_GUIDELINES 변경 = 모든 cache invalidation | 매 호출 변경 자유 |
| 일관성 | reviewer 별 표준화 — 호출 결과 reproducible | 호출별 가이드 미세 다름 |

### 주의 — cache invalidation

agent 정의 (.md system prompt) / SHARED_GUIDELINES / fixed prefix 변경 = 모든 cache invalidation.
변경은 별도 task (review 강도 ↑) 에서. 단발 사용자 결정으로 SHARED 변경 금지.

### 후속 evolution

- (없음 — 본 task 가 prompt cache 의 1차 도입)
- 미래 task: per-vertical reviewer 추가 시 (e.g. `render-reviewer`, `perf-reviewer`) FIXED_PREFIX dict 에 entry 추가
