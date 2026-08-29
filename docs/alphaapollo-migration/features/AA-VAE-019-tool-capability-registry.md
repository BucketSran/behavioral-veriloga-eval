# AA-VAE-019：Tool capability registry

## 功能标识

- ID：`AA-VAE-019`
- 名称：Tool capability registry
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 tool-contract slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 把工具反馈作为多轮 reasoning/evolution 的环境反馈来源；工具能否调用
  不能只靠 prompt 或 action 名称约定。
- coding-agent framework 通常在 dispatch 前做 capability check；vaEVAS 需要把
  proposal syntax allowlist 和真实执行权限分开。

## vaEVAS 适配决策

- 新增 `vaevas-tool-descriptor-v1`，记录 tool identity、lifecycle、model visibility、
  condition allowlist、budget class、state/candidate effect、argument/observation
  schema、evidence policy 和 handler。
- `active` tool 必须有 handler；`reserved` tool 作为未来领域工具占位，不能调用。
- `final_judge_only` 工具不能进入 model-visible registry，也不能写入共享 memory。
- registry 只解析 capability，不执行工具；production runner 暂不导入。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-tool-descriptor-v1.schema.json` | strict tool descriptor schema | schema |
| `runners/agent_harness/tool_registry.py` | condition-aware capability resolution and fail-closed authorization | harness protocol |
| `runners/agent_harness/__init__.py` | 导出 registry/capability/hash API | harness API |
| `tests/test_agent_harness_tool_registry.py` | active/reserved/final-only/syntax-not-authority regressions | tests |

## 数据与状态变化

- 输入：schema-shaped tool descriptor documents。
- 中间状态：condition-specific effective toolset。
- 输出：accepted tool names、capability hash、classified registry errors。
- backward compatibility：不改变 mini-swe、r53、EVAS 0.8.7 或现有 runner。

## 验证证据

- regression tests：`tests/test_agent_harness_tool_registry.py`。
- clean-room smoke：未执行；此切片未接 runtime。
- 未验证部分：真实 tool dispatch、domain tool semantics、per-tool ablation impact。

## Claim boundary

- 能支持：工具能力边界可以机器检查，领域工具可以先占位而不赋予执行权限。
- 不能支持：任何新工具已经能在正式 evaluation cell 中调用，或工具提升模型表现。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
