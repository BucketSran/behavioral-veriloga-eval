# AA-VAE-053：统一公开操作契约

## 问题与思想

离线检查发现 Reasoning 的 provider 请求没有包含 Bash workspace 和
`vabench-submit` 契约；脚本化测试预先知道提交命令，因而没发现问题。
这不是模型能力证据。沿用 environment 定义操作语义、policy 只适配格式的
迁移原则，本次复用 vaEVAS 已有契约，不复制 AlphaApollo 代码。

## 实现位置

- `operations/calibration_pilot/run_native_mini_swe.py::_interactive_prompt`：
  复用 Agentic/No-EVAS 契约，说明每条命令从 `/workspace` 的新 shell 开始、
  `cd` 不跨调用持久化，并要求配置格式中的单个 Bash action。
- 同文件 `run_prepared_native_mini_swe`：Reasoning 初始公开 observation
  包含上述契约；native mini-swe 使用同一公开文本。No-EVAS 不再收到宣称
  可以执行 EVAS 的 system prompt。OneShot 保留独立输出协议。
- `tests/test_agent_harness_reasoning_integration.py`：检查实际 provider
  请求，覆盖两种 interactive 条件及 mini-swe / Reasoning native / strict
  JSON 三种组合；检查工作区、提交、权限说明及 final sentinel 不泄露。
- `tests/test_agent_harness_mini_swe_differential.py`：逐字断言初始提示词的
  两处预期差异，其余请求历史仍全量相等，继续检查提交字节和 hash。

上述 operations 路径位于 `benchmark-vabench-release-v4/` 下。
legacy 实现与默认入口未改；native opt-in 的提示词变更必须记入差分实验。

## 验证及边界

先观察两种 Reasoning 格式的实际请求缺失契约（2 failed），最小修复后
2 passed。后续条件矩阵曾因测试目录撞名失败，修复测试设置后，完整定向
回归为 44 passed、1 opt-in skipped；不能把目录撞名记为功能 RED。
免费 Docker/EVAS 验证与独立审查见 `logs/verification-log.md`。

证明的是模型能看到真实操作契约，不证明模型会遵守或能完成任务。
不修改 r53、EVAS 0.8.7 或旧 live evidence；无付费请求。可选调用额度是
下一独立切片 AA-VAE-054，不在本修复中冒充已完成。
