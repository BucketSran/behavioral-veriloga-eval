# AA-VAE-038：旧/新 mini-swe 行为差分

## 目标与来源

在增加 AlphaApollo Reasoning/Evolution 之前，先证明哪些行为来自既有
mini-swe，哪些来自新的 controller 协议。沿用迁移主线中的“模型只产生动作，
环境管理执行、终止与证据”原则；本切片没有移植新的 AlphaApollo 代码。

基线：fork main `bc7a36b8b9`；mini-swe-agent 2.4.5；r53 + EVAS 0.8.7 不变。
旧入口仍是 `run_campaign.py` 使用的 `DefaultAgent`；新入口是独立 opt-in 的
`run_native_mini_swe.py`。新增测试使用相同的确定性 provider 响应，各自创建新
workspace，真实运行 model adapter、controller、Bash 和 submission gate。
provider 和最终 checker 是测试替身，不是 hosted model / 模型能力实验。

## 行为差分矩阵

以下测试名均位于 `tests/test_agent_harness_mini_swe_differential.py`。

| 场景 | 旧路径 | 新路径 | 结论 / 验证入口 |
| --- | --- | --- | --- |
| 单动作、非零 Bash 返回、后续修复并提交 | 原样公开反馈，继续下一轮 | 相同请求 messages/tool schema/per-call cap，相同 candidate bytes 和 freeze hash | 一致；`test_single_action_feedback_submission_and_candidate_bytes_match` |
| workspace 不完整时 submit | 返回 `submission_rejected`，允许后续修复 | 同样不终止，可修复后提交 | 一致；同上 `reject_first=True` |
| 完整 submit 后的响应 | 不再调用 provider | 不再调用 provider；只对冻结提交终评一次 | 一致的停止边界；同上。仅新路径在该测试中接 fixture final checker |
| 缺工具、坏 JSON、未知工具、非 object 参数、非字符串 command | `FormatError` 重提示；无连续格式错误次数上限，仍受 wall time 约束 | 单次拒绝，不重试，不执行，不评分 | 有意不同；`test_format_recovery_is_legacy_only_and_native_is_protocol_failure` |
| 同一 response 多个 Bash actions | 顺序执行，成功 submit 中止后续 action | 整个 proposal 在执行前拒绝 | 有意不同；`test_multi_action_is_legacy_sequential_but_native_rejected_before_any_dispatch` |
| `finish_reason=length`，但 Bash 参数完整合法 | 记录 telemetry，继续执行 | 同样记录并继续 | 当前一致；`test_valid_bash_at_provider_output_cap_remains_telemetry_in_both_loops`。不能误写成所有 agent 路径都会以 `model_output_limit` 终止 |
| provider timeout/API/context 异常 | `DefaultAgent` 写轨迹后抛出，由外层 campaign 分类 | 不重试，以未评分 `infrastructure_failure/backend_failure` 收束，私有事件保留原异常类型 | 分类粒度不同；`test_provider_failures_are_not_model_protocol_rejections_or_scores` |
| provider 返回时已经过 deadline | 本轮动作仍可能执行，下一轮才检查 wall time | 丢弃迟到动作；完整 workspace 冻结评分，不完整不评分 | 有意更严格；`test_late_response_is_not_dispatched_by_native_but_legacy_checks_next_turn` |

deadline 测试只推进外部时钟，不替换 controller/提交 gate；不等待真实 30 分钟，
也不证明异步 hard real-time interruption。现有 Docker smoke 另行覆盖真实隔离
runtime、pause-before-freeze 和 EVAS 0.8.7 trusted replay。

## 本次修复与代码位置

- `run_native_mini_swe.py::NativeMiniSwePolicy._propose`：将 mini-swe 的
  `FormatError` 转为已有 `ProposalNormalizationError`，不重提示，也不把原始
  错误消息写入 outcome。旧 adapter / `DefaultAgent` 不改。
- `runners/agent_harness/controller.py::EpisodeController.run`：只在 policy
  phase 将该类型归类为 `protocol_failure / proposal_rejected`。只持久化稳定
  code，不复制不可信错误 detail。provider 和其他内部异常仍是 infrastructure；
  若已过 deadline，沿用既有 deadline 优先级。
- `tests/test_agent_harness_controller.py`：覆盖 typed rejection、普通 backend
  failure、deadline 优先级、非 policy phase 的同类异常仍为 infrastructure，
  并验证 cleanup、trajectory、无评分。
- `tests/test_agent_harness_mini_swe_differential.py`：把上表变成可执行回归；
  既有 evaluator-closure CI 的 `tests/test_agent_harness_*.py` 自动纳入，不另造 CI。

原 bug 的 RED：无 tool call 被记为 `infrastructure_failure`，且 message 为空。
修复不改变模型生成、工具能力、打分真值或 legacy 行为，只修失败归因。

Policy 实现约束：`act()` 只能用 `ProposalNormalizationError` 表达不可信模型
proposal 被拒绝，不能用它包装 provider 失败、内部配置错误或程序 bug。当前
复用该异常避免新增包装层；若后续 policy 内部出现混合解析用途，再独立评估
policy 专属拒绝类型，不能通过宽泛捕获 `ValueError` 扩大此分类。

## 验证与剩余门槛

准确命令、计数、独立审查、Docker evidence hashes 与 publication 状态见
`logs/verification-log.md` 的 AA-VAE-038 记录。测试代码的 fake provider/final
checker 只证明给定输入下的工程行为，不能代替真实 r53 Docker 或模型实验。

当前不宣称 strict native 与 legacy 完全等价。正式差分实验必须冻结并报告格式
恢复、多动作和 deadline 差异，否则不能把分数差归因于“架构更好”。context
window 等 provider failure 在新入口尚未拥有外层 legacy campaign 同等细粒度的
terminal taxonomy；私有 error type 不等于公共 result ledger 已补齐。

本机完整回归保留一个旧用例验证缺口：1 秒 EVAS timeout 测试多次未捕获 START，
而 shim 在 START 之前要先运行 candidate hasher。它不是本次代码引入的失败，
也不能用新测试/Docker smoke 的通过来掩盖；没有改旧 runner 或放宽测试。
本机完整回归与后续 CI 的结果分别记录，不宣称所有本机测试全绿。

待独立切片：provider taxonomy/result ledger、全条件和 Testbench、transport retry
archives、Reasoning、round-barrier Evolution、完整 denominator/claim gate。没有
新领域工具、训练路径、付费调用、r53/EVAS 修改或 Spectre 审计。
