# vaEVAS 代码阅读地图

vaEVAS 是 Verilog-A 的生成与评测系统，不是一个新的仿真器。
VABench r53 提供固定任务，agent 生成和改进候选，EVAS 0.8.7 执行仿真，
评测链路把冻结提交、评分和结果证据关联起来。

本页解释**当前代码**；功能状态与下一步只维护在
[当前计划](../plans/current-plan.md)。通过
[入口指南](../benchmark-vabench-release-v4/runners/README.md)选择运行路径，详细命令见
[operations 参考](../benchmark-vabench-release-v4/operations/calibration_pilot/README.md)。

## 先认清三个代码位置

以下是已有路径，不是建议创建的新目录：

```text
behavioral-veriloga-eval/
├── runners/agent_harness/                  共享 agent 契约与执行机制
├── benchmark-vabench-release-v4/
│   ├── release/benchmarkv4-r53/            不可变任务与发布证据
│   ├── runners/                           面向操作者的 campaign 入口
│   └── operations/calibration_pilot/      实际运行装配、公开反馈、终评及报告
├── environment/                           运行环境定义与依赖
├── schemas/                               数据契约
├── tests/                                 行为与边界回归
└── docs/ · plans/ · logs/                  说明、当前任务、历史证据
```

`calibration_pilot` 是沿用的历史名称，今天并不只放 pilot。
根目录 `runners/` 也包含历史脚本；当前通用 harness 是其中的
[`agent_harness/`](../runners/agent_harness/README.md)，不是 v4 下再嵌套一层的包。
EVAS 是同级的独立仓库，本页不改变其实现或版本。

## 一次 native 运行如何经过这些模块

```text
campaign 入口 / 清单
    → native batch / attempt：分配单元、预算与新尝试
    → native launcher：装配 policy、environment、tools 和 recorder
    → controller：动作 → 权限检查 → 执行 → 公开 observation → 下一轮
    → submission freeze
    → final judge：冻结提交 → EVAS replay → terminal score
    → verified reader / result ledger：关联证据、统计和导出
```

从 [campaign 入口](../benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py)
开始，接着读 [operations 模块地图](../benchmark-vabench-release-v4/operations/calibration_pilot/README.md#module-map)，
再进入 [harness 模块地图](../runners/agent_harness/README.md)。
这条链描述 native 路径；默认 legacy mini-swe 保留原来的循环，不能画成
所有 backend 都已经经过共享 controller。

Evolution 复用候选生成机制，但每个 branch 的终点是**候选快照**，不是最终评分。
一轮结束后只封存允许共享的公开反馈；选定最终候选后才执行 freeze 和 final judge。
因此它是不同实验条件，不是给普通单次运行自动加上多模型重试。

## 为什么分这些边界

| 边界 | 负责的事 | 不负责的事 |
| --- | --- | --- |
| Policy / backend | 模型调用与动作适配 | 决定评分真值、授权工具 |
| Controller | 生命周期、动作许可、预算和失败分类 | 具体 Docker/EVAS 实现 |
| Environment / tool | 工作区操作与已授权工具执行 | 把终评分数回传给模型 |
| State / trajectory | 统一事件、状态、可见性及证据关联 | 用某个模型的日志格式替代公共契约 |
| Final judge / result reader | 冻结后评分、核验已有证据 | 为下一轮 evolution 提供隐藏反馈 |

“公开反馈可用”不等于“最终 checker 可见”。普通 native 环境负责冻结，
controller 协调终止和 judge；具体冻结与 replay 实现仍在 operations 中。
评分侧使用 EVAS 不代表具备 Spectre 等价性或正式外部认证。

## 后续修改应该放哪里

- 新模型动作适配：`runners/agent_harness/backends/`；服务调用和装配查 operations。
- 波形查询或检索算法：`runners/agent_harness/tools/`；隔离执行、候选绑定查
  operations 的 `public_waveform.py`、`public_validation.py`。
- 循环或权限规则：harness 的 `controller.py`、`tool_registry.py`。
- 冻结、评分或结果关联：operations 的 `result_protocol.py`、`native_episode.py`、
  `final_replay.py`、`score_campaign.py`，以及 harness 的 result/evidence 模块。

未来的 debug 工具应先沿用这些入口；本次没有增加 MCP、波形会话服务或新框架。

## 仍然存在的结构问题

导航整理之后，已完成一块评分依赖提取，见下面的对照；不是全仓重构：

1. `run_native_mini_swe.py` 实际也装配 Reasoning、OneShot 和可选工具，名字窄于职责。
2. `run_campaign.py` 仍有可继续提取的公开执行和历史解析逻辑；评分器的冷加载与
   单 native cell 回读已不再依赖这个启动器。batch-attempt 回读与 ledger 写入路径
   仍会延迟加载已有编排模块，不能宣称整个报告依赖图都已解耦。
3. `calibration_pilot/` 混合了日常运行与具名实验。仅改目录名会牵动脚本导入、
   测试、CLI 和运行 manifest 的源文件哈希，不能视作纯排版。

后续修改仍应找出上述模块的一块独立职责，先确定调用者、
兼容导出和证据身份，再逐块迁移；不要先设计一套空目录或按行数拆文件。
已有分层清楚的工具 parser 不需要为形式统一再包一层。

## 已落地：评分不再借启动器取共享函数

原来：`score_campaign → 动态加载 run_campaign`，读取 native 配置时还会导入
`run_native_mini_swe`。现在，两侧直接复用已有 operations 层内的明确所有者：

| 所有者 | 从大入口移出的职责 |
| --- | --- |
| `submission_contract.py` | 声明的候选路径、提交工具 schema、源码/include 检查、冻结前 artifact gate |
| `campaign_telemetry.py` | 模型输出额度命中、EVAS 调用与候选变更统计；不把 Bash marker 升格为可信计数 |
| `native_contracts.py` | backend profile、OneShot 提交描述、声明的信息可见面；不启动模型或环境 |
| `final_replay.py` | EVAS 身份核对、命令执行、单次终评限制和 replay；不是公开反馈工具 |

`run_campaign` 和 native launcher 保留原函数名的兼容导出；终评执行注入点也保留。
没有增加一套 agent 循环、工具协议或评分规则。新源码进入运行身份哈希，已有冻结
记录不改写。具体迁移及验证见
[AA-VAE-082](alphaapollo-migration/features/AA-VAE-082-scoring-dependency-extraction.md)。

## 本次采用的方法

依据用户指定的
[`write-clear-code` skill](https://github.com/AndrewZhou924/AlphaApollo-v3-dev/tree/f0dafb0576996802f50f2a41c372c45c37c4ec43/.agents/skills/write-clear-code)：
按职责解释模块、在所属目录维护代码地图、保持已用入口稳定、让同一状态只有一个维护位置。
这里只使用授权的工程方法，没有复制该项目业务代码或引入依赖。

学习“为什么这样设计”可读 [迁移笔记](alphaapollo-migration/README.md)；
学习真实事件怎么对应代码可读 [单任务 case study](alphaapollo-migration/05_单任务代码与轨迹案例_2026-08-31.md)。
