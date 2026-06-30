# How-to: CritterGym에서 정책 학습하기 (한국어)

> 영어(SSOT): [train-a-policy.md](train-a-policy.md)

CritterGym은 표준 Gymnasium env이므로 어떤 RL 라이브러리든 동작합니다. 이 가이드는 번들된
베이스라인으로 가장 빠른 경로를 보여준 뒤, 직접 구현하는 법을 안내합니다.

## 0. RL extra 설치

```bash
pip install -e ".[rl,jax]"
```

`[rl]`은 PPO/recurrent 베이스라인 의존성, `[jax]`는 벡터화 빠른 경로를 제공합니다.

## 1. 직접 정책 학습 (아무 라이브러리)

```python
import gymnasium as gym
from critter_gym.registration import register_envs

register_envs()
env = gym.make("CritterGym-procgen-v0")     # 절차 생성 + 시드별 숨은 타입표
obs, info = env.reset(seed=42)              # train 시드는 < 1_000_000

# ... 학습 루프: obs는 Dict, action_space는 Discrete(6) ...
# obs/action 계약은 docs/reference/observation-action-space.ko.md 참조.
```

**train-region** 시드(`< 1_000_000`)에서만 학습하세요 — held-out region을 건드리지 않아야
일반화 수치가 정직하게 유지됩니다.

## 2. 번들 PPO 베이스라인 + oracle headroom 재현

```bash
python scripts/ppo_baseline.py            # 튜닝 JAX PPO vs scripted oracle 천장, held-out
python scripts/reproduce_results.py --quick   # 스모크; 전체 헤드라인 표는 --runs 5
```

학습된 정책이 **held-out** 시드에서 scripted **oracle**에 얼마나 근접하는지(벤치마크를 어렵게
만드는 *headroom*) 리포트합니다. PPO config(lr, GAE-λ, entropy, 시드)는 `scripts/ppo_baseline.py`에
고정. 수치는 라이브 생성 — 하드코딩 없음.

메모리 에이전트 베이스라인(여기선 부분관측이 load-bearing)은 `scripts/recurrent_ppo_baseline.py`.

## 3. 일반화 갭 측정 (Procgen 방식)

```bash
python scripts/train_ppo.py               # train 시드 학습 후 held-in vs held-out 리포트
```

`critter_gym.generalization`으로 학습된 정책을 held-in(학습 region) vs held-out(test region)
시드에서 채점합니다 — held-out 시드마다 새 맵 **과** 새 숨은 타입표. 갭은 *리포트*되며 pass/fail
임계로 쓰지 않습니다.

## 정직한 주의

- 번들 베이스라인은 적당한 예산의 작은 MLP — *headroom* 잣대이지 튜닝된 SOTA가 **아닙니다**.
  이기는 건 당연; 핵심은 oracle까지의 갭입니다.
- 처리량: JAX 경로는 numpy와 parity 검증(0 mismatch)되고 수억 steps/s로 vmap됩니다.
  `scripts/bench_throughput.py` 참조.
