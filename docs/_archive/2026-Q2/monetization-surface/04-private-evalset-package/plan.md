---
slug: private-evalset-package
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/eval_package.py
  - tests/test_eval_package.py
  - scripts/package_sealed_eval.py
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 비공개 held-out eval 세트 판매 패키지 (monetization-surface #4)

> 작성일: 2026-07-01 | 상태: 계획 | 추진 EC: **M5-EC1** (비공개 held-out eval 세트 — 재현 가능, un-gameable)

## 목표

eval-product 이니셔티브가 지은 **기능 토대**(`SealedEvalSet` / `verify_sealed`→`SealedCertificate`
/ `score_agent`→`Scorecard`) 위에, *팔 수 있는 형태*의 **buyer/seller 패키징 + 서명된
오염-불가 인증서**를 prototype 한다. 즉 "moat 엔진"을 두 당사자(판매자=평가자 / 구매자=제출자)가
주고받을 수 있는 **직렬화·서명·검증 가능한 artifact**로 만든다.

현재 빈틈(코드로 확인): `eval_harness.py`에 직렬화·서명·패키징이 **전혀 없다**. 인증서
(`SealedCertificate`)·점수(`Scorecard`)는 in-memory NamedTuple일 뿐이라 파일로 건네거나 위변조를
검출할 수 없다. 판매 제품이 되려면 (1) 판매자가 **비밀 seed를 노출하지 않고** 구매자에게 건넬 수
있는 매니페스트, (2) 그 매니페스트가 사후 eval 세트 교체(rug-pull)를 막는 **커밋먼트**, (3) 평가자가
발급하고 위변조를 검출 가능한 **서명된 인증서**가 필요하다.

**정직성 게이트(이니셔티브 불변식 계승)**: 이 task는 *기술 artifact*만 만든다(빌드+로컬 검증까지
자율). 실제 판매·가격·고객·hosting·공개 배포는 **사람 게이트**. 서명은 stdlib HMAC-SHA256 기반
prototype이며 — "실제 hosted 제품은 비대칭 서명(구매자가 비밀 없이 검증)·서버측 비밀 보관이
필요"함을 코드·문서·데모 출력에 **명시**한다. (정직성 > 헤드라인.)

## 선행 조건

- `src/critter_gym/eval_harness.py` — 재사용할 토대: `SealedEvalSet`, `verify_sealed`,
  `SealedCertificate`, `score_agent`, `Scorecard`, `TEST_SEED_OFFSET`, `_SEALED_BASE`.
- 참조 패턴: `scripts/build_site.py`(#1) — 순수 함수 + `main()` 실측 + 프레임워크-0·stdlib-only,
  lazy import + guard. 데모 스크립트를 같은 규율로 작성.
- stdlib만 사용(`hashlib`, `hmac`, `json`, `dataclasses`/`NamedTuple`). 신규 의존성 0.

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `src/critter_gym/eval_package.py` | 신규 | 낮음(신규, 기존 import만) | 패키징·커밋먼트·서명·검증 순수 함수 + 데이터 타입 |
| `tests/test_eval_package.py` | 신규 | 낮음 | 왕복(round-trip)·위변조 검출·오염 검출·커밋먼트 무결성 테스트 |
| `scripts/package_sealed_eval.py` | 신규 | 낮음(데모, 런타임) | seller→buyer→seller E2E 데모 + 정직-scope 캡션 |

기존 파일 **수정 없음** — 순수 추가(additive). `eval_harness.py`의 공개 API만 소비.

### 영향 범위 (import 그래프)

- `eval_package.py` → `critter_gym.eval_harness`(기존) 만 import. 역방향 의존 없음.
- `test_eval_package.py` → `eval_package` + `eval_harness`.
- `package_sealed_eval.py` → `eval_package` (lazy: imageio/matplotlib 불필요, 순수 stdlib).
- 기존 테스트/스크립트에 회귀 표면 없음(additive-only).

## Step별 계획

**Step 1 (Red→Green): 서명·검증 코어**
- `sign_payload(payload: dict, key: bytes) -> str` — canonical JSON(정렬 키, 공백 고정) →
  HMAC-SHA256 hexdigest. `verify_signature(payload, sig, key) -> bool` — `hmac.compare_digest`
  로 상수시간 비교(위변조·부분수정 검출). canonical 직렬화 helper 1개로 서명/검증 SSOT.
- 테스트: 왕복 성공 / 페이로드 1비트 변경 시 실패 / 키 불일치 시 실패 / 키 순서 무관(canonical).

**Step 2 (Red→Green): seed 커밋먼트 (rug-pull 방지)**
- `seed_commitment(sealed: SealedEvalSet) -> str` — 정렬된 eval seed + master_seed →
  sha256. 판매자가 사후 eval 세트를 바꾸면 커밋먼트가 달라져 인증서 서명과 불일치 → 검출.
- 테스트: 같은 SealedEvalSet은 결정론적 동일 커밋먼트 / master_seed 다르면 다름 /
  커밋먼트만으론 seed 역산 불가(노출 0 — 값이 seed를 담지 않음 assert).

**Step 3 (Red→Green): buyer 매니페스트 (비밀 미노출 + 서명된 배포물)**
- `EvalManifest` (직렬화 가능): 공개 메타(n_worlds, grid_size, boss config, 지역 경계
  `TEST_SEED_OFFSET`/`_SEALED_BASE`, seed_commitment, key_id, honest-scope 문자열) —
  **비밀 seed·offset 미포함**. `build_manifest(sealed, key, key_id)` — 매니페스트 공개
  페이로드를 **`sign_payload` 로 서명**해 `sig` 필드에 담는다(Step 1 재사용). `to_json()` /
  `from_json()` / `verify_manifest(manifest, key) -> bool`(서명 + 커밋먼트 형식 검증).
- 이유(L1 SUGGEST 반영): 매니페스트 자체를 서명하면 배포물의 임의 필드 변조(grid/boss/커밋먼트
  swap)가 인증서 발급 이전에 buyer 측에서 직접 검출된다 — AC3 의 "매니페스트 변조 → verify_* False"
  를 간접(cert 커밋먼트 비교)이 아니라 **직접** 충족.
- 테스트: 매니페스트 JSON 어디에도 비밀 eval seed/offset이 없음(문자열 부재 assert) /
  round-trip 동일 / 매니페스트 필드 변조 시 `verify_manifest` False / 구매자가 매니페스트만으로
  자기 train seed 오염 사전 자가점검 가능.

**Step 4 (Red→Green): 서명된 인증서 발급·검증 (seller flow)**
- `SignedCertificate` = 직렬화된 {contamination(=`verify_sealed`), scorecard(=`score_agent`),
  seed_commitment, manifest 참조, key_id, sig}. `issue_certificate(submission, declared_train,
  sealed, key, key_id) -> SignedCertificate` — 오염 가드가 실패(overlap>0 등)면 점수 없이
  `ok=False` 인증서 발급(부정 결과도 서명·정직). `verify_certificate(cert, key) -> bool` —
  서명 + 커밋먼트 일치 동시 검증.
- 테스트: 정상 제출 → `ok=True` 서명 검증 통과 / 오염된 train seed → `ok=False` & 여전히
  서명 유효(부정 결과의 무결성) / 인증서 필드 변조 → 검증 실패 / 커밋먼트 불일치 → 실패.

**Step 5 (데모): `scripts/package_sealed_eval.py`**
- seller가 `SealedEvalSet` 생성 → 매니페스트 발급(비밀 미노출) → buyer가 매니페스트로 자가점검 →
  scripted 제출 에이전트로 `issue_certificate` → 제3자가 `verify_certificate`. 정상 케이스 +
  오염 케이스 둘 다 출력. **정직-scope 캡션**(HMAC=prototype / 실제=비대칭·서버측) 명시 출력.
  build_site.py 규율(순수 함수 + `main()` + guard) 준수. 스크립트는 파일을 scratchpad 또는
  `site/`가 아닌 임시 경로에만 쓰거나 stdout 출력(부작용 최소).

## 검증 방법

- `python3 -m pytest tests/test_eval_package.py -q` (또는 unittest — 저장소 현행 러너 확인 후
  일치). 신규 테스트 전부 green.
- 전체 스위트 회귀 0: 기존 테스트 수(현재 baseline) → +신규. 숫자 report에 기록.
- `python3 scripts/package_sealed_eval.py` 무오류 실행 + 정상/오염 두 케이스 + 정직-scope 캡션 출력.
- `ruff check .` / `mypy src` (툴 존재 시) 통과. 없으면 report에 명시.

## 리스크

| 리스크 | 완화 |
|---|---|
| **정직성 오해** — HMAC 서명을 "구매자가 비밀 없이 검증 가능"으로 과대표현 | 코드 docstring·매니페스트 honest-scope 필드·데모 출력에 "shared-secret prototype, 실제=비대칭/서버측" 3중 명시. 헤드라인 금지. |
| `_eval_seeds()`/`_offset()`는 private(`_`) — 매니페스트가 실수로 비밀 노출 | 매니페스트는 **커밋먼트(해시)만** 담고 seed/offset 원본 배제. 테스트가 문자열 부재를 assert(회귀 방지). |
| 서명 canonical 직렬화 불일치로 검증 실패 | `sign`/`verify`가 **같은** canonical helper 사용(SSOT). float 표현 안정화(scorecard 값 반올림/문자열화 규칙 고정). |
| stdlib 한계(비대칭 서명 없음) | prototype 범위로 HMAC 채택 + 한계 명시. 실제 제품은 별도 사람-게이트 task. |
| 데모 스크립트 파일 부작용 | stdout 우선 / 임시 경로만. 저장소에 산출물 커밋 안 함. |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/eval_package.py` 신규 — `sign_payload`/`verify_signature`,
   `seed_commitment`, `EvalManifest`(+`build_manifest`/`to_json`/`from_json`/`verify_manifest`),
   `SignedCertificate` + `issue_certificate`/`verify_certificate` 공개 API 제공. stdlib-only,
   신규 의존성 0.
2. **오염-불가 보장**: 오염된(overlap>0 또는 train이 held-out 영역에 있는) 제출은
   `issue_certificate`가 `ok=False`로 발급하고, 그 부정 인증서도 서명이 유효.
3. **위변조 검출**: 서명된 인증서의 임의 필드 변조 시 `verify_certificate`가 False, **그리고**
   서명된 매니페스트의 임의 필드 변조 시 `verify_manifest`가 False (매니페스트도 서명 — L1
   SUGGEST 반영).
4. **비밀 미노출**: 매니페스트 JSON 어디에도 비밀 eval seed/offset이 포함되지 않음(테스트가
   문자열 부재로 검증). 커밋먼트로부터 seed 역산 불가.
5. `tests/test_eval_package.py` 신규 — 최소 위 1–4 각각을 커버(round-trip / 위변조 / 오염 /
   비밀 미노출 / 커밋먼트 무결성). 전체 스위트 회귀 0.
6. `scripts/package_sealed_eval.py` — seller→buyer→verify E2E 데모가 정상+오염 두 케이스와
   **정직-scope 캡션**을 출력하며 무오류 실행.
7. **정직성**: HMAC=shared-secret prototype 한계가 코드·문서·데모 출력에 명시(비대칭/서버측은
   사람-게이트 후속). CHANGELOG 1줄 entry 추가.
