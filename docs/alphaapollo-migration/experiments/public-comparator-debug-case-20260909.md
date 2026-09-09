# 公开比较器调试 case study

日期：2026-09-09。状态：已完成真实 Docker/EVAS 复现与独立只读审查。
这是公开案例的脚本诊断，不是模型能力实验或正式 r53 成绩。

## 先看结论

**这个极性错误不需要新增 wave-mcp 类工具才能定位。** 现有 Bash、公开示例
检查脚本和 EVAS 日志已经提供了足够的信息，并能通过现有 Controller/bridge
抵达下一次 policy 调用。恢复一行比较符号后，公开检查通过。

发现的是明确的能力边界：**仿真正常结束不代表功能正确，汇总统计不等于
时序诊断。** 没有发现这条受测路径丢失反馈的 harness bug；也没有证明模型
会主动调用工具或自主找到修复。本次没有修改生产代码、添加工具或新增依赖。

## Brief / 范围

在现有公开 `examples/comparator/comparator` 的 `cmp_ideal` 副本中，
把判定差分输入正负的 `> 0` 改为 `< 0`，构造一个能编译但极性错误的候选。
原始示例、r53、EVAS 0.8.7 和生产 harness 均不修改。

复用现有 Docker Bash 环境、mini-swe bridge、Controller、trajectory 和
波形摘要 parser。用脚本 policy 检查“公开仿真/检查 → 下一次 policy 输入
→ 定位 → 修复 → 再检查”。这是预先知道故障和修复的诊断，不是模型自主发现。
公开示例的 validator 明确作为本案例公开材料；它不是 r53 hidden checker，
不得由此把示例 validator 自动安装成 benchmark 的模型工具。

## KPI / 验收

- 错误候选能够完成真实 EVAS 仿真，但公开示例检查失败。
- 公开日志和失败信息确实通过现有 bridge/controller 抵达下一次 policy 调用。
- 临时副本的一行修复改变候选 hash，再次真实仿真后公开检查通过。
- 对同一份输出运行现有波形摘要，区分“可以读到信号统计”和“可以判定功能”。
- 保存命令、版本/源码 hash、原始本地轨迹、精简结论；不读凭据、不调用模型 API。

## Plan / 停止条件

1. 固定公开示例、唯一故障注入、脚本动作和本地证据目录。
2. 先定义诊断测试，使用既有执行组件运行；不新增模型工具或执行循环。
3. 对照代码和实际输出，分类为信息缺口、调用缺口、传递缺口或已有能力足够。
4. 记录验证及残余风险，给出一个最小后续建议；独立只读审查后提交到 fork。

若需要更改 evaluator、sealed release、隐藏评分、生产工具或付费调用才能
继续，停止这一方向，报告具体缺口。本案例不运行 final judge，也不生成分数。
Controller 用固定步骤上限结束诊断，其 `budget_exhausted` 是预定停止方式，
不是一条可计入 benchmark 的成功/失败记录。

## 1. 案例来自哪里，故障是什么？

只读取以下已存在的公开、非评分示例：

- [cmp_ideal.va](../../../examples/comparator/comparator/cmp_ideal.va)：时钟比较器。
- [tb_cmp_ideal.scs](../../../examples/comparator/comparator/tb_cmp_ideal.scs)：公开激励。
- [validate_cmp_ideal.py](../../../examples/comparator/comparator/validate_cmp_ideal.py)：
  公开示例检查，按时间窗口检查输出，不是隐藏终评 checker。

供电 0.9 V，时钟周期 1 ns。输入差分先为 +1 mV，在 1.9–2.0 ns 线性翻转，
2.0 ns 后为 −1 mV。
时钟上升沿应根据差分符号选择正/负输出，下降沿复位。
我们只在临时候选副本中做以下反向修改，之后恢复：

```diff
- if (V(VINP) - V(VINN) - voffset > 0) begin
+ if (V(VINP) - V(VINN) - voffset < 0) begin
```

原始示例不变。测试网表只把 include 路径改为指向临时候选，激励不变。
案例任务 ID 是 `example-cmp-ideal`，没有导出或读取 r53 evaluator。
公开检查脚本是**专门声明的案例输入**，不是当前 benchmark 默认提供的工具。

## 2. 六次脚本 policy 调用实际发生了什么？

使用现有 `EpisodeController` 调用 `MiniSwePolicyBridge`；它返回预写好的 Bash
动作，通过 `MiniSweBashEnvironmentBridge` 和真实 Docker 环境执行。
不是另写一个 agent 循环，也没有接入 LLM provider。

| 调用 | 本轮动作 | 实际反馈 / 下一轮看到的内容 |
| --- | --- | --- |
| 1 | `evas --version` | EVAS 0.8.7；下一轮接收到该输出 |
| 2 | 仿真错误候选，再运行公开示例检查 | 仿真返回 0，检查返回 1；下一轮收到失败与判决日志 |
| 3 | 用 Bash 查看候选第 24–45 行 | 可以看到反向的 `< 0` 判定 |
| 4 | 在候选副本把 `< 0` 恢复为 `> 0` | 候选 tree hash 改变；源示例仍未变化 |
| 5 | 仿真修复候选，再运行同一公开检查 | 仿真返回 0，检查返回 0 |
| 6 | 接收修复后的反馈，执行 `true` | 随后按预定步骤上限结束；不提交、不冻结、不评分 |

脚本提前知道故障和修复，没有根据反馈自主推理或选择动作。
这里测试的是**信息可达性与可复现修复**，不是“模型看懂了错误”。

关键的错误反馈摘录：

```text
simulation_returncode=0
[cmp_ideal] t=0.510 ns | ... | diff=1.0000mV | dec=0
FAIL: before swap, out_p HIGH only 0% (expected >40%)
FAIL: after swap, out_p LOW only 34% (expected >40%)
```

修复后的公开反馈：

```text
simulation_returncode=0
[cmp_ideal] t=0.510 ns | ... | diff=1.0000mV | dec=1
[CSV] All assertions passed.
```

输入为正、判决却为零，已经把问题缩小到极性/分支判定。
输出日志中的 `transition()` 静态警告在修复前后都存在，不是此次极性错误的证据。
`--spectre-strict` 是 EVAS 的模式选项，本案例没有运行 Spectre。

## 3. 现有波形摘要能说明什么？

在同一份实际输出上，**离线调用现有** `summarize_waveform_bytes`，不注册新工具，
也不把这一步冒充 `vaevas_public_simulate` 的隔离执行 receipt。
每次扫描 813 行，`status=available`。正输出 `out_p` 的统计如下：

| 统计 | 错误候选 | 修复候选 |
| --- | ---: | ---: |
| 最小 / 最大电压 | 0 / 0.9 V | 0 / 0.9 V |
| 样本均值 | 0.222514 V | 0.223893 V |
| 首值 / 末值 | 0 / 0.9 V | 0 / 0 V |

**两份真实摘要并不完全相同**，末值和均值也可以提供线索。
但摘要没有回答“在正差分且时钟采样时，正输出是否正确”，更没有给出首个错误时刻。
这里的均值是样本算术均值，不是按时间积分的平均电压。
`available` 仅表示数据可解析，不表示电路正确。

额外的纯 parser 测试用四行显式合成 CSV，把脉冲从 t=1 移到 t=2。
两份 CSV 的 `signals` 统计完全相同，内容 hash 不同。这说明统计一般不能保留
全部时序关系；它不是两次真实 EVAS 波形完全相同的证据。

## 4. 对照代码：到底检查了哪一层？

| 问题 | 现有代码位置 | 本次结论 |
| --- | --- | --- |
| 能否发出结构化 Bash 动作？ | [MiniSwePolicyBridge](../../../runners/agent_harness/backends/mini_swe.py) | 脚本提案被转换成带候选身份的动作 |
| 能否执行仿真、看日志、修改候选？ | [VaBenchBashEnvironment](../../../benchmark-vabench-release-v4/operations/calibration_pilot/mini_swe_vabench.py) | 真实 Docker + EVAS 完成修复前后两次仿真 |
| 工具失败会不会中断或丢失下一轮反馈？ | [MiniSweBashEnvironmentBridge](../../../runners/agent_harness/backends/mini_swe.py) + [Controller](../../../runners/agent_harness/controller.py) | 公开检查返回 1 后仍能继续；错误/修复反馈均抵达下一轮 |
| trajectory 是否能关联真实观察？ | [trajectory.py](../../../runners/agent_harness/trajectory.py) | 事件 hash 链及语义验证通过，逐条关联 observation ID、payload hash、候选 hash |
| 摘要是否足够判断时间窗口内的正确性？ | [waveform_summary.py](../../../runners/agent_harness/tools/waveform_summary.py) | 可读统计，但不是时间关系检查或行为判决 |
| 是否测试了结构化公开 validator、注册波形工具/Evolution？ | 不属于本案例执行路径 | 没有；不能把 Bash/离线 parser 结果外推到这些路径 |

Controller 轨迹按契约记录观察身份和 payload hash，不直接存放原始工具输出。
测试在本地另存 `policy-observations.json`，证明对应内容真的传入 `propose()`；
不是仅检查“日志文件存在”。原始轨迹及波形均不提交。
Bash 的 `public_evas` marker 仍是不可信诊断，不作为上述候选/观察对接或评分的
认证来源；本次也没有使用生产 `PublicEvasValidator` / 隔离波形 receipt。

## 5. 缺口归因和最小下一步

| 可能原因 | 本案例能否支持？ | 后续处理 |
| --- | --- | --- |
| 缺少基本调试执行能力 | 不支持；Bash 已能调用仿真、公开检查、读代码和修改 |
| 反馈在 Controller/bridge 丢失 | 受测路径没有观察到；有逐观察 hash 对接证据 |
| 模型不会主动调用或理解工具 | 未测；没有真实模型，不能下结论 |
| 汇总统计缺少时间关系 | 已展示边界，但公开检查和日志已能解决当前案例 |
| 必须接入 wave-mcp/MCP 才能修复 | 本案例不支持 |

**暂不新增生产工具。** 先用这份案例解释“可执行、可诊断、会使用、有收益”四件
不同的事。只有后续真实轨迹显示 Agent 反复需要自己编写相同的时间窗口/边沿分析，
再考虑将该重复操作封装为查询能力，沿用现有工具和候选绑定契约。
没有日志或公开 checker 的情况、复杂多信号时序问题仍未覆盖。
任何真实模型自然使用实验需另定任务、条件、预算，不能续用已关闭的付费研究。

## 6. 复现与证据

从仓库根目录执行，需已安装项目依赖和已有 EVAS 0.8.7 Docker 镜像。
每次创建新目录，不覆盖以前的测试证据：

```bash
debug_case_root=$(mktemp -d "$PWD/benchmark-vabench-release-v4/reports/public-debug-case-20260909.XXXXXX")
VABENCH_TEST_DOCKER_RUNTIME=1 .venv/bin/python -m pytest -q \
  tests/test_public_debug_case_study.py \
  --basetemp "$debug_case_root/pytest" --junitxml "$debug_case_root/junit.xml"
```

测试源：[test_public_debug_case_study.py](../../../tests/test_public_debug_case_study.py)。
未显式启用 Docker 时，两个纯检查运行，真实执行测试按既有 opt-in 方式跳过。
它不会调用 API、读取凭据或安装依赖。

本地 evidence 记录输入源码、执行代码、Docker image、候选、轨迹及观察 hash。
镜像：`sha256:fe44bb54370160ee99bef939ae67a0ab1f51fb3b9a41d3d0c4cf29e7ea38115b`。
运行中的 EVAS 为 0.8.7 / rust-core 0.2.4 / ABI 20260718；build revision 未知，
不把版本号当成完整构建身份。具体复现根目录和最终验证见
[verification log](../../../logs/verification-log.md)。

最终实跑：**3 passed**；最终根目录为
`benchmark-vabench-release-v4/reports/public-debug-case-20260909.E0Oimv/`。
案例运行报告位于该目录的
`pytest/test_public_comparator_debug_l0/public-debug-case/evidence/case-report.json`，
SHA-256 为 `0dc4a441b931074cd4b0dffd53258aaae52cf1854b32c8bd5b931af8cd5b993a`。
两个此前成功的 fresh-root 运行得到相同的错误/修复 CSV hash。

初版诊断测试曾把 parser 状态误写为 `ok`，并把精简 trajectory event 当成原始
observation；已按实际 `available` 和 hash 对接契约修正测试。
这两项是案例测试自身的假设错误，不是修复了生产 harness bug。

## Review / 声明边界

KPI：真实仿真、公开失败/修复、下一轮观察对接和诊断归因已获得证据。
终止是预定 `max_steps_exhausted`，不生成 final score；最终检查通过只对应公开
示例脚本，不是完整功能证明、benchmark 结果或模型成功率。
本次按项目 workflow 留下复现测试和证据笔记，没有新增一套 framework 或工具。
独立审查未发现阻塞项；根据审查修正了输入在 1.9–2.0 ns 渐变的描述。
