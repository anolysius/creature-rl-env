---
slug: genre-generalization-foundation
initiative: env-core
status: completed
ended: 2026-06-22
mode: heavy
result: passed
milestone: M3
exit_criteria: [M3-EC-reliability]
extracted_to:
  - DESIGN.md   # §3.1.1 (B) — 장르 일반화 토대 착수(second family + env-level 측정), 장르 주장 아님
changelog_entry: docs/CHANGELOG.md
supersedes: []
---

# Report — genre-generalization-foundation · (B) 장르 일반화 측정 토대

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md) (AC1–AC6)
> ⚠ (B)는 이니셔티브급 — 본 task는 **토대 첫 슬라이스**(다수 패밀리·강한 주장은 후속).

## 요약 — (B)의 측정 머신을 end-to-end로 세움 (장르 주장 아님)

지금까지 일반화는 **instance-level**(같은 생성기, 다른 시드)뿐. 이 task는 **environment-level**(구조-상이 env
패밀리 간) 일반화를 *측정 가능하게 하는 최소 토대*를 세웠다:

1. **env-family 추상화**(`env_family.py`): 공유 obs/action 계약(Protocol `conforms`) + family registry.
   CritterEnv(family A)가 **무변경**으로 계약 만족.
2. **family B**(`ForageEnv`): 구조-상이 — **contact-collect**(creature 타일 진입 시 자동 수집, CATCH inert)
   vs family A의 action-collect. **시드 변형 환원 불가 입증**: same-seed·same-actions에서 A≠B trajectory.
3. **env-level 측정**(`genre_generalization.py`): train-family → unseen-family 갭(`generalization` 재사용).

**측정 결과 (critter→forage, held-out 20 시드):**

| 정책 | critter(train) | forage(unseen) | env-level gap |
|---|---|---|---|
| random | 1.45 | 1.80 | −0.35 |
| greedy/scripted (A-튜닝) | 2.50 | 2.50 | +0.00 |

→ A용 scripted 정책이 family B로 **gap≈0 전이**. 측정 머신이 작동함을 입증.

## 정직한 한계 (헤드라인 과대 금지 — typechart-depth 문화)

- **2 패밀리 = 토대지 장르 주장 아님.** 신뢰할 장르 일반화 주장은 *다수* 구조-상이 패밀리 + 더 강한 구조 축 필요.
- **gap은 신호지 threshold 아님.** gap≈0이 "장르 일반화 훌륭"이 아니라, **최소 구조 축(수집 메커닉 하나)이
  관대해서** A-정책이 B에 전이된 것 — 더 상이한 패밀리(다른 배틀/진행)는 gap을 키울 것.
- family B는 **최소** 구조 변형(수집 메커닉 1축). 서브클래스 단일 메서드 override. 더 distinct한 패밀리는 후속.

## 계획 대비 실적 (AC1–AC6)

| AC | 결과 |
|---|---|
| AC1 env-family 추상화 | ✅ `env_family.py`: `conforms`(계약) + registry. CritterEnv 무변경 만족(테스트) |
| AC2 family B 구조-상이 | ✅ `ForageEnv` contact-collect. `check_env` + registry. **same-seed→A≠B trajectory 테스트**(시드 변형 아님). family A 무회귀 |
| AC3 env-level 측정 API | ✅ `genre_generalization.py`(numpy-only): train→unseen family 갭. train-A→eval-B 실행 테스트 |
| AC4 측정 실행+정직 보고 | ✅ critter→forage 측정(위 표) + family B 구조차이 문서화 + "2패밀리=토대" 명시 + DESIGN §3.1.1 (B) 갱신 |
| AC5 family A 무회귀 | ✅ 151→160(신규 9만, skip 동일) + check_env **4종**(fixed/procgen/commit/**forage**) + honesty 가드 |
| AC6 toolchain | ✅ mypy(20)·ruff·pytest 160/2skip·build clean. 신규 core numpy-only |

## 변경 파일 상세

| 파일 | 내용 |
|---|---|
| `env_family.py` (신규) | `CollectionRPGEnv` Protocol + `conforms` + family registry + `trajectory_signature`(A≠B 판별) |
| `envs/forage_env.py` (신규) | `ForageEnv(CritterEnv)` — contact-collect override(단일 메서드, CritterEnv 무변경) |
| `genre_generalization.py` (신규) | env-level 측정 `measure_genre_generalization` + `GenreGapReport`(numpy-only, `generalization` 재사용) |
| `registration.py` | `CritterGym-forage-v0` 등록 + family registry(`critter`/`forage`, 공유 config) |
| `tests/test_env_family.py` (신규) | 계약/registry/구조-상이(same-seed→A≠B)/contact-collect/check_env 6건 |
| `tests/test_genre_generalization.py` (신규) | env-level 측정 API 계약 3건 |
| `DESIGN.md` | §3.1.1 (B) — 토대 착수(장르 주장 아님) 정직 갱신 |

## 발견된 이슈 (심각도)

- **(중·정직성) family B 최소성** — 수집 메커닉 1축 변형이라 "구조-상이"가 thin. 진짜 distinct(다른 배틀
  시스템/진행)는 후속 패밀리. 본 task는 *머신* 토대지 강한 주장 아님(report·DESIGN 명시).
- **(낮) gap≈0의 해석** — 최소 축이 관대해 A-정책 전이. 더 상이한 패밀리로 gap 스트레스 테스트 후속.

## 흡수처 매핑 (extracted_to)

- **`DESIGN.md` §3.1.1 (B)** — "cannot measure (B) yet" → "foundation in place(second family + env-level
  측정 머신), not yet the claim". 이 task의 유일 evergreen 결정.

## 후속 (follow-up)

1. **더 distinct한 패밀리** — 다른 배틀 시스템/진행 메커닉 family C, D → 다수-패밀리 env-level split(진짜 (B) 주장).
2. **학습 정책 env-level 전이** — PPO를 family A 학습 → unseen family eval(learnability 패턴 재사용).

## 툴체인 결과
- `pytest` → **160 passed, 2 skipped**(151 + 신규 9: env_family 6 + genre 3)
- `mypy src` → Success(20) · `ruff` → clean · `build` → OK
- `check_env` ×4(fixed/procgen-v0/commit-v0/**forage-v0**) 통과 · family A 무회귀
