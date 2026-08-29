# AA-VAE-023：Controller capability-aware dispatch

## 功能标识

- ID：`AA-VAE-023`
- 名称：Controller capability-aware dispatch
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 2 controller/state slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 把模型输出、环境执行、反馈观察分开；工具反馈只能来自环境拥有的
  action boundary。
- OpenHands/Codex CLI 等 coding-agent 框架在 action dispatch 前做 capability/policy
  check；vaEVAS 需要在任何 workspace/candidate mutation 之前执行相同的 fail-closed
  gate。

## vaEVAS 适配决策

- `EpisodeController` 必须接收 trusted `ToolRegistry`。controller 在 episode 起点按
  `EpisodeContext.condition` 解析并固定 effective capability hash；每个 model-visible
  action 都必须先授权，授权通过后才会调用 `environment.step`。
- 授权通过会写入 `action_authorized` harness event，记录 effective toolset hash、
  tool id/version、handler id、descriptor hash、candidate hash 和 condition，用于后续
  trajectory/evidence join；这些 handler/capability 证据是 harness-visible，不进入
  model-visible projection。
- 授权失败会写入 `action_rejected` harness event，并以 `protocol_failure` 收束当前
  episode；环境会执行 cleanup，但不会进入 `step`，因此 reserved/unknown/ineligible
  tool 不能突变 candidate/workspace。
- 若 descriptor 声明 `requires_candidate_binding=true`，action 必须绑定最新 trusted
  environment observation 的 candidate hash；缺失、不可用或过期绑定均 fail closed。
- `harness_internal` / final-only capability 不能由模型调用。
- `FinalJudge` 仍然完全位于 registry dispatch 之外，只能由 freeze 后的 terminal
  controller phase 调用。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/controller.py::EpisodeController` | 强制 trusted `tool_registry`，在 `environment.step` 前授权 action、校验 candidate binding，并记录 capability/rejection evidence | harness controller |
| `tests/test_agent_harness_controller.py` | 增加 registry 必填、授权 dispatch、reserved/final-only tool 拒绝、candidate binding 与 visibility 回归 | tests |

## 数据与状态变化

- 输入：`AgentAction.tool_name`、当前 condition、trusted tool registry。
- 输出：`action_authorized` 或 `action_rejected` trajectory event，其中
  `action_authorized` 绑定 effective capability hash。
- authority boundary：controller 不保留 registry-free dispatch 路径；production
  r53/mini-swe runner 仍未导入该 package，因此没有改变既有 benchmark 执行。

## 验证证据

- RED：新增 dispatch 测试最初失败于 `EpisodeController.__init__()` 不接受
  `tool_registry`。
- focused GREEN：两条新增测试 `2 passed`。
- generic harness：最终完整计数见 `logs/verification-log.md`。
- clean-room smoke：未执行；此切片仍未接 production runner。

## Claim boundary

- 能支持：common controller 的 action dispatch 必须绑定 trusted capability registry；
  reserved、final-only 和 stale-bound action 在环境突变前 fail closed，且
  capability/handler 证据不会进入 model-visible projection。
- 不能支持：mini-swe 已经通过 common controller 运行，或 AlphaApollo reasoning/evolution
  backend 已经可执行。
- 本功能不修改 r53、不修改 EVAS、不触发 Spectre parity gate。
