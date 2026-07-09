---
slug: demo-gif-purposeful
initiative: null
status: completed
ended: 2026-07-09
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 홈페이지 데모 GIF 목적성 수리 — 결과 보고서

## 요약 (수치 표)

**사용자가 직접 발견한 문제**("체육관이 시야에 있는데 최단경로로 안 가고 옆옆옆↓옆옆옆 훑는다")를
수리. 원인 = GIF 생성 정책 `greedy_policy`가 `patch == 1`(생물)만 추적, 체육관(`2`)은 아예 안 봄.
수리 = 데모 전용 `demo_policy`(체육관 최단경로 직행) 추가 + GIF 생성만 교체. **greedy/random
byte-identical**(랭킹 baseline 숫자 보호).

| 항목 | 결과 |
|---|---|
| 테스트 | **763 → 770** (+7 demo_policy 계약, 기존 test_baselines 무변경, 회귀 0) |
| lint/type | ruff clean, mypy pre-existing(render.py:82)만 |
| baseline 보호 | `git diff baselines.py` hunk 1개(greedy 끝 뒤 순수 append) — greedy/random 본문 무변경, `_free_policies` 무변경 |
| html 수치 diff | **0** (변경 = en/ko 캡션 `<p>`+`img alt` 4줄만, cleared 캡션 유지) |
| **궤적 개선** (동일 seed 6개) | greedy(old): 51/120/120/120/67/78 step, **3/6 클리어** → demo(new): **29/19/26/14/5/60 step, 6/6 클리어** |
| GIF | 8246 → 5674 bytes (직행으로 에피소드 단축), 체육관 가시 시 최단 접근 |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 demo_policy 우선순위 계약 + greedy byte-identical | ✅ | 7 테스트(gym 최단step·gym>creature·CATCH·battle 공격·sweep=greedy·env 유효) + diff hunk 1개 직접 증거 |
| AC2 무회귀 + lint/type | ✅ | 770 green, ruff clean |
| AC3 GIF만 교체·수치 경로 무변경 | ✅ | `_free_policies` 무변경, html 숫자줄 변경 0 |
| AC4 새 GIF 최단 접근 + 클리어 seed 유지 | ✅ | 궤적 비교 6/6 클리어, cleared 캡션 유지, 사용자에게 GIF 전달·확인 |
| AC5 en/ko 캡션 정직화 + 패리티 | ✅ | "demo-only policy; distinct from the ranked scripted row" en/ko 명시 |

## 변경 파일 상세

- `src/critter_gym/baselines.py` (+43): `demo_policy` additive — 우선순위 battle 공격 > 내칸 CATCH >
  살아있는 체육관 최단 step > 생물 추적 > sweep(greedy와 동일). docstring에 "데모 전용, 랭킹
  baseline 아님·깬 체육관은 패치에서 숨겨져 갇힘 없음" 명시.
- `tests/test_baselines.py` (+87): 계약 테스트 7개(기존 2개 무변경).
- `scripts/build_site.py` (+41/-19): GIF 생성 import/lambda만 demo_policy로, en/ko 캡션 4개 정직화.
- `site/{gameplay.gif,index.html,index.ko.html}`: 재빌드 산출물(수치 불변).

## 발견된 이슈

- 없음. (부수 관찰: demo_policy가 데모 env에서 greedy보다 훨씬 강함(6/6 vs 3/6 클리어) — 랭킹에
  추가하면 "scripted" 행 위 새 행이 되겠지만, 랭킹 변경은 본 task scope 밖·별도 결정.)

## 흡수처 매핑 (extracted_to)

**흡수 없음** — evergreen 4-질문 모두 No(단발 site 수리, 새 설계/절차/명세/ADR 없음).

## 타입 체크 / 빌드 결과

- `pytest`: 770 passed, 0 regression. `ruff`: clean. `mypy`: pre-existing 1건만.
- `build_site.py --out site`: 무오류, 수치 diff 0, GitHub Pages 반영은 merge 시 자동(공개 표면 기존 유지).
