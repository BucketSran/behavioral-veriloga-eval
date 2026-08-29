# AA-VAE-024：Runtime candidate effects and attempt budgets

## 功能标识

- ID：`AA-VAE-024`
- 名称：Runtime candidate effects and attempt budgets
- 状态：已验证
- 负责人或变更任务：Phase 2 controller/state closure
- 日期：2026-08-30

## 思想来源

- AlphaApollo 公开工作的可迁移思想是：多轮 reasoning/evolution 的工具反馈、候选状态和
  计算预算必须由外部 harness 管理，不能依赖模型自述。
- vaEVAS 额外需要 candidate tree、public validation、submission freeze 和 final judge
  的不对称权限。
- “descriptor 应成为运行时后置条件”和“错误 mutation 需要事务性丢弃”是针对 vaEVAS
  coding-agent 环境作出的工程推断，不声称是 AlphaApollo 原实现。

## vaEVAS 适配决策

- 采用：trusted capability 在 dispatch 前决定执行权限和 canonical budget cost。
- 修改：candidate effect 同时接受静态 schema/registry 检查和 controller postcondition。
- 不采用：让 environment/model 自行决定本次调用属于哪个预算类；把 final judge 当普通工具。
- evaluator/claim 边界：public validation 可以消耗 episode 预算并返回公开 observation；final
  judge 仍在 freeze 后独立执行，不进入该工具账本或共享记忆。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/tool_registry.py::ToolRegistry` | active/inactive/reserved、registry hash、effect contract | harness |
| `schemas/vaevas-tool-descriptor-v1.schema.json` | state/candidate/submission-budget 组合约束 | schema |
| `runners/agent_harness/controller.py::EpisodeController` | execution rejection、candidate postcondition、trusted freeze binding、hard-budget preflight | harness |
| `runners/agent_harness/budget.py::BudgetLedger` | attempt-scoped capability-derived counter ledger | harness |
| `runners/agent_harness/state.py::EpisodeContext` | immutable non-negative attempt budget limits | state |

## 数据与状态变化

- 输入：resolved `ToolCapability`、trusted previous observation、`EnvironmentStep`、attempt limits。
- 中间状态：candidate before/after、canonical delta、consumed/remaining counters。
- 输出：accepted observation、classified rejection、`budget_updated` evidence 或 terminal failure。
  freeze mismatch 会拒绝 episode，且不会把未通过绑定校验的 frozen submission 暴露为 result。
- 新增 schema 字段：tool lifecycle 增加 `inactive`；未改变 action/observation wire schema。
- backward compatibility：generic harness contract 更严格；production mini-swe 尚未接入，旧 runner
  行为与 r53 bytes 未改变。

## 验证证据

- regression tests：controller/tool-registry 与完整 `tests/test_agent_harness_*.py`。
- clean-room smoke：本切片未重跑真实模型；最终回归继续保留 r53 smoke gate。
- 未验证部分：token/wall/disk meter、错误 mutation 自动回滚、production adapter parity。

## Claim boundary

- 能支持：通用 controller 会检测 capability/state/budget contract 违规并 fail closed；
  frozen submission 只有在与 terminal candidate hash 匹配后才成为可信结果。
- 不能支持：production mini-swe 已使用该账本，或该机制提升模型分数。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
