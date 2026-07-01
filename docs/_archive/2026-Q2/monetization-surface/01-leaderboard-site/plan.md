---
slug: leaderboard-site
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/**            # 생성 산출물 (index.html + 복사된 killer_demo.gif) — git 추적
extracted_to: []
supersedes: []
---

# 정적 리더보드 웹사이트 (M5 런치 자산 prototype)

> 작성일: 2026-07-01 | mode: standard | 마일스톤: M5-EC3 / 런치

## 목표

`leaderboard.py` 의 결과(rank·name·held-in·held-out·gap)를 **프레임워크 없는 단일 정적 HTML**
페이지로 렌더하는 생성기 `scripts/build_site.py` 를 만든다. 페이지는 (a) 랭크된 리더보드 표
(b) 킬러데모 GIF(`docs/assets/killer_demo.gif`) (c) moat 설명(오염·암기·게이밍 불가 sealed eval,
held-out seed split, RLVR) (d) repo 링크 를 담는다. **npm·빌드스텝·프레임워크 0** — 파이썬이 HTML
한 장 + 자산 복사를 찍어내 `site/` 에 출력, GitHub Pages 로 그대로 호스팅 가능.

**정직 게이트**: 빌드 + **로컬 프리뷰**(`python -m http.server`)까지 자율. **GitHub Pages 공개 토글
= 사람**(공개 배포=공개 게이트). 페이지 문구는 정직(프로토타입·in-process·수치 출처 명시).

## 선행 조건

- `leaderboard.py`: `Leaderboard.from_score_table`/`to_dict`/`to_json`, `run_benchmark(spec, policies)`,
  `LeaderboardEntry(rank, name, heldin_mean, heldout_mean, gap)` — main 안착.
- `scoreboard.py` baseline policies(random/scripted 무료; PPO/recurrent 는 `[rl]` 격리 → 없으면 skip).
- `docs/assets/killer_demo.gif` (EC6) 존재.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `scripts/build_site.py` | 신규 — testable `render_site(leaderboard, *, generated_note) -> str`(순수 HTML 문자열) + main()(leaderboard 빌드/JSON 로드 → `site/index.html` 작성 + GIF 복사 + 프리뷰 안내) | **중** (신규 도메인=web) |
| `tests/test_build_site.py` | 신규 — `render_site` 가 유효 HTML(각 entry rank·name·held-out 포함)·결정론·moat 문구·정직 캡션 포함 | 중 |

### 영향 범위

- `render_site` 는 `Leaderboard.to_dict()` 만 읽음(read-only). 채점·env·기존 스크립트 무변경.
- 출력 `site/` 는 생성물(git 추적: index.html + 복사된 gif). GitHub Pages source 후보.
- 신규 web 도메인이나 프레임워크 0 → 의존성 추가 0(stdlib html/json).

## Step별 계획 (TDD)

1. **Red** — `tests/test_build_site.py`:
   - `render_site` 가 각 LeaderboardEntry 의 name·rank·held-out mean 을 HTML 에 포함.
   - 결정론(같은 leaderboard → 같은 HTML).
   - moat 설명 문구("held-out"/"contamination"/"RLVR" 등) + 정직 캡션("prototype"/"in-process") 포함.
   - `<html`·`<table` 등 최소 유효 골격.
2. **Green** — `build_site.py`:
   - `render_site(leaderboard, *, generated_note)`: stdlib 로 HTML 조립(표 + GIF `<img>` + moat 섹션
     + repo 링크 + 정직 캡션). XSS-safe 하게 `html.escape` 로 값 이스케이프.
   - `main()`: 무료 baseline(random/scripted)로 `run_benchmark` → Leaderboard (또는 `--from-json` 로
     저장된 JSON 로드) → `site/index.html` 작성 + gif 복사 + "로컬 프리뷰: python -m http.server -d site" 안내.
     PPO/recurrent 는 `[rl]` 없으면 skip(표에서 제외, 문구 명시).
3. **Refactor** — 템플릿 문자열 정리, docstring 에 정직 게이트("공개 배포=사람") 명시.

## 검증 방법

- 신규 테스트(HTML 내용·결정론·moat 문구·정직 캡션) 통과.
- `python scripts/build_site.py` → `site/index.html` 생성 + 로컬 프리뷰 수동 1회(브라우저/HTML 확인).
- 전체 pytest 회귀 0(525 유지 + 신규). ruff clean(scripts 는 mypy src scope 외).
- 페이지에 프레임워크/네트워크 의존 0(정적, 로컬 파일로 열림).

## 리스크

| 리스크 | 완화 |
|---|---|
| baseline 점수 계산이 느림/무거움(PPO/recurrent) | 무료 baseline(random/scripted)만 기본, PPO/recurrent 는 `[rl]` 있을 때만. 또는 `--from-json` 로 사전 계산 JSON 로드. |
| 공개 배포를 "완성"으로 과대 | 페이지·docstring 에 "prototype·in-process·공개 토글=사람" 명시. 본 task 는 빌드+로컬 프리뷰까지. |
| 신규 web 도메인 유지비 | 프레임워크 0(stdlib), 단일 파일 생성기 → 유지 표면 최소. |
| HTML 인젝션 | 값은 `html.escape`. baseline 이름은 내부 통제(사용자 입력 아님)지만 방어적으로 escape. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[hard]** `build_site.render_site(leaderboard, *, generated_note) -> str` 가 결정론적으로 유효
   HTML 반환: 각 entry 의 rank·name·held-out mean 포함 + moat 설명(held-out/contamination/RLVR) +
   정직 캡션(prototype/in-process) + 킬러데모 GIF `<img>` 참조. 값 `html.escape`. 신규 테스트.
2. **[tooling]** `scripts/build_site.py` main() 이 leaderboard(무료 baseline 또는 `--from-json`) →
   `site/index.html` 작성 + gif 복사 + 로컬 프리뷰 안내. 프레임워크/네트워크 의존 0. PPO/recurrent
   부재 시 graceful skip.
3. **[honesty]** 페이지 + docstring 에 "prototype·in-process sealing·수치 출처·**공개 배포=사람 게이트**" 명시.
4. **[regression]** 전체 pytest 회귀 0(525 유지 + 신규). ruff clean. 기존 스크립트·채점 무변경.
