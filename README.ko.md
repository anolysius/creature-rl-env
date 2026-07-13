# CritterGym (한국어)

[![ci](https://github.com/anolysius/creature-rl-env/actions/workflows/ci.yml/badge.svg)](https://github.com/anolysius/creature-rl-env/actions/workflows/ci.yml)

> 절차적으로 생성되는 **생물 수집형 강화학습 환경** — 장기 호라이즌 에이전시, 전략적 추론,
> 일반화를 벤치마킹하기 위한 도구. 빠르고, 헤드리스이며, Gymnasium 호환. **게이머가 아니라
> AI/RL 연구자를 위해 만들었습니다.**
>
> English: [README.md](README.md)

CritterGym은 게임이 아니라 *에이전트 능력을 측정하는 계측기*입니다(장기 계획, 온라인 규칙 추론,
일반화). 보상은 **검증 가능**하며(RLVR — 손으로 튜닝한 shaping이 아니라 boolean 서브골 완료),
**절차 생성 시드 분리**로 일반화를 주장하는 게 아니라 *측정*합니다.

**라이브:** [리더보드 & 게임플레이](https://anolysius.github.io/creature-rl-env/index.ko.html) ·
[시험지 작동 원리](https://anolysius.github.io/creature-rl-env/how-it-works.ko.html)
(승리 조건, 숨은 상성표, 그리고 왜 파밍이 없는가)

## 설치

```bash
python -m pip install -U pip    # 구식 동봉 pip(예: macOS 21.2.4)은 pyproject 전용 패키지의
                                # editable 설치 불가 (PEP 660은 pip >= 21.3 필요)
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

## 문제 제보 (그리고 정정이 작동하는 방식)

버그 제보와 공개 수치에 대한 이의 제기를 **환영합니다** — GitHub 이슈로 열어주세요.
이 저장소의 모든 수치는 재현 명령·시드와 함께 제공됩니다; 재현이 안 되면 그것 자체가
발견입니다. 확인된 오류는 수정하고 정정 내역을 **`docs/CHANGELOG.md` 에 공개 기록**합니다
(이 프로젝트는 자신의 결과를 스스로 하향 정정해 온 이력이 있고, 앞으로도 그렇게 합니다).
출처 투명성: 이 프로젝트는 사람이 지휘한 AI 코딩 에이전트(Claude)가 구축했습니다 — 모든
커밋에 AI 공동저자 트레일러가 있으며, 측정은 데이터 이전에 동결된 사전약정 규칙을 따릅니다.

## 측정하는 것

- **검증 가능 서브골 (RLVR):** 생물 ≥ C 마리 catch · ≥ 1 진화 · 각 체육관 격파 · 최종 보스 격파.
- **경쟁력 있는 속도 (JAX) — 실측.** 핫패스를 함수형 JAX로 포팅했고
  (`critter_gym.jax_env`), **numpy env와 parity 검증(0 mismatch)** — 시드→궤적 재현성이 포팅을
  가로질러 보존됩니다. **CPU**에서 `vmap` 벡터화 시 **전체 에피소드 기준 numpy의 ≈27–60×,
  순수 전투 step은 최대 ≈1047×**입니다(numpy ≈123–410k steps/s; 단일 jit env는 오히려 *더
  느림* — 이득은 전적으로 배치 벡터화). JAX-native PPO가 그 위에서 **수 초 만에 학습**됩니다
  (numpy/sb3 경로의 ≈170×). *정직한 범위: CPU·단일-run 방향 신호이며, ≥10M steps/s GPU 목표
  (M4-EC3)는 미측정입니다.*
- **네 env family 전부 벡터화 (A/B/C/D).** critter(A), forage(B), **duel(C — 타입 무관
  RPS/스태미나 전투)**, muster(D)가 하나의 JAX 엔진에서 parity 0으로 돌아갑니다 — 기준
  family만이 아니라 family 전 폭.
- **(A) 인스턴스 일반화 — 실측.** held-out *시드*는 새 맵 + 새 숨은 타입표를 만듭니다. 학습된
  에이전트의 보스 격파율은 **held-out 45% vs held-in 40%** — 갭 ≈ 0 (암기가 아닌 일반화).
- **어렵고 *동시에* 학습 가능 (실측 headroom).** 튜닝된 PPO baseline(GAE+clip, on-device
  JAX)이 held-out 시드에서 scripted oracle의 **21–28%**에 그칩니다(**5-run robust**; 기본
  3-체육관·hard 8-체육관 config). 일반화는 되고(held-in ≈ held-out), hard config에선
  무추론 `type_blind` arm *아래*에 있습니다 — 뚜렷한 능력 사다리(oracle ≫ type_blind > PPO)와
  큰 실측 headroom. *이 예산에서의 baseline/신호이지, 튜닝된 SOTA sweep이 아닙니다.*
- **규칙 추론이 load-bearing.** 팀-커밋 경제에서 scripted 4-arm 게이트(42 held-out 시드)가
  `oracle − type_blind ≥ 0.20`과 `infer − probe ≥ 0.10`을 freeze합니다: 타입표를 아는 것이
  결정적이고, 재등장 상성을 *추론*하는 것이 매 전투 *찔러보기*를 이깁니다. 학습된 PPO 정책이
  이를 획득합니다(gym-clear-only 지표에서 `infer` 기준선 이상에 도달).
- **(B) 장르 일반화 — 토대이지, 아직 주장 아님.** env-*family* 추상화가 구조적으로 다른
  수집-RPG들 간 전이를 측정합니다(env 수준 leave-one-out). 3개 축(수집/전투 시스템/성장)의
  4개 family에서 갭은 *정책 특이적*입니다: 예컨대 duel family에서 A-튜닝 정책은 전이에 실패
  (갭 ≈ +3.9)하고 적절한 정책은 전이합니다(≈ +0.2). 이는 기계장치를 세운 것이지 — 장르
  일반화의 **증명이 아닙니다**(그건 훨씬 많은 family가 필요).

**두 헤드라인 표(처리량 + oracle headroom)를 한 명령으로 재현:**

```bash
pip install -e ".[jax,rl]"
python scripts/reproduce_results.py --quick    # 빠른 스모크 (수 초)
python scripts/reproduce_results.py --runs 5   # 전체 multi-run headroom (수 분)
```

수치는 라이브로 생성됩니다(하드코딩 0); 각 서브-벤치가 자신의 정직 프레이밍을 함께 출력합니다.

전체 결과·출처·정직한 한계: **[`docs/paper/critter-gym.md`](docs/paper/critter-gym.md)**
(figure→소스 맵은 [`docs/paper/README.md`](docs/paper/README.md)). 범위 SSOT:
[`DESIGN.md`](DESIGN.md) §3.1.1.

## 포지셔닝 (정직)

CritterGym은 **절차적-일반화** 벤치마크입니다; **Procgen / Craftax / XLand-MiniGrid**와
비교하세요, 포켓몬이 아니라. **포켓몬은 쉬운 설명을 위한 비유**(생물 + 타입 상성 + 체육관이
과제를 읽기 쉽게 만듦)이지 **경쟁 주장이 아닙니다** — 포켓몬의 열린 난이도를 *측정 가능성*과
맞바꿨습니다. 인스턴스 일반화(A)는 실측됐고, 장르 일반화(B)는 정직한 *토대*이지 증명이
아닙니다. 헤드라인보다 정직.

## 재현성

시드 기반·결정론: `reset(seed)`가 region을 정확히 재현하고, train/test 시드는 구조적으로
분리됩니다(누수 가드가 갭을 유리하게 꾸미는 것을 방지). 기준 config는 고정(pinned)입니다.

## 기여

개발 환경 셋업과 task lifecycle은 [`CONTRIBUTING.md`](CONTRIBUTING.md)를 보세요.

## 인용

```bibtex
@misc{crittergym2026,
  title  = {CritterGym: A Procedurally-Generated Creature-Collection Benchmark for
            Measuring Long-Horizon Agency and Generalization},
  author = {CritterGym contributors},
  year   = {2026},
  note   = {Working draft, docs/paper/critter-gym.md}
}
```

## 릴리스 상태

- **버전:** `1.0.0rc1` — **release candidate**. 무료 오픈소스 env는 기능 완성 상태이고
  (M0–M2 ✅; M3 런치 준비 대부분 ✅; M4 처리량 CPU에서 ✅), 헤드라인 결과는 parity 검증·재현
  가능합니다.
- **2026년 7월부터 공개:** 저장소는 공개돼 있고
  [라이브 사이트](https://anolysius.github.io/creature-rl-env/index.ko.html)(리더보드·게임플레이·
  커뮤니티 제출 트랙)가 운영 중입니다.
- **`1.0.0` 태그 전에 남은 것(각각 명시적 게이트):** **≥10M steps/s GPU** 측정(M4-EC3; CPU
  vmap은 순수 슬라이스에서 이미 통과), **arXiv 원고**(M3-EC4, 초안은 `docs/paper/`),
  **버전 태그 / eval-허브 등재** — 각각 메인테이너(사람)의 결정입니다.
- **라이선스:** MIT ([`LICENSE`](LICENSE) 참조).

## 라이선스

[MIT](LICENSE).

---

> 본 한국어 문서는 영문 [README.md](README.md)의 번역 미러입니다 — 두 문서가 어긋나면 정식
> 사실의 SSOT는 영문/코드입니다.
