# AA-VAE-052：预算内六单元试跑与完整结果分母

日期：2026-08-30。范围：独立 opt-in pilot，不替换默认 benchmark CLI。

## 思想与来源

沿用 controller/environment/state/trajectory/final-judge 分层，不再实现一套
agent。新增的是可信 host 的实验调度：在模型调用前冻结设计与计费约束，
把运行预算中止和模型表现分开。这是 vaEVAS 工程补充，不是复制 AlphaApollo
的模型训练或 Evolution 代码；本轮不启用跨候选共享记忆。

## 代码映射

- `operations/calibration_pilot/run_deepseek_pilot.py`：metadata-only API
  preflight；冻结 family029 的 DUT/bugfix/Testbench × 两个 native backend；
  按 form 交替 backend 顺序，串行创建独立 client/runtime。
- 复用 `pilot_credentials.load_pilot_key`、`build_campaign.build_campaign`、
  `deepseek_budget.DeepSeekPilotBudget/BudgetedDeepSeekClient`、
  `run_campaign.run_cell_preserving_failure`、`score_campaign.read_native_cell`。
  不修改这些模块，不重复执行 final judge。
- `tests/test_agent_harness_deepseek_pilot.py`：metadata 错误/脱敏、计划冻结、
  重入拒绝、真实 Docker/EVAS + 免费 HTTP、未知费用停止、八次/cell 上限。
- `tests/test_agent_harness_ci_gate.py` / evaluator-closure workflow：路径触发
  和三种真实 Docker 场景进入现有免费 CI，不使用 provider secret。

上述 operations 路径均位于 `benchmark-vabench-release-v4/`。

## 新增证据

私有输出目录保存 `pilot-manifest.json`、两份 `campaign.json`、逐项
`execution.jsonl`、预算 `budget.jsonl` 以及最终 `pilot-index.json`。
index 始终保留六行：正常完成、运行中止、未启动；中止/未启动 score 为 null。
已启动项引用并校验原有 native trajectory、freeze、score sidecar，未启动项
不伪造 native receipt。公开日志不包含 key、账户余额、模型内容或终评细节。

每次 HTTP 前持久化最坏费用预留；只有合法 terminal usage 才核减。
单任务调用上限允许下个任务继续；未知请求费用/全局余额不足则停止后续请求。
index 中金额是保守上界，不是供应商账单。完整分母不等于六项均已完成。

## 边界

只有 main 协调者执行一次有界 live schedule；不按终评分数重试/扩大样本。
CLI 拒绝脏 source tree 和已有输出，绑定代码 commit、Docker image ID、EVAS
identity、campaign hash 与发布 manifest。它不是抵御同用户恶意主机进程的
安全边界；进程被强杀或磁盘失败时可能只有 write-ahead journal，不可冒充
完整结果或创建新预算原地恢复。

固定 r53 + EVAS 0.8.7；不改 legacy、训练、Evolution、Spectre 或任务内容。
free fixture 验证工程连通，不证明真实模型效果；live 结果另记，始终仅为
development-only 小样本工程试跑，不是 baseline 复现或优劣结论。

## 2026-08-31：冻结费用上限接线修复

`execute_pilot` 现在把 manifest 的 `cap` 显式传给已有
`DeepSeekPilotBudget`，避免较小冻结额度被 guard 的默认额度替代。
guard 算法、CLI 默认额度和 `freeze_pilot` 参数均未改变；没有新增 cap CLI。
同一测试先证明旧路径会放行 stub HTTP，再验证 CNY 0.01 时零 HTTP、
journal/index 同额度、六行分母与未启动记录保留。新增两种 cap 漂移回归
确认参数与文件不一致时在 native/HTTP 和运行日志创建前拒绝；这是已有校验，
不是第二项运行时修复。仅合成 fixture 修改测试输入，不允许修改已运行的
冻结 manifest 或重置历史预算。本切片不读取凭据、不调用真实服务；
精确免费验证与本地提交状态见 verification log。

## 2026-08-30：真实调用结果（独立于免费 fixture）

已执行一次：[脱敏审计](../experiments/deepseek-pilot-20260830.md)。16次 HTTP，
两个 DUT 单元分别因八次上限、SSL 握手失败后的未知费用保护而中止，后四项
未启动；零项最终评分。费用保守上界 ¥3.420315，不是账单。证明真实 API
接通和预算失败关闭，不证明六单元已评分或任一 backend 更好；没有自动重跑。
