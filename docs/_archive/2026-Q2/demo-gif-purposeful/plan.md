---
slug: demo-gif-purposeful
initiative: null
status: active
started: 2026-07-09
acceptance_freeze: true
mode: standard
task_type: general
domains: [rl-env, site]
scope_paths:
  - src/critter_gym/baselines.py
  - tests/test_baselines.py
  - scripts/build_site.py
  - site/gameplay.gif
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
---

# 홈페이지 데모 GIF 목적성 수리 — gym-seeking 데모 정책 (baseline 숫자 불변)

> 작성일: 2026-07-09 | 상태: 계획 | 단발 (site 첫인상 개선)

## 목표

**사용자가 직접 발견한 문제를 고친다.** 홈페이지 `gameplay.gif`는 `greedy_policy`로 생성되는데, 이
정책의 시야 처리는 `patch == 1`(생물)만 추적한다 — **체육관(`_PATCH_GYM=2`)은 아예 안 본다**
(`baselines.py:46`). 그래서 체육관이 5×5(데모 env는 7×7) 시야에 들어와도 곧장 가지 않고 잔디깎이
훑기(→→→↓←←←↓)를 계속하다 우연히 밟는다. 사이트 문구는 "scripted agent가 체육관을 클리어"라고
파는데 정작 데모 정책은 체육관을 목표로도 안 삼는 미스매치 — **GIF가 실제보다 목적 없어 보인다.**

수리: **데모 전용 `demo_policy`를 `baselines.py`에 추가**(체육관도 최단경로로 향함) + GIF 생성만
이 정책으로 교체. **`greedy_policy`는 1바이트도 안 바꾼다** — 랭킹 테이블("scripted" 행)의 공개
baseline 점수가 그 함수에서 나오므로 불변이 무회귀의 핵심.

정책 설계(우선순위): ① battle 중(`in_battle`)이면 공격(action 0) ② 내 칸에 생물이면 CATCH ③ 시야에
**살아있는 체육관**(patch==2; 깬 체육관은 env가 패치에서 숨김 — critter_env.py:409-411, 갇힘 없음)이
보이면 가장 가까운 쪽으로 한 칸(생물 추적과 동일한 Manhattan step) ④ 시야에 생물이 보이면 그쪽으로
⑤ 아무것도 없으면 기존 잔디깎이 sweep. — 체육관 우선 = "목적 있는 움직임"이 GIF에 드러남.

**정직성 유지**: GIF 정책 ≠ 랭킹 테이블의 "scripted" 행이 되므로, 캡션이 랭킹 행과 동일 정책이라고
암시하지 않게 en/ko 캡션에 한 구절 명시(예: "a gym-seeking scripted demo policy"). 수치·리더보드·
차트는 전부 불변(같은 `_free_policies` 그대로).

## 선행 조건

- main = c380920 (#119 머지), 763 tests green, clean. ✅
- GIF 생성처: `build_site.py:781-802` `build_assets` — heldout 앞 12 seed 중 첫 클리어 seed 채택,
  실패 시 uncleared 캡션 fallback. 이 구조는 유지(정책만 교체).
- 데모 env: grid8·3gym·120step·patch_radius **3**(7×7 시야) — 체육관 가시 빈도 높음.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/baselines.py` | `demo_policy` 신규(additive). `greedy_policy`·`random_policy` 무변경 | **중** | 랭킹 baseline 불변이 핵심 계약 |
| `tests/test_baselines.py` | demo_policy 계약 테스트 추가(체육관 최단 step·battle 공격·catch·sweep fallback·gym>creature 우선) | 낮음 | 기존 greedy 테스트 무변경 |
| `scripts/build_site.py` | GIF 생성만 `demo_policy`로 교체 + en/ko 캡션 한 구절 정직화 | 낮음 | `_free_policies`(랭킹) 무변경 |
| `site/{gameplay.gif,index.html,index.ko.html}` | 재빌드 산출물 | 낮음 | 수치 SSOT 불변 확인 |

### 영향 범위 (import 그래프)

- `baselines.greedy_policy` 소비처(scoreboard·site 랭킹·기존 테스트) **무영향**(무변경).
- `demo_policy` 소비처 = build_site GIF 경로만. site html 재빌드는 캡션 문구 외 수치 diff 0이어야 함
  (리더보드·SVG 차트는 leaderboard entries에서 나오고 정책 목록 불변).

## Step별 계획

1. **테스트(Red)** — demo_policy 계약: (a) 시야 내 살아있는 체육관으로 최단 Manhattan step,
   (b) 체육관·생물 동시 가시 시 체육관 우선, (c) 내 칸 생물 CATCH, (d) in_battle이면 0(공격),
   (e) 아무것도 없으면 greedy와 동일 sweep, (f) greedy_policy 기존 테스트 전부 무변경 green.
2. **baselines.py demo_policy(Green)** — greedy 구조 재사용(중복 최소), docstring에 "데모 전용,
   랭킹 baseline 아님" 명시.
3. **build_site.py 교체** — GIF 경로만 demo_policy, en/ko 캡션 구절 추가, 재빌드(`--out site`).
4. **검증** — GIF 실제 프레임 확인(체육관 향해 직진하는지), site 수치 diff 0, en/ko 패리티.

## 검증 방법

- `.venv/bin/python -m pytest -q` → 763 + 신규 무회귀 green (특히 기존 test_baselines 불변).
- `.venv/bin/python -m ruff check .` + `.venv/bin/python -m mypy src` → clean (render.py:82 제외).
- **greedy/random byte-identical 직접 검증**: `git diff src/critter_gym/baselines.py`에서
  `greedy_policy`/`random_policy` 함수 본문에 변경 hunk가 0임을 확인(테스트 green과 별도 직접 증거).
- `.venv/bin/python scripts/build_site.py --out site` → 재빌드 무오류, gameplay.gif 갱신.
  **html 수치-only diff 절차**: `git diff site/index*.html`의 변경 hunk가 캡션 문구
  (demo_cleared/demo_uncleared/demo_alt 텍스트)에만 국한되고, 숫자 패턴(`[0-9.]+` — 리더보드 행·
  차트 값·gap 수치)이 포함된 줄에 변경 hunk 0임을 grep으로 확인.
- 새 GIF 육안/프레임 검사: 체육관 가시 시 최단경로 이동이 실제로 보이는지.

**커밋 단위**(L1 SUGGEST 반영): 단일 PR 1커밋 — (테스트+demo_policy+build_site 교체+재빌드 산출물).
scout류와 달리 원자적 변경(정책 추가↔GIF 교체가 상호의존)이라 분할 이득 없음; diff가 작아(≤6파일)
리뷰 추적 가능.

## 리스크

- **R1 (baseline 점수 오염)**: greedy를 건드리면 사이트 랭킹 숫자가 바뀜. **완화**: greedy 무변경
  계약을 AC로 고정, 기존 테스트 무변경 green + 재빌드 html 수치 diff 0 확인.
- **R2 (데모가 안 깨짐)**: gym-first가 오히려 초반 전력(잡기 없이)으로 체육관에 붙어 질 수도.
  단 현 데모 env에선 CATCH가 파티 강화가 아니라 점수일 뿐이라 전투력 무관 — 지는 조합이면 기존
  fallback(첫 12 heldout 중 클리어 seed 선택)이 흡수. **완화**: 기존 seed-선택 루프 유지.
- **R3 (캡션 정직성)**: GIF 정책과 랭킹 "scripted" 행이 다른 정책인데 같아 보이면 오도. **완화**:
  캡션에 데모 정책임을 한 구절 명시(en/ko 패리티 테스트 확인).

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `baselines.demo_policy` 신규 — 우선순위(battle 공격 > 내칸 CATCH > 살아있는 체육관 최단
  step > 생물 추적 > sweep) 계약이 테스트로 고정. `greedy_policy`·`random_policy` byte-identical.
- **AC2**: 기존 스위트 무회귀(763 green, 기존 test_baselines 무변경), ruff/mypy clean.
- **AC3**: `build_site.py`가 GIF 생성에만 demo_policy 사용 — `_free_policies`(랭킹·차트 수치 경로)
  무변경, 재빌드 html의 수치 부분 diff 0.
- **AC4**: 재생성된 `site/gameplay.gif`에서 체육관 가시 시 최단경로 접근이 확인됨(프레임 검사),
  boss_defeated 클리어 seed 우선 선택 유지.
- **AC5**: en/ko 캡션에 데모 정책 명시 구절 추가(랭킹 행과 동일 정책 오인 방지), en/ko 패리티 유지.
