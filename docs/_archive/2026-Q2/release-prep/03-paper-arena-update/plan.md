---
slug: paper-arena-update
initiative: release-prep
status: active
started: 2026-07-06
acceptance_freeze: true
task_type: general
mode: standard
domains: [rl-env]
scope_paths:
  - docs/paper/critter-gym.md
  - docs/reference/milestones.md
  - CITATION.cff
  - README.md
  - README.ko.md
extracted_to: []
supersedes: []
---

# paper-arena-update — 공개 전 준비 ③ (tech report 확정 + 인용 + 신고 정책)

> 작성일: 2026-07-06 | 상태: 계획 | 마일스톤: M3-EC4/EC5 Phase A-3 (공개 전 마지막 자율 단계)

## 목표

논문을 **in-repo technical report 로 확정**하고 (arXiv 무기한 보류 — 사용자 결정
2026-07-06), 공개 전 마지막 문서 부채를 정리한다:

1. **§5 아레나 실측 반영**: engagement confound 가 "남은 경계"에서 "측정 완료"로 —
   arena 도구(#22)+Fable 5 실측(#23): 5-run 0.132±0.037 **종결적 INCONCLUSIVE**,
   engagement 가설 기각. **모델 세대 명시 구분** (기존 probe=claude-opus-4-8 /
   arena=claude-fable-5 — 직접 비교 금지, 구조 결론은 arena 내 self-contained).
   §5 한계 (i)에 strict_battle 반증(#6) 1줄 (min-1 클램프는 binding 아님 — 중립 chip
   +순환+재입장 힐이 attrition 의 실체).
2. **§7/§9 stale 수리**: "GPU 미측정" 2곳 → M4-EC3 실측 반영 (T4 overworld vmap
   ~950M steps/s = 목표 95×; 경계: single run·free T4·overworld slice, CPU
   full-episode ~22M/s 로 EC 초과).
3. **CITATION.cff** 신설 — GitHub "Cite this repository" (arXiv 없이 표준 인용).
4. **milestones EC4 재정의**: "arXiv 초안" → "in-repo technical report" [x] + arXiv
   보류 기록 (사용자 결정 명시).
5. **README 신고 정책** (en/ko): 버그·오류 제보 환영 + "정정은 CHANGELOG 에 공개
   기록" + AI-구축 투명성 1줄 (커밋 trailer·사전약정 측정 규율) — 사용자 두려움
   (비난 리스크)에 대한 구조적 대응, 논문 Acknowledgments 에 AI 공개 문구.

## Acceptance Criteria (G1 freeze)

- **AC1 (§5)**: arena 단락 추가 — 도구·프로토콜·5-run 수치·종결성·engagement 기각 +
  **모델 세대 구분 명시** + battle-arena.md 참조; 한계 (i)에 strict falsify 1줄;
  abstract 1구 동기화. 과장 0 (기존 라벨 규율 유지).
- **AC2 (§7/§9)**: "unmeasured" 문구 0건 — 실측+경계 라벨로 대체 (검증: grep).
- **AC3 (CITATION.cff)**: cff-version 1.2.0 유효 (yaml parse), 저자=Myungsoo Park
  (사용자, 커밋 계정 기준 — 표기 변경은 사용자 1줄 수정으로 가능함을 report 에 명시).
- **AC4 (milestones)**: EC4 재정의+[x]+arXiv 보류 사유 기록; EC5 문구는 유지.
- **AC5 (README en/ko)**: "Reporting problems" 소절 (제보 환영·정정 정책·AI 투명성).
- **AC6 (무회귀)**: 제품 코드 0 파일, 699/0.

검증 커맨드: grep("unmeasured")=0 · yaml parse(CITATION.cff) · pytest 699/0 ·
`git diff -- src tests`=0. 커밋 단위: 단일 커밋(단독 PR). 다음: (사람) Public+Pages.
