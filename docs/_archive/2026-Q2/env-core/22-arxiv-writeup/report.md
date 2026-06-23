---
slug: arxiv-writeup
initiative: env-core
status: completed
ended: 2026-06-23
extracted_to:
  - docs/paper/critter-gym.md     # the draft itself (evergreen artifact)
  - docs/paper/README.md          # figure→source reproduction map
changelog_entry: docs/CHANGELOG.md (env-core, 2026-06-23)
---

# arXiv writeup 초안 (M3-EC4) — 결과 보고서

## 요약

활성 M3의 미충족 **EC4(arXiv writeup)** 전진: 측정 자산을 **arXiv 논문 초안**으로 패키징(docs-only).
`docs/paper/critter-gym.md`(8 섹션) + `docs/paper/README.md`(수치↔출처 재현 맵). 모든 정량 주장이 코드/측정에
근거(날조 0), **CI-reproducible(test-frozen gate) vs run-derived(run 평균)** 구분 라벨.

| 섹션 | 내용 |
|---|---|
| §2 env design | obs/action, RLVR, procgen seed split, throughput ~266k (run-derived) |
| §3 (A) 인스턴스 일반화 | held-in 40% vs held-out 45%, gap≈0 (run-derived) |
| §4 load-bearing + learnability | Gate0≥0.20/Gate1≥0.10 **CI-frozen**, margin ≈0.48/0.36 run-derived; gym-clear-only oracle/infer 4.19≫type_blind 1.81>probe 1.06 |
| §5 (B) 장르 토대 | 4 family/3 축; C gap +3.9 vs +0.2; D muster 1.42≫rush 0.00; B forgiving — within-family 대조 = skill-structural |
| §6 related work | Procgen/Craftax/XLand 대비, Pokémon=메타포 |
| §7 limitations | B=토대 아닌 증명 / D confound / 단일run·N / learnability 천장·oracle==infer / C win 예측가능성 / 재현 tier |

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 8섹션 초안 | ✅ | abstract~conclusion 완비 |
| AC2 수치 출처 일치 + tier 라벨 | ✅ | README 맵; L3 accuracy reviewer 코드 대조 APPROVE(4.188→4.19 등 정확) |
| AC3 정직 포지셔닝 | ✅ | Pokémon=메타포(abstract/§1/§6), Procgen/Craftax/XLand 벤치 |
| AC4 honest limitations | ✅ | §7 전 caveat + L3 SUGGEST(duel 예측가능성) 반영 |
| AC5 재현 포인터 + broken-link 0 | ✅ | README figure→source 맵 |
| AC6 docs-only 무회귀 + L3 | ✅ | 제품 코드/테스트 무변경(181 passed 불변), L3 APPROVED |

전 AC ✅. acceptance를 *정직한 초안 + 수치 출처 근거*로 freeze(제출 아님).

## 변경 파일 상세

**신규(docs-only)**
- `docs/paper/critter-gym.md` (≈245줄) — arXiv 초안. abstract/intro+positioning/env design/측정 결과(A·load-bearing·learnability·B)/related work/honest limitations/conclusion.
- `docs/paper/README.md` — 수치↔모듈/테스트 재현 맵 + CI-reproducible vs run-derived tier.

## 발견된 이슈 (심각도)

- **(낮음, L3 honesty reviewer 반영)** family C ≈4.3 win에 DESIGN의 duel-boss 예측가능성 caveat가 누락 → §5/§7에 추가(고정 패턴+charge obs 노출로 win이 예측가능성 일부 반영; skill-structural gap은 유효).
- **(낮음, L1 반영)** load-bearing 1.00/0.52/0.84/0.47은 run-derived, 테스트는 ≥0.20/≥0.10 gate만 동결 → 라벨 구분.

## 흡수처 매핑 (extracted_to)

- `docs/paper/critter-gym.md` + `docs/paper/README.md` — 초안 자체가 evergreen 산출물. 정직 scope는 DESIGN §3.1.1 SSOT 준수.

## 타입 체크 / 빌드 결과

docs-only — 제품 코드 무변경. pytest 181 passed/2 skipped 불변(영향 없음). broken-link 0.
