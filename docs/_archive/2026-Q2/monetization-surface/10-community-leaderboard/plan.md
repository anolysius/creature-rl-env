---
slug: community-leaderboard
initiative: monetization-surface
status: active
started: 2026-07-02
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/community.py
  - tests/test_community.py
  - scripts/community_submit.py
  - scripts/build_site.py
  - tests/test_build_site.py
  - community/submissions/
  - docs/how-to/submit-your-model.md
  - docs/how-to/submit-your-model.ko.md
  - docs/CHANGELOG.md
  - site/index.html
  - site/index.ko.html
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 커뮤니티 리더보드 — 시즌제 공개 시험지 + 자가-신고 경쟁 (monetization-surface #10)

> 작성일: 2026-07-02 | 상태: 계획 | 추진 EC: **M5-EC3**(공개 리더보드 운영)의 *기술 artifact*.
> 사용자 지시(2026-07-02): "내 모델 사용하시는 분들이 자체적으로 공개 시험지로 자기 LLM 모델
> 벤치마크 경쟁" — 재미(시즌·순위) + 유입 퍼널(공개→봉인 트랙).

## 목표 — 2-트랙 설계의 공개 트랙

커뮤니티가 **로컬에서**(비용=제출자 부담) 자기 모델을 **시즌제 공개 seed 블록**에서 돌리고, 결과
JSON 을 repo 에 제출(장차 GitHub PR)해 사이트의 **Community leaderboard** 에 랭크되는 구조의
기술 artifact 전부. 봉인 트랙(#4–6 서명 인증서)이 "증명"을 담당하고, 공개 트랙은 **honor-system
(자가 신고)** 임을 사이트·가이드에 항상 라벨한다.

**시즌 = 우리 moat 가 재미가 되는 지점**: 절차생성이라 시즌마다 새 공개 블록 발급 가능(고정
벤치마크는 불가) — 순위 리셋 재미 + 오염 구조 완화.

**사람 게이트(불변식)**: 본 task 는 기술 artifact(스키마·검증·렌더·가이드·예시)까지. **실제 공개
운영(Pages 공개·PR 접수 공지·시즌 개시 선언·Hub 등록)=사람**. 사이트 섹션은 "prototype —
submissions open when announced" 라벨을 달고 출항한다.

## 설계 (freeze 대상 핵심 결정)

1. **시즌 seed 유도(결정론·공개)**: `season_seeds(season, n=100)` = `range(TEST_SEED_OFFSET +
   season*1000, +n)` (season ≥ 1, n ≤ 1000, `season*1000 + n ≤ 100_000` 가드). 성질: (a) 공개
   held-out 영역 안 → train 영역·**sealed 영역(≥1.1M)과 구조적 분리**, (b) 기존 default 공개 블록
   (`heldout_seeds`, 1.0M 시작)과 분리(season 1 = 1_001_000 시작), (c) 시즌 간 서로소, (d) 비밀
   없음 — 누구나 재현.
2. **제출 스키마(JSON)**: `schema_version`·`season`·`model`(이름)·`submitter`·`heldout_mean`
   (gym-clears)·`n_worlds`·`spec`(pinned BenchmarkSpec dict)·`reproduce`(한 줄 명령)·`date`·
   `self_reported: true`(스키마가 강제). `validate_submission(dict) -> list[str]`(빈 리스트=합격):
   필수 필드·타입·season 가드·spec 이 시즌 표준 spec 과 일치·점수 범위 sanity.
3. **랭킹**: `load_submissions(dir)` — 검증 통과분만, `heldout_mean` 내림차순, 시즌별 그룹.
4. **사이트 섹션**: `community/submissions/*.json` 을 빌드 시 읽어 시즌별 표 렌더 + **정직 라벨**
   ("self-reported, honor-system — 검증된 결과는 sealed 트랙" + "prototype, 접수 공지 전") +
   봉인 트랙 퍼널 한 줄. 제출 0 이어도 섹션은 "how to be first" 안내로 렌더(빈-상태 우아).
5. **예시 제출 1건**: 우리 scripted baseline 을 season 1 에서 실측해 `community/submissions/` 에
   커밋(organizer example 라벨) — 포맷의 살아있는 견본 + 빈 리더보드 방지.
6. **가이드**: `docs/how-to/submit-your-model.md` — 5분 흐름(러너 실행→JSON 생성→PR), honor-system
   규칙(재현 명령 필수·시즌 seed 만·자가 신고 명시), 시즌 개념, LLM 은 `llm_eval` 러너 참조.

## 작업 범위 (수정 대상)

| 파일 | 종류 | 변경 요지 |
|---|---|---|
| `src/critter_gym/community.py` | 신규 | season_seeds+가드, 스키마 상수, validate_submission, load_submissions(랭킹) |
| `tests/test_community.py` | 신규 | 시즌 유도(서로소·sealed 분리·가드)·스키마 검증(합격/각 오류)·랭킹·예시 파일 합격 |
| `scripts/community_submit.py` | 신규 | `--validate FILE`(CI용) / `--demo`(scripted baseline 을 season 1 실측→예시 JSON 생성) |
| `scripts/build_site.py` | 수정 | community 섹션(_community_html) + _COPY en/ko 키 + 빈-상태 |
| `tests/test_build_site.py` | 수정(추가만) | 섹션 렌더·정직 라벨·빈-상태·escape |
| `community/submissions/*.json` | 신규 | organizer 예시 1건(실측) |
| `docs/how-to/submit-your-model.md`(+`.ko.md`) | 신규 | 제출 가이드 en/ko(기존 evaluate-an-llm-agent 선례 — L1 SUGGEST) |
| `site/*.html` | 재생성 | `--no-assets` 재빌드 |

기존 core src 무수정(community.py 는 additive; build_site 는 섹션 추가).

## Step

1. (Red→Green) `community.py`: season_seeds(성질 4종 테스트) + validate_submission(합격+오류별) +
   load_submissions(랭킹·불합격 skip).
2. (Red→Green) `community_submit.py`: `--validate`(exit 0/1) + `--demo`(scripted baseline 실측 →
   스키마 합격 JSON). 예시 제출 생성·커밋.
3. (Red→Green) 사이트 섹션: 시즌별 표 + 정직 라벨 + 빈-상태 + 봉인 퍼널(en/ko). 재빌드+브라우저 확인.
4. 가이드 문서. 전체 스위트.

## 리스크

| 리스크 | 완화 |
|---|---|
| **공개 트랙을 "증명"으로 오인** | 스키마가 `self_reported: true` 강제 + 사이트/가이드 상시 라벨 + 봉인 트랙 퍼널 문구. |
| 시즌 블록이 sealed 와 충돌 | `season*1000+n ≤ 100_000` 가드(sealed 는 1.1M+) + 테스트가 분리 검증. |
| 사이트 하드코딩 회귀 | 섹션은 community/ 디렉토리와 SSOT 상수만 렌더. 예시 점수도 실측 산출물. |
| 접수 안 열었는데 열린 것처럼 보임 | "prototype — submissions open when announced(사람 결정)" 라벨을 섹션에 상시. |
| **default 블록 잠재 충돌**(L1 SUGGEST) — `heldout_seeds(n)` 에 상한 가드가 없어 n≥1000 호출 시 season 1(1_001_000~)과 겹칠 수 있음 | season 테스트에 경계 케이스 포함: `season_seeds(1,1000)` 과 `heldout_seeds(1000)` 서로소 assert(암묵 가정을 테스트로 명시화). |
| spec 위조 제출 | validate 가 시즌 표준 spec 일치 강제(불일치=불합격). 단 **점수 자체는 검증 불가**(honor-system) — 라벨로 정직 처리, 증명은 sealed 트랙. |

## Acceptance Criteria (G1 freeze)

1. `community.py`: `season_seeds` 4성질(공개 영역 내·sealed(≥1.1M) 분리·시즌 서로소·default 블록
   분리 — **`heldout_seeds(1000)` 과 서로소 경계 테스트 포함**, L1 SUGGEST) + 범위 가드 ValueError
   — 테스트로 고정. `validate_submission` 이 필수필드·타입·season·
   spec-일치·점수 sanity 를 검사하고 오류 리스트 반환(빈=합격). `self_reported: true` 필수.
2. `load_submissions`: 검증 통과분만 heldout_mean 내림차순 랭킹, 불합격 파일 skip(경로 보고).
3. `community_submit.py`: `--validate`(합격 exit 0/불합격 1+오류 출력, CI용), `--demo`(scripted
   baseline 을 season 1 seed 에서 **실측**해 스키마-합격 JSON 생성). 예시 제출 1건 커밋되고
   `--validate` 합격.
4. 사이트 Community 섹션: 시즌별 표(제출 렌더) + **정직 라벨**(self-reported·honor-system·sealed
   트랙 퍼널·"submissions open when announced") en/ko + 빈-상태 우아 + 전 값 escape. 재빌드+브라우저
   확인.
5. `docs/how-to/submit-your-model.md` **+ `.ko.md`**: 5분 제출 흐름·honor-system 규칙·시즌 개념·
   LLM 러너 참조(양 언어 — L1 SUGGEST).
6. 회귀 0(baseline 630 — 기존 site 테스트 불변), ruff/mypy clean. CHANGELOG 1줄. **사람 게이트
   명시**: 접수 공지·Pages 공개·시즌 개시·Hub 등록은 본 task 산출물에 포함되지 않음.
