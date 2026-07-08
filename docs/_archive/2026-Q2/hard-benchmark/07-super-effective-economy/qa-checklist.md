# QA Checklist — super-effective-economy (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.
> **사전약정(측정 질문·판정 규칙)은 여기 freeze 되면 데이터와 무관하게 불변** — seed 확충만 허용.

## Acceptance (plan AC 1-5)

- [ ] AC1 — `Battle(super_effective_only=True).damage()`가 super-effective(eff>NEUTRAL) 타만 >0, 중립·저항 타는 정확히 0. default(False)는 기존 `max(1, …)` 공식과 byte-identical.
- [ ] AC2 — numpy `Battle.damage` ↔ jax `_gym_damage` parity가 SE-only on/off 양쪽에서 성립(신규 테스트).
- [ ] AC3 — `super_effective_only=False`(default)에서 전체 기존 스위트 무회귀(718 green, `test_jax_hard_config_parity` 포함). ruff/mypy clean.
- [ ] AC4 — `scripts/super_effective_scout.py --quick`가 default/strict/SE-only 3경제의 arm spread(oracle−blind) + attrition probe + **oracle winnability 플래그**를 출력(사전약정 Q1·Q2 판정 재료).
- [ ] AC5 — scout 출력·docstring에 정직 프레이밍(scripted·1-seed·SIGNAL·falsify·헤드라인 금지) 명시, Q2(winnability)를 falsify 가능 결론으로 정직 서술.

## 사전약정 측정 질문 (freeze — 데이터 무관 불변)

- **Q1 (변별밴드 widening)**: SE-only가 scripted arm 변별밴드(oracle−type_blind gym-clear spread)를 strict/default보다 넓히면 = 레버 후보 SIGNAL. 안 넓히면 그대로 falsify 보고.
- **Q2 (fairness/winnability)**: SE-only에서 oracle이 winnable(≥ 절반 gym)을 유지해야 공정 레버. 밑돌면 "너무 가혹" → falsify, knob은 무해한 opt-in default-off로 남긴다.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check .` / `mypy src` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
