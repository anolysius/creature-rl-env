---
slug: matchup-validity
initiative: eval-product
status: completed
ended: 2026-06-30
extracted_to: []
changelog_entry: docs/CHANGELOG.md (eval-product 섹션)
---

# eval-config matchup validity — 결과 보고서

## 요약 (수치 표)

| 항목 | 값 |
|---|---|
| 변경 파일 | `src/critter_gym/region.py` (필터 1줄 + 가드 + 주석), `tests/test_region.py` (+3 테스트) |
| 테스트 | 514 → **517 passed** (+3 신규), 2 skipped, 회귀 0 |
| 타입/린트/빌드 | mypy 31 files clean · ruff clean · build(wheel+sdist) OK |
| oracle SE-rate (demonstrator) | 붕괴 0.055/0.227/0.115 (n=4/6/8) → **1.000 at every n∈{1,2,3,4,6,8}** |
| 변별 band (oracle − type_blind) | n=8 **+0.93** · n=16 **+0.97** (≥0.3) |
| oracle n_moves (n=8) | 391 (attrition grind) → **62** (결정적 SE 승리) |

## 계획 대비 실적 (✅/⚠️/❌)

- ✅ **AC1 [hard]** — `test_every_placed_boss_has_super_effective_party_type`: vary=True, num_types∈{3,4,6}, 80 seed(train 40 + heldout 40)에서 **모든 placed boss 에 strictly super-effective 한 starter(party 무브) 타입 존재**. PASS.
- ✅ **AC2 [정량]** — 비붕괴: `test_oracle_se_rate_does_not_collapse_with_world_count` (oracle 1.000 @모든 n). 변별: `test_oracle_discriminates_from_chart_blind_at_eval_scale` (band +0.93/+0.97 @n=8,16). PASS.
- ✅ **AC3 [회귀]** — fixed mode(vary=False) byte-identical(필터는 `if vary:` 블록 내부, else 분기 무변경). 517 passed, 회귀 0. mypy/ruff/build clean. PASS.
- ✅ **AC4 [정직]** — 본 report 의 §정직 경계에 명시(아래). 전투 economy 재설계는 사람 게이트.

## 변경 파일 상세

### 수정 — `src/critter_gym/region.py`
- vary=True boss-placement 필터: `chart.effectiveness(s, t) >= NEUTRAL` → **`> NEUTRAL`** (변수명 `winnable` → `exploitable`).
  - **근본 버그**: boss 타입 `t` 자신이 `_STARTER_TYPES` 에 포함 → `effectiveness(t, t) == NEUTRAL ≥ NEUTRAL` 이 **항상 참** → num_types=3 에서 필터가 **no-op**. transitive chart 의 최상위 타입(어떤 타입에도 안 짐) boss 가 SE 카운터 없이 배치 → oracle 이 neutral attrition grind → SE-rate 붕괴.
- **빈-집합 가드**: `exploitable` 가 비면 `ValueError`. num_types≥3 토너먼트 in-degree 합 C(n,2)≥n 으로 **이론상 도달 불가**(증명 주석) — 1200 region(3~8 types) 검증서 미발동. silent 분포 왜곡 방지용 방어.
- 주석: "winnable" → "inference-exploitable(SE 보장)" 서술 정합. `_STARTER_TYPES == party 무브 타입` 결합 불변식 박제.

### 신규 — `tests/test_region.py` (+3 테스트, +79 lines)
- `test_every_placed_boss_has_super_effective_party_type` (AC1 불변식).
- `test_oracle_se_rate_does_not_collapse_with_world_count` (AC2 비붕괴, 모든 n).
- `test_oracle_discriminates_from_chart_blind_at_eval_scale` (AC2 변별, n=8/16).

## 발견된 이슈 (심각도)

- **[중] band 의 소표본 아티팩트** — n_worlds=1,3 에서 type_blind(고정 챔피언 FIRE)도 SE-rate 1.000 → band 0. 이는 fix 결함이 아니라 **변별이 집계 속성**이기 때문(소수 world 블록에선 고정 챔피언이 우연히 정답과 일치). 정직 처리: 비붕괴 floor 는 모든 n 에서, 변별 band 는 정의가 성립하는 현실 규모(n=8,16)에서 검증. floor(0.5)는 측정 후 **약화하지 않음**(실측 oracle=1.000) → p-hacking 아님. L3 plan-reviewer 가 독립 확인.

## 흡수처 매핑 (extracted_to)

- **없음** — 새 evergreen 설계 narrative/runbook/ADR 없음. 본 수정은 기존 generate_region 의 *생성 correctness 버그* 정정(render_obs #14 와 동성격)으로, 살아있는 결정은 코드 주석 + INITIATIVE 시퀀스 한 줄에 흡수됨. cross-task 의존성 없음(archive invariant 충족).

## 정직 경계 (AC4)

- 본 task 의 hard 보장은 **"각 placed boss 에 super-effective 무브가 *존재*한다"** 뿐이다 — oracle 이 *매번* 그 무브를 쓴다는 보장이 아니다. (commit-economy 상 cross-gym 챔피언 lock 가능성은 별개.) 실측상 demonstrator 에서 oracle SE-rate 가 1.000 으로 나온 건 강한 결과지만, 이는 측정값이지 정의상 보장이 아니다.
- 전투 모델 재설계(`damage=max(1)` attrition → gym-clear 변별 band 협소)는 **벤치마크 정의 변경 = 사람 게이트**로 남긴다. 본 수정은 그와 무관한 *생성 필터* correctness.
- 단일 config(demonstrator)·scripted oracle/type_blind proxy 기반 신호. LLM 실측은 별도 probe(사용자 로컬).

## 타입 체크 / 빌드 결과
- mypy: Success, no issues in 31 source files.
- ruff: All checks passed.
- build: critter_gym-1.0.0rc1 wheel + sdist OK.
- pytest: 517 passed, 2 skipped.
