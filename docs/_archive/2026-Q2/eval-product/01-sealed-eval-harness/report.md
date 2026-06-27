---
slug: sealed-eval-harness
initiative: eval-product
status: completed
ended: 2026-06-26
extracted_to:
  - docs/_active/eval-product/INITIATIVE.md   # M5 eval-product 이니셔티브 narrative (신규)
changelog_entry: docs/CHANGELOG.md (## eval-product)
---

# Sealed held-out eval harness — 결과 보고서 (M5 enabler 프로토타입)

## 요약

M5 비공개 eval 제품의 **기능 토대 프로토타입** — moat 메커니즘("외울 수도 오염될 수도 없는 eval")을
*동작하는 코드*로 입증. 신규 `critter_gym.eval_harness`(순수 numpy, core·CI 테스트 가능):
- **`SealedEvalSet`** — secret `master_seed`로 held-out 구역(≥1M) 비공개 블록 선택(결정론·재생성).
- **`verify_sealed`** — 오염 가드: 제출 train이 sealed eval과 겹치거나 train 구역(<1M) 밖이면 검출.
- **`score_agent`** — verifiable subgoal로만 채점(gym-clears·cleared/caught/evolved rate·frac_of_oracle).
- **`Agent` Protocol** `act(obs)->int` — 학습 정책·scripted·LLM-agent 공통 제출 인터페이스.

**demo 실측 (master_seed=20260626, 16 sealed worlds)**:

| 제출 | gyms | cleared% | of-oracle |
|---|---|---|---|
| oracle (scripted) | 1.88 | 94% | 100% |
| type_blind | 0.94 | 62% | 50% |
| random agent | 0.38 | 31% | 20% |

→ 깨끗한 능력 사다리(RLVR subgoal). **오염 가드**: honest(train 0..50k)→ok=True·overlap0 / **leak 시도
(sealed seed 학습)→ok=False·overlap16 검출·거부**. moat 메커니즘 end-to-end 입증.

## 계획 대비 실적

| AC | 상태 | 결과 |
|---|---|---|
| AC1 봉인 held-out | ✅ | _eval_seeds 전부 ≥1M·결정론·재생성, 3 테스트 |
| AC2 오염 가드 | ✅ | clean ok / 겹침 ok=False overlap>0 / 구역밖 ok=False, 3 테스트 + demo leak 검출 |
| AC3 RLVR 채점 | ✅ | subgoal-only, oracle>random, rate∈[0,1], demo 능력 사다리 |
| AC4 제출 인터페이스 | ✅ | Agent Protocol + EnvPolicy 둘 다 수용, demo end-to-end |
| AC5 회귀0+정직경계 | ✅ | 기존 src 무변경, 442→450(+8), mypy29/ruff/build clean, 경계 명시 |

## 변경 파일 상세

**신규**:
- `src/critter_gym/eval_harness.py` — `SealedEvalSet`/`verify_sealed`/`score_agent`/`Agent`/`Scorecard`/
  `SealedCertificate`. 기존 심볼만 import(env/learnability/region 무변경). 순수 numpy(core·CI 테스트).
- `tests/test_eval_harness.py` — 8 테스트(봉인 disjoint·결정론·재생성·오염 가드 3종·RLVR 채점·obs-only 인터페이스).
- `scripts/eval_harness_demo.py` — 봉인 등록 + 3 제출 채점 + 오염 가드(honest vs leak) end-to-end.
- `docs/_active/eval-product/INITIATIVE.md` — 신규 M5 이니셔티브 narrative.

## 발견된 이슈

- **(설계, 정직 경계)** "봉인"은 **in-process 컨벤션**(secret이 `SealedEvalSet` 객체 안) — 실제 hosted
  제품은 서버측 secret seed + 제출 샌드박스 필요. 모듈 docstring·INITIATIVE·demo에 명시.
- **(메커니즘 강점)** sealed 블록을 held-out 구역 *상단*(base=1.1M)에 둬 공개 `heldout_seeds(n)`(1M~) 범위와
  비충돌. 오염 가드가 "train<1M ∧ eval∩train=∅"로 누수를 *검증 가능*하게 만듦(파는 신뢰의 근거).

## 흡수처 매핑

- `docs/_active/eval-product/INITIATIVE.md` — M5 eval-product 이니셔티브(moat 메커니즘·정직 경계) narrative.
- ADR 가치: 경계선(seed-region 기반 봉인 규약). 현재는 INITIATIVE에 흡수, 별도 ADR은 hosted 인프라 task 때.

## 타입 체크 / 빌드 결과

- `mypy src`: 29 files clean. `ruff check .`: passed. `build`: 1.0.0rc1 OK. `pytest`: 450 passed, 2 skipped.

## 후속 (initiative, 일부 사람/전략 게이트)

- held-out 봉인 인프라 강화(서버측 secret·제출 샌드박스·결과 서명) / 다중 config / **agentic-LLM 어댑터**
  (LLM agent를 `act(obs)->action`으로 래핑) / hosted eval-as-a-service. **고객·가격·공개는 사람 게이트.**
