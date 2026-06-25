# 인수인계서 — CritterGym (세션 이후: KR2 마무리[duel C 포트] + KR3 패키징[v1.0.0-rc])

> 다음 세션용. 직전 세션이 **bounded-YOLO 자율 런**으로 2 task를 main 머지: duel(C) JAX 포트(KR2
> 마무리 → **4/4 family 전부 벡터화**) + KR3 결과 패키징(README/paper 통합 + 1-command 재현 + **버전
> 1.0.0-rc**). **자율 OKR(KR1/KR2/KR3) 전부 달성.** 남은 것은 (a) GPU 측정[하드웨어 필요] (b) **공개
> [사람 게이트]** 둘뿐. 이 문서 = *무엇이 끝났고 / 자율 런 결산 / 남은 두 갈래(둘 다 사람·하드웨어 의존)*.
> SSOT: `DESIGN.md`(§3.1.1·§4), `docs/explanation/jax-throughput.md`, `docs/explanation/competitive-analysis.md`,
> `docs/_active/{jax-throughput,difficulty-scaling}/INITIATIVE.md`, `docs/CHANGELOG.md`, `README.md`,
> `docs/paper/critter-gym.md`, `CLAUDE.md`(규율), 메모리(`autonomous-v1-mandate`·
> `plain-language-task-summaries`·`user-non-math-background`).

---

## 0. 오프닝 프롬프트 (새 세션에 붙여넣기)

> CritterGym 작업을 이어서 한다. 먼저 `docs/HANDOFF-next-session.md`, `README.md`,
> `docs/explanation/jax-throughput.md`, `docs/explanation/competitive-analysis.md`, `DESIGN.md` §3.1.1+§4,
> `docs/_active/jax-throughput/INITIATIVE.md`, `docs/CHANGELOG.md` 상단, `docs/reference/milestones.md`,
> `scripts/reproduce_results.py` 를 읽어라. main HEAD=`ed22898`, **415 tests green**(2 skip), 버전
> **1.0.0rc1**.
>
> [직전 세션 요약] bounded-YOLO 자율 런으로 2 PR 머지(#55 jax-duel-integration: duel(C) type-agnostic
> RPS 배틀을 jax_env에 통합 = **4/4 family 벡터화 완성**[KR2], parity 0; #56 v1-results-packaging:
> README/paper에 강한 결과 통합 + `reproduce_results.py` 1-command 재현 + **버전 1.0.0rc1**[KR3]). 전부
> 사전약정 규칙·freeze 전 pilot·정직 보고·L3 2/2 APPROVE.
>
> [현황] **자율 OKR(KR1 tuned-PPO+robust headroom / KR2 4/4 family / KR3 패키징) 전부 달성.** 남은 두
> 갈래는 **둘 다 자율 범위 밖**: (a) **GPU 측정**(M4-EC3)=현 .venv는 CPU jax라 하드웨어 필요, (b)
> **공개**(OSS 리스팅·arXiv 제출·git tag v1.0.0 push)=**사람 게이트**. → **다음 세션은 사람의 결정을
> 먼저 받아라**(공개할지/GPU 환경 줄지/M5 모네타이즈로 피벗할지). 새 자율 task를 임의로 시작하지 말 것.
>
> [방침] 하네스 규율 100% 유지(매 task `/task-start`→L1→freeze 전 pilot→G1 freeze→TDD/G2→L3
> APPROVED→`/task-end`). main 직접 금지=feature→PR→merge. parity 포트는 **0 mismatch 비협상**. 정직성 >
> 헤드라인. 매 task 시작·끝 수식 없는 한 문단 요약. `.claude/projects/`는 매 커밋 `git reset .claude/projects/`로 제외.

---

## 1. 현재 상태 (한 줄)

M0·M1·M2 ✅, M3 대부분(EC1–EC3·EC6 ✅ / **EC4 arXiv·EC5 OSS = 사람 게이트**), **M4 거의 완성**: **4/4
family(A critter / B forage / C duel / D muster) 전부 JAX 벡터화** + commit·non-commit 배틀 + full-episode
env + tuned PPO + robust headroom + **1-command 재현** + **버전 1.0.0rc1**. **415 tests**(2 skip),
numpy-only core + `[rl]`/`[viz]`/`[render]`/`[jax]` extra. main HEAD=`ed22898`. **M4 남은 단 하나 = GPU
측정(EC3, 하드웨어)**.

## 2. 직전 세션 2 task (전부 main 머지)

| PR | task | 정직한 결과 |
|---|---|---|
| #55 | `jax-duel-integration` (KR2 마무리) | duel(C) type-agnostic RPS/stamina 배틀을 별도 `duel_battle_branch`로 jax_env 통합. numpy `DuelEnv(commit_battles=False)` 대비 **parity 0**. duel 고유: 동시 데미지(동시 기절=loss)·raw `floor(atk×(1+charge))`(`_damage` 미사용)·charge obs(family-aware). pilot이 19,200 steps 0 mismatch + always-attack 0승 포착(탱키 보스)→scripted-optimal로 win/evolve 자극. vmap 40–83×. **4/4 family 벡터화 = full breadth.** 396→415(+19). |
| #56 | `v1-results-packaging` (KR3) | 흩어진 결과를 README/paper에 통합 + `scripts/reproduce_results.py`(throughput+headroom 2표 라이브 재생성) + 버전 0.0.1→**1.0.0rc1**. README "What it measures"에 competitively-fast(27–1047×·4 family)+hard-and-learnable(PPO 21–28% of oracle robust) 헤드라인. paper 신규 §6 Throughput+§4 headroom. **공개는 사람 게이트로 명시**(태그/OSS/arXiv 안 함). src 무변경. |

## 3. ⚠ 정직한 결론 (과대 금지)

- **M4 (JAX)**: 4/4 family + commit·non-commit 배틀 + full-episode env + tuned PPO 전부 벡터화·parity 0.
  **속도 이득=vmap 한정**(단일 jit는 손해)·**CPU**(GPU 미측정 M4-EC3 — 유일한 M4 잔여).
- **헤드라인 자산 2개**: (1) **competitively fast** = JAX vmap 27–1047× numpy(CPU)·4/4 family parity 0.
  (2) **hard-and-learnable** = tuned PPO가 oracle의 21–28%만(5-run robust), gap≈0, hard서 PPO<type_blind.
  둘 다 정직 caveat 동반(CPU·vmap-only·oracle=scripted proxy·5-run·이 예산·GPU 미측정).
- **버전 1.0.0rc1**: release **candidate** — 무료 OSS env는 기능 완성, 결과는 parity-proven·재현 가능. 단
  **공개·태그·arXiv는 사람 결정**(README Release status 명시). 과대 아님.

## 4. 다음 세션 — 두 갈래 (둘 다 사람/하드웨어 의존 → 먼저 사람 결정 받기)

자율 OKR 완료 후, **임의로 새 자율 task를 시작하지 말 것.** 남은 것은:

### (a) GPU 측정 — `vectorized-bench` (M4-EC3, 마지막 M4 항목)
현 `.venv`는 CPU jax. ≥10M steps/s **GPU** 측정엔 GPU 환경 필요. CPU vmap은 슬라이스에서 이미 10M/s 초과.
→ **사람이 GPU 환경을 제공하면** task로 진행. 없으면 보류(하드웨어 블록, 사람 게이트 아님).

### (b) 공개 — **사람 게이트 (자율 금지)**
`git tag v1.0.0` push · OSS 공개 리스팅 · arXiv 제출. 본 자율 런이 그 직전까지 전부 준비(1.0.0rc1·README·
paper·재현 스크립트). **반드시 사람 결재 후에만.** competitive-analysis의 peer-fact `[verify]` 항목(Procgen/
Craftax/XLand/NetHack 수치·라이선스)은 공개 전 1차 출처 확인 필요(아직 미확인).

### (c) 피벗 후보 (사람 결정)
- **더 깊은 hard-benchmark**(별도 이니셔티브급): "PPO가 oracle에 못 닿는" 변별 — 다중타입 보스·부분관측·전략
  깊이. 큰 연구(difficulty-scaling INITIATIVE "다음 task" 참조).
- **M5 모네타이즈**: 비공개 held-out eval 세트·커스텀 고난도 env(DESIGN §8). v1 이후.
- **family 폭 확장 + 학습 정책의 held-out family 일반화**(B claim, M5 enabler).

## 5. 코드 포인터 (이번 세션 산출, 전부 main)

- `src/critter_gym/jax_env.py` — `_FAM_DUEL=3` + `JaxEnvState.{player_charge,enemy_charge}` + `duel_battle_branch`
  (동시 데미지·raw 데미지·charge·40턴 cap) + `encode_obs` family-aware charge + step dispatch(duel 분기).
  duel은 `make_jax_env(JaxEnvConfig(family=_FAM_DUEL, commit=False))`로만 접근(default API byte-identical).
- `tests/test_jax_duel_parity.py` — 5 정책 parity(`test_duel_parity_scripted`/`_random`) + `test_duel_battery_is_non_vacuous`(6신호) + `test_duel_jit_and_vmap`.
- `scripts/reproduce_results.py` — `[--quick] [--runs N]`: `bench_throughput.py`+`ppo_baseline.py` 오케스트레이션,
  throughput+headroom 2표 라이브 재생성(수치 하드코딩 0, honest framing 보존).
- `README.md`(What it measures 2 헤드라인 + Release status 1.0.0-rc) · `docs/paper/critter-gym.md`(신규 §6
  Throughput + §4 PPO headroom) · `docs/paper/README.md`(source map) · `pyproject.toml`(1.0.0rc1).

## 6. 하네스 메모 (이번 세션 학습)

- **freeze 전 pilot이 핵심(재확인)**: duel pilot이 19,200 steps 0 mismatch + **always-attack 0승**(테스트
  설계 보강: scripted-optimal 추가) 포착. 패키징 pilot이 reproduce 2표 라이브 재생성 검증.
- **archive `git mv` 주의**: 신규(untracked) task 폴더는 `git mv` 실패(`source directory is empty`) → 일반
  `mv` 후 `git add`. (duel은 plan이 일부 tracked라 통과, KR3는 plain mv 필요했음.)
- **pytest 요약줄 non-tty 억제**: 이 repo는 redirect 시 "N passed" 요약줄이 안 보임 → **exit code(0)로 판정**.
- **bounded-YOLO 정지 조건 도달**: 자율 OKR(KR1/2/3) 완료 → 남은 건 하드웨어(GPU)·사람 게이트(공개)뿐.
  자율 런이 자연 종료점에 도달 = 새 task 임의 시작 금지, 사람 결정 대기.

## 7. 정직성 문화 (계승 필수)

매 task acceptance를 *성능* 아닌 *측정+정직 보고*로 freeze. parity 0으로 가짜 속도 차단, vmap 한정·CPU·이
예산 한정 명시, oracle=scripted proxy·single/few-run 라벨. 사전약정 결정규칙(데이터 전 고정)으로 p-hacking
차단, pilot이 전제 검증(falsify시 reframe), 다층 검증(pilot+parity/property+non-vacuity 가드+adversarial L3).
**front-facing 문서(README/paper)도 동일** — 수치 라이브 재생성으로 fabricate 0, 1.0.0-rc는 잔여 게이트
명시. 헤드라인보다 정직성 — moat 층3(trust) 재료.

## 8. 사용자 메모 (계승)

사용자는 수학/RL 깊은 배경 아니나 **전략·정직성·방향으로 지휘**. **매 task 시작·끝 수식 없는 한 문단 요약**
(뭘/왜/비유/결과)을 표·용어와 *별도로* 동반. **자율 mandate**(메모리 `autonomous-v1-mandate`): v1.0.0/moat까지
bounded-YOLO 자율 task 연속+커밋푸시, **공개는 사람 게이트**. 자율 런 OKR — **KR1 ✅ / KR2 ✅ / KR3 ✅
전부 달성**. 남은 두 갈래(GPU·공개)는 둘 다 사람/하드웨어 의존 → **다음 세션은 사람 결정 먼저**.
