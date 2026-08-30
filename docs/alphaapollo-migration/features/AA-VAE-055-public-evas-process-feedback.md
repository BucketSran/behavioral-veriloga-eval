# AA-VAE-055：公开 EVAS 进程反馈与操作计数

## 为什么做

前次 pilot 诊断发现：`evas simulate ... | tail` 的 Bash 返回码可能为 0，
但 EVAS 本身已经失败。模型只有普通文本输出时，容易把管道成功误读为仿真成功。
此外，`evas --help`、`evas --version` 不应该被描述成一次成功仿真。

延续 environment-owned observation 的迁移原则：执行器传递公开诊断并注明信任边界，
policy 负责传递，controller 保留权限和终态，final judge 不参与改进反馈。
本次复用现有 Bash 包装器、typed observation 和事件链，没有复制外部代码、
新增工具、修改 EVAS，也没有强制改变 Bash 的 pipefail 语义。

## 模型实际看到的变化

原 Bash `returncode` 保持不变；native Agentic 的 observation 增加 `public_evas`：

- `schema_version=vaevas-public-evas-feedback-v1`，只覆盖当前 action 的
  `captured_sandbox_markers`。顶层、每条记录和计数均标记 `authenticated=false`；
  反馈/计数的 `authority=diagnostic_only`，不是可认证的执行审计。
- 每次调用记录 `invocation_id`、`operation`、`status`、`returncode` 和调用开始时
  candidate tree hash。正常包装器根据 argv 报告 operation，不解析模型 Bash
  字符串；模型也能伪造同格式报告，所以不能据此证明 EVAS 确实执行过。
- `help/version/other/unknown` 与 `simulate` 分开；`simulate --help` 是帮助查询。
  `reported_simulation_status_counts` 只汇总声称为 simulate 的标记结果。
- 最多返回末尾 16 条调用明细，`omitted_invocations` 显式计数；operation summary
  汇总本次捕获中的标记记录。输出丢失/截断标 `capture_complete=false`；
  未看到结束记录时不能编造退出状态。非法/缺失 END 状态为 unknown。
- `task_correctness=not_evaluated`：进程零退出既不证明有效波形，也不证明任务正确。

mini-swe 原格式化器只消费 output/returncode；native adapter 将有内容的结构化
反馈显式渲染到下一轮 tool message。没有 EVAS 调用且捕获完整时，不额外渲染
空反馈块。Reasoning 的 native-tool 和 strict-JSON 两种格式都传递 canonical
observation。无旧 action 状态冒充新 action，历史消息也不被回写。

## 对照代码

`calibration/` 指 `benchmark-vabench-release-v4/operations/calibration_pilot/`。

| 边界 | 代码位置 | 改动 |
| --- | --- | --- |
| 执行与有限捕获 | `calibration/mini_swe_vabench.py::VaBenchBashEnvironment` | opt-in sandbox 标记报告、当前命令截取、完整性与有界诊断 |
| 共用诊断计数 | 同文件 `summarize_evas_operations`；`calibration/run_campaign.py::summarize_evas_invocations` | help/version 与 simulate 报告分开；每 cell 只读 score row 隔离保留 `untrusted_operation_summary` |
| typed observation | `runners/agent_harness/backends/mini_swe.py::_legacy_output_payload` | 保留结构化字段，复用 observation hash 与原有事件 join |
| 策略与配置 | `calibration/run_native_mini_swe.py::{run_prepared_native_mini_swe,NativeMiniSwePolicy}` | native Agentic 启用；manifest 冻结反馈版本；mini-swe 请求显式传递 |

旧 `calls_executed/calls_succeeded` 保留历史语义：EVAS 包装器标记记录的汇总，
**不是仿真计数，也不是不可伪造的真实进程计数**。
历史无 operation 的记录不从 shell 字符串反推新计数，也不改写旧结果。新增分类是
per-cell/selected-attempt 诊断；没有新增跨 attempt 预算，也没有把旧汇总表改成
“所有 attempt 的仿真总数”。Legacy 默认仍关闭该反馈，No-EVAS/OneShot 不获得
EVAS 权限；普通无 EVAS action 的 legacy/native 文本差分仍保持原有约束。

## 安全与 claim boundary

包装器可被模型在公开 sandbox 中观察/绕过，其 marker 不是不可伪造的证明。
这条反馈用于可读诊断，不参与权限授予、预算扣减、最终分数或成功标签。
绕过包装器、输出截断、无 START 的记录都可能造成漏计，伪造可能造成多计；
不能宣传为防作弊计量或可靠下界。可信逐次计量需要单独的隔离执行接口。
公开字段不复制私有 nonce、wrapper command 或最终 checker 内容。

候选 hash 是调用开始时状态，不证明整个仿真期间 candidate 未变化，也不证明
任意 netlist 实际使用了该 candidate。严格 public-validator 的前后 drift 检查
仍是独立路径。这次没有激活 waveform summary 或改变 validation/final-test 分离。

## 验证

- `tests/test_agent_harness_public_evas_feedback.py`：管道失败、help/version、
  实际 argv、截断、异常 END、超时、明细上限、legacy/no-EVAS、真实 Docker EVAS。
- `tests/test_agent_harness_reasoning_integration.py`：三种 native policy/format
  的真实下一轮请求、manifest 和只读 score row；最终评分内容不进入模型。
- 既有 mini-swe differential 与完整 harness 回归；免费六 cell Docker/EVAS
  闭环复验。精确 RED/GREEN、审查与 smoke 结果见 verification log。

这是 harness 可观测性修复，不是模型能力提升证据。r53、EVAS 0.8.7、旧 pilot
证据不变；没有读取凭据或发起付费重跑。
