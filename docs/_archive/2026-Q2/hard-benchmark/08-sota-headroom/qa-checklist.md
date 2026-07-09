# QA Checklist — sota-headroom (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.
> **사전약정(sweep grid·best 선택·runs·임계)은 여기 freeze 되면 데이터와 무관하게 불변** — seed/run 확충만 허용.

## Acceptance (plan AC 1-5)

- [ ] AC1 — `headroom.classify_scaled_headroom` 신규(순수·numpy·결정론): best-non-tiny 선택 + `classify_headroom` 위임 + non_vacuous(best>tiny)/exceeds(best>oracle) 플래그. 기존 `classify_headroom` 무변경.
- [ ] AC2 — 단위테스트가 5-branch(robust/closes/exceeds/vacuous/inconclusive) + tiny-제외 선택 + 경계(빈 sweep·non-positive oracle raise) 커버.
- [ ] AC3 — 전체 기존 스위트 무회귀(746 green), ruff/mypy clean.
- [ ] AC4 — `scripts/sota_headroom.py --quick` 무오류: recurrent PPO sweep·oracle winnable·#3 h128 대비·사전약정 branch 출력. script가 판정 전 사전약정 규칙 출력.
- [ ] AC5 — 본측정(full budget, ≥3 run) 완주 — 사전약정 branch 그대로 보고(reframe/robust/vacuous 무관). 정직 라벨(CPU·runs·non-SOTA·oracle proxy·scaled-not-arch·frozen) 명시.

## 사전약정 (freeze — 데이터 무관 불변)

- **sweep grid**: tiny=`GRU h128`(=#3 published) / wide=`h256` / wider=`h384`. budget: base_iters=300(=#3 full) / long_iters=600(scaled config).
- **best 선택**: tiny 제외 config 중 held-out mean 최대 = "strong baseline".
- **판정**: `classify_headroom(frac=0.75, k=1.0)` on best-scaled runs. non-vacuity(best>tiny) 미충족→verdict 보류. exceeds(best>oracle)→(c).
- **runs**: 기본 3, opt-bound가 0.75·oracle의 ±0.3 gym 이내 borderline 시 5로 확충. **frac·k·임계 불변.**
- **결과 해석 규율**: robust여도 "SOTA-hard 입증" 금지 — "scaled baseline(≠arch class·GPU·SOTA algo)에도 headroom 유지 → hard 주장 강화, SOTA는 OPEN".

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check .` / `mypy src` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
