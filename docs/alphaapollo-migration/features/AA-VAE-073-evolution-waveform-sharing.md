# AA-VAE-073：Evolution 的公开波形反馈与共享

日期：2026-09-01；基线 `025276c6fc`；r53 / EVAS 0.8.7 不变。

## 为什么这样接

复用已有的 AlphaApollo 风格多分支、多轮候选生命周期，以及 vaEVAS 已有的隔离
公开仿真工具。分支保持 NoEVAS：它们可以通过 Bash 写候选、检索声明的资料，
但不能直接调用最终 checker，也不能随意启动协调器的 EVAS。

一次候选的流程为：

`branch proposal → sealed candidate → coordinator public waveform → round barrier`

下一轮只收到上一轮已封存的候选代码及其绑定的公开反馈。整个 Evolution 最后
仍然只选择一个候选，冻结后做一次严格 EVAS final replay。最终 verdict 和 hidden
内容不进入下一轮；不按最终分数重新选候选或重试。

## 代码对应

- `operations/calibration_pilot/run_native_evolution.py`：新增 opt-in 参数
  `public_waveform=True` 和 `evolution_extension_config()`。默认未开启时不改变
  原有 public-validator 配置。启用后冻结扩展、公开预算和执行模式。
- `_SharedPublicValidator`：复用 `public_waveform.IsolatedPublicWaveformExecutor`，
  使用独立 Agentic 协调器上下文。每个候选消耗原来的一个公开验证额度，执行一次
  波形仿真，不再额外执行旧的 validator。
- `_public_feedback_for_prior_candidate`：复用已有候选 store 与 receipt 恢复链路；
  检查候选/上下文/事件、固定 profile、实际公开任务树、命令、反馈范围和镜像身份。
  自洽地重算一组伪造 receipt 哈希不能替代这些实际输入绑定。
- `tests/test_agent_harness_evolution_waveform.py`：NoEVAS 分支、额度耗尽、公开
  profile 漂移、同轮不可见、下一轮反馈和重算哈希后的伪造输入回归。

这些路径均以仓库根下 `benchmark-vabench-release-v4/` 为起点；`runners/agent_harness`
中的通用 Evolution reducer、调度/选择规则、memory schema 和 final scorer 未重写。
复用工具中的 bounded waveform summary，不把原始 CSV、私有 checker 或 final score
塞入共享记忆。公开仿真成功只是 runtime feedback，不代表任务正确。

## 验证与局限

新增 API/实际 executor 接口与旧回归通过；独立审查进一步复现了“重算 receipt
哈希后可伪造公开命令/任务输入”的漏洞。补充实际输入绑定后，四类篡改均拒绝。
本模块与原 Evolution/extension/batch 回归：65 passed / 1 optional skip。

组合入口、完整工具使用证据与真实 Docker/EVAS（模拟模型回复）的验证另见
AA-VAE-075。没有修改 EVAS、benchmark、候选选择分数或执行付费模型实验。
波形摘要是否能提升真实模型的修复能力，仍是后续实验问题。
