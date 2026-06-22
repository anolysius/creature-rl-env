---
slug: typechart-depth
initiative: env-core
status: done
started: 2026-06-22
ended: 2026-06-22
mode: standard
result: passed-descoped
milestone: M3
exit_criteria: [M3-EC-reliability]
extracted_to:
  - DESIGN.md   # §3.1.1 "infer-the-meta load-bearing?" = open problem / future work
changelog_entry: docs/CHANGELOG.md
---

# Report — typechart-depth (DESCOPED) · M3 신뢰성

> plan: [plan.md](./plan.md) (DESCOPE NOTE) · acceptance: [qa-checklist.md](./qa-checklist.md) (D1–D10)

## 결과 요약 — 정직한 부분 성공

타입 풀을 **3 → 15**로 확장(procgen num_types=12)하고, 보스 타입을 **시드별 소수 풀에서 반복 추출**
(에피소드 내 재출현), winnability 보장. 시드별 숨은 차트가 **66 정향 관계**(3-cycle 대비 훨씬
외우기 어려움)가 되고 train≠held-out 누수 0. **M1 고정월드 완전 무회귀.** Acceptance D1–D10 충족,
**128 passed/2 skipped**, mypy/ruff/build canonical clean.

## ⚠ 디스코프 — 원래 목표는 *달성 불가*로 입증됨 (정직성)

원래 목표 = "infer-the-meta(숨은 상성표 추론)를 **provably load-bearing**". G1 후 **pilot**으로 검증:
4 scripted arm(type_blind/probe/infer/oracle) × 20 held-out 시드 측정 결과 —

```
type_blind 0.764  > probe 0.742 > oracle 0.719 > infer 0.640
```

→ no-heal keystone에선 **switch 비용이 매치업 이득을 압도** → 타입지식이 *손해*, 추론이 꼴찌. "추론을
증명가능하게 load-bearing"하게 하려면 open-ended battle-economy 재설계 필요(수렴 미보장). **사용자
결정 (가): 디스코프** — 안전한 깊이만 ship, no-heal/infer>probe 드롭, "추론 load-bearing = future work"로
DESIGN §3.1.1 정직 명시.

이건 **포기가 아니라 falsification**: 가설을 G2 *전에* 경험적으로 반증하고, transparent하게(무효 AC
이력 보존, DESIGN 헤드라인 강등) 축소했다. 정직성이 헤드라인보다 우선.

## 계획 대비 실적 (DESCOPED D1–D10)

| AC | 내용 | 결과 |
|---|---|---|
| D1 | ElementType ≥12 (F/W/G=0/1/2 유지) + num_types | ✅ |
| D2 | active subset 두 호출부 + ValueError 가드 + obs 미노출 | ✅ |
| D3 | 보스 타입 재출현 (≥절반 에피소드, was 0/40) | ✅ |
| D4 | winnability 구조 (보스마다 ≥1 스타터 NEUTRAL+) | ✅ |
| D5 | obs 타입 경계=풀 고정(num_types 무관), shape 불변 | ✅ |
| D6 | K=12 차트 antisymmetric·distinct·train≠heldout(누수0) | ✅ |
| D7 | **M1 무회귀** (no-heal 드롭=풀리힐 유지; 결정론·차트 동일) | ✅ |
| D8 | procgen-v0 = num_types=12 + num_gyms=8 | ✅ |
| D9 | "추론 load-bearing=future work" DESIGN 명시 + **honesty 가드 테스트** | ✅ |
| D10 | mypy(core)·ruff·pytest·build + 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 내용 |
|---|---|
| `types.py` | ElementType 3→15 (F/W/G 앞 3 고정); 차트 생성기는 임의 K 지원(기존) |
| `region.py` | `num_types` + active subset(boss샘플·차트 둘 다) + winnability 필터 + 보스 풀 재출현 |
| `critter_env.py` | `num_types` wiring; obs 경계=풀; **no-heal 드롭(M1 풀리힐 유지)** |
| `registration.py` | procgen-v0 = num_types=12, num_gyms=8, max_steps=400 |
| `tests/test_meta_difficulty.py` | 신규 9건 (D1–D6 + D9 honesty 가드) |
| `tests/test_gym_battle.py` | 무회귀 1줄 (vary-chart 참조가 num_types subset 반영) |
| `DESIGN.md` | §3.1.1 "infer-the-meta load-bearing?" open problem 단락 |

## L3 리뷰 + 흡수

L3 reviewer A APPROVE / reviewer B **BLOCK(정직성)** → 즉시 해소: 코드 docstring 2곳(region.py·types.py)에
남은 "load-bearing"/"pay off" 과대표현을 caveat화 + **honesty 가드 테스트**(과대표현 재발 방지) 추가.
정직성이 이 task의 D9 핵심이라 reviewer가 정확히 게이트.

## 학습 (process)

**가설(load-bearing 추론)을 freeze 전에 pilot로 검증했어야 했다** — 2 round L1 + pilot 후에야 구조적
불가능을 발견. 교훈: "X를 *증명가능하게* 만든다"류 acceptance는 freeze 전 achievability pilot 권장.
(retro 후보.)

## 툴체인 결과

- `pytest` → **128 passed, 2 skipped**([render] smoke, imageio 제거 core 상태)
- `mypy src` → Success(16, canonical) · `ruff` → clean · `python -m build` → OK
- `check_env`(fixed + procgen-v0 K=12) 통과 · M1 결정론·FIXED_CHART 확인
- out-of-scope: imageio 설치 dev 에서 `render.py` save_gif overload 1건(core CI 무관) — follow-up
