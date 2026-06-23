# QA Checklist — obs-harmonization (G1 freeze 대상)

> plan: [plan.md](./plan.md) | G1 통과 시 acceptance_freeze:true 로 동결. 이후 추가 BLOCK.
> ⚠ 이 task = "전이하는 학습 정책" 이니셔티브의 **선행(enabler) 슬라이스**. 전이 gap 줄이기는 다음 task(scope 밖).
> ⚠ 마일스톤 override: M5/moat 층2 enabler 를 M3 공개보다 먼저(사람 방침). G1 에서 이 override 도 함께 승인.

## Acceptance Criteria (frozen at G1)

- [x] **AC1** — `HARMONIZED_OBS_KEYS`가 `env_family`에 SSOT로 선언되고, 4 family(critter/forage/duel/muster)가
  모두 동일한 obs Dict 키를 노출(조화 헬퍼/wrapper 적용 후). 측정: 4 family obs 키 집합 동일 테스트.
- [x] **AC2** — 비-duel family(critter/forage/muster)의 `player_charge`/`enemy_charge`가 0으로 마스킹되고,
  duel은 실제 charge 값 보존. 측정: 마스킹/보존 테스트 green.
- [x] **AC3** — 기존 scripted 레퍼런스 정책(`type_attacker`/`duel_aware`/`rush`/`muster`/`nav_toward_gyms`)
  점수가 조화 전후 **동일**(고정 seed). 측정: 점수 수치 비교 테스트(패딩 행동 불변 증명).
- [x] **AC4** — env id 6종 + 기존 테스트 전부 무회귀(185 유지/증가), `check_env` 4 family 통과,
  `mypy src`/`ruff check .`/`build` clean. 측정: `python3 -m unittest` 전체 + 툴체인 exit 0.
- [x] **AC5** — `assert_obs_compatible`가 duel 포함 4 family 통과 + `_MultiFamilyEnv`가 4 family(duel 포함)
  조화 obs 로 구성 가능(smoke; **실험 실행은 다음 task**). 측정: smoke 테스트(importorskip).
- [x] **AC6** — DESIGN §3.1.1 + 관련 독스트링이 "obs 조화 완료, 4-family 학습 전이는 다음 task"로 정직 갱신 +
  마일스톤 override(M5 enabler, M3 공개보다 먼저) 기록. 측정: diff 검토.
- [x] **AC7** — CHANGELOG 1줄 append(rules/80 §F.5).

## L1 이력
- round 1: plan-reviewer **APPROVE**(5축 전부) / qa-verifier **APPROVE**(3축 전부, INLINE) → **APPROVED** (no-progress 없음).

## 정직성 불변식
이 task 의 성공 = "전이 gap 을 줄였다"가 **아니다**(그건 다음 task). 성공 = 4 family 가 한 obs 공간을 공유하고
기존 동작이 무회귀이며 정직하게 문서화된 것. 패딩/마스킹이 기존 정책 점수를 안 바꿈을 *수치로* 증명.
(reasoning-load-bearing/learnability/difficulty 의 "측정+정직보고로 freeze" 패턴 일관.)
