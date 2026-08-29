# AA-VAE-031：Immutable score sidecar store

## 功能标识

- ID：`AA-VAE-031`
- 名称：Immutable score sidecar store
- 状态：generic store 已验证；production final executor integration 待实现
- 负责人或变更任务：Phase 5 immutable evidence persistence
- 日期：2026-08-30

## 问题

`ProfileBoundFinalJudge` 已经能把 final profile、frozen submission、judgment 和 sidecar 在
内存中绑定，但普通 `write_text`/replace 写法仍可能覆盖旧证据，进程故障也可能留下半文件。
writer 还必须与 controller/model trajectory 解耦，避免 final evidence 被误作下一轮 observation。

## 持久化契约

- 在创建目录或文件前调用统一 sidecar authority validator；验证失败零落盘。
- canonical JSON bytes 的 SHA-256 同时作为 receipt identity 和文件名，文件内容与名称可直接
  复核。
- 临时文件与目标文件位于同一目录；写入后执行 file fsync 和只读权限设置，再用 hard link
  做原子且不覆盖的 exclusive publish，清理临时文件后 fsync 目录。
- 已有同名证据始终拒绝，即使内容相同；调用方不能借 writer 把“重用”伪装成新的 judge
  attempt。
- output root 或 `score-sidecars` 为 symlink 时 fail closed；receipt 不含 structured result 或
  sidecar body。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `result_store.py::write_immutable_score_sidecar` | authority-first、content-addressed、exclusive persistence | trusted evidence store |
| `result_store.py::ImmutableScoreSidecarRecord` | sidecar/profile/profile-input identity receipt | trusted evidence store |
| `result_store.py::_publish_exclusive` | 同目录 hard-link publish，禁止覆盖 | filesystem boundary |
| `tests/test_agent_harness_result_store.py` | canonical bytes、重复写、故障清理、symlink、trajectory isolation | tests |

## TDD 与验证

- RED：测试 collection 因 `runners.agent_harness.result_store` 不存在失败。
- GREEN focused store suite：`9 passed`。
- 完整 generic harness + meta-schema：`306 passed`。
- Ruff 0.12.12、Python bytecode compilation、`git diff --check` 通过。

## Claim boundary

- 能支持：generic trusted coordinator 可以把已验证 sidecar 原子、不可覆盖地持久化，并拿到
  content/profile/input receipt。
- 不能支持：production `run_trusted_replay` 已通过该 API、真实 campaign 已生成 receipt、
  final output 在 resume/checkpoint 中绝不回流，或 r53 result ledger 已完成。
- 不修改 r53、EVAS 0.8.7、mini-swe 默认 runner、production score authority 或 Spectre 条件门。
