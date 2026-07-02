---
slug: tier-eval-bundle
initiative: monetization-surface
status: active
started: 2026-07-01
acceptance_freeze: true
domains: [rl-env]
scope_paths:
  - src/critter_gym/eval_marketplace.py
  - tests/test_eval_marketplace.py
  - scripts/tier_eval_bundle_demo.py
extracted_to: []
supersedes: []
mode: standard
task_type: general
---

# 판매-표면 통합 캡스톤 — 티어 eval 번들 (monetization-surface #6)

> 작성일: 2026-07-01 | 상태: 계획 | 추진 EC: **M5-EC1 + M5-EC2 결합** (판매 표면 end-to-end)

## 목표

#4(`eval_package` — 서명된 오염-불가 인증서)와 #5(`env_tier` — 난이도 티어 API)를 **한 흐름의
buyer 경험**으로 엮는다: **티어 선택 → 그 티어의 sealed eval 매니페스트 발급 → 제출 → 서명된
티어-인증서 발급 → 검증**. 지금 두 제품은 main 에 조각으로 존재하고 조합 가능성만 문서화돼 있을 뿐,
*구매자가 실제 겪는 end-to-end*가 없다. 이 task 가 그 캡스톤을 만들어 판매-표면 스토리를 닫는다.

빈틈(코드로 확인): `env_tier.build_sealed(name, master_seed)` 가 티어→`SealedEvalSet` 을 만들고,
`eval_package.build_manifest`/`issue_certificate`/`verify_certificate` 가 sealed→서명 artifact 를
만들지만, **둘을 잇는 buyer-facing 표면(어떤 난이도를 파는지 + 그 sealed 의 서명 매니페스트를 함께
제시하는 "offer", 티어 선택 후 인증서 발급·검증)** 이 없다.

**정직성 게이트(이니셔티브 불변식 계승)**: *기술 artifact*만(빌드+로컬 검증 자율). 실판매·가격·
hosting=사람. 두 층의 정직성 note 가 **함께 travel** 해야 한다 — (1) 패키징 `HONEST_SCOPE`
(HMAC=shared-secret prototype), (2) 티어 `difficulty_note`(hard=실측 한정, SOTA/recurrent=open,
sealed 변형이 patch_radius/num_gyms 드롭으로 덜 어려울 수 있음). 어느 것도 캡스톤에서 유실 금지.

## 선행 조건

- `src/critter_gym/eval_package.py`(main): `EvalManifest`/`build_manifest`/`verify_manifest`,
  `SignedCertificate`/`issue_certificate`/`verify_certificate`, `HONEST_SCOPE`.
- `src/critter_gym/env_tier.py`(main): `TierSpec`/`get_tier`/`tier_names`, `build_sealed`.
- 참조 패턴: `scripts/package_sealed_eval.py`·`list_env_tiers.py` — 순수 함수 + `main()` + stdout.
- stdlib만. 신규 의존성 0. 두 모듈의 공개 API만 소비(additive, 기존 무수정).

## 작업 범위

### 수정 대상 파일 (영향도 표)

| 파일 | 종류 | 영향도 | 변경 요지 |
|---|---|---|---|
| `src/critter_gym/eval_marketplace.py` | 신규 | 낮음(신규, 기존 import만) | TierOffer + build_tier_offer + publish_catalog + issue/verify tier certificate |
| `tests/test_eval_marketplace.py` | 신규 | 낮음 | offer round-trip·정직 note travel·인증서 발급/검증·티어 바인딩·오염 |
| `scripts/tier_eval_bundle_demo.py` | 신규 | 낮음(데모) | seller catalog → buyer 선택 → 제출 → 서명 인증서 → 검증 E2E |

기존 파일 **수정 없음** — 순수 추가(additive). `eval_package`/`env_tier` 공개 API만 소비.

### 영향 범위 (import 그래프)

- `eval_marketplace.py` → `critter_gym.eval_package` + `critter_gym.env_tier`(둘 다 main). 역방향 없음.
- `test_eval_marketplace.py` → `eval_marketplace` + 두 모듈.
- `tier_eval_bundle_demo.py` → `eval_marketplace` (+ `reference_arm` for a scripted submission).
- 기존 테스트/스크립트 회귀 표면 없음(additive-only).

## Step별 계획

**Step 1 (Red→Green): TierOffer (판매자가 티어별로 게시하는 offer)**
- `TierOffer`(직렬화): `tier_name`, `difficulty_note`, `harder_knobs`, `manifest`(EvalManifest).
  `to_json()`/`from_json()`. offer = "이 난이도를 이 (서명된, 비밀 미노출) sealed 매니페스트로 판다".
- `build_tier_offer(tier_name, master_seed, key, key_id, **sealed_overrides) -> TierOffer` —
  `env_tier.build_sealed(tier_name, master_seed, **overrides)` → `eval_package.build_manifest` →
  티어 difficulty 메타와 함께 wrap.
- 테스트: offer round-trip 동일 / offer.manifest 서명 유효(`verify_manifest`) / offer 에 비밀
  eval seed 부재(문자열 부재) / `difficulty_note` 가 티어의 정직 note 를 그대로 담음.

**Step 2 (Red→Green): publish_catalog (여러 티어 offer 카탈로그)**
- `publish_catalog(tier_names, master_seed, key, key_id) -> list[TierOffer]` — 티어마다 **서로 다른
  master_seed**(예: `master_seed + i`)로 offer 생성(블록 분리). 미지 티어는 env_tier 가 KeyError.
- 테스트: standard/hard 카탈로그 2 offer / 각 offer 커밋먼트가 서로 다름(다른 sealed 블록) /
  모든 offer 서명 유효.

**Step 3 (Red→Green): seller handle + issue/verify tier certificate (buyer 흐름)**
- **L1 SUGGEST 반영 — 단일 진실원(seller handle)**: `SellerListing`(tier_name, master_seed, key,
  key_id 를 한 번 묶는 seller-side handle) — `.offer() -> TierOffer` 와
  `.issue_certificate(submission, declared_train, **overrides) -> SignedCertificate` 를 제공해,
  offer 생성값과 cert 발급값이 **구조적으로 동일**(재입력 불일치 오사용 방어). `build_tier_offer`/
  `issue_tier_certificate` 는 이 handle 위 얇은 함수로 유지(둘 다 사용 가능).
- `issue_tier_certificate(submission, declared_train, tier_name, master_seed, key, key_id,
  **overrides) -> SignedCertificate` — `build_sealed` → `eval_package.issue_certificate`. 오염
  제출은 `ok=False` 미채점(그대로 위임).
- `verify_offer_certificate(offer, cert, key) -> bool` — `verify_certificate(cert, key,
  manifest=offer.manifest)` — **인증서가 이 offer 의 티어 sealed 에 바인딩**됨을 커밋먼트로 증명.
- 테스트: 정상 제출 → `ok=True` 서명 유효 + offer 바인딩 통과(**같은 tier·같은 master_seed**) /
  **같은 tier + 다른 master_seed → 바인딩 실패**(L1 SUGGEST: seed confound 를 knob 차이와 분리 —
  seed 재사용 리스크의 완화를 격리 증명) / 다른 티어 offer → 바인딩 실패 / 오염 제출 → `ok=False`
  미채점·서명 유효 / 인증서 변조 → 검증 False / `SellerListing` 의 offer↔cert 가 동일 handle 로
  항상 바인딩 성공(재입력 불일치 불가).

**Step 4 (Red→Green): 정직성 travel 계약**
- offer/cert 가 **두 층 정직 note 를 모두 노출**: `TierOffer` 에 `difficulty_note`(티어) +
  `manifest.honest_scope`(패키징). `bundle_honesty(offer) -> tuple[str,str]` 헬퍼(둘 다 반환).
- 테스트: hard offer 의 difficulty_note 에 "open"(미측정) 포함 + manifest.honest_scope 에
  "prototype" 포함(문자열 검증) — 어느 것도 유실 안 됨.

**Step 5 (데모): `scripts/tier_eval_bundle_demo.py`**
- seller 가 `publish_catalog(["standard","hard"], ...)` → buyer 가 hard offer 선택(난이도 note
  출력) → scripted 제출로 `issue_tier_certificate` → `verify_offer_certificate` 통과 → 다른
  티어 offer 로 바인딩 실패 시연 → 오염 케이스. **두 층 정직-scope 캡션** 출력. build_site 규율.

## 검증 방법

- `.venv/bin/python -m pytest tests/test_eval_marketplace.py -q` 전부 green.
- 전체 스위트 회귀 0 (baseline 578 → 578+신규). report 에 숫자 기록.
- `.venv/bin/python scripts/tier_eval_bundle_demo.py` 무오류 + 정상/바인딩실패/오염 케이스 + 정직 캡션.
- `ruff check` / `mypy src/critter_gym/eval_marketplace.py` 통과.

## 리스크

| 리스크 | 완화 |
|---|---|
| **정직성 note 유실** — 캡스톤이 두 층 note 중 하나를 떨어뜨림 | offer 가 difficulty_note+honest_scope 둘 다 보유, `bundle_honesty` + 테스트가 둘 다 존재 검증. |
| master_seed 재사용으로 offer↔cert 바인딩 실패/성공 혼동 | 발급·검증이 **동일 master_seed** 사용해야 커밋먼트 일치 — 데모/테스트가 same-seed 성공 + cross-tier 실패 명시. |
| 오염 제출 처리 중복 구현 | `eval_package.issue_certificate` 에 위임(재구현 금지). 캡스톤은 조합만. |
| cross-branch/stacked | #4·#5 모두 main 머지 완료(확인). 본 브랜치 main 기준 단독 PR. |

## Acceptance Criteria (G1 통과 시 freeze)

1. `src/critter_gym/eval_marketplace.py` 신규 — `TierOffer`(+to_json/from_json),
   `SellerListing`(offer/issue_certificate 단일 진실원), `build_tier_offer`, `publish_catalog`,
   `issue_tier_certificate`, `verify_offer_certificate`, `bundle_honesty` 공개 API. stdlib-only,
   신규 의존성 0, `eval_package`+`env_tier` 만 소비.
2. **offer**: `build_tier_offer` 가 티어 sealed 매니페스트(서명·비밀 미노출)+difficulty 메타를 담고,
   `publish_catalog` 가 티어별 서로 다른 커밋먼트의 offer 리스트 생성.
3. **buyer 흐름**: `issue_tier_certificate` 정상 제출 → `ok=True` 서명 유효,
   `verify_offer_certificate` 가 **같은 티어·같은 master_seed** offer 에 바인딩 성공, **같은 티어+다른
   master_seed** 및 다른 티어엔 실패(seed confound 격리). `SellerListing` 은 offer↔cert 를 동일
   handle 로 묶어 재입력 불일치 오사용을 구조적으로 방지.
4. **오염-불가 위임**: 오염 제출 → `ok=False` 미채점·서명 유효(eval_package 위임, 재구현 없음).
5. **정직성 travel**: offer 가 티어 `difficulty_note`("open" 포함)+`manifest.honest_scope`
   ("prototype" 포함) 둘 다 노출(`bundle_honesty` + 테스트로 검증).
6. `tests/test_eval_marketplace.py` 신규 — AC1–5 커버, 전체 스위트 회귀 0.
7. `scripts/tier_eval_bundle_demo.py` — seller catalog→buyer 선택→제출→서명 인증서→검증(+바인딩
   실패·오염) E2E, 두 층 정직 캡션, 무오류 실행.
8. **정직성**: 두 층 note 유실 0(코드·데모). CHANGELOG 1줄 entry.
