# QA Checklist — strict-battle (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.

## Acceptance (plan AC 1-6)

- [ ] AC1 — default-off byte-identical: `strict_battle` 미지정/False 시 기존 동작 완전 동일 — 고정 seed episode trace 동일성 테스트 + 기존 전체 테스트(baseline 650) 회귀 0.
- [ ] AC2 — strict 규칙: strict on 에서 effectiveness < NEUTRAL(1.0) 공격 데미지 0, ≥ NEUTRAL 은 기존 `max(1, ...)` 동일 — 양방향(플레이어→보스, 보스→플레이어) 단위 테스트.
- [ ] AC3 — winnability sweep: vary·num_types=8·min_gyms=num_gyms 구성, boss_secondary off/on 각각 seed ≥ 200 — 모든 보스에 strict-damage > 0 파티 무브 존재 (unwinnable 0건).
- [ ] AC4 — JAX parity 0: strict on (commit + noncommit, boss_secondary off/on) numpy↔JAX 동일 시드·동일 액션열 obs 전 key + reward + term + trunc 0 mismatch; 기존 parity 테스트 무회귀.
- [ ] AC5 — scout 실측 + 정직 라벨: `scripts/strict_battle_scout.py` 가 strict off/on 의 oracle−type_blind spread 출력 + 1-run·scripted·no-threshold·헤드라인-금지 라벨. 수치 방향은 AC 아님 (falsify 도 보고).
- [ ] AC6 — 문서: `docs/reference/strict-battle.md` evergreen 1장 (규칙·opt-in 계약·경계·후속 조건).

## Default DoD

- [ ] 전체 테스트 green, 회귀 0. `mypy src` · `ruff check .` clean. L3 APPROVED(≥2). CHANGELOG append.
