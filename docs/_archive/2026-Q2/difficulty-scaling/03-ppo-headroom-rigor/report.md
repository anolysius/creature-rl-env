---
slug: ppo-headroom-rigor
initiative: difficulty-scaling
status: completed
ended: 2026-06-25
extracted_to:
  - docs/explanation/jax-throughput.md   # PPO headroom 표 robust 갱신
  - DESIGN.md                            # §3.1.1 multi-run-robust headroom
changelog_entry: docs/CHANGELOG.md
---

# PPO oracle-headroom multi-run rigor — 결과 보고서

## 요약 (수치 표, CPU·5-run)

| config | PPO held-out (5-run) | oracle | PPO/oracle | 낙관상한(m+std) | 임계(0.75·oracle) | gap | verdict |
|---|---|---|---|---|---|---|---|
| default(3 gym) | 0.52±0.06 | 1.84 | **28%** | 0.58 | 1.38 | +0.20 | **hard-and-learnable (robust)** |
| hard(8 gym) | 1.52±0.28 | 7.28 | **21%** | 1.80 | 5.46 | +0.12 | **hard-and-learnable (robust)** |

- single-run(32%/15%) → multi-run(28%/21%) 일관. 낙관적 PPO 상한도 임계를 한참 밑돎 = headroom **robust**.
- R2 PPO≥A2C 양 config(2.44≥0.72 / 3.24≥2.26). hard서 PPO(1.52)<type_blind(2.03) 유지.
- 전체 372 passed(365+7), 2 skipped. mypy(28)/ruff/build clean.

## 계획 대비 실적

AC1–AC7 전부 ✅(qa-checklist 1:1). `ppo-closes` 미발동 → reframe/정지 조건 불발동(정상).

## 변경 파일 상세

**신규**: `src/critter_gym/headroom.py`(+62, numpy-only CI: `classify_headroom`+`HeadroomVerdict`,
사전약정 frac=0.75·k=1.0) · `tests/test_headroom.py`(+56, 7 단위).
**수정**: `scripts/ppo_baseline.py`(+11, runs>1 robust verdict; single-run fallback 보존).

## 발견된 이슈 (심각도)

- **[정보·marketing] headroom robust 입증** — 과거 (B) 스레드가 single-run을 4회 노이즈로 교정한 학습을
  이 헤드라인에 적용. 5-run으로 "PPO가 oracle 21–28%, seed 전반 robust"가 방어 가능한 명제로 굳음.
- **[caveat]** 5-run(대규모 sweep 아님)·작은 net·CPU·200iter·oracle proxy. hard std(0.28)는 default
  (0.06)보다 크나 verdict 여유 큼(낙관상한 1.80 ≪ 임계 5.46).

## 흡수처 매핑 (extracted_to)

- `jax-throughput.md` — PPO headroom 표를 5-run mean±std + robust verdict로 갱신.
- `DESIGN.md` §3.1.1 — multi-run-robust headroom 문단.
- ADR 가치 없음(측정 rigor, 신규 결정 아님). INITIATIVE task 3 행으로 충분.

## 타입 체크 / 빌드 결과

`mypy src` Success(28). `ruff` passed. `pytest` 372 passed/2 skipped. `build` 성공.
