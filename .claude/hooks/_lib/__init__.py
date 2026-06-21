"""
Task-lifecycle harness Claude Code Hooks — 공용 라이브러리.

하네스 hooks/*.py 스크립트가 이 패키지를 import하여 공통 로직(git policy,
commit intent, worktree safety, active-plan scope, path matching)을 재사용한다.
스키마 변경 시 전파를 한 파일 내로 국한시키는 단일 진입점 역할.
"""
