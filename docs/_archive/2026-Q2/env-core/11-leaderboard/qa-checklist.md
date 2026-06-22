# QA Checklist — leaderboard (G1 freeze) · M3-EC2

> G1 통과 시 freeze (2026-06-21). task-verify(G2)·task-end 가 1:1 대조.

## Acceptance Criteria
- [x] AC1 (리더보드 포맷): `leaderboard.py`(numpy-only) = `BenchmarkSpec` + `Leaderboard`(`to_markdown`/`to_json`) + `run_benchmark(spec, policies)`
- [x] AC2 (개명 완료): `to_dict` 키 `{heldin_mean,heldout_mean,gap,n_heldin,n_heldout}`; 리터럴 `train_mean`/`test_mean` grep=0(산문 포함, 전 reader 동기화)
- [x] AC3 (numpy-only): leaderboard/scoreboard/generalization 모두 torch/sb3 미import (import 순수성)
- [x] AC4 (재현성): 동일 `BenchmarkSpec`+결정론 정책 → 동일 `to_json`(canonical, sort_keys); spec 직렬화 round-trip
- [x] AC5 (랭킹): `entries` held-out 평균 내림차순 + `rank` 1..N 연속; scripted > random
- [x] AC6 (누수 가드 상속): `run_benchmark` 가 split API 경유 (held-in⊂train영역, held-out⊂test영역)
- [x] AC7 (benchmark.py 소비자): `run_benchmark`→랭크 `to_markdown` + 재현 spec 헤더; sb3 미설치 graceful; ruff 통과
- [x] AC8 (툴체인+무회귀): `mypy src`∧`ruff check .`∧`pytest -q`∧`python -m build` 통과; 기존 86 tests 회귀 0
