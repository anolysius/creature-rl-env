# How-to: 장르(env-family) 전이 측정하기 (한국어)

> 영어(SSOT): [measure-genre-transfer.md](measure-genre-transfer.md)

CritterGym은 하나의 obs/action 계약을 공유하는 **구조적으로 구별되는 네 env family**를
제공합니다. 그래서 정책이 학습한 적 없는 게임 *구조*로 일반화되는지 측정할 수 있습니다 —
시드 수준 일반화보다 한 단계 위인 env 수준 held-out 분리.

| family | id | 구조 축 |
|---|---|---|
| A | `CritterGym-procgen-v0` | catch → 체육관 → 보스 (기본 RPG) |
| B | `CritterGym-forage-v0` | contact-collect 수집 메커닉 |
| C | `CritterGym-duel-v0` | 타입 무관 스태미나/커밋 **전투 시스템** |
| D | `CritterGym-muster-v0` | 수집-게이트 파워 (이기려면 먼저 파티를 모아야 함) |

## 학습된 정책의 held-out family 전이

```bash
pip install -e ".[rl,jax]"
python scripts/genre_learned_transfer.py
```

**train family**(에피소드마다 무작위 family)에서 PPO를 학습하고, 학습한 적 없는 **held-out
family**로의 전이를 측정합니다. 모든 family가 조화된 observation space를 공유하므로(참조:
`docs/reference/observation-action-space.ko.md`) 단일 네트워크가 전부 소비합니다.

## scripted 스킬-구조 대조

```bash
python scripts/difficulty_generalization.py   # 난이도 / 일반화 슬라이스
```

family를 가로지르는 scripted 정책 대조(스킬-구조 차이)는 `critter_gym.genre_generalization` 참조.

## 정직한 범위

- 이건 **토대이지 증명이 아닙니다**: 3개 축의 4 family는 대부분 벤치마크가 안 겨냥하는
  *방향*이지만, 넓은 meta-RL 태스크 커버리지는 **아닙니다**(cf. XLand-MiniGrid).
- 가장 구별되는 family(`duel`, 다른 전투 시스템)로의 전이는 fine-tuning이 필요할 것으로
  예상됩니다 — 이 한계는 `DESIGN.md` §3.1.1에 명시(숨기지 않음).
