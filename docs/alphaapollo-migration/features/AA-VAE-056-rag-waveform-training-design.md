# AA-VAE-056：RAG、波形、SFT/RL 并行设计

> 历史设计，以下状态只对应当时基线。RAG/波形已在后续切片接通，
> AA-VAE-059/062 合成训练原型已于 2026-09-01 退役。
> 当前能力和待办以 [current-plan](../../../plans/current-plan.md) 为准。

日期：2026-08-31。状态：**设计完成，未实现、未启用**。
代码对照基线为 `8467af3d38`，公开 EVAS 过程反馈另见 AA-VAE-055。
三个只读 adviser 分别审查现有代码，由主线程整理本记录；没有并行修改代码。

本轮参考的是既有 AlphaApollo 迁移结论和 vaEVAS 当前公开代码/契约，
没有新增外部实现借用，没有读取 private AlphaApollo，也没有启动模型或训练。
这不是“引入三个框架”的计划，而是在已建成的 controller/environment/
tool/state/trajectory 边界上补适合 vaEVAS 的能力。

## 先区分现有能力与新增价值

| 方向 | 现在有什么 | 真正要补什么 | 本轮不做什么 |
| --- | --- | --- | --- |
| RAG | 冻结 public skills 的 precedent；reserved retrieval marker；统一工具权限和预算 | 有来源/许可/版本的离线检索，以及模型看到哪份语料的证据 join | 不下载语料，不接在线搜索/向量服务，不激活 marker |
| 波形 | Bash 已能读公开 EVAS 的 logs/`tran.csv`；public validator 有 candidate/profile 绑定 | 有界、可复现、明确缺失/数值异常的 CSV 摘要 | 不做 hidden checker，不返回任务 pass/score，不先引入绘图或视觉模型 |
| SFT/RL | typed trajectory、budget、termination、candidate lineage、public/final 隔离 | 独立训练数据契约、split/来源门禁、public-only 标签或 reward | 不把 reviewer export 当数据集，不导出真实轨迹，不训练/选 GPU 栈 |

`vaevas.reserved.*` 仍是不可调用、模型不可见的 namespace marker。
[AA-VAE-028](AA-VAE-028-domain-tool-namespace-gate.md) 的激活条件保持有效。

## A. RAG：先冻结语料，再接检索

建议 MVP 是一个新的 `vaevas.docs.search` active tool；reserved marker 原样保留。
先使用确定性的离线词法检索与固定 tie-break，复用 `tool_call` 预算；不要为了
MVP 新增 embedding 服务、网络或 `retrieval_calls` 全链路计数。
这只是假定的最小实现方案，不是本轮已激活的 descriptor。

拟定输入：`query`、有上限的 `top_k`、可选且枚举化的 `section_filter`。
拟定输出：corpus profile/tree/index hash、query hash、rank、doc/chunk ID、
source/content hash、许可状态、有界片段、截断标志；不接受任意 host path。
所有内容视为检索资料，不作为新的系统指令或权限来源。

语料 profile 要冻结：来源路径/版本/许可、允许/排除清单、内容 tree hash、
index 和 builder hash、chunking/tie-break 算法、输出 byte cap、network=disabled。
排除 r53 task solutions/任务包、hidden decks/checkers/gold/certified faults、
final scores、旧 episode artifacts、私有 reports/AlphaApollo。不能把含这些内容
的 summary 换个名称后纳入语料。

现有 skill snapshot 的部分来源标为 `not_declared_in_source_repository`，
因此不能把“文件公开可读”直接当作训练/再分发许可。第一批测试使用合成 fixture；
真实语料需要逐项明确许可依据。不要从运行中的 EVAS image 临时抽取语料：
Agentic/No-EVAS 安装资产可能不同，无法保证配对条件看到相同资料。

比较设计：若 RAG 是实验变量，单独命名 FrozenDocs 条件，至少成对覆盖
EVAS yes/no；若把它当公共支持能力，两边必须使用相同 corpus/index/hash 和预算。
OneShot 不支持交互检索：第一版先不并入此消融；未来若预注入片段，另冻配置。
Evolution 最多共享同 episode 的公开检索摘要，不能跨 task/cell 自动累积资料。

拟改落点（尚未创建/修改）：

- 新 `schemas/vaevas-retrieval-corpus-profile-v1.schema.json` 和离线 corpus validator。
- 新 `runners/agent_harness/tools/offline_docs.py`：纯检索 handler、稳定排序与有界返回。
- 复用 `tool_registry.py`、`budget.py`；native 当前 Bash-only bridge 需要明确的
  composite dispatch，不能把一个新工具偷偷塞进 Bash action parser。
- `result_artifact.py` 与 native request/manifest 增加 corpus/index identity join；
  只记录 tool schema hash 不足以证明模型看到哪份资料。

第一批 RED 测试：缺失许可/未知来源不能激活；symlink/path traversal 拒绝；
索引漂移拒绝；相同 query/hash 返回相同排序；预算恰好一次；禁止网络；
跨 condition corpus mismatch 拒绝；模型请求、trajectory、result 能互相 join。

## B. 波形：公开 CSV 摘要，不是正确性判定

建议先做纯 `tran.csv` 摘要器，再作为**显式 opt-in public-validation profile**
的 observation 子对象。复用既有运行/预算/候选绑定，不先增独立可调用工具。
若日后证明按需调用能减少输出 token，再单独设计 `vaevas.waveform.summary`。

重要接线区别：`PublicEvasValidator` 是已存在的结构化 validation seam，
native mini-swe/Reasoning 目前的任意 Bash 调用不会自动经过该 validator。
所以“在 validator 加摘要”不等于已经为所有 Agentic Bash episode 启用波形工具。
接入 Bash 时还需要同次 invocation 的受限输出定位与 hash receipt，不能直接
读取一个可能由旧调用/模型覆盖的共享 `tran.csv`，再声称它属于当前 candidate。

拟定摘要：`available/missing/invalid/too_large/truncated`、CSV bytes/hash、
scanned rows、returned/omitted signals、每列 finite/nonfinite/empty 数量和
min/max/mean/first/last。JSON 不允许 NaN/Inf；数值异常必须显式标记，不能默认为 0。
单位仅在公开 profile/CSV contract 明确时填写，否则 unknown；不能把每列都当电压。
MVP 不做边沿计数、数字高低或容差判断，这些需要额外公开阈值并进入配置 hash。

来源仅限同一次公开 EVAS invocation 的隔离输出；固定相对 CSV 路径，不接受
用户任意文件路径。检查 traversal/symlink/文件类型/大小/行数/列数，绑定
invocation ID、candidate hash、validation profile hash、source file hash。
摘要是公开波形的统计，不包含 task-level `passed/score`、hidden thresholds 或
最终 sidecar，也不能单凭摘要把 simulation process success 升级为任务成功。

拟改落点（尚未创建/修改）：

- 新 `runners/agent_harness/tools/waveform_summary.py`：独立有界 CSV parser。
- `operations/calibration_pilot/public_validation.py`：显式 summary-enabled profile
  和同次输出 provenance；`authority_profiles.py` 已识别 `waveform_summary` 类型，
  但当前 profile 仅 runtime/log_excerpt，不能默认扩大。
- 原有 `Observation.payload_sha256` / controller event join 可复用；不复用 hidden
  checker 的 CSV helper，避免其缺省值/跳行策略变成模型可见判据。

第一批 RED 测试：空/缺失/重复 header/NaN/Inf/坏数值/超限文件；非法路径和符号
链接；旧 invocation 或不同 candidate 的 CSV 拒绝；payload/source hash 可 join；
没有 score/pass/hidden 参数；No-EVAS/OneShot 无该权限；原 profile byte-for-byte 不变。
具体 file/row/signal/output caps 在实现前作为测试常量冻结，不在此冒充已选定。

## C. SFT/RL：训练与评测分开

首先新增独立的 training-export schema + validator，只跑合成轨迹 fixture。
现有 reviewer export 明确 `may_enter_model_observation=false` / memory=false，
不能直接改名后用于训练。现有 scored result/score sidecar 也不是训练样本。

拟定导出字段：source artifact/normalizer hash、episode/task/source release identity、
split manifest hash、来源许可/provider terms/项目授权、exposure policy、public
prompt/context 引用、accepted action、public observation、mask snapshot、budget、
termination 和明确的 label/reward authority。默认排除 raw provider payload、
raw hidden reasoning、凭据和 trusted/private events，缺少 provenance 则 fail closed。

SFT 与 RL 是两个后续分支：

- SFT 使用独立 train/dev 数据上的 public context/actions 和允许的标签。
  环境 observation 不冒充 assistant target；budget stop 不冒充成功示范。
- RL 的 in-episode reward 只能来自专门声明的 public validation，记录生成器
  hash、reward 含义和预算/终止；不把本次 AA-VAE-055 进程零退出等同任务 reward。
  Final-test score 不进 replay buffer、reward model、candidate selection 或 memory。
- 先冻结 train/dev/held-out split、去重/污染检查与 checkpoint，再作训练后评测。
  当前 r53 benchmark test tasks、gold/certified faults/checker/final outputs 全部
  排除训练，而不是只过滤掉 final score 字段。不能用 benchmark 的题面/解答先训练，
  再把同任务上的终评称为 held-out 泛化。

拟改落点（尚未创建/修改）：新 `schemas/vaevas-training-export-v1.schema.json`、
split manifest schema、`runners/agent_harness/training_export.py` 和独立 fixture tests。
复用 trajectory semantic/hash validator、action/observation、budget/termination；
不修改原 reviewer-export 的允许用途，也不为训练导出放宽 final authority。

第一批 RED 测试：tampered trajectory、跨 split task、缺少许可/授权、trusted
event、final sidecar、混入 hidden 内容的 summary 均拒绝；provider hidden reasoning
不导出；SFT target/环境文本分开；RL reward authority 必须 public；terminal mask
和预算可重建。先证明合成数据转换的边界，再讨论真实数据/训练栈和算力费用。

## 后续可并行执行的最小切片

1. RAG：合成 corpus profile/validator/检索函数测试，不接真实 corpus。
2. 波形：合成 CSV parser/边界测试，不默认改变 Agentic 观察面。
3. 训练：合成 export/split validator 测试，不导出真实数据。
4. 主线程审查公共接口与权限/manifest 接线，再分别启用命名 opt-in 条件。

三个叶子模块可以并行，但 schema/registry/controller/result 等共享接口由主线程
统一集成。每个切片单独 RED→GREEN、独立审查、commit；不把“设计写好”计为功能上线。
真实 RAG 语料许可、波形 caps/启用条件、训练 split/授权尚需冻结。
后续正式实验仍须先审计安装 examples 的配对差异，再单独确认模型和付费预算。

## 当前代码依据

- `runners/agent_harness/{reserved_tools,tool_registry,budget,controller,state}.py`
- `runners/agent_harness/{trajectory,evidence_export,result_artifact,authority_profiles}.py`
- `benchmark-vabench-release-v4/operations/calibration_pilot/{mini_swe_vabench,public_validation}.py`
- `schemas/vaevas-{public-validation-profile,final-test-profile,score-sidecar}-v1.schema.json`
- [AA-VAE-028](AA-VAE-028-domain-tool-namespace-gate.md)、
  [AA-VAE-035](AA-VAE-035-production-public-validation-observation.md)、`AGENTS.md`
