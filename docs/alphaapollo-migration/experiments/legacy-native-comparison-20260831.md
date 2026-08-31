# Legacy / native mini-swe：第一轮工作流对照协议

日期：2026-08-31。代码基线：`2c07dca529277a103fe08f8854fe3957ddc29a6a`。
配套 [机器可检查的蓝图与六单元 tracker](legacy-native-comparison-20260831.json)。
状态：**离线协议；尚不可启动真实模型实验**。JSON 不是 runner campaign，
`live_authorized=false` 不是已有运行器的权限开关；真正启动仍需生成并验证新的
campaign、预算和证据配置。不能把此文件直接交给普通 CLI 后开始付费运行。

## 1. 要回答什么，不回答什么

主问题：同一模型在相同公开任务和资源设置下，旧、新 mini-swe 工作流分别如何
完成请求、修改、提交和评分？能否为每个计划单元保留完整可核查的终态和成本？
支持问题：失败主要出现在模型输出协议、工具执行、候选提交还是基础设施；
差异是否落在已经明确披露的控制策略上？

第一轮是工程校准，不复现 AAAI 论文的性能表，不估计全量 r53 分数，也不证明
“native 架构使模型更强”。AlphaApollo 的启发沿用项目已有迁移记录：把推理过程、
反馈和状态作为独立可审计对象；coding-agent 的实际对照对象仍是保留的 mini-swe。
这里新增实验约束和证据检查，不移植另一套 agent，不引入训练。

最小证据：六个预注册单元均有状态；完整对的结果可追溯到各自冻结提交和评分证据；
缺失、预算中止和未知用量都明确列出。能成功解析工具或执行 EVAS，不等于通过题目。
测试全绿也不等于已经得到真实模型的比较结果。

## 2. 固定样本、系统和运行顺序

选 family `001`，仅 `Agentic` / `G2`：

| 顺序 | 任务 | 形态 | episode backend |
| --- | --- | --- | --- |
| 1 | v4-001 | DUT | legacy |
| 2 | v4-001 | DUT | native-mini-swe |
| 3 | v4-1001 | bugfix | native-mini-swe |
| 4 | v4-1001 | bugfix | legacy |
| 5 | v4-501 | Testbench | legacy |
| 6 | v4-501 | Testbench | native-mini-swe |

这是固定的工程样本：family001 已用于免费 fixture/case study，**不声称它从未暴露**。
选择它是为了三种形态的可核查衔接，不是根据这次尚不存在的模型分数挑题。
不把已跑过 DeepSeek 的 family029 旧结果、候选或对话带入本轮。三种形态来自同一
family，不是三个独立随机家族；只做描述性配对，不做显著性或泛化结论。

每单元一次全新 attempt，无 resume、无自动重试、无跨单元记忆；串行执行，
相邻配对并交替先后顺序，但三个 pair 不能完全平衡顺序效应。这里不声称消除了
provider 的时间漂移。预算/基础设施中止后不靠重排、换题或补成功样本完成表格。
后续多家族/多 seed 试验另行预注册，不能在看完这六个结果后当作本轮原定方案。

两个系统均 `agent_scaffold=mini-swe`；**不是**旧 `--agent-scaffold native`。
本轮不加入 native-reasoning、Evolution、OneShot、NoEVAS、G3–G5 skills、RAG、
波形工具、SFT/RL。已有能力仍在，只是不混入第一对工作流比较。

## 3. 匹配控制与有意差异

固定 r53 + EVAS 0.8.7；mini-swe-agent 2.4.5 和仓库锁文件。
每个 pair 必须使用同一模型/服务身份、可用快照标识、解码设置、流式模式和 transport
retry 策略；实际响应标识另行记录。模型、价格及快照可用性在启动时验证，不能从
旧 DeepSeek 脚本中的常量推断当前最便宜型号或取得了新的消费授权。

蓝图保留 r53 的 1800 秒墙钟规则。每调用输出上限暂定4096，request/tool/judge
watchdog 各1800秒；启动前核对实际 client 参数及 deadline 剩余额度裁剪。
4096 不是累计 token 预算。两个 backend 均不设置 controller model-call cap
（native `model_call_limit=null`），以免 native 单独增加停止条件和剩余额度提示。
若以后改为有限 N，必须在两边实现并测试等价 admission/提示/计量，再发新版协议。

| 维度 | 共同点 | 必须披露的差异 |
| --- | --- | --- |
| 模型请求 | 同一 mini-swe system prompt、Bash JSON tool schema、公共题目 | native 操作说明要求每轮恰好一个动作，并解释 fresh shell/cwd；初始完整消息并非字节相同 |
| 格式错误 | 共用模型适配层 | legacy FormatError 可提示重试；native protocol_failure 终止 |
| 多动作 | 均可产生 Bash proposal | legacy 顺序执行直到提交；native 整个 proposal 在执行前拒绝 |
| 公开反馈 | 共用 Bash/environment 和 EVAS | native 增补有界 `public_evas` 过程诊断；不是隐藏正确性信息，也不是可信预算 receipt |
| 截止时间 | 墙钟1800秒，完整候选按各自既有规则冻结/评分 | legacy 晚到 response 可能先执行、下轮检查；native dispatch 前检查，不执行晚到动作 |
| 证据 | 候选、提交门、EVAS终评 | legacy 与 native 原始格式/失败类别/sidecar 接入不同，不能伪造同一 typed trajectory |

因此本轮干预是上述**整套工作流**。若要隔离 controller 的因果收益，需要另建
匹配 prompt、恢复策略、反馈内容和边界时间行为的 ablation，不能改原 baseline
使它迎合本轮结果。完成长度上限处的合法 Bash 在两边仍可执行；length 是遥测，
不能被分析脚本直接改写成失败。

## 4. 信息面审计：观察、声明、缺口分开

### 本轮实际核查

- JSON 记录选定三题的 `public_contract.json` SHA-256，以及 `public/` 下全部普通
  文件的路径→内容哈希映射摘要和数量（3、4、3）。算法是对按路径排序、紧凑 JSON
  映射计算 SHA-256；拒绝 symlink。这是**源公开文件**，不是 export 后全树 hash。
- 既有 differential 测试使用 scripted provider，经真实 legacy DefaultAgent 和 native
  控制循环捕获实际请求，核对单动作场景的 messages、tools/max_tokens、反馈和
  candidate/freeze。单测证明正常路径仅有已列出的操作说明差异；它是 synthetic
  task/provider/judge，不冒充选定 r53 三题的完整运行。公开 EVAS 诊断另有专门测试。
- 本地缓存镜像 `sha256:fe44bb54370160ee99bef939ae67a0ab1f51fb3b9a41d3d0c4cf29e7ea38115b`
  为 linux/amd64，实测 `evas-sim=0.8.7`。安装包的 `evas/examples` 有78个文件；按
  同一紧凑路径/哈希映射算法，摘要
  `90f9719c68d0a76350e017955ef586a63d55686cd3fd05cee243987b0d67d0ec`。
  这是安装示例目录的有界检查，不是全镜像内容安全审计，也不是未来机器的镜像 pin。
- 新增 opt-in Docker 检查用 synthetic workspace，分别设置旧/新环境的 structured
  feedback 开关。它读取实际容器 Mounts、NetworkMode、ReadonlyRootfs、CapDrop 和
  Image，而非只信 serialize 声明；检查精确的三个 bind 源/目标、读写属性和 synthetic
  evaluator sentinel 不可见。无 provider、无仿真或 final judge。它验证共用环境，
  **不是两个完整 campaign 的 isolation 证明**；具体通过情况见验证日志。

### 启动前必须补齐

1. 同 pair 的完整 export：task、初始 submission、work、skills、外部工具脚本、
   模板、实际发出的 messages/tools/decoding，逐项 hash 和 allowed-difference 核对。
   bugfix 初始 submission 来自公开 buggy bundle；DUT/TB 为空。Testbench 提供的
   reference DUT 是公开输入，不可把它误标为泄漏或从一边删除。
2. exporter 的 `public_support_files()` 会按 evaluator/family_spec 内的公开声明选择
   support；完整 exporter 还验证/复制私有评分包。本轮没有调用这些隐藏读取路径。
   因此源 `public/` 快照**不能证明所有导出 helper 已审计**。后续由可信准备边界
   产出仅含已声明公开 helper 的 manifest，再核对实际挂载；不向模型或公开日志
   导出 family_spec/solution/hidden checker 内容。
3. 两个实际运行容器必须 pin 同一 image ID（不仅同 tag），保存受限 inspect 证据，
   核对 network disabled、只读任务和无 sibling/host/evaluator 挂载。工具 PATH、
   安装示例/库及环境变量名称要记录；不要 dump credential 值。模型 API 客户端在 host，
   sandbox 禁网不等于 host 不能访问 provider。

`declared_information_surface`、MODEL_ACCESS_POLICY 只是预期策略；实测不符即停止，
不把“不知道”填为“相同”。此轮 Agentic-only 使用同镜像即可匹配安装资料；未来
NoEVAS 镜像卸载 EVAS 也会移除其示例，需单独处理该资料差异，不能沿用本轮结论。

## 5. 预算和停止条件

**真实费用上限未授权，真实模型未冻结，本轮实际模型调用为0。**
已有 `DeepSeekPilotBudget/BudgetedDeepSeekClient` 在 HTTP 前预留最坏费用、校验 usage、
未知成本停止，技术上能作为两路共同 client；但普通 campaign CLI 创建的是未包装
client，现有 `run_deepseek_pilot` 调度/免费集成只覆盖 native backend。不能把
“存在预算类”当作 legacy 已有付费保护，更不能运行普通 CLI 后事后看账单止损。

下一实现切片应复用该边界，不造第二套预算器：固定全部六单元、共享不可重置 journal，
把 legacy/native 都接到同样的真实 HTTP admission；验证每次 transport attempt 的预留、
未知/缺失 usage、异常、跨 client/attempt 不退款、费用中止状态和未启动单元。
现有 guard 的型号/费率/上限/调用 cap 是旧 pilot 契约，需要新的适用性审查。
若费用保护另设调用上限或120秒等 client watchdog，必须显式匹配并记录对1800秒
benchmark 规则的操作性删失；不得悄悄只对一边启用。

达到费用保护、未知成本或 provider 身份漂移即停止后续调度，保留当前终态与所有
未开始单元；不自动加预算、换模型、退回未包装 client 或重置目录。该费用保护不是
provider 账户全局账单上限。无需花完整上限；它是停止边界，不是消费目标。

## 6. 评分、结果验收与统计口径

公开 validation 只反馈可见仿真；final trusted replay 只对冻结提交运行，不进入下一次
模型请求/跨单元记忆/选题/候选选择。DUT/bugfix 的 visible stimulus 与 replay stimulus
复用，held-out 的是 checker 权限，**不是独立隐藏刺激集**。Testbench 公共 reference
运行也不是隐藏故障检测评分。

结果必须保留 `judge_engine=evas`、0.8.7、`development_only`、原生 verdict/score，
不将 EVAS replay 叫作 Spectre 结果；不新增通过阈值或把 Testbench 分数强制二值化。
模型/预算配置、prompt/tool/image、提交 hash、judge/checker/input 和 sidecar hash 都要
join。native scorer 只读既有终评，不执行第二次 judge；legacy 经各自 trusted freeze/
replay evidence 验证，不制造 native 记录来凑统一格式。

现有 native ledger 的 Agentic/NoEVAS/OneShot 配对不是这个跨 backend 比较器。
**只读跨 backend result join 尚未验收**，是独立启动前缺口。实现时保留各自来源，
对缺行/重复/错误任务、模型、image、submission/score hash 都 fail closed。

固定输出两张表（未运行时不得填成功率）：

- 表A，6行审计账：scheduled/started/terminal 状态、backend、task/form、attempt、
  original terminal reason、候选/协议/基础设施/预算删失分类、score 或 null、清理事故、
  时间、model logical calls、transport attempts、已报告 tokens/费用及未知计数、证据 hash。
- 表B，3行工作流配对：同 task 的两个来源、二者是否均有有效评分、原始 score 差值、
  wall/call/token 描述差异；不完整 pair 明示缺口，不插补成0。无已完成 pair 时比率为 null。

固定计划分母是6；有效评分、未评分 candidate/protocol failure、基础设施失败、预算
删失、未启动分别计数并核对总数。只有有效 sidecar 的数值0才是0分，未知分数不是0。
模型协议失败不能静默删掉；质量描述同时显示 planned、started、scored 分母，不能只报
幸存者成功率。deadline-primary 与 post-deadline sensitivity 分开，晚到动作不可悄悄
并入 primary；若 legacy 缺少足够时间证据，阻断该时间口径，不能推测恢复。

## 7. 执行 tracker 与 stop/go

| 块 | 当前状态 | 通过标准 / 下一动作 |
| --- | --- | --- |
| P0 协议和免费差分 | 已有蓝图；本轮验证记录见日志 | source public 快照、实际 synthetic requests、公开反馈、预算单测和实际 Docker mounts；不声明完整导出已审计 |
| P1 付费保护与结果 join | 未完成 | 共用 guard 的 legacy 集成 + 两路只读结果 join，先用免费 fixture 验证；不改评分/默认 backend |
| P2 启动冻结 | 阻塞 | 明确 model/service/decoding、费用授权、完整 public export、image ID、代码/协议 hash；禁止继承旧 pilot 预算 |
| P3 六单元运行与审计 | 6/6 not_started | 新目录按固定顺序执行，freeze→final sidecar，无新增尝试；中止状态和未知成本完整 |
| P4 后续研究决策 | 未开始 | 工程缺口先修并另记版本；有可用配对才考虑更大样本、Reasoning/Evolution/工具 ablation |

最低可用里程碑是 P0；它已经可以帮助人工审查“比的是什么”。P1/P2 全部完成才 go，
不是只填 API key 就 go。真实结果不追加到这份 offline JSON：新建不可变 run manifest/
tracker，引用本蓝图 hash，保留6个原定 ID 到生产 cell ID 的一一映射。未知模型/费用
必须由明确配置替代；身份变化、选择/限额修改都发新协议，不覆盖旧证据。

## 8. 免费复查入口与代码落点

仓库根目录执行（不读取密钥）：

```sh
uv run --locked --extra agentic python -m pytest -q \
  tests/test_agent_harness_comparison_protocol.py \
  tests/test_agent_harness_mini_swe_differential.py \
  tests/test_agent_harness_deepseek_budget.py \
  tests/test_agent_harness_public_evas_feedback.py \
  tests/test_agent_harness_model_call_budget.py \
  tests/test_v4_r53_active_entrypoints.py tests/test_agent_harness_ci_gate.py
```

真实 mount 检查另设 `VABENCH_TEST_DOCKER_RUNTIME=1`，只选新测试文件的
`-k observed_docker`，并将 `--basetemp` 指向 reports 下**未用过的新目录**。
需要已存在的 pinned image；不把默认 skip 当通过。本测试未加入新自动 Docker stage，
既有 hosted 全套仍有自己的 Docker gates；本轮新增 mount 检查的执行证据是本地的。

代码入口：calibration_pilot 下 `mini_swe_vabench.py::run_mini_swe_episode`、
`run_native_mini_swe.py::NativeMiniSwePolicy/_interactive_prompt`、
`run_campaign.py::run_cell`、`deepseek_budget.py`、`score_campaign.py`；通用控制器为
`runners/agent_harness/controller.py`。源输入/导出边界见 tri_form_derivation_prep 下
`export_tri_form_runtime.py::{install_public,public_support_files,render_prompt}`。
具体历史差异见 [AA-VAE-038](../features/AA-VAE-038-mini-swe-behavior-differential.md)、
[AA-VAE-053](../features/AA-VAE-053-public-operational-contract.md) 和
[AA-VAE-055](../features/AA-VAE-055-public-evas-process-feedback.md)。
