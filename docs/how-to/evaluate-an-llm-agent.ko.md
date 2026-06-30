# How-to: 봉인 held-out eval에서 LLM 에이전트 평가하기 (한국어)

> 영어(SSOT): [evaluate-an-llm-agent.md](evaluate-an-llm-agent.md)

CritterGym은 **agentic LLM**을 봉인된, 한 번도 본 적 없는 월드에서 채점할 수 있습니다: 모델
앞에 신선한 held-out 월드를 놓고, 숨은 규칙을 추론해 체육관을 깨게 한 뒤, **검증 가능한
서브골**로 채점 — 학습할 수 없었던 월드에서. 이것이 오염 방지 eval(해자 속성)입니다.

## 먼저 알아둘 것 (정직한 범위)

- 이건 **in-process 프로토타입**이지 hosted 서비스가 아닙니다. 본인 머신에서 실행하며, 서버측
  봉인 eval(에이전트 제출→점수 회신)은 후속/펀딩 작업(M5)입니다.
- **비용:** 매 env 스텝이 LLM 호출 1회. 첫 probe는 `--worlds`·`--max-steps`를 작게. 러너가 예상
  호출 수를 출력하고 지출 전에 경고합니다.
- 결과는 **신호이지 verdict가 아닙니다** — scripted-oracle proxy·단일 난이도 band의 작은 probe.
  그대로 기록하고, floor를 "LLM이 못 한다"로 reframe하지 마세요.

## 옵션 A — 번들 러너 (Claude CLI 또는 Anthropic API)

```bash
# 로컬 Claude Code 구독 사용 (API 키 불요, rate-limit, 느림):
python scripts/llm_eval_run.py --provider claude-cli --worlds 2 --max-steps 40 --runs 3

# 또는 Anthropic API (ANTHROPIC_API_KEY 설정; 토큰 과금, 빠름):
python scripts/llm_eval_run.py --provider anthropic --model claude-opus-4-8 --worlds 2 --max-steps 40
```

유용한 플래그:

| 플래그 | 의미 |
|---|---|
| `--provider {anthropic,claude-cli}` | API(`ANTHROPIC_API_KEY` 필요) vs 로컬 Claude Code 구독 |
| `--worlds N` / `--max-steps M` | 봉인 월드 × 에피소드 스텝 상한 (작게 — `N×M` ≈ LLM 호출 수) |
| `--runs K` | K회 반복 → robust `inference_score` verdict (mean ± std, 사전약정 분류기) |
| `--stateful` / `--battle-memory` | 에피소드 메모리 / 무브별 전투-결과 메모리 부여 |
| `--telemetry` | super-effective-무브율도 리포트 (attrition-무관 추론 신호) |
| `--grid-size / --num-types / --boss-hp / --boss-atk / --boss-def` | demonstrator-config 노브 |

헤드라인은 **`inference_score`** ∈ [0,1]: `0` = chart-blind baseline처럼 둠, `1` = 차트 아는
전문가처럼 둠. 월드가 봉인돼 있어 암기·오염 불가.

🔑 **API 키를 채팅에 붙여넣거나 커밋하지 마세요.** 러너는 환경변수 `ANTHROPIC_API_KEY`에서 읽고
인자로 받지 않습니다.

## 옵션 B — 직접 에이전트 채점 (아무 provider)

`complete(prompt) -> reply` 콜러블을 감싸거나 `Agent` 프로토콜을 직접 구현:

```python
from critter_gym.eval_harness import SealedEvalSet, score_agent, verify_sealed
from critter_gym.llm_eval import LLMAgent  # 또는 StatefulLLMAgent / BattleMemoryLLMAgent

def my_complete(prompt: str) -> str:
    ...  # 모델 호출, 텍스트 응답 반환

sealed = SealedEvalSet(master_seed=20260627, n_worlds=4)   # 평가자의 비밀 블록
card = score_agent(LLMAgent(my_complete), sealed)
print(card.inference_score, card.frac_of_oracle, card.cleared_rate)
```

`Agent`는 `act(obs) -> int`(과 월드별 메모리용 선택적 `reset()`)만 있으면 됩니다.
키 불요·무비용 데모는 `scripts/eval_harness_demo.py`, `scripts/llm_eval_demo.py`(결정론 stub LLM).

## 오염 없음 증명

```python
cert = verify_sealed(declared_train_seeds=my_train_seeds, sealed=sealed)
assert cert.ok   # train 시드가 봉인 eval 블록과 겹치지 않고, 모두 train region 안
```

`verify_sealed`는 "이 eval로 학습할 수 없었다"를 **검증 가능**하게 합니다 — 고정 벤치마크가
유출되면 못 주는 신뢰.
