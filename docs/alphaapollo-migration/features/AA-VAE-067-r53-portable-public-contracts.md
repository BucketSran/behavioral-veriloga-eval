# AA-VAE-067：r53 公开 portable 契约兼容

## 功能标识与来源

- 日期：2026-08-31；负责人：主线程；状态：已实现并通过本地集成，发布验证中。
- 来源：本仓库已封存的 r53 公开运行契约及反馈链路审查，不是 AlphaApollo
  新代码移植。延续迁移原则：environment/tool 的可执行契约必须由代码约束，
  并与真实任务包一致，不能只靠单题成功推断整个 benchmark 可用。
- 实测缺口：原适配器接受 1,194/1,200 份公开契约；family 102、112 的
  DUT、bugfix、Testbench 共 6 题使用 portable 命令，原 strict-only 匹配拒绝它们。

## 适配决策

只扩充固定命令白名单：DUT/bugfix 的 runtime-v3 必须同时声明 portable；
Testbench reference-v1 保留 reference-only 绑定，并按显式 portable 选择无
`--spectre-strict` 的固定命令。strict 组合保留原命令；未知 mode/schema、
混合 flag、附加 shell 命令和工作目录替换仍拒绝。不是仿真失败后的自动降级。

既不更改 r53 文件，也不修改 EVAS 0.8.7、最终 judge、模型预算或候选排序。
public observation 仍只包含过程诊断；最终 sidecar 只在 freeze 后生成，不能
进入 Evolution 共享记忆。历史结果不重写；源码变化使新运行的 profile hash 改变。

## 代码改动

| 文件/符号 | 改动 | 层 |
| --- | --- | --- |
| `operations/calibration_pilot/public_validation.py::public_execution_contract` | 固定 strict/portable schema-mode-command 匹配 | harness |
| `tests/test_agent_harness_public_execution_contract.py` | 全量 1,200 契约、6 个 portable 回归及非法组合 | test / CI |
| `tests/test_agent_harness_production_public_validation.py` | portable observation、真实公开调用与 trajectory | test |
| `tests/test_agent_harness_public_waveform.py` | portable 固定执行、profile 区分与漂移拒绝 | test |
| `tests/test_agent_harness_waveform_integration.py` | portable native 反馈 → freeze → score reader | integration |
| `tests/test_agent_harness_evolution_campaign.py` | portable 双分支双轮与 selected-final-only | integration |

上述 operations 路径位于 `benchmark-vabench-release-v4/` 下。既有 CI 的 harness
通配套件与相同 Docker test 节点自动包含新参数用例，无需新增独立 workflow。
`public_waveform.py`、native Agentic 与 Evolution 均复用同一契约选择器，不复制
新的 parser，不改变默认 legacy mini-swe 路由。输入/输出 schema 没有新增字段。

## 验证与边界

逐类 RED → GREEN：4 个 DUT/bugfix 拒绝、2 个 Testbench 拒绝均先复现；
再复现并修正 3 个未知/混合 mode 漏检。全量公开契约按 form 验证各 400 题，
portable 各 2 题。静态、独立审查、真实 Docker 证据与精确计数见
`logs/verification-log.md`，不把契约识别数写成仿真通过数。
最终 focused 回归 192 通过 / 20 个 opt-in 跳过；三组 Docker 覆盖 17 个用例，
其中包含必须保留失败的负例。较大的历史本地套件缺少精简掉的历史资产，不能
宣称本地全仓库全绿；独立审查无阻断项，LSP/typecheck 不可用另行披露。

未改变的限制：公开仿真成功不等于行为正确；波形摘要还不是任务指标；
Evolution 模型可收到公开日志，但 reducer 仍仅按 `sim_success` 和确定性
tie-break 选择。DUT/bugfix 的 validation/final 分离是 shared-stimulus /
held-out-checker authority，不能声称输入完全独立。真实模型收益仍未测量。

本轮真实执行还发现：family 102 DUT 的已发布公开 support LFSR 使用动态数组
访问，固定 EVAS 0.8.7 报 `dynamic_state_array_access` 不支持。回归明确要求
保留非零退出和 failed observation，不把它改成 succeeded 或跳过任务。此为
公开运行能力限制，尚未修复；本切片的契约兼容不能被称为全量仿真兼容。
Evolution 的 family 102 DUT/Testbench 脚本候选终评实测为 `compile_failure`，
因此用例明确检查该分类，而不是套用 family 001 的 `behavior_failure`。
smoke index 同时记录 family 和真实 final status；链路通过不代表候选通过。
这些终态来自 trusted sidecar，只核对结构化状态，不读取或发布 hidden 诊断。

另有旧 `--agent-scaffold native` sensitivity 入口 `run_campaign.run_public_evas`
未注册 r53 schema，且 Testbench portable 判定需要审计；它不是默认 mini-swe
或本次 active native/Evolution 公开适配器。此旧路径问题保留为独立后续项，
不能因本次修复就宣称所有历史入口兼容。

没有 Spectre 执行或 parity 声明：EVAS 未改动，条件门未触发。
