# AA-VAE-059：独立的合成训练样本契约

日期：2026-08-31。状态：synthetic projection/validator；不导出真实轨迹、不训练。

沿用 AlphaApollo 将推理轨迹与未来 SFT/RL 分开的架构思想，但不把 vaEVAS reviewer
export 或最终评分产物改名成训练数据。没有引入训练框架、GPU、模型权重或依赖。

新增 `runners/agent_harness/training_export.py`：

- `build_training_export(source, split_manifest=..., mode="sft"|"rl")`：严格检查合成
  来源/许可/provider-use/项目声明、split、公开事件内容/hash、终止和标签契约。
- `validate_training_export(document, source=..., split_manifest=...)`：从相同输入
  重建，拒绝改写输出；不是只检查一个可以重新计算的 export hash。

SFT 保留顺序 messages，assistant loss=true，环境/用户上下文 loss=false；环境
反馈不是 assistant target。budget stop 不充当正例。RL 只接受专门声明的 public
validation reward 和 generator identity，不把 EVAS exit=0 自动当 reward；
这只是训练数据契约，不是 rollout collector、replay buffer 或训练器。

当前只接受固定 synthetic release 和独立 synthetic task namespace；heldout
不能导出作训练，r53/v4 benchmark 身份拒绝，split 重复/交叉和未知结构拒绝。
事件数、身份/来源声明长度、事件内容和 split 任务数量均有上限，非有限数字拒绝。
版本、source、split 和 normalizer 身份随结果保存；`exporter_contract_sha256`
哈希的是声明的导出契约，不冒充实现代码 hash。结构检查不能证明操作者刻意伪装的文本无泄漏；
本轮依靠手工合成 fixture，不声称关键词黑名单能完成真实 corpus 去污染。

测试：`tests/test_agent_harness_training_export.py`。覆盖 content/hash 错配、
rehashed 导出篡改、未知字段、真假来源、heldout/split、SFT mask/终止、RL authority。
最终测试和审查 evidence 见 `logs/verification-log.md`。

## 后续边界

真实 native trajectory → 训练样本 adapter、action mask/candidate lineage 与预算
重建、按内容去重/跨 split 污染检查、真实数据与 provider 条款审查、checkpoint
冻结和训练后独立评测均未实现。当前 fixture 结构不是 canonical harness event
chain，不冒充已完成真实轨迹训练导出。r53 final/test、gold、certified faults 和
trusted sidecar 始终不得进入训练/奖励/后续模型 memory。
