# 커뮤니티 리더보드에 내 모델 제출하기

> **상태: 프로토타입.** 제출 접수는 공지 후 열립니다(사람의 결정). 이 가이드는 접수 첫날 바로
> 참여할 수 있도록 흐름을 미리 문서화한 것입니다.

커뮤니티 트랙은 **시즌제 공개 시험지**에서 벌이는 **자가 신고(honor system)** 경쟁입니다. 자기
모델을 로컬에서 돌리고(컴퓨트·비용=본인 부담), 작은 JSON 을 만들어 PR 을 열면 사이트가 시즌별로
랭크합니다. **검증된 오염-불가** 결과는 **봉인 트랙**(서명 인증서)입니다 — 이 트랙은 재미와
자랑, 그리고 정직한 신호를 위한 곳입니다.

## 5분 흐름

1. **시즌 시험지 받기** (공개 유도식 — 모두가 같은 세계를 받습니다):

   ```python
   from critter_gym.community import season_seeds, season_spec
   seeds = season_seeds(1, 16)   # 시즌 1, 공개 held-out 세계 16개
   spec = season_spec()          # 고정 벤치마크 설정 — 바꾸면 안 됩니다
   ```

2. **에이전트 실행**: 위 seed 들을 고정 spec 으로 돌리고 **평균 체육관 클리어**(커뮤니티 지표 —
   RLVR-clean, `num_gyms` 상한)를 기록합니다. scripted/학습 정책은
   `scripts/community_submit.py --demo` 를 그대로 참고하세요(무료 baseline 을 end-to-end 채점).
   **LLM 에이전트**는 `docs/how-to/evaluate-an-llm-agent.ko.md` 를 보고 같은 seed 를 채점하세요.

3. **제출 JSON 작성** (`community/submissions/season1-scripted-baseline.json` 복사 후 수정):

   ```json
   {
     "schema_version": 1,
     "season": 1,
     "model": "모델-이름",
     "submitter": "github-핸들",
     "heldout_mean": 1.25,
     "n_worlds": 16,
     "spec": { "...": "season_spec() 출력을 그대로" },
     "reproduce": "당신의 수치를 재현하는 한 줄 명령",
     "date": "YYYY-MM-DD",
     "self_reported": true
   }
   ```

4. **로컬 검증** (CI 가 돌릴 것과 같은 검사):

   ```bash
   python scripts/community_submit.py --validate your-file.json
   ```

5. **PR 열기**: 파일을 `community/submissions/` 에 추가하는 PR. 머지되고 사이트가 재빌드되면
   순위표에 올라갑니다.

## 규칙 (honor system)

- **시즌 seed 에서만, 고정 spec 으로만** 채점 — 다른 설정은 검증기가 거부합니다.
- **`reproduce` 필수**: 당신의 수치를 재현하는 한 줄 명령. 누구든 돌려볼 수 있습니다.
- **`self_reported: true` 는 스키마가 강제** — 이 트랙은 검증된 척할 수 없습니다.
- 시즌은 순환합니다: 새 시즌마다 새 공개 블록 발급(절차생성 — 시험지 무한 재발급 가능), 순위
  리셋 + 암기 가치 제한.
- **검증된** 결과가 필요하면 봉인 트랙으로: 비공개·재생성 가능한 eval + 서명된 오염-불가 인증서
  (`docs/reference/sealed-eval-packaging.md`).
