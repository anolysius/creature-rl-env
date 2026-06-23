# QA 체크리스트 — competitive-analysis (docs-only)

## 영향도
- docs-only: `docs/explanation/competitive-analysis.md` 신규. 제품 코드/테스트 무변경.

## 회귀 가드
- [x] .py 무변경(diff = competitive-analysis.md + plan/report)
- [x] pytest 181 passed/2 skipped 불변
- [x] broken-link 0(docs/paper/*, DESIGN.md 실재)

## 정직성 (L3 검증)
- [x] 열위 축 먼저·분명(§3 "where we lose, stated first": 속도/성숙·채택/난이도/meta-RL 폭)
- [x] "전 축 우위" 서술 0
- [x] 우리 수치(266k, 45/40%, gate ≥0.20/≥0.10, C +3.9) 논문 일치(날조 0)
- [x] peer 사실 정성/[verify] 라벨(과신·날조 0)
- [x] 속도 basis 명시(CPU/core ≠ GPU 동일행 비교 금지)
- [x] DESIGN §9 "moat prospective" 자기평가와 일치(과대 0)

## 갭 탐지기
- [x] 갭 register: 6 갭 × (못함/이유/필요기능/unblocks 마일스톤)
- [x] 다음 기능 우선순위 입력으로 사용 가능(난이도/JAX/family/multi-run)
