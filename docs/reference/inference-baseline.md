# Inference baseline — 보정된 분포 위 scripted 변별 band + 재측정 프로토콜

> 봉인 held-out eval 에서 LLM 의 in-context 숨은-규칙 추론을 *해석 가능하게* 읽기 위한
> **scripted 기준선(尺)**. 매치업 fix(#15) 이후 분포 기준. `eval_harness.inference_baseline`
> 가 SSOT — 본 문서 수치는 그 함수의 결정론 출력이다.

## 왜 이 문서

매치업-validity fix(#15)가 held-out 세계 분포를 바꿨다(이제 **SE-exploitable boss 만 배치**).
그래서 **이전 LLM inference 수치(#11/#13/#14)는 옛(매치업-broken) 분포에서 측정된 것이라 새
분포와 직접 비교할 수 없다.** 재측정을 하려면 *보정된 분포 위*의 새 scripted band 가 먼저
있어야 LLM 점수를 해석할 수 있다. 본 문서가 그 band 와 고정 재측정 절차다.

## 4-arm scripted band (무료·결정론, LLM 아님)

`inference_baseline(sealed)` 는 4개 scripted reference arm 을 같은 봉인 세계에서 **세계별 격리**
(arm 을 세계마다 새로 생성 → 세계 간 메모리 누수 0, 봉인 모델·`learnability` 와 일치)로 돌려
arm 별 `gym_clears`·`se_rate`·`inference_score` 를 반환한다.

| arm | 의미 |
|---|---|
| `oracle` | 차트를 *아는* 전문가 (상한, ceiling) |
| `infer` | 매치업을 처음 보고 학습해 재사용하는 **추론 에이전트 proxy** — *LLM 이 아니다* |
| `type_blind` | 절대 교체 안 함, 한 챔피언으로만 — 차트-blind 바닥 (floor) |
| `probe` | 전투마다 무기억 blind 추측 — blind-guess 앵커 |

### 보정 분포 band (master_seed=20260627)

**demonstrator** (grid5, types3, boss 140/6/18) — 러너 inference-demo preset:

| arm | SE-rate (n=8) | SE-rate (n=16) | gym-clears | inference_score |
|---|---|---|---|---|
| oracle | **100%** | **100%** | 2.12 | 1.00 |
| infer | **90%** | **89%** | 2.12 | 1.00 |
| type_blind | 7% | 3% | 1.25 / 0.81 | 0.00 |
| probe | 0% | 0% | 0.00 | 0.00 |

**runner-default** (grid10, types8, boss 120/12/12):

| arm | SE-rate (n=8) | SE-rate (n=16) | gym-clears | inference_score |
|---|---|---|---|---|
| oracle | **100%** | **100%** | 2.12 | 1.00 |
| infer | **85%** | **85%** | 2.12 | 1.00 |
| type_blind | 4% | 3% | 1.00 / 0.94 | 0.00 |
| probe | 1% | 5% | 0.38 / 1.00 | 0.00–0.05 |

## 어느 신호를 읽는가 — SE-rate 가 변별자, gym-clears 는 아님

- **gym-clears 는 saturate 한다**: inference-gated config 에서 `infer`(추론 proxy) gym-clears 가
  oracle 과 **같다**(2.12 == 2.12) → gym 기반 `inference_score` 도 1.0 으로 포화. 이유는 전투가
  `damage=max(1)` attrition 이라 *에피소드 내 학습 + 소모전*으로 winnable gym 을 다 깬다(#12 교훈).
  즉 **gym-clears 로는 "추론하는 에이전트"와 "전문가"를 구별 못 한다.**
- **SE-rate 가 attrition-proof 변별자다**: oracle 100% > infer 85–90% ≫ type_blind 3–7% > probe 0%.
  추론 행위(=super-effective 무브 선택)를 승리/소모전과 분리해 직접 잰다. **LLM 은 이 band 위
  어디에 떨어지는가로 읽어라.**

## 고정 재측정 프로토콜 (유료 LLM 실측 = 평가자 로컬)

scripted band 는 무료지만, **실제 LLM probe 는 평가자가 자기 구독/키로 로컬 실행**한다(기존 규율 —
키는 사용자 것·비용 발생). 고정 명령:

```bash
# 구독(claude CLI) — API 키 불요, 느림(콜당 ~수초)·소규모 권장
python scripts/llm_eval_run.py --provider claude-cli \
  --master-seed 20260627 --worlds 8 --num-types 3 \
  --grid-size 5 --boss-hp 140 --boss-atk 6 --boss-def 18 \
  --battle-memory --telemetry --runs 3
# 또는 API
python scripts/llm_eval_run.py --provider anthropic --model claude-opus-4-8 [...동일 노브...]
```

- `--telemetry` 가 위 4-arm band(oracle/infer/type_blind/probe)와 submission 의 SE-rate 를 같이
  출력 → LLM 을 band 위에 즉시 위치시킨다.
- `--runs N` (N>1) 은 `classify_inference` 사전약정 분류기로 robust verdict(infers /
  at-chart-blind-floor / inconclusive) 산출 — single-run 노이즈 방지(#10).
- `--master-seed` 를 바꾸면 *다른* 봉인 블록(재현 가능·disjoint).

## 정직 경계

- 본 band 는 **scripted proxy** 다 — `infer` arm 은 추론 *에이전트 proxy* 이지 LLM 이 아니다.
- single config·scripted-oracle proxy·작은 N — *신호*이지 LLM 능력 *verdict* 아님.
- 이전 LLM 수치(#11/#13/#14)는 옛 매치업-broken 분포 측정 → **본 분포와 비교 금지**. 재측정은
  반드시 본 분포(매치업 fix 적용) 위에서.
- 전투 모델 재설계(`damage=max(1)` attrition → gym-clear 변별 band 협소)는 벤치마크 정의 변경 =
  사람 게이트로 남는다. 본 문서는 그 전제 위에서 SE-rate 를 1차 변별자로 쓴다.

## 코드 참조

- `src/critter_gym/eval_harness.py` — `inference_baseline`, `ArmBaseline`, `InferenceBaseline`,
  `score_inference_telemetry`, `score_agent`.
- `src/critter_gym/learnability.py` — `reference_arm` (oracle/infer/type_blind/probe).
- `scripts/llm_eval_run.py` — `--telemetry` 가 본 band 를 출력.
