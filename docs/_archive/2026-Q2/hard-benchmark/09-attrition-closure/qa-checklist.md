# QA Checklist — attrition-closure (G1 freeze)

> G1 통과 시 freeze. task-verify(G2)·task-review(L3)가 이 목록에 1:1 대조한다.
> **사전약정(grid·floor·closure 3조건·마진)은 여기 freeze 되면 데이터와 무관하게 불변** — seed 확충만 허용.

## Acceptance (plan AC 1-4)

- [ ] AC1 — `scripts/attrition_closure_scout.py`가 `type_blind` 6칸(commit×{default,strict,SE-only}) + probe floor(commit,SE-only) + oracle/blind winnability + 추론 gap(oracle−type_blind) 출력. 판정 전 사전약정 규칙 출력.
- [ ] AC2 — 결정론 메커니즘 테스트(Battle-level): commit+SE-only에서 (a) non-super champion=데미지 0·winner≠champion, (b) 정답 super commit=승리, (c) commit이 non-commit의 순환 등판을 제거함을 증명.
- [ ] AC3 — 전체 기존 스위트 무회귀(758 green), ruff clean. (신규 src 없음 — mypy 대상 무변경.)
- [ ] AC4 — 본측정 완주 — 사전약정 closure branch(a/b/c) 그대로 보고. 정직 라벨(floor≠0·scripted·1-seed-set·헤드라인 금지) 명시.

## 사전약정 (freeze — 데이터 무관 불변)

- **grid**: `type_blind` × {commit, non-commit} × {default, strict, SE-only} 6칸. floor arm=`probe`(commit, SE-only). config=hard(grid16·5gym·420step·num_types8·patch2). seeds=heldout(16).
- **closure 판정**: **(a) CLOSED** iff `type_blind(commit,SE-only) ≤ type_blind(non-commit,SE-only) − 0.25` ∧ `type_blind(commit,SE-only) ≤ probe(commit,SE-only) + 0.5` ∧ `oracle(commit,SE-only) ≥ 0.5·num_gyms`. 둘째 미충족→(b) NOT CLOSED. 셋째 미충족→(c) TOO HARSH.
- **마진 근거**: 0.25/0.5 gym = 5-gym 1칸(0.2)보다 약간 큰, #7 type_blind seed-분산(~0.3–0.6) 흡수용 보수적 마진.
- **해석 규율**: "완전 폐쇄" target=~0 아닌 blind-luck floor. floor>0을 실패로 오도 금지.

## Default DoD

- [ ] 전체 테스트 green (`.venv/bin/python -m pytest -q`), 회귀 0.
- [ ] `ruff check .` 통과.
- [ ] L3 리뷰 APPROVED (≥2 reviewer).
- [ ] CHANGELOG.md 1줄 append.
