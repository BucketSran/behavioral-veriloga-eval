# AA-VAE-069：旧/新 mini-swe 工作流对照协议

- 日期：2026-08-31；主线程独占写入/集成/Git。
- 状态：离线协议和有界审计已验证；真实实验未启动。
- [计划](../../../plans/legacy-native-comparison-protocol.md)；
  [中文协议](../experiments/legacy-native-comparison-20260831.md)；
  [蓝图与六单元 tracker](../experiments/legacy-native-comparison-20260831.json)。

## 思想来源与适配

沿用 AA-VAE-038/053/055 与既有迁移主线：AlphaApollo 提醒我们把多轮交互、反馈和
状态作为实验对象；coding-agent 的可替换性需要在真实请求和环境边界上检查。
本切片是 vaEVAS 自己的对照协议，不是新移植 AlphaApollo 代码，也不是新文献比较。

同一 mini-swe 模型适配层不代表相同工作流。旧/新有操作说明、格式恢复、多动作、
公开诊断和截止行为差异，因此先描述整套工作流，不声称纯 controller 因果收益。
固定一个已有工程暴露的 family、三种 form、一个 Agentic 条件、六个独立单元；
不启动 Reasoning/Evolution/工具/训练扩展。

## 改动与复用

| 文件/符号 | 本次作用 | 层 |
| --- | --- | --- |
| experiments/legacy-native-comparison-20260831.md | 控制/差异、信息审计、预算、结果口径、stop/go 和验收计划 | 协议 |
| 同名 .json | offline-only 蓝图，固定六单元顺序和公开源输入摘要；model/fee/live image 保留 null | 计划数据，非 runner manifest |
| tests/test_agent_harness_comparison_protocol.py | 6个离线约束/源输入检查，2个 opt-in 实际 Docker Mounts/安全字段检查 | 测试 |
| 既有 mini_swe_differential/public_evas_feedback/deepseek_budget/model_call_budget 测试 | 重跑真实控制路径和模拟 provider 边界；不重写 harness | 复用 |

**生产 runner、controller、scorer 没有改动**。不增加 launcher、数据依赖或公共 schema；
JSON 的 blueprint schema_version 只标识这份计划数据，不能授权付费或正式评分。
原始轨迹、私有 checker、真实密钥和镜像示例正文不发布。

## 输入、输出与证据

只读取 r53 manifest/index、三个 public contract/public tree、公开代码/测试，以及
隔离容器的受限字段。公开源文件数量为 DUT3、bugfix4、Testbench3；hash 算法明确
记录在协议/测试中。源文件快照不代表包含 evaluator-declared support 的完整 export。

镜像实测 EVAS0.8.7 和78个安装示例文件；只发布数量/hash，不声称完整镜像审计。
Docker 两项检查分别覆盖 shared environment 的旧/新 structured-feedback 设置，
实际验证精确 bind 源/目标、task只读、submission/work可写、禁网、只读root、cap-drop、
image ID 和 synthetic私有 sentinel 不可见。没有模型、仿真或最终 judge 调用。

TDD 首个测试因蓝图不存在 RED（1失败）；补齐后离线新文件6项通过。
聚焦差分/预算/反馈/导航/CI测试115通过、3跳过；新增Docker审计单独2通过、6未选。
具体命令、静态检查、独立审查及发布状态见 verification-log。

## Claim boundary / 下一步

支持：比较目标和有意差异可人工审查，公开源输入可重检，现有 synthetic request
差分和真实共享环境挂载有有界证据。它不是完整三题 export/backend smoke，也不是
新运行防火墙或已完成的模型效果实验。

真实模型/解码身份与新费用授权、legacy/native共同消费保护的集成、完整导出与
实际镜像审计、只读跨backend结果join均为启动前缺口。现有预算client可复用，但
普通legacy CLI没有接入；native ledger也不自动提供该跨backend比较器。
下一安全实现切片是用免费fixture补共同预算和结果join，不改默认backend/评分。
EVAS0.8.7和r53不变；无Spectre触发、真实付费运行或训练。
