# QA Checklist — multitype-boss-headroom (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.
> **사전약정(임계·규칙)은 여기 freeze 되면 데이터와 무관하게 불변** — seed 확충만 허용.

## Acceptance (plan AC 1-6)

- [ ] AC1 — `headroom.classify_depth` 신규(순수, 사전약정 규칙 그대로) + 단위 테스트(deeper-robust/not-deeper/inconclusive + 경계·입력검증). 기존 `classify_headroom` 무변경.
- [ ] AC2 — **사전약정 freeze**: (A) `classify_headroom(frac=0.75, k=1.0)` on 다중-config recurrent PPO held-out gym-clears; (B) `classify_depth` — oracle-fraction 정규화, `mean(frac_single)−mean(frac_multi) > max(std)` ∧ 양쪽 winnable → deeper-robust / gap≤0 → not-deeper / else inconclusive; runs 기본 3(borderline 시 5, **임계 불변**). script 가 결과 산출 전에 규칙을 출력.
- [ ] AC3 — `scripts/multitype_boss_headroom.py` `--quick` pilot 무오류: 두 config oracle+winnable, recurrent PPO ×N, (A)+(B) branch 출력, 정직 라벨(CPU·seed·非SOTA·oracle proxy·frozen 명시).
- [ ] AC4 — 본측정 완주(≥3 runs, full budget): (A)·(B) branch 산출 — **어떤 branch 든 그대로 보고**(반증 포함).
- [ ] AC5 — 회귀 0(전체 스위트, baseline 620), ruff/mypy clean.
- [ ] AC6 — `multitype-boss.md` 측정 결과 섹션(branch·수치·경계 그대로). CHANGELOG 1줄.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check` / `mypy src/critter_gym/headroom.py` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
