# AA-VAE-025：Trajectory semantic validation and CI gate

## 功能标识

- ID：`AA-VAE-025`
- 名称：Trajectory semantic validation and CI gate
- 状态：已验证
- 负责人或变更任务：Phase 2 evidence closure
- 日期：2026-08-30

## 思想来源

- AlphaApollo 把完整多轮轨迹作为推理/evolution 的核心对象，而不是只保存最终答案。
- vaEVAS 需要进一步证明 attempt identity、tool authority、candidate/freeze 和 trusted judge
  的事件顺序及 visibility 合法。
- hash-chain 与 semantic validator 分层是 vaEVAS 的可信评测适配：重新计算过 hash 的非法
  事件序列仍必须被拒绝。

## vaEVAS 适配决策

- 采用：append-only trajectory、action/observation join、完整 episode lifecycle。
- 修改：新增语义验证，不把“链完整”误写成“评测语义正确”。
- 不采用：final judgment 或 freeze 后事件回流模型上下文。
- evaluator/claim 边界：final judgment 必须 trusted-only 且晚于 submission freeze；semantic
  validation 本身不证明 EVAS/Spectre 数值一致。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/trajectory.py::validate_trajectory_semantics` | identity/lifecycle/action/visibility/freeze rules | trajectory |
| `runners/agent_harness/controller.py` | observation event 加入 action ID | trajectory |
| `.github/workflows/evaluator-closure.yml` | generic harness path filters 和 test gate | CI |
| `tests/test_agent_harness_trajectory.py` | 合法链上的语义攻击回归 | tests |
| `tests/test_agent_harness_ci_gate.py` | workflow contract regression | tests |

## 数据与状态变化

- 输入：已通过 SHA-chain 校验的 event documents。
- 中间状态：固定 attempt identity、pending/authorized action、terminal/freeze state。
- 输出：semantic validation boolean。
- 新增 schema 字段：无；`environment_observed.payload.action_id` 成为 join evidence。
- backward compatibility：保留原 `validate_trajectory` hash-only API；生产 mini-swe 尚未切换。

## 验证证据

- regression tests：跨 attempt、无 proposal 授权、final visibility、post-freeze model event、
  controller success/failure trajectory。
- CI：evaluator closure 对 `runners/agent_harness/**`、`schemas/vaevas-*-v1.schema.json` 和
  `tests/test_agent_harness_*.py` 触发并执行。
- 未验证部分：production mini-swe normalization、result sidecar join、真实 hosted trajectory。

## Claim boundary

- 能支持：generic trajectory 同时具备 cryptographic chain 和独立语义 gate。
- 不能支持：当前 paper campaign raw trajectory 已全部按新协议重建或验证。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
