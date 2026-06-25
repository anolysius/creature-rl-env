# QA Checklist — jax-battle-full (G1 freeze)

- [ ] **AC1** jax_battle_full.py 신규: FullBattleState/FullBattleParams + full_battle_step(non-commit 1턴: switch/item/move[speed order]/force-switch/party-wipe, branch-free) + params_from_parties/initial_state bridge. import jax 모듈, 코어 numpy-only(__init__ 미import).
- [ ] **AC2** test_jax_battle_full_parity.py(importorskip): numpy Battle(commit_mode=False)(starter 3 vs boss 1) 대비 parity 0 mismatch — 배터리(attack/switch/item-heal/force-switch/party-wipe/truncation)+random(고정 seed), 매 턴 party_a_hp·active_a·boss_hp·done·winner·turn 일치 + jit/vmap.
- [ ] **AC3** bench_throughput.py full-battle vmap 행, 정직 framing("빠르다"=부등식 성립시).
- [ ] **AC4** core CI numpy-only 불변: 310 무회귀(importorskip 격리, __init__ 미import), canonical clean.
- [ ] **AC5** freeze 전 pilot R1(parity)/R2(jit)/R3(speed-order). parity mismatch 비협상. report 박제.
- [ ] **AC6** 측정/정직보고: parity 0 박제+속도 vmap·CPU·single-run 라벨+한계효용(commit load-bearing·full-env 통합 별도) 명시.
- [ ] **AC7** 문서 jax-throughput.md(§5)+DESIGN§4+CHANGELOG+INITIATIVE, broken-link 0.

## 사전약정 규칙 (freeze)
- parity 게이트: 배터리+random 전부 0 mismatch(party_a_hp·active_a·boss_hp·done·winner·turn). 비협상.
- speed: vmap full-battle steps/s > numpy 성립 시만 "빠르다"(vmap·CPU·single-run 라벨).
