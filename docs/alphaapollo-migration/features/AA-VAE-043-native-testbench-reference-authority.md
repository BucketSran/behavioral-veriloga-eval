# AA-VAE-043：Native Testbench 与九-cell 验收

## 思想与代码对应

继续迁移 AlphaApollo 的 environment / verifier 边界，不复制数学 verifier，
也不把最终评分当作公开反馈。Testbench 的公开环境只有 r53 提供的 reference
DUT；隐藏 fault suite 仍只由冻结后的最终评分器读取。无新依赖或第三方代码复制。

- `operations/calibration_pilot/public_validation.py`（v4 下）：严格匹配
  `r53-direct-evas-testbench-reference-v1` 的固定命令、路径和 feedback scope；
  绑定公开 reference DUT 内容摘要，拒绝公开输入/权限漂移和 candidate include
  越界，反馈仅为 `reference_dut_only` 的运行状态/日志，不生成任务正确性分数。
- `mini_swe_vabench.py`：EVAS invocation hasher 使用 harness 指定的绝对
  candidate 根，防止 agent `cd` 后记录成缺失文件。Adapter 另按 telemetry
  framing 重算并核对输入摘要；不把它与 canonical submission digest 混淆。
- 同目录 `run_native_mini_swe.py`、`run_campaign.py` 和 v4 campaign wrapper：
  放行 Testbench 三条件，沿用既有 image、authority absence、freeze 和 final
  join。默认 legacy mini-swe 与旧 sensitivity flag 含义不变。
- `tests/test_agent_harness_native_testbench.py`：公开 authority、reference
  漂移、命令/路径/scope 篡改、include 越界与无分数 observation 回归。
- `scripts/run_v4_r53_clean_room_smoke.py`：Testbench 夹具只从公开合同读取
  source path template、实例/端口/trace 声明，输入恒定为零，不构造 gold 解。
- `tests/test_agent_harness_native_campaign_smoke.py` 和 Evaluator Closure CI：
  扩展为三个 form × 三个 condition，共九个独立 runtime；验证完整分母、
  public authority 有无、最终 sidecar 关联以及 scorer 只读哈希不变。

## RED → GREEN 与证据

公开 Testbench profile 起初被 DUT-only guard 拒绝；加入固定 reference-only
合同后通过。后续负例证明不能复用 DUT public command，也不能绕过 include
绑定。三条件 wrapper 从拒绝 Testbench 到可冻结计划，其他不支持配置仍拒绝。

首次 Docker 运行揭示 smoke 夹具未逐字使用公开合同的 `./dut/{artifact_path}`
模板：公开仿真能运行，但最终 source binding gate 拒绝。只修正夹具生成器并
补回归，没有改 evaluator/release，也没有依据 hidden fault 优化候选行为。
失败运行目录保留。第二次真实 Docker/EVAS：**3 passed in 25.21s**。独立审查
后新增 wrong-candidate 校验，实际公开 Testbench 测试进一步暴露相对 cwd 的
telemetry 根错误；`cd work` 单测 RED→GREEN 后，最终两个 public adapter
场景及九-cell smoke 共 **5 passed in 44.06s**。九条均为预期的
`behavior_failure`，不是模型成绩；独立复审无剩余代码阻断。

本地 ignored evidence：
`benchmark-vabench-release-v4/reports/native-nine-cell-cgoDPgBp/cwd-bound/test_r53_docker_all_native_thr0/`。
`smoke-evidence-index.json` SHA-256：
`c4fc92a2fc650ad7cae55213f07a586a75abd012729c7c30d1409d2c256231d5`。
原始私有日志、提交与评分文件不进入 Git。

## Claim boundary

本切片仅补齐 native 三种 form 的连通性；不证明全 r53、真实模型质量、
新旧 backend 全量 parity 或 Spectre 一致性。EVAS 仍为 0.8.7、score authority
仍为 `development_only`。自动 retry、完整证据导出、Reasoning/Evolution
运行接入和统计结果闭环由后续独立提交完成，不能据此标为已完成。

后续状态：上述运行功能已分别由 AA-VAE-044–049 实现并验证；本篇仍只证明
Testbench 切片自身的范围。当前状态以 `plans/current-plan.md` 为准。
