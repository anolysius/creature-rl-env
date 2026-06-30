# CritterGym (한국어)

> 절차적으로 생성되는 **생물 수집형 강화학습 환경** — 장기 호라이즌 에이전시, 전략적 추론,
> 일반화를 벤치마킹하기 위한 도구. 빠르고, 헤드리스이며, Gymnasium 호환. **게이머가 아니라
> AI/RL 연구자를 위해 만들었습니다.**
>
> English: [README.md](README.md)

CritterGym은 게임이 아니라 *에이전트 능력을 측정하는 계측기*입니다(장기 계획, 온라인 규칙 추론,
일반화). 보상은 **검증 가능**하며(RLVR — 손으로 튜닝한 shaping이 아니라 boolean 서브골 완료),
**절차 생성 시드 분리**로 일반화를 주장하는 게 아니라 *측정*합니다.

## 설치

```bash
pip install -e .                # 코어 (numpy 엔진 + Gymnasium API)
pip install -e ".[rl]"          # + PPO 학습 스크립트 (stable-baselines3)
pip install -e ".[viz]"         # + matplotlib 메트릭 플롯
pip install -e ".[render]"      # + GIF 인코딩 (imageio)
```

Python 3.9+. 코어 엔진은 numpy 전용이며, 무거운 학습 의존성은 extras 뒤에 둡니다.

## 빠른 시작

```python
import gymnasium as gym
from critter_gym.registration import register_envs

register_envs()
env = gym.make("CritterGym-procgen-v0")   # 절차 생성 월드 + 시드별 숨은 타입표
obs, info = env.reset(seed=42)            # reset(seed)는 region을 정확히 재현
obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
```

**등록된 환경 (6종):**

| id | 설명 |
|---|---|
| `CritterGym-v0` | 고정 M1 월드 (catch → 체육관 전투 → 보스 → 진화); env *family A* 기준 |
| `CritterGym-procgen-v0` | 절차 region + 시드별 숨은 타입표 (train/test 시드 분리) |
| `CritterGym-commit-v0` | 팀-커밋 보스 경제 (타입표 추론을 load-bearing하게 만듦) |
| `CritterGym-forage-v0` | env *family B* — contact-collect (장르 일반화) |
| `CritterGym-duel-v0` | env *family C* — 타입 무관 스태미나/커밋 듀얼 전투 |
| `CritterGym-muster-v0` | env *family D* — 수집-게이트 파워 (이기려면 먼저 모아야 함) |

## 무엇을 할 수 있나? (가이드)

CritterGym은 하나의 env로 네 가지 연구 워크플로를 지원합니다. 각 가이드는 짧고 실행 가능한
레시피입니다:

| 하고 싶은 것 | 가이드 |
|---|---|
| **RL 정책 학습** + PPO-vs-oracle headroom·일반화 갭 재현 | [how-to/train-a-policy](docs/how-to/train-a-policy.ko.md) |
| **LLM 에이전트 평가** — 봉인된 오염 방지 held-out eval(`inference_score`) | [how-to/evaluate-an-llm-agent](docs/how-to/evaluate-an-llm-agent.ko.md) |
| **장르 전이 측정** — 학습 안 한 env *family*로 일반화되는가? | [how-to/measure-genre-transfer](docs/how-to/measure-genre-transfer.ko.md) |
| **observation/action/reward 계약**과 env-variant 노브 조회 | [reference/observation-action-space](docs/reference/observation-action-space.ko.md) |

## 측정하는 것 (요약)

- **검증 가능 서브골 (RLVR):** 생물 ≥ C 마리 catch · ≥ 1 진화 · 각 체육관 격파 · 최종 보스 격파.
  dense shaping 없음 — 각 서브골 완료 시 `+1.0`.
- **경쟁력 있는 속도 (JAX) — 실측.** 핫패스를 함수형 JAX로 포팅, numpy env와 **parity 0 mismatch**
  검증. CPU에서 수천만 steps/s, GPU(T4) overworld vmap에서 수억 steps/s.
- **절차 생성 + train/test 시드 분리 (해자 속성).** held-out 시드는 새 맵 *과* 새 숨은 타입표를
  생성 → 정책이 외울 수 없음. 일반화를 *측정*(암기가 아님)할 수 있게 함.

> 전체 설계·포지셔닝·정직한 한계는 영문 [README.md](README.md) · [DESIGN.md](DESIGN.md) 참조.
> 본 한국어 문서는 온보딩 미러입니다(정식 사실의 SSOT는 영문/코드).
