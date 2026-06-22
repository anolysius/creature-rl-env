# QA Checklist — typechart-depth (DESCOPED) · M3 신뢰성

> G1 freeze (2026-06-22) → **DESCOPED 2026-06-22 (사용자 (가))**: pilot 가 infer>probe·no-heal keystone
> 달성 불가 입증 → 안전한 깊이만 ship, 추론-load-bearing 은 future work. plan DESCOPE NOTE 참조.

## Acceptance Criteria (DESCOPED)
- [x] D1 (타입 풀): `ElementType` ≥12 (F/W/G=인덱스 0/1/2 유지); `num_types` 파라미터 region+env
- [x] D2 (active subset): region 이 boss 샘플 **및** `generate_typechart` 둘 다 `[:num_types]` 전달; `num_types>3 ∧ vary=False`→ValueError; 차트 antisymmetric·무모순·obs 미노출
- [x] D3 (타입 재출현): procgen 에피소드가 보스 타입을 시드별 소수 풀서 반복 → 같은 타입 ≥2회 출현(테스트)
- [x] D4 (winnability 구조): 각 procgen 보스 타입 ≥1 스타터 NEUTRAL+ (승리불가 시드 0)
- [x] D5 (obs 고정): 타입 경계=풀 크기(num_types 무관); shape 불변
- [x] D6 (K≥12 차트): per-seed distinct; train≠held-out(누수0)
- [x] D7 (M1 무회귀): fixed 결정론·trajectory·차트 동일; no-heal/난이도 변경 없음(드롭); 고정월드 테스트 green; check_env(fixed+procgen)
- [x] D8 (procgen 등록): `CritterGym-procgen-v0`=num_types≥12+보스 재출현(num_gyms↑); fixed-v0=K3 M1
- [x] D9 (정직 표기): "추론 provably load-bearing=future work(battle-economy)" DESIGN/roadmap 명시
- [x] D10 (툴체인): `mypy src`(core)·`ruff`·`pytest`·`build` 통과 + 무회귀 (imageio-dev 의 render.py overload는 out-of-scope follow-up)
