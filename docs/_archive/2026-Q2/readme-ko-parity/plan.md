---
slug: readme-ko-parity
initiative: null
status: active
started: 2026-07-13
acceptance_freeze: true
mode: standard
task_type: general
domains: [docs]
scope_paths:
  - README.md
  - README.ko.md
extracted_to: []
supersedes: []
---

# 한국어 README 완전 패리티 + 영문 stale 수정 (마케팅 전 체크리스트 #3)

> 작성일: 2026-07-13 | 상태: 계획 | 단발 (사용자 요청: "한국 리드미를 영문 그대로 번역으로")

## 목표

사용자 지적: 한국어 README가 부실(78줄/6섹션 vs 영문 161줄/12섹션). 조사 중 **정직성 drift 발견**:
ko가 "GPU(T4)에서 수억 steps/s"를 주장하나 영문은 "GPU 목표(M4-EC3) **미측정**"이라고 명시 —
낡은 ko 요약이 영문이 부정한 수치를 주장. 영문에도 stale 존재: Release status가 "공개는 의도적으로
미수행"이라 하나 **repo는 이미 public**(2026-07-06 공개).

수리 3건:
1. **README.ko.md 전면 재작성** — 영문 12섹션 완전 번역 패리티(CI 배지·What it measures 7불릿
   정직 라벨 포함·reproduce 원커맨드·Positioning·Reproducibility·Contributing·Citation·Release
   status·License). 과대 주장(GPU 수억) 제거, 영문의 정직 캐비앗("CPU, single-run directions;
   GPU 미측정") 그대로 번역.
2. **README.md stale 수정(최소)** — Release status의 "making the repository public ...
   deliberately not performed" → 이미 공개됨 반영(남은 게이트: GPU 측정·arXiv·버전 태그).
3. **양쪽에 사이트 링크 추가** — 라이브 사이트(리더보드)와 how-it-works(작동 원리) 페이지 링크
   (en→en 페이지, ko→ko 페이지). 마케팅 유입 동선.

**한국어 웹사이트는 범위 외** — en/ko 키 패리티가 테스트로 이미 강제(구조적 패리티), #122 머지로
최신 반영됨. README만이 실제 격차.

## 선행 조건

- main = 7e5640a (#122 머지), 791 tests green. ✅
- 영문 README 전문 확보(161줄). 번역 시 수치·정직 라벨은 영문 문장 그대로(SSOT=영문/코드) —
  ko 하단의 기존 "SSOT는 영문/코드" 미러 각주 유지.

## 작업 범위

| 파일 | 변경 | 영향도 |
|---|---|---|
| `README.ko.md` | 전면 재작성(12섹션 완전 패리티, 과대주장 제거) | 낮음(docs) |
| `README.md` | Release status stale 1블록 수정 + 사이트 링크 1-2줄 | 낮음(docs) |

코드/테스트 무변경 — docs-only.

## Step별 계획

1. README.md stale 수정 + 사이트 링크.
2. README.ko.md 전면 재작성(영문 최신본 기준 완전 번역).
3. 상호 링크·앵커·상대경로(.ko.md 가이드 링크) 검증.

## 검증 방법

- docs-only: 테스트 스위트 무회귀 확인(791 — 코드 무변경 sanity, 그 이상의 의미 없음).
- 링크 검증(L1 SUGGEST 반영, 방법 명시): 상대 링크는 `ls <대상>`으로 파일 존재 확인;
  **외부 사이트 URL은 `curl -sI <url> | head -1`로 HTTP 200 확인**(= 링크 대상이 라이브).
- 정직성 diff 검증(방법 명시): **메인이 수동 대조 후 그 대조표를 L3 prompt에 inline 제공** —
  ko의 모든 수치 토큰(%, ×, steps/s, 버전)을 추출해 영문 대응 문장 존재를 1:1 확인. 자동
  스크립트는 과잉(1회성 docs)이라 채택 안 함(사유 명시).

## 리스크

- **R1 (번역 중 의미 drift)**: 수치·정직 라벨이 번역에서 강해지거나 약해질 위험. **완화**: 수치
  포함 문장은 영문 값 그대로, 정직 캐비앗은 이탤릭/굵기까지 대응 번역. 최종 대조를 L3에서 확인.
- **R2 (영문 stale 수정의 사실 오류)**: Release status 수정이 현실과 어긋날 위험. **완화**: 공개
  상태(repo public·사이트 라이브)는 세션에서 확인된 사실만 반영, 남은 게이트(GPU·arXiv·태그)는
  기존 서술 유지.

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: README.ko.md가 영문 12섹션 전부를 커버(섹션 수 ≥ 영문과 동일), 영문에 없는 수치 주장
  0(특히 "GPU 수억 steps/s" 제거), 정직 캐비앗 전부 번역 유지.
- **AC2**: README.md Release status가 공개 완료 사실을 반영(남은 게이트 서술 유지), 양쪽에 라이브
  사이트+how-it-works 링크(언어 대응) 추가.
- **AC3**: 문서 내 상대 링크 전부 유효(대상 파일 존재 `ls` 확인) + **새로 추가하는 외부 사이트
  URL이 HTTP 200**(`curl -sI`; README가 링크하는 페이지가 라이브임을 확인 — 사이트 *내용*은
  범위 외 그대로).
- **AC4**: 코드/테스트 무변경 sanity(791 green 재확인 — README는 코드 경로가 아니므로 당연히
  무회귀여야 하며, 이 확인은 실수로 다른 파일을 건드리지 않았다는 증거), CHANGELOG 1줄.
