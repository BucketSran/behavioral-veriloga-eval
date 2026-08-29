# AA-VAE-017：Fail-closed proposal normalization

## 功能标识

- ID：`AA-VAE-017`
- 名称：Fail-closed provider-native / strict JSON proposal normalization
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 proposal-normalization slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 的公开推理结构需要把不同模型产生的动作放入同一种 trajectory 状态，
  否则多模型 candidate/evolution 无法做公平比较。
- coding-agent 的公开共同边界是“provider syntax → internal action → environment
  execution”；解析不能和 tool execution、candidate mutation 或 verifier authority
  混在一起。
- vaEVAS 现有 mini-swe 路径已经严格解析 provider `tool_calls` 中的 JSON object
  arguments；legacy artifact 路径仍含 fenced/marker/猜测型 regex fallback。前者是
  行为参考，后者不能成为新的 formal action protocol。

## vaEVAS 适配决策

- 新增单一 `normalize_proposal()` 边界，同时接纳 exactly-one provider-native
  function call 或 strict standalone JSON proposal。
- 模型仅可提供 `tool_name` 和 `arguments`。`action_id`、`source_backend`、
  `candidate_tree_sha256` 以及允许的 tool name 集合由 trusted `ProposalEnvelope`
  注入；arguments digest 由 `AgentAction` 重新计算。
- native transport 可带已有 provider 格式中的可选 `id` metadata；normalizer 校验它是
  非空字符串但不把它复制到 canonical Action。真正的 action ID 仍由 trusted
  envelope 注入，其他额外字段继续被拒绝。
- syntax allowlist 只回答“本次 parser 是否接受这个名字”，不回答条件权限、预算、
  可见性或状态副作用；后四项仍属于待实现的 capability registry。
- 严格拒绝 malformed/fenced JSON、duplicate key、NaN/Infinity、非 object arguments、
  missing/extra fields、zero/multiple native calls、非 function call 与 unknown tool。
- normalizer 只创建 `AgentAction`，不调用现有 `execute_tool()`、不产生 `Observation`、
  不修改 candidate。
- 不直接导入 `run_campaign.py` 或 `mini_swe_vabench.py`：现有解析与 provider/query、
  submit repair、tool execution 耦合，直接复用会把 legacy 宽松行为或生产副作用带入
  通用 protocol。后续 mini-swe adapter 继续复用已有 `BASH_TOOL` 和 environment。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/proposals.py::ProposalEnvelope` | 定义 trusted identity 与 syntax policy | protocol |
| `runners/agent_harness/proposals.py::normalize_proposal` | 把两种 untrusted syntax 归一为 canonical action | protocol |
| `runners/agent_harness/proposals.py::ProposalNormalizationError` | 提供 fail-closed 分类错误 | protocol |
| `runners/agent_harness/__init__.py` | 导出已验证 proposal API | harness API |
| `tests/test_agent_harness_proposals.py` | 锁定等价、伪造与拒绝边界 | tests |

## 数据与状态变化

- 输入：trusted `ProposalEnvelope` 与 untrusted native call sequence/strict JSON text。
- 中间状态：duplicate-safe JSON object、exact-field validation、syntax tool allowlist。
- 输出：一个 canonical `AgentAction`，或带稳定 code 的
  `ProposalNormalizationError`。
- 新增 schema 字段：无；proposal 是进入 `vaevas-action-v1` 前的非持久化输入边界。
- backward compatibility：production mini-swe 仍走现有路径；未修改 provider query、
  bash environment、campaign 或 scorer。

## 验证证据

- regression tests：`tests/test_agent_harness_proposals.py` 覆盖 native/strict JSON
  等价、trusted-field forgery、malformed/duplicate/non-finite JSON、extra/missing shape、
  zero/multiple call、unknown tool 与 trusted envelope identity。
- regression safety：protocol/controller/proposal 三组 harness tests 共同运行。
- clean-room smoke：未执行；normalizer 尚未接入 production runner。
- evidence/manifest hash：不适用；没有生成实验结果。
- 未验证部分：真实 provider adapter、mini-swe old/new equivalence、tool descriptor 与
  capability dispatch、observation normalization、controller integration。

## Claim boundary

- 能支持：两种批准的模型 action 语法可以安全归一到同一个内部 Action，trusted 字段
  不由模型提供，常见歧义/修复路径会 fail closed。
- 不能支持：任何工具实际可执行、capability 公平性、mini-swe production parity、
  reasoning/evolution 效果、正式 r53 evaluation 已迁移。
- 本功能没有修改 EVAS 代码、版本、compiler/simulator/ABI 或 packaging，不触发
  Spectre parity gate。
