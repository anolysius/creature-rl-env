---
slug: typechart-depth
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC-reliability
task_type: env
mode: standard
domains: [rl-env]
scope_paths:
  - src/critter_gym/types.py
  - src/critter_gym/region.py
  - src/critter_gym/party.py
  - src/critter_gym/envs/critter_env.py
  - src/critter_gym/registration.py
  - tests/test_types.py
  - tests/test_region.py
  - tests/test_env.py
  - tests/test_gym_battle.py   # 무회귀 유지: vary-chart 참조가 num_types subset 반영하도록 1줄 갱신
  - tests/test_meta_difficulty.py
extracted_to: []
supersedes: []
---

# typechart-depth (M3 신뢰성 — 타입 풀 심화)

> 작성일: 2026-06-22 | 상태: 계획

> ## ⚠ DESCOPE NOTE (2026-06-22, 사용자 승인 (가))
> G1 후 **pilot 가 AC3(infer>probe)·keystone(no-heal)을 *달성 불가*로 입증** — no-heal 에선
> switch 비용이 매치업 이득을 압도해 type-blind 가 1위(타입지식이 *손해*)였다. "infer-the-meta 를
> *증명가능하게* load-bearing" 하게 만들려면 open-ended battle-economy 연구가 필요(수렴 미보장).
> **사용자 결정 (가): 디스코프** — 안전한 깊이(K=12 타입 풀 + 보스 타입 재출현 + winnability)만 ship,
> no-heal keystone·infer>probe 게이트는 **드롭**, "추론 provably load-bearing 은 future work"로 DESIGN
> 에 정직히 명시. 아래 본문 중 (b) keystone·AC3·AC4 는 **무효**(취소선 취지) — 유효 acceptance 는 하단
> "## Acceptance Criteria (DESCOPED)" 가 SSOT. (silent 약화 아님 — 전부 transparent·문서화.)

## 목표

**infer-the-meta 를 진짜 필수로.** K=3 라 추론 자명 + (L1) K↑ 단독은 brute-force(틀린 타입 시도→데미지로
교정)로 풀림. 사용자 결정 (1): **K↑ + 값싼 probing 봉쇄.** 핵심 = **gym 간 추론이 within-battle probing
을 이기게** 만든다.

**진짜 brute-forcer 두 종류를 봉쇄해야 함** (L1 round2):
- **within-battle probe**: 한 배틀 안에서 공격→데미지로 effectiveness 관측→교정. → 봉쇄책: 틀린 타입
  probing 이 *누적 비용*(아래 keystone)이라 한 배틀 안 교정만으론 시드 전체를 못 깸.
- **무료 재시도**: 크리처 3 = probe 3번. → 봉쇄책: **gym 간 풀-리힐 제거**(procgen) — 허비한 크리처가
  다음 gym 까지 회복 안 됨 → probing 누적 비용 → *예측(추론)*하는 agent 가 더 많이 깸.

**측정(핵심 게이트)**: scripted 4-arm 으로, **cross-gym 추론 정책이 within-battle probe 정책을 유의하게
앞선다**(numpy-only CI). = 환경이 *gym 간 메타 추론*을 load-bearing 으로 만든다는 직접 증거.

**비협상: M1 무회귀.** 모든 난이도/이코노미 변경은 **procgen 한정**, fixed-v0=M1 불변.

## 선행 조건

- ✅ `generate_typechart(seed, types, vary=True)` 임의 K 지원. **region 호출부가 `types=` 미전달(전체풀
  fallback) + boss 샘플도 전체풀 → 두 호출부 모두 active subset 전달 필요** (L1).
- ✅ battle/creatures 는 타입 값-무관(K 안전). party.py 만 F/W/G + boss 스탯.
- ✅ 현재 "배틀 진입 시 풀 리힐" (`critter_env`) — probing 을 무료로 만드는 지점. procgen 에서 변경 대상.
- ✅ 시드 내 gym 들이 **같은 숨은 차트 공유** → 추론 amortize 가능(기존).

## 설계 결정

### (a) 타입 풀 + num_types (M1 무회귀)
- `ElementType` ~15(FIRE/WATER/GRASS=인덱스 0/1/2 유지, 신규 append → `_TYPE_TO_INT` M1 불변).
- `num_types`(region+env): fixed=3, procgen ≥12. 크리처/gym 타입 = `list(ElementType)[:num_types]`.
  region 의 **boss 샘플·차트생성 둘 다** active 전달. `num_types>3 ∧ vary=False` → ValueError.
- obs 타입 경계=풀 크기(고정), shape 불변.

### (b) keystone — 값싼 probing 봉쇄 (procgen 한정)
- **gym 간 풀-리힐 제거(procgen)**: 배틀 후 HP/기절 상태가 다음 gym 으로 이월(부분 회복만/혹은 미회복).
  → probing 으로 허비한 크리처가 누적 손실 → cross-gym 추론(예측)이 더 많은 gym 격파.
- (필요시) 보스 stat·스텝버짓 보조 튜닝. **튜닝 목표 = 아래 4-arm 게이트(infer ≫ probe) 만족** — 정확한
  값은 구현서 게이트 충족하도록 조정.
- fixed-v0 = 기존 풀 리힐·M1 stat 유지(불변).

### (c) winnability (노이즈 0, 추론 보존)
- 각 procgen 보스 타입 ≥1 스타터 NEUTRAL+. **검증 = oracle scripted 가 실제 배틀로 표본 시드 전부 승리**
  (타입관계 아님). 추론 필요성 보존(어느 타입인지 미노출).

### (d) scope: 팀빌드(caught→party) deferred.

## Step별 계획

1. **타입 풀** (`types.py`): ElementType ~15. generate_typechart K≥12 검증. FIXED_CHART 불변.
2. **num_types + active subset** (`region.py`): boss 샘플 **및** 차트생성 둘 다 `[:num_types]`. ValueError 가드.
   winnability 생성 제약.
3. **keystone 이코노미** (`critter_env`/`party.py`): procgen 에서 gym 간 풀-리힐 제거(상태 이월) +
   보스 stat 튜닝. **fixed 경로는 기존대로**(M1).
4. **wiring** (`env`/`registration`): obs 경계=풀. procgen-v0=num_types≥12+keystone; fixed-v0=M1.
5. **테스트** (`test_meta_difficulty.py` 신규):
   - **4 scripted arm** (provenance 명시):
     - `oracle` (차트 읽어 늘 super-effective) = winnability **상한**(추론 증명 아님).
     - `type_blind` (타입 무시, 늘 attack) = **바닥**.
     - `probe` (한 배틀 안 데미지 관측→교정, **gym 간 메모리 없음**) = within-battle brute-forcer.
     - `infer` (관측한 type-pair effectiveness 를 **gym 간 누적**해 예측; 차트 미열람) = 추론 demonstrator.
   - **핵심 게이트**: N≥20 procgen 시드서 **`infer` 보스격파율 > `probe` 보스격파율 (유의 마진)** +
     `type_blind` ≪ 둘 + `oracle` ≥ infer(상한). → within-battle probing 봉쇄 + cross-gym 추론 load-bearing.
     마진은 시드수 기반(임의 /2 아님; 예: infer−probe ≥ 명시 절대차, N 시드 평균).
   - winnability: `oracle` 표본 시드 전부 실제 승리(불가 시드 0).
   - infer-the-meta 구조: K≥12 차트 antisymmetric·per-seed distinct·train≠heldout(누수0).
   - obs 고정 · **M1 무회귀**(fixed 결정론·풀리힐 유지·기존 고정월드 테스트 green)·check_env(fixed+procgen).
6. **(비CI, report)** `[rl]` procgen(K↑+keystone) 재학습 → held-in vs held-out + 이상적으로 비-추론 RL
   baseline 열화. acceptance 아님.

## 검증 방법
- `mypy src`·`ruff check .`·`pytest -q`·`python -m build` + 기존 118 무회귀 + check_env(fixed+procgen).

## 리스크

| 리스크 | 완화 |
|---|---|
| **within-battle probe 가 봉쇄 안 됨**(데미지로 교정) | keystone(gym 간 누적 비용)으로 *시드 전체* probing 을 비싸게; **게이트 = infer ≫ probe** 가 행동으로 검증 |
| **크리처 3 = 무료 probe 3** (L1) | gym 간 풀-리힐 제거 → 허비 크리처 누적 손실; probe 정책이 게이트서 열화함을 직접 측정 |
| "oracle=cheat 이라 추론 증명 아님" (L1) | oracle 은 *winnability 상한*으로만 명시; 추론 증명은 **infer(차트 미열람, gym간 메모리) > probe** |
| 게이트 임계가 flaky | 시드수 기반 마진·결정론 scripted; 충분 N | 
| 이코노미 변경이 M1 변질 | procgen 한정; fixed=풀리힐·M1 stat; M1 테스트+check_env |
| infer ≫ probe 분리가 튜닝으로 안 나옴(설계 미수렴 가능) | 구현서 keystone 강도 조절; **분리 실패 시 = 증분이 목표 미달 → 사용자 에스컬레이션**(정직) |
| region 두 호출부 active 미전달 (L1) | Step2 둘 다 패치 + AC2 명시 |
| 팀빌드 없이 반쪽 | 본 증분=추론 load-bearing 까지; 팀빌드 후속 |

## Acceptance Criteria (DESCOPED — SSOT, 위 DESCOPE NOTE 참조)

D1. `ElementType` ≥12(F/W/G=인덱스 0/1/2 유지); `num_types` 파라미터 region+env.
D2. region 이 boss 샘플 **및** `generate_typechart` 둘 다 active subset(`[:num_types]`) 전달(전체풀
   fallback 제거); `num_types>3 ∧ vary=False` → ValueError; 차트 antisymmetric·무모순·obs 미노출.
D3. **타입 재출현**: procgen 에피소드가 보스 타입을 시드별 소수 풀에서 *반복* 추출 → 일부 에피소드에
   같은 보스 타입이 ≥2회 (테스트로 검증; "infer 가 *쓸 자리*는 만듦" — load-bearing 증명은 아님).
D4. **winnability (구조)**: 각 procgen 보스 타입은 ≥1 스타터(F/W/G)가 NEUTRAL 이상 — 승리불가 시드 0
   (생성기 제약, 구조 검증).
D5. **obs 고정**: 타입 id 경계=풀 크기(num_types 무관); shape 불변.
D6. **K≥12 차트**: per-seed distinct; **train 차트 ≠ held-out 차트**(누수0).
D7. **M1 무회귀**: fixed(num_types=3, vary=False, M1 풀-리힐·stat) 결정론·trajectory·차트 동일;
   no-heal/난이도 이코노미 변경 **없음**(드롭됨); 기존 고정월드 테스트 green; check_env(fixed+procgen).
D8. **procgen 등록**: `CritterGym-procgen-v0`=num_types≥12 + 보스 재출현(num_gyms 상향); fixed-v0=K3 M1.
D9. **정직 표기**: "추론 provably load-bearing 은 미해결(battle-economy 연구)" 를 DESIGN/roadmap 에 명시.
D10. `mypy src`(core, no-extras)·`ruff check .`·`pytest -q`·`python -m build` 통과 + 기존 무회귀.
   (참고: imageio 설치된 dev 에선 out-of-scope `render.py` save_gif overload 1건 노출 — core CI 무관,
    별도 follow-up.)

---
### (구) Acceptance Criteria — DESCOPE 로 무효 (이력 보존)

1. `ElementType` ≥12(F/W/G=0/1/2 유지); `num_types` region+env.
2. region 이 **boss 샘플 *및* generate_typechart 둘 다 active subset 전달**(전체풀 fallback 제거);
   `num_types>3 ∧ vary=False` → ValueError; 차트 antisymmetric·무모순·obs 미노출.
3. **추론 load-bearing (핵심 게이트, numpy-only CI)**: N≥20 procgen 시드서 4 scripted arm 측정 —
   **`infer`(gym간 메모리, 차트 미열람) 보스격파율 > `probe`(within-battle only) (명시 마진)**,
   `type_blind` ≪ 둘, `oracle`(상한) ≥ `infer`. = within-battle probing 봉쇄 + cross-gym 추론 필수 증명.
   **마진은 구현 전 pilot(소수 시드의 infer−probe 분포)로 산출·고정** → "튜닝 분리 실패"가 게이트 미충족인지
   임계 미설정인지 모호하지 않게 (L1 SUGGEST). pilot 에서 분리 안 나오면 = 증분 목표 미달 → 사용자 에스컬레이션.
4. **keystone**: procgen 에서 gym 간 풀-리힐 제거(상태 이월)로 probing 누적 비용화; fixed 는 풀-리힐 유지.
   (게이트 3 이 행동으로 검증.)
5. **winnability**: `oracle` scripted 가 표본 procgen 시드 전부 실제 배틀 승리(불가 시드 0).
6. **obs 고정**: 타입 경계=풀 크기(num_types 무관), shape 불변.
7. **K≥12 차트**: per-seed distinct; train≠held-out(누수0).
8. **M1 무회귀**: fixed(num_types=3,vary=False,풀리힐,M1 stat) 결정론·trajectory·차트 동일; 난이도/이코노미
   튜닝 procgen 한정; 기존 고정월드 테스트 green; check_env(fixed+procgen).
9. **procgen 등록**: `CritterGym-procgen-v0`=num_types≥12+keystone; fixed-v0=K3 M1.
10. (비CI, report) Step6 재측정 수치.
11. `mypy src`·`ruff check .`·`pytest -q`·`python -m build` + 기존 118 무회귀.
