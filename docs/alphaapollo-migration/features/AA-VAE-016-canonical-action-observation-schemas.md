# AA-VAE-016：Action/Observation canonical wire schema

## 功能标识

- ID：`AA-VAE-016`
- 名称：Action/Observation canonical wire schema
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 canonical protocol slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 的公开架构把 reasoning 过程保留为可复查 trajectory；不同模型产生的
  候选和反馈必须能进入同一种后续演化状态。
- coding-agent 的公开共同模式把 provider 输出先归一化为内部 action，再由受控
  environment 执行并产生 observation。
- 对 vaEVAS 而言，统一 wire shape 是后续比较 mini-swe、单轨 reasoning 与多模型
  evolution 的前置条件；这是对公开模式的适配推断，不是复制任一项目的代码。

## vaEVAS 适配决策

- 采用严格的 `vaevas-action-v1` 与 `vaevas-observation-v1` JSON schema；顶层未知字段
  一律拒绝。
- `AgentAction.to_document()` 与 `Observation.to_document()` 是可信 serializer，返回
  与内部 frozen state 解耦的 JSON-compatible 文档。
- `arguments_sha256` 与 `payload_sha256` 由可信 serializer 所在的 state 层按键排序、
  UTF-8、紧凑 JSON 计算；输入 mapping 的插入顺序不影响 hash。
- schema 只检查 wire shape 和 digest 格式，不能重新计算 digest；哈希真实性仍由
  trusted constructor/serializer 与后续 trajectory join 负责。
- `tool_name` 保持非空字符串，而不是在 schema 中枚举领域工具。可调用性、条件权限、
  budget 与状态副作用属于后续 capability registry 的权限决策。
- 拒绝非 object 的 action arguments/observation payload、非字符串 JSON object key、
  NaN/Infinity 和非非负整数的 budget delta，避免构造出无法规范序列化的对象。
- 本切片不实现 XML/regex parser，不实现 provider-native/strict JSON normalizer，也不
  接入 production runner。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-action-v1.schema.json` | 定义严格 canonical action wire shape | schema |
| `schemas/vaevas-observation-v1.schema.json` | 定义严格 canonical observation wire shape | schema |
| `runners/agent_harness/state.py::_freeze_json` | 拒绝非规范 JSON key/number | state |
| `runners/agent_harness/state.py::AgentAction.to_document` | 输出 detached canonical action document | state |
| `runners/agent_harness/state.py::Observation.to_document` | 输出 detached canonical observation document | state |
| `tests/test_agent_harness_protocol.py` | 锁定 schema、detachment、hash 与非法输入行为 | tests |

## 数据与状态变化

- 输入：trusted harness 构造的 action arguments 或 tool observation payload。
- 中间状态：递归 frozen JSON object 与 canonical SHA-256。
- 输出：严格、detached、JSON-compatible action/observation document。
- 新增 schema 字段：没有超出 Phase 0 state 对象的新语义字段；本切片把现有字段冻结为
  machine-checkable wire contract。
- backward compatibility：production runner 尚未导入 `runners.agent_harness`，因此
  当前执行路径无行为变化；后续 mini-swe adapter 必须做旧/新 deterministic fixture
  等价回归。

## 验证证据

- regression tests：`tests/test_agent_harness_protocol.py` 覆盖 detached document、两份
  schema、额外字段拒绝、mapping 顺序无关 hash 与非规范 JSON 输入拒绝。
- regression safety：`tests/test_agent_harness_controller.py` 继续覆盖 Phase 0 controller
  合同。
- clean-room smoke：未执行；本切片未接入 production runner，既有 r53 smoke 不能
  被冒充为新协议的 runtime 证据。
- evidence/manifest hash：不适用；没有生成实验结果。
- 未验证部分：模型输出 normalization、tool descriptor/registry、backend identity、
  validation/final-test profile、evolution manifest、memory/candidate lineage schema。

## Claim boundary

- 能支持：`AgentAction`/`Observation` 原型现在有严格、稳定、可机器校验的 wire shape，
  canonical payload hash 不受 mapping 插入顺序影响。
- 不能支持：backend parsing 正确性、unknown-tool 拒绝、mini-swe 行为等价、
  AlphaApollo reasoning/evolution 收益、正式 r53 评分链路已经迁移。
- 本功能没有修改 EVAS 代码、版本、compiler/simulator/ABI 或 packaging，不触发
  Spectre parity gate。
