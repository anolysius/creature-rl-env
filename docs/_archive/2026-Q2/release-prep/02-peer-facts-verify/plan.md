---
slug: peer-facts-verify
initiative: release-prep
status: active
started: 2026-07-06
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - docs/explanation/competitive-analysis.md
  - docs/paper/critter-gym.md
  - .github/workflows/pages.yml
extracted_to: []
supersedes: []
---

# peer-facts-verify — 공개 전 준비 ② (피어 사실 검증 + 약관 확인 + Pages 워크플로)

> 작성일: 2026-07-06 | 상태: 계획 | 마일스톤: M3-EC5 Phase A-2

## 목표

공개 전 마지막 사실 검증. 경쟁 분석 문서가 스스로 명령한 것("**[verify] 표기는 1차
자료 확인 전 공개 금지**")을 이행한다:

1. **피어 사실 검증** (WebSearch/WebFetch, 1차 자료 = 공식 repo/논문): Procgen·
   Craftax/Crafter·XLand-MiniGrid·NetHack(NLE)/MiniHack 의 [verify] 표기 항목 —
   확인된 것은 표기 해제+출처 명시, 확인 못한 것은 **주장 완화 또는 삭제** (틀린
   피어 주장 공개 = 신뢰 타격).
2. **약관 2건 확인** (Anthropic 최신 정책 원문): (a) 구독 CLI 대량 자동화 측정의
   허용 범위 (b) Claude 벤치마크 수치 공개 관련 조항 — 결과를 문서에 1줄씩 기록
   (문제 시 사용자 에스컬레이션, 임의 해석 금지).
3. **Pages 배포 워크플로**: `.github/workflows/pages.yml` — `site/` 폴더를 GitHub
   Pages 로 배포 (공식 actions/deploy-pages; **workflow 는 준비물일 뿐, Pages 활성화
   = Settings 토글 = 사람**).
4. (부수) molt.church 정찰 — 실재·성격·게시 규칙 확인만 (게시는 사람 게이트,
   결과는 report 에 기록).

## 영향도

| 파일 | 변경 | 등급 |
|---|---|---|
| `docs/explanation/competitive-analysis.md` (수정) | [verify] 전수 종결 + §4 를 검증 기록으로 대체 | 낮음 (docs; 참조처=roadmap 문맥뿐, 링크 무변경) |
| `docs/paper/critter-gym.md` (수정) | 피어 언급 동일 기준 처리 (있는 경우만) | 낮음 (docs) |
| `.github/workflows/pages.yml` (신규) | Pages 배포 준비물 (활성화=사람 토글 전까지 no-op) | 낮음 (CI 메타, 제품 무관) |

검증 커맨드: `[verify]` grep 0건 · `python3 -c "yaml.safe_load(...)"` (pages.yml) ·
`.venv/bin/python -m pytest -q` (699/0). 커밋 단위: 단일 커밋(단독 PR). 다음 단계 진입
조건: 본 task 머지 → A-3 `paper-arena-update` → (사람) repo Public + Pages 토글.

## Acceptance Criteria (G1 freeze)

- **AC1 (피어 사실)**: competitive-analysis.md 의 [verify] 표기 전수 처리 — 각 항목이
  (확인됨+출처) / (완화됨) / (삭제됨) 중 하나로 종결, 미처리 [verify] 0건. §4
  verify-list 섹션을 검증 결과 기록으로 대체. 논문(critter-gym.md)의 피어 언급도
  동일 기준 (있는 경우).
- **AC2 (약관)**: 두 확인 결과가 문서에 기록됨 (출처 URL+확인 날짜) — 리스크 발견 시
  자율 판단 금지, 사용자 보고.
- **AC3 (Pages 워크플로)**: pages.yml YAML 유효 + 공식 액션 사용 + `site/` 배포 구성;
  실행/활성화는 범위밖(사람) 명시.
- **AC4 (무회귀)**: 제품 코드 0 파일, 전체 테스트 699/0.

## 리스크

| 리스크 | 대응 |
|---|---|
| 웹 검증이 기존 주장을 뒤집음 (예: 피어에도 sealed eval 존재) | 정직 원칙 그대로 — 문서를 사실에 맞춰 하향 수정하고 보고 (반증 환영) |
| 약관 해석 애매 | 임의 해석 금지 — 원문 인용+사용자 에스컬레이션 |
| Pages 워크플로가 머지 즉시 배포 시도 | Pages 미활성 상태에선 no-op; 활성화 자체가 사람 토글임을 워크플로 주석에 명시 |
