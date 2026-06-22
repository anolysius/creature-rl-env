---
slug: killer-demo
initiative: env-core
status: done
started: 2026-06-22
ended: 2026-06-22
mode: standard
result: passed
milestone: M3
exit_criteria: [M3-EC6]   # 전진(데모 수단 ship + 파이프라인 CI 검증) — EC6 미충족 유지([ ])
extracted_to:
  - docs/reference/milestones.md       # M3-EC6 토대 메모 갱신 (checkbox [ ] 유지)
changelog_entry: docs/CHANGELOG.md
---

# Report — killer-demo (데모 수단 ship + 파이프라인 CI 검증) · M3-EC6 전진 ✅

> plan: [plan.md](./plan.md) · acceptance: [qa-checklist.md](./qa-checklist.md)

## 결과 요약

킬러 데모(M3-EC6)의 **재현 가능한 수단**을 ship 하고 그중 **CI 검증 가능한 부분(녹화 파이프라인)을
못 박았다**. `critter_gym.demo.record_episode` = 정책 rollout → `env.render()` 프레임 수집 + 보스격파
감지(numpy-only). `scripts/killer_demo.py`(`[rl]`+`[render]`) = train 학습 → **held-out 시드** 녹화 →
GIF(우리 moat 의 시각적 증명 수단). Acceptance **8/8**, **118 passed/3 skipped**(113→118, 회귀 0).

## ⚠ 정직성 — EC6 는 **미충족**으로 남는다

EC6 의 핵심 = *held-out(새 타입표)에서 보스격파* = **일반화**. CI 가 증명한 건 **파이프라인·감지**
(type-aware scripted 가 **seed=3, train 영역**에서 gym 격파를 녹화) — *일반화가 아니다*. "학습된
에이전트가 held-out 보스격파"는 학습 품질 의존이라 비CI(스크립트 실행 산물). **milestones M3-EC6
체크박스 `[ ]` 유지** — `[x]` 자격 = 실제 held-out 보스격파 GIF 육안 확인 + 별도 결재(후속).
(world-render 가 토대로 `[ ]` 유지한 선례와 동일 기준.)

## 계획 대비 실적

| AC | 내용 | 결과 |
|---|---|---|
| AC1 | `record_episode`→`EpisodeRecording`, numpy-only, render_mode 가드 | ✅ |
| AC2 | 프레임수=steps+1·`(H,W,3) uint8`·결정론(byte-identical) | ✅ |
| AC3 | 보스격파 감지(seed=3=파이프라인 검증, 일반화 아님 명시) | ✅ |
| AC4 | numpy-only 격리(top-level torch/sb3/imageio 미import) | ✅ |
| AC5 | `[render]` smoke(GIF 비어있지 않음, core skip) | ✅ |
| AC6 | `killer_demo.py` held-out 녹화→GIF(deterministic=True), graceful | ✅ |
| AC7 | 정직 표기(milestones EC6 `[ ]` 유지) | ✅ |
| AC8 | mypy/ruff/pytest/build 통과 + 기존 113 무회귀 | ✅ |

## 변경 파일 상세

| 파일 | 종류 | 내용 |
|---|---|---|
| `src/critter_gym/demo.py` | 신규 | `record_episode`(rollout→프레임+격파감지, numpy-only, render_mode 가드) + `EpisodeRecording` + `save_demo`(render.save_gif 위임). 측정 eval rollout 과 직교(프레임 vs 점수) |
| `tests/test_demo.py` | 신규 | 6건 — 보스격파 녹화(seed=3)·프레임 계약·결정론·render_mode 가드·import순수성 + `[render]` smoke |
| `scripts/killer_demo.py` | 신규 | `[rl]`+`[render]` — train 64시드 학습 → held-out 녹화(deterministic=True) → GIF + 격파 리포트, graceful |

## 설계 결정

- **검증 가능/불가능 분리** — 파이프라인(CI) vs 학습된 held-out 보스격파(비CI). 전 task(generalization·
  baseline·viz·render)의 일관 패턴.
- **직교성** — `record_episode`(프레임+격파감지) ≠ `generalization` eval rollout(점수만). 책임 중복 0.
- **정직 표기** — EC6 미충족 유지. 데모 *수단*을 ship 하되 일반화 *증명*은 스크립트 실행에 위임.

## L3 리뷰 + 흡수

L3 ≥2 reviewer **APPROVED**. 비차단 SUGGEST 중 plan 텍스트 정확성 1건 흡수(plan 이 `EvalResult`
import 을 언급했으나 실제 코드는 직교성상 미import → plan 동기화). gymnasium top-level 미import 주장은
gymnasium 이 core 의존이라 부적절 — 보류.

## 흡수처 매핑 (extracted_to)

| 흡수처 | 내용 |
|---|---|
| `docs/reference/milestones.md` | M3-EC6 토대 메모 — `killer-demo` 데모 수단+파이프라인 ship; **checkbox `[ ]` 유지**(일반화 미검증) |

## 툴체인 결과

- `pytest` → **118 passed, 3 skipped**(`[rl]`+`[render]`×2 smoke; 113→118, 회귀 0)
- `ruff check .` → clean · `mypy src` → Success (16 files) · `python -m build` → OK
- scripted seed=3 gym 격파 녹화 확인 (파이프라인·감지 CI 검증)
