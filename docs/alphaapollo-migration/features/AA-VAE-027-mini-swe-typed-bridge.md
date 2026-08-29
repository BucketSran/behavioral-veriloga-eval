# AA-VAE-027：mini-swe typed compatibility bridge

## 功能标识

- ID：`AA-VAE-027`
- 名称：mini-swe typed compatibility bridge
- 状态：已验证，opt-in differential path
- 负责人或变更任务：Phase 3 mini-swe compatibility
- 日期：2026-08-30

## 思想来源

- AlphaApollo 和通用 coding-agent harness 都把 model proposal、environment
  execution、observation 和 terminal state 分成显式边界。
- vaEVAS 已有稳定的 mini-swe `DefaultAgent -> execute(dict)` 路径，因此本功能采用
  compatibility adapter，而不是重写或替换已验证的 runner。
- 本实现没有复制 AlphaApollo 或第三方 agent 框架代码；只把项目内既有 mini-swe
  行为映射到 vaEVAS 的 canonical Action/Observation/Environment contracts。

## vaEVAS 适配决策

- `MiniSwePolicyBridge` 接受 provider-native Bash tool calls，但 action ID、backend
  identity 和 candidate binding 由 harness 注入；provider call ID 不进入可信动作身份。
- `MiniSweBashEnvironmentBridge` 继续调用既有 `execute({"command": ...})`，只把返回值
  归一为 typed observation。
- 只有显式绑定的 mini-swe `Submitted` exception class 可成为 terminal submission；
  submission gate 拒绝继续作为普通失败 observation，其他 runtime exception 不被吞掉。
- candidate hash 与 freeze callback 必须由 production runtime 显式注入。不能从可选的
  EVAS invocation telemetry 推断 candidate state，因为没有调用 EVAS 的 Bash action 同样
  可能修改 candidate。
- Bash capability 采用保守的 `candidate_mutation/mutate` contract；读命令允许 hash 不变，
  写命令必须返回可信 after-hash。旧路径中的 `vabench-submit` transport 仍由 legacy
  environment 识别，generic controller 在 terminal observation 后执行独立 freeze/hash
  一致性检查。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/backends/mini_swe.py::MiniSwePolicyBridge` | native proposal → candidate-bound `AgentAction` | backend adapter |
| `runners/agent_harness/backends/mini_swe.py::MiniSweBashEnvironmentBridge` | legacy `execute(dict)` → typed `EnvironmentStep` | environment adapter |
| `runners/agent_harness/backends/mini_swe.py::mini_swe_bash_tool_descriptor` | 固定 Bash handler/schema/effect/evidence contract | capability registry |
| `tests/test_agent_harness_mini_swe_backend.py` | normalization、dispatch、submit、cleanup、controller tests | tests |
| `tests/test_agent_harness_mini_swe_integration.py` | 真实 legacy environment old/new parity 与 immutable freeze | integration test |

## 数据与状态变化

- 输入：mini-swe native Bash proposal、当前 trusted candidate hash、legacy Bash result。
- 中间状态：canonical `AgentAction`、typed `Observation`、candidate before/after identity。
- 输出：普通 non-terminal step 或精确分类的 submitted terminal step。
- backward compatibility：production `DefaultAgent` 与 `VaBenchBashEnvironment.execute(dict)`
  未修改；正式 campaign 默认路径没有切换。

## 验证证据

- focused bridge tests：`17 passed`。
- complete generic harness：`265 passed`。
- generic harness + existing mini-swe：`295 passed, 3 skipped`。
- independent production boundary regression：mini-swe + calibration pilot
  `137 passed, 3 skipped`。
- Ruff 0.12.12、Python bytecode compilation、`git diff --check` 均通过。
- independent code review：`APPROVE`，零 blocking finding。

## Claim boundary

- 能支持：mini-swe proposal 与 Bash environment 可以在不修改旧 runner 的前提下进入
  generic typed contracts；确定性 fixture 上 old/new submission artifacts、command
  dispositions 和 freeze identity 等价。
- 不能支持：formal campaign 已切换 generic controller、hosted provider trajectory 已逐
  token 等价、或 AlphaApollo reasoning/evolution 已经实现。
- 本功能不修改 r53 release bytes、EVAS 0.8.7、score authority 或 Spectre 条件门。
