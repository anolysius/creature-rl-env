# QA Checklist — genre-generalization-foundation (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ (B)는 이니셔티브급 — 본 task는 토대 첫 슬라이스. 다수 패밀리·강한 장르 주장은 후속.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** ✅ — `env_family.py`: `conforms`(공유 obs/action 계약) + family registry(register/make/names).
  CritterEnv 계약 만족 테스트(무변경). 6 테스트.
- [x] **AC2** ✅ — `ForageEnv`(contact-collect) 동일 obs/action, `check_env`, registry(`forage`+gym id).
  **구조-상이 판별**: `trajectory_signature` same-seed·same-actions → **A≠B trajectory** 테스트 green(시드변형 아님).
  family A 무회귀.
- [x] **AC3** ✅ — `genre_generalization.py`(numpy-only): `measure_genre_generalization` train→unseen family +
  `GenreGapReport`. train-A→eval-B 실행 테스트 3건. `generalization.evaluate` 재사용.
- [x] **AC4** ✅ — critter→forage 측정 실행(random gap −0.35, greedy gap +0.00) + family B 구조차이 문서화 +
  "2패밀리=토대,장르주장 아님" + DESIGN §3.1.1 (B) 갱신. gap=신호(threshold 무).
- [x] **AC5** ✅ — family A 무회귀: 151→160(신규 9만, skip 동일) + `check_env` **4종**(fixed/procgen/commit/forage) +
  honesty 가드 무회귀.
- [x] **AC6** ✅ — mypy(20) clean · ruff clean · pytest 160/2skip · build OK. 신규 core numpy-only.

## L1 이력
- round 1: plan-reviewer SUGGEST(구조차이 판별 기준) / qa-verifier **BLOCK**(AC2/4/5 측정기준) → BLOCKED.
- 보완: AC2 same-seed→A≠B trajectory 판별 기준 / AC4 객관 합격 3조건 / AC5 postcondition(151+N·check_env 3종).
- round 2(selective): plan-reviewer APPROVE / qa-verifier APPROVE(INLINE) → **APPROVED**.

## 정직성 불변식
2개 패밀리로 "장르 일반화 입증"은 과대 — 본 task=토대+측정 하네스+정직 문서화. gap은 신호. 강한 주장은
다수 env 패밀리 후속(M5). (reasoning-load-bearing/learnability의 "측정+정직보고로 freeze" 패턴 일관.)
