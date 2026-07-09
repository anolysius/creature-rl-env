---
slug: attrition-closure
initiative: hard-benchmark
status: active
started: 2026-07-08
acceptance_freeze: true
mode: standard
task_type: general
domains: [rl-env]
scope_paths:
  - scripts/attrition_closure_scout.py
  - tests/test_attrition_closure.py
extracted_to: []
supersedes: []
---

# 완전-attrition-폐쇄 — commit-mode가 순환-grinding 우회로를 죽이는가

> 작성일: 2026-07-08 | 상태: 계획 | 이니셔티브: hard-benchmark (M3 신뢰성 자산)

## 목표

**#7 (super-effective-economy)이 남긴 정확한 끝을 측정한다.** #7은 SE-only가 attrition을 *부분만*
축소하고 **완전 폐쇄(~floor)엔 미달**임을 정직 보고했다 — 이유는 **non-commit party-cycling**: 활성
creature가 faint하면 force-switch가 파티를 순환시켜, 무추론 정책도 언젠가 super-effective 멤버를
만나 boss를 grind로 잡는다. #7의 NOTE가 명시: *"완전 폐쇄는 commit-mode(순환 제거)=별개 축."*

본 task는 그 별개 축을 친다. **엔진 변경 없이** 기존 두 opt-in knob(`commit_battles` + `super_
effective_only`)을 조합하고, 무추론 arm이 commit on/off에서 어떻게 갈리는지 측정한다. 핵심 통찰:
`type_blind` reference arm이 정확히 "무추론" 정책이다 —
- **non-commit**: 활성 faint → force-switch 순환 → **union coverage**(파티 전체 타입 합).
- **commit**: creature 0 고정, 순환 없음, 잘못 commit하면 SE-only에서 데미지 0 → 못 이김 → **단일
  creature coverage**.

사전약정 질문 (데이터 전 freeze):
- **commit-mode가 순환-grinding 우회로를 죽이는가?** hard config에서 `type_blind`(무추론)를
  {commit, non-commit} × {default, strict, SE-only} 6칸으로 측정:
  - **(a) CLOSED** — `type_blind(commit, SE-only)` < `type_blind(non-commit, SE-only)`(순환 이득
    제거) **그리고** blind-luck floor(`probe`=매 전투 무작위 commit)에 근접(순환-grinding이 단일
    blind commit 이상 아무것도 안 벌어줌) **그리고** `oracle(commit, SE-only)` winnable(≥ 절반 gym).
    → 추론이 이김의 유일 경로에 가장 근접 = eval-validity 최대.
  - **(b) NOT CLOSED (falsify)** — commit이 무추론 arm을 못 낮추거나, floor 위로 유의미 초과 →
    순환 외 다른 grinding 잔존. 그대로 보고.
  - **(c) TOO HARSH (falsify)** — oracle이 commit+SE-only에서 winnable 밑돌면 공정 레버 아님.
- **부수 지표**: 추론-load-bearing gap = `oracle − type_blind`가 commit+SE-only에서 가장 넓은가.

**정직 프레이밍(북극성 5)**: scripted arm only, no learned/LLM. **"1 결정론 seed set"** = 16개
held-out seed 위 결정론 1-pass(seed당 반복시행·variance 추정 없음 — 학습 arm의 run-to-run std와
다른 의미). "완전 폐쇄"의
현실적 target은 **~0이 아니라 blind-luck floor**(단일 무작위 commit도 매치업 분포상 일부 boss엔
super-effective라 floor > 0). "0으로 안 감"을 실패로 오도 금지 — floor 대비로 판정. 방향 SIGNAL이지
measurement 아님. 헤드라인 금지. floor·grid·판정 규칙 데이터 전 freeze(p-hacking 방지).

**이 task가 advance하는 EC**: hard-benchmark 절대 난이도 — 논문 §5 한계(i) attrition confound의
*완전* 상환 여부 확정(#6 strict falsify·#7 SE-only partial 계열의 종결점). eval-validity 경화.

## 선행 조건

- main = 5c4b80a (#8 머지), 758 tests green, clean. ✅
- 두 knob 모두 존재·테스트됨: `commit_battles`(battle.py commit_mode — SWITCH 무시·faint=즉시
  패배·순환 없음), `super_effective_only`(#7, eff≤NEUTRAL 데미지 0). **엔진 변경 불요**.
- arm 4종 존재(`learnability.reference_arm`): oracle(정답 commit)·infer(학습)·**type_blind(creature
  0 고정=무추론)**·**probe(매 전투 blind guess=luck floor)**. commit-mode aware(#7에서 검증).
- #7 `super_effective_scout.py` — attrition probe·economy·winnability·honest NOTE 구조 템플릿.
- config: `hard_benchmark_memory.py` 상수(grid16·5gym·420step) mirror.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `scripts/attrition_closure_scout.py` (신규) | type_blind 6칸(commit×economy) + probe floor + oracle winnability + 추론 gap + 사전약정 closure verdict 출력 | 낮음 | numpy only, 무료·자율 |
| `tests/test_attrition_closure.py` (신규) | commit+SE-only 폐쇄 **메커니즘** 결정론 테스트(Battle-level): 무-super champion=데미지 0·못 이김 / 정답 commit=이김 / commit이 non-commit 순환을 제거 | 낮음 | 결정론, 빠름 |

### 영향 범위 (import 그래프)

- **src 무변경** — 기존 knob·arm 조합만. scout은 CritterEnv·reference_arm·run_episode 소비.
- 메커니즘 테스트는 Battle(super_effective_only + commit_mode) 직접 구동(결정론, #7 test 패턴).

## Step별 계획

1. **메커니즘 테스트(Red→Green)** — Battle-level 결정론: (a) commit+SE-only에서 champion move가
   boss에 non-super면 데미지 0 → winner≠champion(패배 또는 draw). (b) 정답(super) commit이면 이김.
   (c) non-commit에선 faint 후 순환으로 다른 creature 등판(commit-mode는 안 등판) 대조.
2. **scout script** — hard config에서 type_blind 6칸(commit×{default,strict,SE-only}) + probe floor
   (commit,SE-only) + oracle/blind winnability + 추론 gap(oracle−type_blind) + 사전약정 closure
   verdict 출력. 판정 전 규칙 출력. honest NOTE(floor≠0·scripted·1-seed·헤드라인 금지).
3. **본측정** — full seed로 완주, 사전약정 branch 그대로 보고(closed/not-closed/too-harsh).

## 사전약정 (G1 freeze — 데이터 무관 불변)

- **grid**(freeze): `type_blind` × {commit, non-commit} × {default, strict, SE-only} 6칸. floor arm=
  `probe`(commit, SE-only). config=hard(grid16·5gym·420step·num_types8·patch2). seeds=heldout(full 16).
- **closure 판정**(freeze): **(a) CLOSED** iff `type_blind(commit,SE-only) ≤ type_blind(non-commit,
  SE-only) − 0.25 gym`(순환 이득 제거, 노이즈 마진) **∧** `type_blind(commit,SE-only) ≤ probe(commit,
  SE-only) + 0.5 gym`(luck floor 근접) **∧** `oracle(commit,SE-only) ≥ 0.5·num_gyms`(winnable).
  둘째 미충족→**(b) NOT CLOSED**. 셋째 미충족→**(c) TOO HARSH**. 그대로 보고.
- **마진 근거**(freeze): 0.25/0.5 gym은 5-gym config의 1칸(=0.2)보다 약간 큰 값 — #7 scout의
  seed-간 분산(type_blind std ~0.3–0.6 관측)을 노이즈 마진으로 흡수해 1-seed-set 스파이크를
  "이득/근접"으로 오판하지 않게 하는 보수적 선택. 데이터 전 고정, 확충해도 불변.
- **해석 규율**(freeze): "완전 폐쇄" target은 ~0 아닌 blind-luck floor. floor>0을 실패로 오도 금지.
  scripted proxy — 학습/LLM 무추론 arm의 진짜 grinding은 별개(money-gated).

## 검증 방법

- `.venv/bin/python -m pytest -q` → 758 + 신규(메커니즘 테스트) 무회귀 green.
- `.venv/bin/python -m ruff check .` → 신규 2파일 clean. (mypy: 신규 src 없음 — script/test만.)
- `.venv/bin/python scripts/attrition_closure_scout.py` → 6칸 표 + floor + winnability + closure
  verdict 출력(본측정 CPU 가벼움 — scripted, 즉시).

## 리스크

- **R1 (floor 오해)**: "완전 폐쇄=0"으로 오도하면 floor>0을 실패로 잘못 판정. **완화**: 판정을 probe
  floor 대비로 freeze, 해석 규율 명시.
- **R2 (commit이 이미 낮춤 = novelty 부족 우려)**: #7이 commit type_blind(2.19)를 이미 관측. **완화**:
  본 task의 novelty=**commit vs non-commit 대조**(순환 이득 격리) + floor 대비 폐쇄 판정 + 결정론
  메커니즘 증명 — #7은 non-commit attrition만 probe했고 commit-vs-noncommit 무추론 대조는 미측정.
- **R3 (too-harsh)**: commit+SE-only가 oracle을 unwinnable로 만들면 falsify(c). **완화**: winnability
  게이트를 판정에 포함, 그대로 보고(#7 secondary-unwinnable 경계 계승).

## Acceptance Criteria (G1 통과 시 freeze)

- **AC1**: `scripts/attrition_closure_scout.py`가 `type_blind` 6칸(commit×{default,strict,SE-only}) +
  probe floor + oracle/blind winnability + 추론 gap(oracle−type_blind)을 출력. 판정 전 사전약정 규칙 출력.
- **AC2**: 결정론 메커니즘 테스트 — commit+SE-only에서 (a) non-super champion=데미지 0·winner≠champion,
  (b) 정답 super commit=승리, (c) commit이 non-commit의 순환 등판을 제거함을 Battle-level로 증명.
- **AC3**: 전체 기존 스위트 무회귀(758 green), ruff clean. (신규 src 없음 — mypy 대상 무변경.)
- **AC4**: 본측정 완주 — 사전약정 closure branch(a/b/c)를 **그대로** 보고. 정직 라벨(floor≠0·scripted·
  1-seed·헤드라인 금지) 명시.
