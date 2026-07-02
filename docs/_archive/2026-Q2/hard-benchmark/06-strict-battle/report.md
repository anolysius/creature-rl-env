---
slug: strict-battle
initiative: hard-benchmark
status: completed
ended: 2026-07-02
extracted_to:
  - docs/reference/strict-battle.md
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# strict-battle — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 650 → **677** (+27: 단위 11 + JAX parity 16), 회귀 0 |
| JAX parity | strict on {commit, noncommit} × {single, multitype} **0 mismatch** (16 케이스) |
| winnability sweep | 200 seed × {single, multitype} — unwinnable 0건 |
| scout (16 held-out seed) | **FALSIFY** — commit spread delta +0.00 (grid16 2.56→2.56, grid10 1.62→1.62), non-commit attrition probe 5.00/3.00 gyms 클리어 strict on/off 무차이 |
| lint/type | ruff clean; mypy 잔여 1건 = render.py pre-existing (클린 트리 재현, scope 외) |
| L1 / L3 | 2/2 APPROVE (L1 SUGGEST 1: 커밋 단위 명시 → 단일 PR 커밋으로 확정) / 2/2 APPROVE |

## 계획 대비 실적

- ✅ AC1 default-off byte-identical — 고정 seed trace 동일성 테스트 + 전체 스위트 회귀 0
- ✅ AC2 strict 규칙 — <NEUTRAL → 0, ≥NEUTRAL 기존 `max(1,...)`, 양방향 대칭 단위 테스트
- ✅ AC3 winnability sweep — 매치업 보장(#15)이 strict 를 실제로 커버함을 200 seed × 2 로 실검증
- ✅ AC4 JAX parity 0 — `_gym_damage` 4지점 치환(잔여 `_damage` 직접 호출 0, L3 가 코드로 재확인)
- ✅ AC5 scout + 정직 라벨 — 실측 결과는 **falsify** 이며 그대로 보고 (아래)
- ✅ AC6 evergreen — `docs/reference/strict-battle.md` (falsify 결과 포함)

## 핵심 발견 — 정직 결론 (falsify)

**strict_battle 은 규칙으로서 옳게 구현·검증됐지만, §5 한계 (i) attrition confound 를 닫지 못한다.**

1. **commit 모드**: resisted 커밋은 legacy 규칙에서도 이미 진다 (챔피언 15/turn vs 보스
   ~30/turn — attrition 이 이길 시간이 없음). strict 가 뒤집는 scripted 결과 0건 → spread 불변.
2. **non-commit 모드** (confound 의 본거지): 무추론 always-attack 정책이 두 구성 모두
   **전 gym 클리어**, strict on/off 무차이. attrition 은 중립타 chip(30 dmg) + 파티 순환 +
   재입장 풀힐로 굴러가는데, strict 는 설계상 **비효과타만** 0 으로 만들기 때문.

즉 confound 의 실체는 "min-1 클램프"가 아니라 "중립타 경제 + 순환/재입장" — 더 강한 변형
(super-effective 만 유효타, 재입장 풀힐 제거, 보스 경제 knob)은 **별도 설계 결정 + 새 scout**
(사람 게이트에 올릴 후속 후보). strict_battle 은 그 후속의 기반 엔진 규칙으로 유효하며,
판매-티어 레버 주장은 scripted 증거상 **금지** (learned/LLM 효과는 미측정 open).

## 변경 파일 상세

| 파일 | 변경 |
|---|---|
| `src/critter_gym/battle.py` | `Battle(strict_battle=False)` + `damage()` 단일 choke point + `scripted_opponent` 불변식 주석 |
| `src/critter_gym/envs/critter_env.py` | `strict_battle` kwarg → Battle 전달 |
| `src/critter_gym/jax_env.py` | `JaxEnvConfig.strict_battle` + `_gym_damage` (정적 bool, off=기존 식 그대로) + 4지점 치환 |
| `tests/test_strict_battle.py` (신규) | 규칙·대칭·다중타입 곱·교착 truncation·default-off·sweep·플럼빙 11 테스트 |
| `tests/test_jax_strict_battle_parity.py` (신규) | 2×2 구성 × {gym-clearing, random, held-out} 16 parity 테스트 |
| `scripts/strict_battle_scout.py` (신규) | commit spread + non-commit attrition probe, HONEST/NOTE 라벨 |
| `docs/reference/strict-battle.md` (신규) | evergreen — 규칙·계약·falsify·경계 |

커밋 단위: 단일 커밋 (opt-in 원자 변경 — L1 SUGGEST 반영해 여기 확정).

## 발견된 이슈

- (info) mypy `render.py:81` pre-existing — 본 task 와 무관, 별도 chore 후보.
- (design, 후속 seed) attrition confound 는 strict(resisted-only)로 안 닫힘 — 더 강한
  변형은 기본 규칙/경제 변경이라 **사람 결정** 필요 (autonomous mandate 범위 밖).

## 타입 체크 / 빌드 결과

`pytest -q` 677 passed / `ruff check .` clean / `mypy src` 신규 오류 0 (pre-existing 1 유지).
