# QA 체크리스트 — oss-release-prep

## 영향도
- 루트 메타 파일만(LICENSE 신규, README.md 갱신, CONTRIBUTING.md 신규). 제품 코드/테스트 무변경.

## 회귀 가드
- [x] .py 무변경(diff = LICENSE/README/CONTRIBUTING + plan/report)
- [x] pytest 181 passed/2 skipped 불변(코드 무영향)
- [x] LICENSE ↔ pyproject `license={text="MIT"}` 정합
- [x] broken-link 0(README/CONTRIBUTING 링크 전부 실재 파일)

## 정확성 (L3 코드/논문 대조)
- [x] env id 6종 = registration.py 일치(v0/procgen/commit/forage/duel/muster)
- [x] quickstart(register_envs+gym.make+reset(seed)) 동작
- [x] install 4 extra([rl]/[viz]/[render]/[dev]) = pyproject 일치
- [x] 수치(40/45%, ~266k, ≥0.20/≥0.10, C +3.9/+0.2) = 논문 verbatim

## 정직성
- [x] Pokémon=메타포(비경쟁), Procgen/Craftax/XLand 대비
- [x] (A) 측정 / (B) 토대지 증명 아님
- [x] 외부 발행(Hub/repo-public)=사람 게이트, EC5 자동충족 주장 0
- [x] 과대 마케팅 0(상세·caveat는 논문으로 라우팅)
