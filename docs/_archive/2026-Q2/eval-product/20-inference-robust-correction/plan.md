---
slug: inference-robust-correction
initiative: eval-product
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
task_type: general
mode: standard
review_profile: docs-only
scope_paths:
  - docs/paper/critter-gym.md
  - docs/explanation/competitive-analysis.md
extracted_to: []
supersedes: []
---

# §5 정정 — 단일-run "부분 추론(50%)"은 robust 하지 않았다 (정직 하향)

> 작성일: 2026-07-01 | 상태: 계획 | 마일스톤: M3-EC4 (arXiv 초안 정직성)

## 목표

#17 이 §5·Abstract·competitive-analysis 를 **"보정 분포 위 부분적·실재하는 in-context 추론
(SE ≈50%)"** 로 reframe 했으나, 그 근거는 **단일 run(n=8)** 이었다. #18 로 만든 SE-rate robustness
도구로 **3-run(n=4) robust 측정**을 돌린 결과: **정규화 SE-rate inference score 0.10 ± 0.08 →
INCONCLUSIVE**(near-floor; gym 기반도 0.04 ± 0.06 INCONCLUSIVE), 마지막 run SE-rate 14%. **단일-run
50% 는 robust 하게 재현되지 않았다.** §5 의 "partial, real inference" 단언은 non-robust 한 한 판에
기댄 과대 주장 → 정직 하향.

**동시에 — 설계는 건강함을 명시**(과소 reframe 방지): eval 은 scripted **infer 앵커를 robust 하게
높게(SE ≈89%) 잡으므로**, "추론이 있을 때 registered 됨"이 검증된다. 따라서 LLM 이 near-floor 인 것은
*eval 아티팩트가 아니라 LLM 에 대한 진짜 신호*다. 다만 engagement/survival confound(이전 #13/#14
박제) 는 잔존 → "강한 신호지 최종 verdict 아님".

**정직성 > 헤드라인.** 이건 #18(robustness 도구)이 **우리 자신의 #17 reframe 이 non-robust 했음을
잡아낸** 사례이자, "앵커로 검증한 뒤에도 예측이 깨지는 것 = eval 이 정직히 작동" 이라는 moat 논리의
실증이기도 하다.

## 선행 조건 (측정된 근거)

- 단일 run(n=8, max_steps=40): LLM SE 50%, 정규화 0.32 (#17 근거).
- **robust 3-run(n=4, max_steps=40, claude-cli)**: 정규화 SE 0.10 ± 0.08 INCONCLUSIVE / gym 0.04 ±
  0.06 INCONCLUSIVE / band oracle 100% · infer 89% · type_blind 6% · probe 0% · LLM 14%.
- **caveat**: 단일-run 은 n=8, robust 는 n=4 — world 수 다름(직접 반박 아님·floor 도 다름:
  n=8 27% vs n=4 6%). apples-to-apples n=8 3-run 은 후속. 단 50%↔14% 격차가 커 "50%=optimistic
  outlier" 강한 신호.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 |
|---|---|---|
| `docs/paper/critter-gym.md` | Abstract(line 29-31 "partial ... signal") + §5(line 222-226 "≈50% ... partial, real inference" + Honest scope 231) 정정: 단일-run 50% 는 robust 미확인, 3-run inconclusive/near-floor, infer 앵커로 설계 건강 검증, engagement confound 잔존, n=8 3-run 후속 | **중** (공개 narrative) |
| `docs/explanation/competitive-analysis.md` | "monetizable eval" 행의 #17 부분-추론 문단을 robust 결과로 정정(동일 정직 하향 + 설계 건강 명시) | 중 |

### 영향 범위

- 코드 0(docs-only). 측정·env·도구 무변경.
- §5 내부 정합: "three stacked confounds" 서사·infer 앵커 서술 유지, 결론만 하향.

## Step별 계획 (docs-only, TDD 없음)

1. §5 결론 단락: "partial, real inference" → "**단일 run(n=8) 은 SE ≈50% 였으나, robust 3-run(n=4) 은
   inconclusive/near-floor(정규화 0.10±0.08) — 단일 신호는 재현되지 않음.** eval 은 scripted infer
   앵커를 robust 하게 높게(89%) 잡으므로 설계는 추론을 registered 함 → LLM near-floor 는 진짜 신호
   (engagement confound 잔존; n=8 3-run 후속)." 로 정정.
2. Abstract line 29-31: "partial in-context inference signal" → "단일-run 신호는 robust 미확인,
   현재 near-floor/inconclusive" 로 하향.
3. §5 Honest scope: robust 3-run 결과 + n=8 apples-to-apples 후속 명시.
4. competitive-analysis: 동일 정정.

## 검증 방법

- 수치 정합: 인용 robust 수치(0.10±0.08 inconclusive / infer 89% 앵커 / 14%)가 실측 출력과 일치.
- 정직 균형: 과대("부분 추론 확정") 제거 ∧ 과소("설계 실패/eval 못 잼") 방지(infer 앵커=설계 건강 명시).
- broken-link 0. docs-only(코드 0).

## 리스크

| 리스크 | 완화 |
|---|---|
| 과소 reframe(설계가 틀렸다는 인상) | infer 앵커 89%(robust)로 "eval 이 추론을 registered 함=설계 건강" 명시. LLM near-floor=진짜 신호. |
| n=4 vs n=8 혼동(직접 반박 오인) | world 수 다름·floor 다름 명시, "단일 50%=optimistic outlier 강한 신호, 확정은 n=8 3-run 후속". |
| #17 을 통째 부정(이전 task 폄하) | #17 의 매치업/render/memory 서사·infer 앵커는 유효; **결론(50% partial)만** robust 미확인으로 하향(correction). |
| 반복 정정으로 신뢰 저하 | 오히려 robustness 도구(#18)가 자기 오류를 잡은 것 = 정직·un-gameable 실증으로 프레이밍. |

## Acceptance Criteria (G1 통과 시 freeze)

1. **[정직-하향]** §5 결론 + Abstract 가 "단일-run 50% 는 robust 미확인, 3-run(n=4) inconclusive/
   near-floor(정규화 0.10±0.08)" 를 반영하고 "partial, real inference" 단언을 제거/하향.
2. **[설계 건강 명시]** §5 + competitive-analysis 에 "eval 은 scripted infer 앵커를 robust 하게
   높게(SE ≈89%) 잡음 → 추론이 있으면 registered → LLM near-floor 는 eval 아티팩트 아닌 진짜 신호"
   명시(과소 reframe 방지) + engagement confound 잔존.
3. **[수치·caveat 정합]** 인용 수치(0.10±0.08 inconclusive·infer 89%·14%·단일 50%) 실측 일치;
   n=4 vs n=8 world-수 caveat + n=8 3-run 후속 명시.
4. **[무회귀]** docs-only(코드 0). broken-link 0. L3(docs-only) APPROVED.
