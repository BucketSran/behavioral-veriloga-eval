# AA-VAE-054：可选调用额度与可信剩余提示

## 为什么做、迁移了什么思想

先前 DeepSeek pilot 为控成本选择每 cell 八次调用，但 native 策略看不到剩余
次数。调用上限应是实验配置，不是固定 benchmark 规则。沿用 environment-owned
control loop：模型选择动作，controller 掌握可用资源并负责终止，policy 只把
可信状态转换成模型输入。本次复用 vaEVAS 的 ledger/controller/attempt 设施，
没有复制 AlphaApollo 代码，也没有增加第二套 agent loop。
缺失 Bash/submit 操作说明是另一项独立修复，已在 AA-VAE-053 完成。

## 明确的运行语义

- 普通 campaign 的 `--native-model-call-limit N` 接受任意正整数；未配置时不
  增加按调用次数停止的规则，也不添加 budget 字段或提示。legacy 默认不变。
- 每次进入 `policy.act` 前由 controller 预留一次 logical call；失败、无效输出
  也计入。模型看到 `limit / call_number / remaining_after_this_call`，最后一次
  收到 remaining=0，但其合法动作仍然执行，可以显式提交。
- 耗尽后没有下一次调用。没有提交则记录 `budget_exhausted / model_call_limit`，
  不自动冻结或评分，score 为 null；不会与 deadline 同时触发时偷跑终评。
  已发生的独立终态错误保留真实原因，不为统一标签而改写成 budget stop。
- 新 infrastructure attempt 继承累计用量，不退回已预留额度。只有明确发生在
  controller 之前且 provider trace 为空的 sandbox startup failure 可以记零新增。
  缺失/非法计量降为 `model_call_accounting_unknown` infrastructure failure、
  score=null，禁止重试；不能保留成功状态或把未知当零。
- logical call 不是 HTTP attempt：一次 admitted call 可能在 RPC 前失败，也可能
  包含已有 transport retry。费用、HTTP 限制、output-token cap、wall time 都独立。
  DeepSeek pilot 保留默认八次，但预算对象和 freeze API 接受其他正整数。
- OneShot 仍只有一次输出式生成；native mini-swe、Reasoning native-tool/strict-JSON
  都显示当前额度。Evolution 仍使用其独立 branch budget，不新增 campaign flag。

## 对照代码结构

下表 `calibration/` 简写为 `benchmark-vabench-release-v4/operations/calibration_pilot/`。

| 边界 | 具体代码 | 改动 |
| --- | --- | --- |
| 资源与控制 | `runners/agent_harness/budget.py::{BudgetLedger,model_call_budget_text}`；`controller.py::EpisodeController`；`state.py::EpisodeContext` | 预留、可信剩余状态、Nth action、显式耗尽、累计 offset |
| 模型适配 | `calibration/run_native_mini_swe.py::{NativeMiniSwePolicy,_OneShotModel,run_prepared_native_mini_swe}`；`runners/agent_harness/backends/reasoning.py` | 每次实际请求注入最新额度；无 cap 保持原请求 |
| 配置冻结 | `benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py`；`calibration/run_campaign.py` | 正整数/非 legacy 校验；冻结 CLI/config 并拒绝漂移 |
| attempt lineage | `runners/agent_harness/attempt_sequence.py`；`calibration/run_native_attempts.py` | 失败也计数、fresh attempt 不重置、未知计量禁止成功/重试 |
| 证据与结果 | `runners/agent_harness/trajectory.py`；`calibration/{native_episode,score_campaign,result_ledger}.py` | event 语义校验；manifest/request/outcome/receipt/row 绑定；安全导出 |
| 独立费用保护 | `calibration/{deepseek_budget,run_deepseek_pilot}.py` | 共享 guard/freeze 接受 N，仍保留费用保护与完整六行分母 |

## Trajectory 与结果记录

每次预留增加 harness-only `model_call_admitted` 事件；model-visible request
使用当前 observation，而不是把私有 event 原样暴露给模型。终态记录：

```json
{"limit": 5, "used_before_attempt": 2, "admitted_in_attempt": 3,
 "used_total": 5, "remaining": 0}
```

只读 scorer 检查计数、累计 offset、冻结配置和证据 join；重算 hash 不能绕过
顺序/数值校验。预算证据缺失、伪造零上限、超额、删改 admission 或未知成功
状态均有回归。result ledger 保留配置和计量；censored/null 不变成模型失败零分。
这些是受信 harness 的一致性检查，不是针对任意恶意主机的密码学证明。

## 测试与 claim boundary

- `tests/test_agent_harness_model_call_budget.py`：N=1/2/5/11、最后一次提交、
  最后一次普通动作、失败预留、累计 offset、deadline 冲突和 rehashed 伪造。
- `test_agent_harness_reasoning_integration.py`、`test_agent_harness_native_conditions.py`：
  两个 interactive 条件 × 三种策略格式的实际请求，OneShot、CLI/API 配置和 score join。
- `test_agent_harness_attempt_{sequence,integration}.py`：完整 receipt 重建、零新增
  startup、跨 attempt 无退款、计量未知时降级和拒绝伪造成功。
- `test_agent_harness_{deepseek_budget,deepseek_pilot,result_ledger}.py`：共享费用边界、
  非八次参数、真实 Docker/EVAS 配免费 HTTP、完整分母和 null-score 导出。

精确 RED/GREEN、最终完整回归和免费 smoke 记录见
[verification log](../../../logs/verification-log.md)。没有调用付费模型、读取凭据、
改写旧 live evidence 或修改 r53/EVAS 0.8.7。测试证明资源/证据协议可用，不能证明
给定 N 足够完成真实任务，更不能据此声明 Reasoning 优于 mini-swe。
