---
slug: oss-release-prep
initiative: env-core
status: active
started: 2026-06-23
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - LICENSE
  - README.md
  - CONTRIBUTING.md
extracted_to: []
supersedes: []
---

# OSS 릴리스 준비 (M3-EC5) — MIT LICENSE + 공개용 README

> 작성일: 2026-06-23 | 상태: 계획

## 목표

활성 M3의 미충족 **EC5(OSS 공개)** 전진: 오픈소스 릴리스에 필요한 **로컬 산출물**(MIT `LICENSE` 파일 +
실제 빌드 상태를 반영한 공개용 `README.md` + `CONTRIBUTING.md`)을 준비. `pyproject.toml`은 이미 `license =
{ text = "MIT" }` 선언 — 누락된 LICENSE 파일을 추가하고, stale README("Phase 0 — Nothing built yet")를
실제 상태(작동하는 벤치마크 + 측정 결과 + 논문 초안)로 갱신.

**정직성 = 자산(공개 표면에서 특히)**: README는 DESIGN §3.1.1 정직 scope를 따른다 — Pokémon=메타포(비경쟁),
(A) 측정/(B) 토대지 증명 아님. 과대 마케팅 금지.

**범위 경계(정직 표기 필수)**: **실제 외부 발행**(Prime Intellect Hub 리스팅, GitHub repo public 전환)은
계정·자격증명·사람 판단이 필요한 **외부 행위 = 사용자 게이트**(M3-EC6 killer-demo 선례: 코드 task가 아니라
사람이 결재). 본 task는 *릴리스 산출물 준비*까지. EC5 "충족"은 사람이 외부 발행 후 결재.

**EC 매핑**: M3-EC5 전진(준비). (LICENSE/README는 비-src 루트 파일 → 제품 코드 무변경.)

## 선행 조건

- `pyproject.toml`(MIT 선언·메타·`[rl]`/`[viz]`/`[render]` extra) — 라이선스/패키징 정합 확인
- `docs/paper/critter-gym.md`(arXiv 초안) — README가 링크할 결과 SSOT
- DESIGN §3.1.1, milestones.md — 정직 scope SSOT
- 작동 env id 6종 + 측정 모듈 — README quickstart/positioning 근거

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `LICENSE` (신규) | MIT 라이선스 전문 + copyright("CritterGym contributors", 2026 — 사용자가 법적 주체로 교체 가능) | 신규 |
| `README.md` (갱신) | stale Phase 0 → 실제 상태: 한 줄 소개·install(`pip install -e .` + extras)·quickstart(`gymnasium.make` 6 env id)·정직 positioning·측정 결과 요약(논문 링크)·재현(seed split)·citation·license=MIT·외부발행 상태 | 갱신 |
| `CONTRIBUTING.md` (신규) | 개발 셋업(.venv/ruff/mypy/pytest)·task lifecycle 한 줄·정직성 규율 | 신규 |

## Step별 계획

1. **LICENSE** — 표준 MIT 전문, copyright "2026 CritterGym contributors"(사용자 교체 가능 주석).
2. **README** — 실제 상태로 재작성: install·quickstart(env id 6종)·positioning(Pokémon=메타포, Procgen/Craftax/XLand)·측정 요약(A 측정/B 토대, 논문 링크)·재현(train/test seed split)·citation·license·**외부 발행 상태(준비됨, Hub/public은 사람 게이트)**.
3. **CONTRIBUTING** — dev 셋업 + lifecycle + 정직성 규율.
4. **정합 확인** — pyproject MIT ↔ LICENSE, README 수치는 논문/DESIGN과 일치(날조 0), broken-link 0.
5. **L3 리뷰** — 라이선스 정합·README 정직성/정확성·과대표현 0.

## 검증 방법

- `LICENSE` 존재 + MIT 전문 + pyproject `license` 정합.
- README install/quickstart가 실제 동작(`gymnasium.make` env id 6종 실재, `pip install -e .`).
- README 정량 주장은 논문/DESIGN과 일치(날조 0), Pokémon=메타포·(B) 토대 명시.
- 외부 발행이 사람 게이트임을 README/report에 정직 표기(EC5 자동충족 주장 금지).
- broken-link 0. 제품 코드·테스트 무변경(181 passed 불변).

## 리스크

1. **과대 마케팅**(공개 README 유혹) → DESIGN §3.1.1 정직 scope 준수 + L3 정직성 축.
2. **EC5 과대 주장**(준비를 "공개 완료"로) → 외부 발행=사람 게이트 명시, report에서 EC5 "준비"로 한정.
3. **copyright 주체 오기** → "CritterGym contributors" 중립 표기 + 사용자 교체 안내 주석.
4. **README quickstart 부정확** → 실제 env id/설치로 검증.

## Acceptance Criteria (G1 통과 시 freeze)

> *릴리스 산출물 준비 + 정직 표기*로 freeze. 외부 발행은 사람 게이트.

- **AC1** — `LICENSE` 신규: 표준 MIT 전문 + copyright. `pyproject.toml` `license = {text="MIT"}`와 정합.
- **AC2** — `README.md` 갱신: 실제 상태(작동 벤치마크) — install(`pip install -e .` + extras) + quickstart(`gymnasium.make` env id 6종) + 정직 positioning(Pokémon=메타포, Procgen/Craftax/XLand) + 측정 요약(논문 링크) + 재현(seed split) + citation. stale "Phase 0/Nothing built" 제거.
- **AC3** — README 정량/주장이 논문(`docs/paper/`)·DESIGN §3.1.1과 **일치**(날조 0), (A) 측정/(B) 토대지 증명 아님 명시. **인용 수치는 논문 표에서 verbatim**(패러프레이즈 금지): 인스턴스 gap≈0(held-in 40%/held-out 45%), throughput ~266k, load-bearing gate(≥0.20/≥0.10), (B) C gap +3.9 vs +0.2·D muster≫rush — 각 수치는 `docs/paper/README.md` 출처 맵 경유(run-derived/CI-frozen 라벨 보존).
- **AC4** — **외부 발행 = 사람 게이트** 정직 표기: Prime Intellect Hub 리스팅·repo public은 본 task 범위 밖(사람 결재), README/report에 명시. EC5 자동충족 주장 금지.
- **AC5** — `CONTRIBUTING.md` 신규: dev 셋업(.venv/ruff/mypy/pytest) + lifecycle + 정직성 규율. broken-link 0.
- **AC6** — 무회귀: 제품 코드·테스트 무변경(181 passed 불변). LICENSE↔pyproject 정합. M3-EC5 전진(준비; 외부 발행은 사람 게이트).
