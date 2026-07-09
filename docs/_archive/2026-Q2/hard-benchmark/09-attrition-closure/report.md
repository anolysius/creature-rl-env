---
slug: attrition-closure
initiative: hard-benchmark
status: completed
ended: 2026-07-08
extracted_to: []
changelog_entry: docs/CHANGELOG.md
---

# 완전-attrition-폐쇄 — 결과 보고서 (정직 (b) NOT CLOSED, 미묘: 순환은 닫힘·고정리드 커버리지 잔존)

## 요약 (수치 표)

#7이 남긴 끝: SE-only가 attrition을 부분만 축소한 원인=non-commit party-cycling. **엔진 변경 없이**
기존 두 knob(`commit_battles`+`super_effective_only`)을 조합해 무추론 `type_blind` arm을
{commit,non-commit}×{default,strict,SE-only} 6칸으로 hard config(grid16·5gym)에서 측정.

| 항목 | 결과 |
|---|---|
| 테스트 | **758 → 763** (+5 결정론 메커니즘 테스트, 회귀 0) |
| lint | ruff clean (신규 src 없음 — mypy 무대상) |
| **type_blind non-commit** | default 5.00 · strict 5.00 · SE-only **3.75** |
| **type_blind commit** | default **2.44** · strict 2.44 · SE-only **2.19** |
| commit이 제거한 순환 이득 | default **−2.56** · SE-only **−1.56** (commit이 순환 grind 확실히 죽임) |
| blind-luck floor (probe, commit+SE-only) | **1.25** |
| oracle (commit+SE-only) | **5.00, winnable=True** (default-econ oracle도 5.00) |
| 추론 gap (oracle − type_blind) @ commit+SE-only | **2.81** (가장 넓음 = eval-validity 최대) |
| **사전약정 verdict** | **(b) NOT CLOSED** — cycling-removed=True, at-floor=**False**(2.19 > 1.75) |

**정직 결론(SIGNAL)**: **commit-mode는 #7이 지목한 *순환(cycling)* confound를 확실히 닫는다** —
non-commit 3.75 → commit 2.19(SE-only), default에선 5.00 → 2.44(순환이 무추론 arm에 +2.56 gym을
벌어줬음). 조건1(cycling-removed) 충족. **그러나 attrition을 blind-luck floor까지 *완전히* 닫지는
못한다** — committed type_blind 2.19가 probe floor 1.25보다 여전히 높다(조건2 미충족). 원인:
`type_blind`는 **고정 리드(creature 0)**로 싸우는데, 그 한 마리의 타입이 무작위 blind commit보다
많은 boss(~44% vs ~25%)를 super-effect한다 — 순환이 아닌 **"고정 리드 타입 커버리지"가 잔존
무추론 신호**. 즉 confound는 *순환 성분*만 닫히고, *고정-리드 커버리지 성분*은 남는다. oracle은
winnable 유지(공정 레버, (c) 미발동), 추론 gap 2.81로 commit+SE-only가 여전히 eval-validity 최대
config. 완전 폐쇄엔 리드 커버리지 제거(무작위 시작 파티 등)가 추가로 필요 — 별개 축. scripted·
1-seed-set·floor≠0 — 헤드라인 금지, 학습/LLM 무추론 grinder는 money-gated 후속.

## 계획 대비 실적

| AC | 상태 | 근거 |
|---|---|---|
| AC1 scout 6칸+floor+winnability+gap+규칙 | ✅ | attrition_closure_scout.py 출력 전부 포함, 판정 전 규칙 출력 |
| AC2 결정론 메커니즘 테스트 | ✅ | 5 케이스: non-super champion 데미지0·못이김(2), 정답 commit 승리(1), commit이 순환 제거 vs non-commit 순환 승리(2) |
| AC3 무회귀 + ruff | ✅ | 758→763(+5), ruff clean, 신규 src 없음 |
| AC4 본측정 + 사전약정 그대로 | ✅ | full 16-seed 완주, **(b) NOT CLOSED를 그대로 보고**(commit이 순환 닫음을 유리하게 "closed"로 승격 안 함), 정직 라벨 |

## 변경 파일 상세

**신규 (src 변경 0 — 기존 knob·arm 조합만)**
- `scripts/attrition_closure_scout.py` (+~110): type_blind 6칸(commit×economy) + probe floor +
  oracle/blind winnability + 추론 gap + 사전약정 3조건 closure verdict + honest NOTE.
- `tests/test_attrition_closure.py` (+~95): Battle-level 결정론 메커니즘 5 테스트(commit+SE-only
  non-super=0·못이김·neutral draw·정답 super 승리·non-commit 순환 승리 vs commit 순환 차단).

## 발견된 이슈 (심각도)

- **[중/메타-발견] attrition confound는 *2 성분***: (1) 순환 grinding = commit이 닫음(−1.56~−2.56),
  (2) 고정-리드 타입 커버리지 = 남음(2.19 > luck floor 1.25). #7·#6이 (1)만 다뤘고 본 task가 (1)의
  폐쇄를 확정하되 (2)를 드러냄. **버그 아님** — 완전 폐쇄의 정직한 경계(리드 무작위화=별개 축).
- **[정보] commit+SE-only = eval-validity 최대 config**: 추론 gap 2.81(6칸 중 최대), oracle winnable.
  "완전 폐쇄"는 아니어도 추론을 가장 load-bearing하게 만드는 조합.

## 흡수처 매핑 (extracted_to)

**흡수 없음(빈 배열)** — evergreen 4-질문 모두 No. 결과=SIGNAL(1-seed-set), 기존 knob 조합의 파생
측정, 아키텍처/절차/명세/ADR 신규 없음. INITIATIVE.md에 1행. **후속**(사람 결정): 고정-리드 커버리지
성분 제거(무작위 시작 파티 등)로 완전 폐쇄 재도전 — 기본 규칙/파티 구성 변경이라 사람 선행.

## 타입 체크 / 빌드 결과

- `pytest`: 763 passed, 0 regression.
- `ruff check .`: All checks passed.
- mypy: 신규 src 없음(script/test만) — 대상 무변경.
