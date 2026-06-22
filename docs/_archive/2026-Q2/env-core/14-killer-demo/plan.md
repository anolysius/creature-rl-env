---
slug: killer-demo
initiative: env-core
status: active
started: 2026-06-22
acceptance_freeze: true
milestone: M3
exit_criteria: M3-EC6
task_type: general
mode: standard
domains: [render, rl-env]
scope_paths:
  - src/critter_gym/demo.py
  - tests/test_demo.py
  - scripts/killer_demo.py
extracted_to: []
supersedes: []
---

# killer-demo (M3-EC6 — 데모 수단 ship; 일반화 충족은 미검증)

> 작성일: 2026-06-22 | 상태: 계획

## 목표

킬러 데모(M3-EC6: "같은 에이전트 → **unseen held-out 시드**(새 맵+새 타입표) → 보스 격파" GIF)의
**재현 가능한 수단**을 ship 하고, 그중 **CI 검증 가능한 부분(녹화 파이프라인)을 못 박는다**. 이게 우리
moat(infer-the-meta + 증명 가능한 일반화)의 시각적 증명 토대 — 포켓몬 레드가 *구조적으로 못 하는* 것.

### ⚠ 정직성: 이 task 는 EC6 를 **전진**시키되 **완전 충족하지 않는다** (world-render 선례)

EC6 의 핵심 주장 = *held-out(새 타입표)에서 보스격파* = **일반화**. 그런데:
- **CI 가 검증하는 것** = 녹화 파이프라인·보스격파 감지 (type-aware scripted 가 **seed=3(train 영역)**
  에서 gym 격파를 녹화). 이건 *파이프라인 정확성*을 증명할 뿐 **일반화를 증명하지 않는다** (seed=3 은
  학습 가능 영역).
- **CI 가 검증하지 않는 것** = "학습된 에이전트가 **held-out** 보스격파". `scripts/killer_demo.py` 가
  *수단*을 ship 하나, 성공은 학습 품질 의존 → 산출 GIF 는 *실행 산물*(비CI).

→ **milestones M3-EC6 체크박스는 `[ ]` 유지**(또는 `[~]` 부분). `[x]` 충족 자격 = 실제 held-out
보스격파 GIF 육안 확인 + 별도 결재(후속). 본 task 의 acceptance 는 *수단 ship + 파이프라인 CI 검증*까지.

### 경계 (중복 회피)

`record_episode`(데모) = **프레임 수집 + 격파 감지** 전용. `generalization`/`scoreboard` 의 eval
rollout = **점수 측정** 전용(프레임 없음). 둘은 직교 — record 는 render 프레임을 모으고, eval 은 보상만.

## 선행 조건

- ✅ M3-EC6 토대 `world-render` — `CritterEnv(render_mode="rgb_array").render()` (numpy-only 프레임),
  `critter_gym.render.save_gif`(프레임→.gif, `[render]` extra).
- ✅ env `info` — `info["subgoals"]["gyms_defeated"]`, `info["remaining_gyms"]`; terminated = 전 gym 격파.
- ✅ split API `heldout_seeds(n)`(≥ `TEST_SEED_OFFSET`); 학습 패턴 `scripts/train_ppo.py`(`_SeededReset`+PPO).
- ✅ True-path 재현원 — `tests/test_gym_battle.py` 의 type-aware `_scripted_action` 이 seed=3 에서 ≥1
  gym 격파(학습 없이 보스격파 녹화 가능 → 파이프라인 CI 검증).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 변경 | 영향도 | 비고 |
|---|---|---|---|
| `src/critter_gym/demo.py` | **신규** | 높음 (신규 공개 데모 API) | `record_episode`(numpy-only) + `EpisodeRecording` + `save_demo` |
| `tests/test_demo.py` | **신규** | 중 | core: 녹화·감지·결정론(scripted 보스격파) / `[render]` smoke: GIF |
| `scripts/killer_demo.py` | **신규** | 중 | `[rl]`+`[render]` — 학습→held-out 녹화→GIF(EC6 산출) |

### 영향 범위 (import 그래프)

- `demo.py` → import `render.save_gif`(numpy-only top-level), `CritterEnv`, numpy 만 (측정 스택과
  직교 — `EvalResult` 등 미import). **torch/sb3/imageio top-level 미import**(imageio 는 `save_gif` 가
  지연; import 순수성 테스트).
- `killer_demo.py` → import `demo`, `render`, `region.heldout_seeds`; sb3 지연 import(없으면 안내).
- 기존 `src/**`(env·render·측정) **무수정** — 순수 추가.

## Step별 계획

### Step 1 — `demo.py` 녹화 파이프라인 (numpy-only) [RED→GREEN]

```python
@dataclass(frozen=True)
class EpisodeRecording:
    frames: tuple[np.ndarray, ...]   # 각 (H,W,3) uint8 (reset + 매 step)
    steps: int
    total_reward: float
    gyms_defeated: int               # info subgoals
    boss_defeated: bool              # remaining_gyms == 0 (전 gym 격파)
    seed: int

def record_episode(env, policy, seed, max_steps=None) -> EpisodeRecording:
    """seed 로 reset 후 정책 rollout, 매 스텝 env.render() 프레임 수집.
    env.render_mode != 'rgb_array' 면 ValueError. 보스격파는 종료 시 info 로 감지."""

def save_demo(recording, path, fps=5) -> str:   # render.save_gif 위임([render])
```

- 프레임 = reset 1 + step 당 1 → `len(frames) == steps + 1`. 결정론(고정 seed+결정론 정책 → 동일 프레임).

### Step 2 — `tests/test_demo.py` [RED→GREEN]

- **core(numpy-only)**: type-aware scripted(env 내부 읽는 closure)로 seed=3 녹화 → `gyms_defeated >= 1`
  (보스격파 감지 입증), `boss_defeated == (remaining_gyms==0)` 일관, `len(frames)==steps+1`, 각 프레임
  `(H,W,3) uint8`; render_mode 미설정 env → ValueError; **결정론**(동일 seed 2회 byte-identical 프레임).
- **import 순수성**: `demo` 모듈 top-level 에 torch/sb3/imageio 미import.
- **`[render]` smoke**(`importorskip("imageio")`): `save_demo` 가 .gif(비어있지 않음) 저장.

### Step 3 — `scripts/killer_demo.py` (`[rl]`+`[render]`) [GREEN]

- train 시드로 PPO 학습(`_SeededReset`+train_ppo 패턴 재사용).
- `seed = heldout_seeds(...)` 중 하나(**held-out** — 새 맵+새 타입표); `env = CritterEnv(render_mode=
  "rgb_array", **CFG)`; `rec = record_episode(env, ppo_policy, seed)`; `save_demo(rec, "killer_demo.gif")`.
- PPO 정책은 `predict(obs, deterministic=True)` — 재현 GIF 흔들림 축소(AC2 결정론은 scripted CI
  path 한정이나 스크립트도 결정론적 추론 사용).
- 출력: `held-out seed S | gyms_defeated=N | boss_defeated=bool | frames=F → killer_demo.gif`.
- sb3/imageio 미설치 시 안내 + 비차단.

## 검증 방법

- `mypy src` · `ruff check .` · `pytest -q` · `python -m build`.
- 수동(EC6 산출): `pip install -e ".[rl,render]" && python scripts/killer_demo.py` → held-out GIF +
  보스격파 리포트 육안 확인.
- 기존 113 tests 무회귀 + 신규 test_demo.py(core green, `[render]` smoke skip-or-pass).

## 리스크

| 리스크 | 완화 |
|---|---|
| 학습이 held-out 보스격파 실패(데모 flaky) | 학습품질은 acceptance 아님 — 파이프라인·감지가 CI 산출물; GIF 는 실행 산물(재현 *수단* ship). seed/CFG 쉬운 값 + 시도 |
| record_episode 가 render_mode 미설정 env 에서 None 프레임 | 명시 ValueError 가드 + 테스트 |
| imageio 의존이 core 오염 | demo.py top-level imageio 미import(save_gif 지연) + import 순수성 테스트 |
| EC6 "충족" 과대주장(보스격파 CI 비검증) | 정직 표기 — 충족 = 재현 가능 데모 *수단*(파이프라인+스크립트) ship + CI 가 scripted 보스격파 녹화 검증; held-out GIF 는 스크립트 실행으로 재현 |
| 기존 env/render 회귀 | 순수 추가(read-only) — 113 tests 가드 |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/demo.py` `record_episode` 가 정책 에피소드를 녹화 — `EpisodeRecording`(frames +
   steps + total_reward + gyms_defeated + boss_defeated + seed), **numpy-only**; `render_mode!="rgb_array"`
   env → ValueError.
2. **프레임·결정론** — `len(frames)==steps+1`, 각 `(H,W,3) uint8`; 고정 seed+결정론 정책 → byte-identical 프레임.
3. **보스격파 감지(파이프라인 검증 — 일반화 아님)** — type-aware scripted 가 **seed=3(train 영역)**
   에서 녹화 시 `gyms_defeated >= 1`, `boss_defeated == (remaining_gyms==0)` 일관(CI 검증). 이 AC 는
   *녹화·감지 파이프라인 정확성*만 증명하며 **held-out 일반화는 증명하지 않는다**(명시).
4. **numpy-only 격리** — `demo.py` top-level 에 torch/sb3/imageio 미import; `save_demo` 가 `render.save_gif`
   위임(`[render]`). import 순수성 테스트.
5. **`[render]` smoke** — `importorskip("imageio")` 가 `save_demo` .gif 생성(비어있지 않음) 검증(core skip).
6. `scripts/killer_demo.py` 가 train 학습 → **held-out 시드**(≥`TEST_SEED_OFFSET`) 녹화 → GIF +
   보스격파 리포트(gyms_defeated/boss_defeated; PPO `deterministic=True`). `[rl]`+`[render]` 격리,
   미설치 graceful, core/CI 무영향. **(산출 GIF 는 비CI 실행 산물 — acceptance 는 스크립트가 *동작*함까지)**.
7. **정직 표기** — milestones M3-EC6 체크박스는 `[ ]` 유지(전진, 미충족); `[x]` 충족은 실제 held-out
   보스격파 GIF 육안 확인 + 별도 결재(후속 조건). report 에 "수단 ship / 일반화 미검증" 명시.
8. `mypy src` · `ruff check .` · `pytest -q` · `python -m build` 통과 + 기존 113 tests 무회귀.
