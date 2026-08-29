# AA-VAE-030：Final authority sidecar adapter

## 功能标识

- ID：`AA-VAE-030`
- 名称：Final authority sidecar adapter
- 状态：generic runtime 已验证；production executor/writer 待实现
- 负责人或变更任务：Phase 5 final authority separation
- 日期：2026-08-30

## 问题

generic controller 已保证 `FinalJudge` 只在 submission freeze 后运行，且 judgment 事件为
trusted-only；result artifact 也会验证外部提供的 sidecar。但二者之间缺少一个运行时 seam：
final executor 返回的 judgment 和 sidecar 尚不能在同一次调用中绑定 final profile、frozen
submission 与 judge attempt lifecycle。

## 运行时契约

- `ProfileBoundFinalJudge` 在构造时验证并深拷贝 final profile，caller 或 executor 不能改写
  adapter 内部 authority identity。
- `judge()` 只接受 `FrozenSubmission`；executor 必须同时返回 `FinalJudgment` 和
  `vaevas-score-sidecar-v1` document。
- sidecar 必须与 final profile 的 benchmark、manifest、judge/version/identity、checker、
  runtime、campaign、command 和 sidecar schema contract 一致，也必须与 judgment 和
  submission tree 一致。
- `score_authority` 也是 final profile contract 的一部分；legacy v1 profile 缺少该字段时
  只能产生 `development_only` sidecar，只有显式声明 `formal` 的 profile 才能接受 formal
  sidecar，防止开发期 EVAS 分数被高报为正式结果。
- adapter 在首次有效调用前置位 single-use 状态。executor exception 或验证失败不能在同一
  adapter 上静默重试；基础设施 replay 必须走既有 replay classifier 并使用新 judge attempt。
- 成功后只向 trusted outer coordinator 暴露 detached sidecar、sidecar hash 与
  profile-input identity。controller 的模型事件仍只含 final judgment 的 trusted event，
  sidecar 不成为 Observation 或 memory。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `authority_adapters.py::FinalTestExecution` | 同一次 final invocation 的 typed judgment/sidecar output | final authority |
| `authority_adapters.py::ProfileBoundFinalJudge` | detached profile、single-use lifecycle、submission/profile/sidecar binding | final authority |
| `result_artifact.py::validate_score_sidecar_authority` | 复用统一 sidecar semantic validator | evidence join |
| `result_artifact.py::score_sidecar_sha256` | canonical sidecar identity | evidence join |
| `authority_profiles.py::_require_score_sidecar_contract` | profile 允许显式权限并为 legacy v1 提供安全默认值 | profile validation |
| `vaevas-final-test-profile-v1.schema.json` | 可选 `score_authority`，保持 v1 文档读取兼容 | schema |
| `tests/test_agent_harness_final_authority_runtime.py` | mutation isolation、single-use、checker/submission/schema mismatch | tests |

## TDD 与验证

- RED：测试 collection 因 `FinalTestExecution`/adapter 尚不存在失败。
- GREEN focused final authority、result artifact、controller、authority profile：`92 passed`。
- reviewer 首轮发现 formal authority 未绑定；修复后的 focused authority/result/profile/meta
  suite 为 `66 passed`，完整 generic harness + meta-schema 为 `297 passed`。
- 同一 reviewer 复审 `5719fac7fa` 后报告 `APPROVE`、零剩余 finding，并分别动态验证
  legacy、显式 development-only 和显式 formal 三种 profile。
- Ruff 0.12.12、Python bytecode compilation、`git diff --check` 通过。

## Claim boundary

- 能支持：generic final execution 可以把 frozen submission、final profile、judgment 与
  immutable sidecar 在运行时 fail-closed join；失败后不能复用同一 judge attempt。
- 不能支持：production EVAS final executor 已接入、sidecar 已原子落盘、formal campaign
  已切换，或 legacy trajectory 已满足 typed result artifact。
- 不修改 r53、EVAS 0.8.7、mini-swe 默认 runner、production score authority 或 Spectre
  条件兼容门。
