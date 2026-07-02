---
slug: battle-arena-probe
initiative: eval-product
status: completed
ended: 2026-07-02
extracted_to:
  - docs/reference/battle-arena.md
changelog_entry: docs/CHANGELOG.md#2026-Q2
---

# battle-arena-probe — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 테스트 | 650 → **663** (+13, 회귀 0) — 이 브랜치는 main 분기; plan 의 "677" 은 strict-battle PR #103 머지 가정 추정치였음 (파일 겹침 없음, 두 PR 머지 후 합산 690) |
| arena band (12 held-out seed, K=10) | oracle SE **100%**·wins 10/10 / infer 96% / probe 69% / type_blind 46% — **spread +54pp (변별)**, winnable |
| 핵심 구조 발견 | arena 는 floor 앵커가 오버월드 대비 크게 상승 (type_blind 2%→46%, probe 1%→69%, **probe>type_blind 역전**) → "arena 점수는 arena band 양 앵커로만 읽기, 오버월드 표 접합 금지" 라벨 명문화 |
| LLM 실측 | **미실행** (quota=사용자 승인 게이트) — fake complete 단위 검증 + `--arena` 플래그 노출 확인만 |
| lint/type | ruff clean; mypy 잔여 1건 = render.py pre-existing |
| L1 / L3 | BLOCK 1(AC7 구체성)→보완→APPROVE, SUGGEST 1(커밋 단위)→반영 / plan-reviewer MALFORMED 1회→재호출 APPROVE, qa-verifier APPROVE — 최종 **2/2** |

## 계획 대비 실적

- ✅ AC1 arena 메커니즘 — reset 즉시 전투·K회 체인·승패 무관 진행·bout당 풀힐·결정론 (테스트 8)
- ✅ AC2 무회귀 — additive; `--arena` 미지정 시 조기분기 미발동으로 기존 경로 코드 무변경 (L3 코드 확인); 기존 650 회귀 0
- ✅ AC3 band 변별 — oracle−type_blind +54pp, oracle 10/10 winnable (테스트 + 실측)
- ✅ AC4 telemetry 재사용 — `_super_effective_move`/`se_inference_score`/`classify_inference`, 새 임계 0 (band↔telemetry 일치 테스트로 두 경로 고정)
- ✅ AC5 프로브 스크립트 + 정직 라벨 — arena vs 오버월드 band 병렬 출력, scripted-only·승인-필요·헤드라인-금지
- ✅ AC6 LLM wiring 실행-없이 검증 — fake complete 로 arena 투입 검증(실호출 0) + `--help` 노출 테스트
- ✅ AC7 문서 — `docs/reference/battle-arena.md` 4섹션 (모드 계약/측정 프레임/band 실측 표/경계)

## 핵심 발견

1. **도구는 유효하다**: 오버월드를 제거해도 scripted band 는 추론을 강하게 변별(+54pp)하고
   winnable — engagement confound 없이 SE-rate 를 읽을 수 있는 측정기가 준비됨.
2. **앵커 이동은 실측으로만 알 수 있었다**: 보스 타입이 작은 per-seed pool 에서 순환하므로
   arena 의 우연 SE 수준이 크게 올라가고(46%/69%), probe 가 type_blind 위로 역전.
   → arena 점수를 오버월드 band 나 기존 표와 접합하면 오독 — 문서·러너 출력 양쪽에 금지 명문화.
3. **질문은 아직 열려 있다**: "LLM 이 추론을 못 하는가" 는 이 task 로 *계측 가능해졌을 뿐*
   아직 측정되지 않음. 실측은 CLI 구독 quota → 사용자 승인 후
   `python scripts/llm_eval_run.py --provider claude-cli --arena --battle-memory --runs 3` 급이 다음 단계.

## 변경 파일 상세

| 파일 | 변경 |
|---|---|
| `src/critter_gym/envs/arena_env.py` (신규) | ArenaEnv — 부모 `_maybe_enter_battle`/`_step_battle` 재사용(전투 규칙 상속, 복사 0), bout 승수 재무장 패턴 |
| `src/critter_gym/envs/__init__.py` | export 1줄 |
| `src/critter_gym/arena.py` (신규) | `arena_band`/`score_arena_telemetry`/`arena_factory` — 기존 telemetry·분류기 재사용 |
| `scripts/battle_arena_probe.py` (신규) | scripted 검증 프로브 (arena vs 오버월드 band) |
| `scripts/llm_eval_run.py` | `--arena`/`--k-battles` + `run_arena` 조기분기 (기존 경로 무변경) |
| `tests/test_arena_env.py` (신규) | 13 테스트 (메커니즘 8 + band/telemetry 3 + LLM wiring 2) |
| `docs/reference/battle-arena.md` (신규) | evergreen 4섹션 |

커밋 단위: 단일 커밋 (plan 명시대로).

## 발견된 이슈

- (info) plan 검증 문구의 baseline "677" 은 PR #103 머지 가정 수치 — 본 브랜치 실측은 650→663
  (L3 SUGGEST 반영해 여기 명시; 두 PR 모두 머지되면 690).
- (후속, 사람 게이트) **LLM arena 실측** — 승인 시 위 명령으로 실행; engagement-vs-inference
  질문의 실제 답은 그때 나옴.

## 타입 체크 / 빌드 결과

`pytest -q` 663 passed / `ruff check .` clean / `mypy src` 신규 오류 0 (pre-existing 1 유지).
