---
slug: paper-arena-update
initiative: release-prep
status: completed
ended: 2026-07-06
extracted_to:
  - docs/paper/critter-gym.md
  - CITATION.cff
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# paper-arena-update — 결과 보고서

| 항목 | 값 |
|---|---|
| §5 | arena 단락 신설 — 도구·검증 band·Fable 5 5-run 0.132±0.037 **종결적 INCONCLUSIVE**·engagement 기각·**모델 세대 caveat**(opus-4-8 probe ↔ fable-5 arena 직접 비교 금지) + 한계(i) strict falsify + abstract 동기화. L3 가 battle-arena.md 와 수치 완전 일치 확인 |
| §7/§9 | stale "GPU 미측정" 수리 → M4-EC3 실측(950M/T4/95×) + 경계 라벨(single run·free T4·overworld slice) |
| Acknowledgments | tech report 명시 + AI 구축 공개(maintainer 책임·commit trailer·사전약정·CHANGELOG 정정) |
| CITATION.cff | cff 1.2.0, 저자 "Park, Myungsoo" — **표기 변경은 이 파일 2줄 수정이면 됨** (사용자 자유) |
| milestones | EC4 [x] 재정의(arXiv→tech report, 보류=사용자 결정 기록·재개 가능) — **M3 는 EC5(사람 게이트)만 남음** |
| README en/ko | "Reporting problems" — 제보 환영·정정=CHANGELOG 공개·AI 투명성 (soft-launch 방침과 세트) |
| 검증 | cff yaml OK·"unmeasured" 0·699/0·src/tests 0 파일. L3 2/2 APPROVE (plan-reviewer MALFORMED 1회→재호출) |

**Phase A 완료.** 남은 것 = 사람 게이트: ① repo Public ② Pages 토글 → Hub 등록·soft launch.
