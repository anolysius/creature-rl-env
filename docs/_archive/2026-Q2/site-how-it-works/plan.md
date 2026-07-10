---
slug: site-how-it-works
initiative: null
status: active
started: 2026-07-10
acceptance_freeze: true
mode: standard
task_type: general
domains: [site]
scope_paths:
  - scripts/build_site.py
  - tests/test_build_site.py
  - site/index.html
  - site/index.ko.html
  - site/how-it-works.html
  - site/how-it-works.ko.html
extracted_to: []
supersedes: []
---

# 사이트 "시험지 설명" 페이지 — 방문자의 진짜 질문에 답하기 (랜딩+딥다이브 1페이지)

> 작성일: 2026-07-10 | 상태: 계획 | 단발 (사용자 요청·구조 선택 완료: 랜딩+1페이지)

## 목표

**사용자가 GIF를 보며 실제로 던진 질문들 = 방문자들의 질문**이라는 관찰에서 출발. 현재 사이트는
"왜 생물을 안 잡고 체육관을 깨지?", "체육관 승리 조건이 뭐지?", "이 시험지가 뭘 재는 거지?"에
답이 없어 — 방문자가 포켓몬 문법을 가정하고 보면 룰이 제각각으로 *보이는* face-validity 구멍.

수리(사용자 선택 구조): **랜딩은 짧게 유지 + "How the exam works" 딥다이브 1페이지(en/ko) 추가.**

1. **랜딩 추가분(작게)**: ① "재는 것 / 일부러 안 재는 것" 요약 박스 + 딥페이지 링크,
   ② 범례에 잡기 명확화 한 줄("잡기는 별도 점수 과제 — 전투는 고정 스타터 파티, 잡아도 전투력
   불변"), ③ 데모 캡션 근처에 딥페이지 링크.
2. **신규 페이지 `how-it-works(.ko).html`** (역학=객관 사실만, **신규 측정 주장 없음** — LLM 곡선
   등 단일-run 결과는 판매 페이지 게재 = 사람 게이트라 제외):
   - **체육관 승리 조건**: 파티 전멸 전에 보스 HP 0 (결정론·무운). 데미지 = 위력×(공/방)×**상성
     배수(×2/×1/×0.5 = 유리 vs 불리 4배 스윙)** — 상성이 사실상 승패를 가름.
   - **숨은 상성표**: 보스 타입 *번호*는 보이지만 *뭐가 이기는지*는 세계(seed)마다 재추첨 —
     암기 불가, 관찰-추론만 가능. (moat 서사와 연결)
   - **카운터 찾기의 복잡도**: 후보 3개(스타터)·실험 1번=정답 1칸 — 탐색은 작게 설계. 난이도는
     실험의 **비용 구조**에: 실험 중 피격·걸음 예산 소모·장부 크기(등장 타입 수×3)·(knob)
     찔러보기 금지(commit)·관찰 오염(숨은 2차 타입)·오답 데미지 0(strict/SE-only).
   - **안티-grinding 룰 표**(일관성 원칙): 야생 파밍 없음 / 잡기≠전투력 / 레벨업=승리 보상만 /
     재도전 무한·결정론 → 각각 "이해 없이 이기는 우회로" 차단. "수학 시험장에서 계산기·오픈북
     금지" 비유.
   - **재는 것 / 안 재는 것**: 재는 것 = 장기 계획·숨은 규칙 추론·실험 규율·일반화. 안 재는 것 =
     RPG식 자원·성장 관리(의도적 배제, 이유 명시). 정직 톤 유지.
3. **빌더 리팩터(최소)**: `_COPY`에 how-page 키 추가(en/ko 패리티), `render_how_page(lang)` 신규,
   `main()`이 4개 html 기록. 기존 `render_site` 산출물은 추가 박스·범례·링크 외 **수치 diff 0**.

## 선행 조건

- main = 4a8d672 (#121 머지), 785 tests green, clean. ✅
- 빌더 구조 확인: `_COPY[lang]` 사전 + `render_site(lang)` + main이 2 html 기록(build_site.py:842-878)
  → 페이지 추가 = copy 키 + 렌더 함수 + 기록 루프 확장.
- 콘텐츠 소스 = 이번 대화에서 검증된 사실들(battle.py 데미지 공식·guarantee #15·안티-grinding 룰의
  코드 근거) — 전부 이 세션에서 코드로 확인됨.
- en/ko 키 패리티는 기존 테스트가 강제(test_build_site) — 신규 키도 동일 규율.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `scripts/build_site.py` | `_COPY` how-키 추가(en/ko) + `render_how_page` 신규 + 랜딩 박스·범례 1줄·링크 + main 4-html 기록 | **중** | 기존 랜딩 수치 diff 0 유지 |
| `tests/test_build_site.py` | 신규: how-page 렌더(en/ko)·키 패리티·랜딩↔딥페이지 상호 링크·잡기 명확화 문자열·"안 재는 것" 정직 문자열·수치 SSOT 불변 | 낮음 | 기존 테스트 무변경 |
| `site/{index,index.ko}.html` | 재빌드(박스·범례·링크 추가, 수치 불변) | 낮음 | |
| `site/{how-it-works,how-it-works.ko}.html` (신규) | 신규 산출물 | 낮음 | GitHub Pages가 머지 시 서빙 |

### 영향 범위 (import 그래프)

- **src 무변경** — 순수 사이트 텍스트/빌더. leaderboard·차트·티어·커뮤니티 데이터 경로 무변경.
- 신규 페이지는 데이터 미소비(정적 설명) → 수치 하드코딩 0 원칙 자동 충족(수치 인용 시 상성 배수
  ×2/×1/×0.5 같은 **엔진 상수**만, 측정 결과는 게재 안 함).

## Step별 계획

1. **테스트(Red)** — how-page: en/ko 렌더 성공·키 패리티·랜딩에 링크 존재·딥페이지에 back-링크·
   잡기 명확화 문자열(범례)·"deliberately does NOT measure" 류 정직 문자열·기존 랜딩 수치 불변.
2. **빌더(Green)** — copy 키 + `render_how_page` + 랜딩 3개 추가분 + main 4-html.
3. **재빌드 + 검증** — `--no-assets`(GIF 재생성 불필요), 수치 diff 0 확인, 브라우저/HTML 구조 검사.

## 검증 방법

- `.venv/bin/python -m pytest -q` → 785 + 신규 무회귀 green (기존 test_build_site 무변경).
- `.venv/bin/python -m ruff check .` clean (src 무변경 — mypy 대상 불변).
- `.venv/bin/python scripts/build_site.py --out site --no-assets` → 4 html 기록.
- **랜딩 수치-diff 0 절차**(demo-gif task 계승): `git diff site/index*.html`에서 숫자 패턴 포함
  줄의 변경 hunk 0(추가 박스·범례·링크 텍스트만).
- en/ko 패리티: 신규 copy 키 집합 동일(테스트 강제).
- **상수 code-sync**(L1 SUGGEST 반영): how-페이지가 인용하는 엔진 상수(상성 배수)를 테스트가
  `critter_gym.types.SUPER_EFFECTIVE/NOT_VERY_EFFECTIVE` 실제 값에서 유도해 페이지 문자열과 대조 —
  나중에 엔진 값이 바뀌면 사이트 문구가 낡는 즉시 테스트가 잡음(code-content drift 방지).

## 리스크

- **R1 (과잉 주장)**: 설명 페이지가 측정 결과를 슬쩍 헤드라인화할 위험. **완화**: 역학=객관
  사실만(엔진 상수·룰), 측정 주장 0 — LLM 곡선 게재는 별도 사람 결정으로 명시 배제. 정직 문자열
  테스트로 고정.
- **R2 (en/ko 표류)**: 페이지가 늘며 번역 불일치. **완화**: 기존 키-패리티 테스트 규율을 신규
  키에 동일 적용.
- **R3 (랜딩 수치 오염)**: 빌더 리팩터가 기존 랜딩 데이터를 건드릴 위험. **완화**: 수치-diff 0
  검증 절차 + 기존 테스트 무변경 green.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `site/how-it-works(.ko).html` 신규 — 승리 조건(상성 4배 스윙)·숨은 상성표(암기 불가)·
  카운터 복잡도(탐색 작음/비용 구조)·안티-grinding 룰 표·"재는 것/안 재는 것"을 담고, **측정 주장
  0**(엔진 상수만 인용).
- **AC2**: 랜딩에 ① 재는것/안재는것 요약 박스+딥페이지 링크 ② 범례 잡기 명확화 1줄 ③ 데모 캡션
  링크 — 추가되고, **기존 수치 포함 줄 변경 hunk 0**.
- **AC3**: en/ko 패리티 — 신규 copy 키 집합 동일 + 딥페이지 상호 언어 토글.
- **AC4**: 신규 테스트가 AC1-3(렌더·패리티·링크·정직 문자열·수치 불변)을 커버, 기존 테스트 무변경.
  785 무회귀, ruff clean.
- **AC5**: 재빌드 완료(4 html), 브라우저 또는 HTML 구조 검사로 en/ko 딥페이지 확인.
