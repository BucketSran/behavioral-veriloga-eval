# AA-VAE-082 — 评分与启动器的依赖提取

日期：2026-09-09。这是已存在能力的责任调整，不是新增 agent 或评分算法。

## 为什么改、参考什么

原评分器通过 `importlib` 加载整个 `run_campaign.py`，只为复用提交校验、
replay 和统计；读取 native backend 配置又导入整个 `run_native_mini_swe.py`。
读证据的模块因此依赖启动运行的模块，增加了理解、隔离测试和后续演进的成本。

借鉴用户指定的 AlphaApollo-v3-dev 的分层方向：workflow 负责装配，runtime/
environment/tool 各自持有能力契约；并使用其
[write-clear-code 方法](https://github.com/AndrewZhou924/AlphaApollo-v3-dev/tree/6d1be0e1fe3b5235b10554b0ab2ad5fef06e8aae/.agents/skills/write-clear-code)
检查依赖闭包、兼容调用者和源码身份。引用固定 commit，避免把未来设计当成当前事实。

这不是把 vaEVAS 改为 robotics 的子项目：领域不同，可复用的是职责边界。
本次只移动并调整我们自己的代码，不复制外部业务实现、不新增依赖包。

## 代码具体改在哪里

下列文件都在
[`operations/calibration_pilot`](../../../benchmark-vabench-release-v4/operations/calibration_pilot/README.md)：

| 所属文件 | 持有能力 | 兼容入口 |
| --- | --- | --- |
| [submission_contract.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/submission_contract.py) | 候选路径、提交 schema、include 校验、artifact gate | `run_campaign` 原函数名直接 re-export |
| [campaign_telemetry.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/campaign_telemetry.py) | output-limit 与 EVAS/candidate 统计 | `run_campaign` 原函数名直接 re-export |
| [native_contracts.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/native_contracts.py) | backend/OneShot tool profile、声明的信息面 | launcher 原私有函数名及 runner 的 surface 函数 |
| [final_replay.py](../../../benchmark-vabench-release-v4/operations/calibration_pilot/final_replay.py) | 执行 cwd/env/watchdog、EVAS 身份与 replay 生命周期 | runner 保留 facade、同一异常类及 `_run_trusted_replay` 注入点 |

评分器直接导入所有者。native 运行器、Evolution 和 final authority 的源码哈希清单
覆盖新文件。公开波形的运行身份补入提交契约；回读时兼容旧记录的原哈希投影，
不能删除新来源后仍冒充与新 profile 一致。没有修改旧 manifest、trajectory 或 sidecar。

```python
# 结构示意；不是新增一套循环
gate = submission_contract.submission_artifact_gate(runtime)
frozen = result_protocol.snapshot_submission(runtime, gate)
replay = final_replay.run_trusted_replay(runtime, command, timeout, evas, frozen)

# 已完成 native 运行：只核对已有结果，不再次调用上面的 replay
row = score_campaign.read_native_cell(runtime, scheduled_cell, campaign_file_sha256=sha)
```

这里的普通 replay 兼容入口仍接受历史调用形式；profile-bound 路径依旧要求 context、
profile 与冻结提交齐备，并持久保留 single-use reservation。伪代码不授予运行权限。

## 验收与证据

- 先加回归，初始 **2 failed / 1 passed**：缺少明确 owner，评分器仍动态加载 runner。
- [依赖回归](../../../tests/test_agent_harness_scoring_dependencies.py)：旧导入对象一致，
  嵌套提交校验、任意 cwd CLI、独立解释器加载/回读 native 结果；源文件字节不变。
- [终评回归](../../../tests/test_agent_harness_production_final_replay.py)：共享异常与
  reservation、原执行注入点、新来源 drift 在 judge 前被拒绝。
- [波形回读回归](../../../tests/test_agent_harness_waveform_integration.py)：新/旧来源
  投影均可读取，来源篡改与 profile 不符则拒绝；不模拟成新的仿真结论。
- 实际测试计数、免费 Docker smoke、独立审查与本机历史资产限制统一记录在
  [verification log](../../../logs/verification-log.md)，不在多个文档重复维护状态。

## 不变与剩余边界

r53、EVAS 0.8.7、legacy 默认、三条件、预算、输出 schema、评分语义及 public/final
隔离不变。新运行源码身份哈希会变化，这是准确记录实现版本，不是改评分标准。

没有证明吞吐提升、模型效果提升、防 hack 完备性或 Spectre 等价性。没有付费调用。
mini-swe bridge 仍被共享统计/声明依赖；batch-attempt 与部分公开执行仍使用原编排
模块。后续按具体需求继续提取，不为了目录美观重写整个仓库。
wave-mcp/debug 工具建设是后续独立工作，本次没有新增查询工具或 MCP 服务。
