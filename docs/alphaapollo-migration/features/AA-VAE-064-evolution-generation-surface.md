# AA-VAE-064：Evolution 生成区与 checker 信息面一致性修复

日期：2026-08-31。这是 harness 的具体缺陷修复，不改 EVAS/r53 或选择规则。

## 发现与代码

`run_evolution_campaign.py` 从 Agentic cell 构建 Evolution 条件。此前
`run_native_evolution.py::_run_branch` 原样导出这个 cell，虽然 Docker 和
environment 已禁用 EVAS，但 exporter 只对 Agent-No-EVAS 做提示词/文件覆盖，
导致模型看到的生成说明与实际可执行能力不一致。

现在 `_branch_generation_cell` 生成内部 NoEVAS 副本，用于分支 export 和
environment 初始化；controller/context 保持原始 Evolution 实验身份。
`branch_generation` config 和 `branch-runtime.json` 记录实际导出 arm。
公开 validation 与最终评分原本已有独立运行区，继续使用原始 cell，保留各自
所需的公开 checker 配置。原始 cell 不变，final 仍只评分一个冻结候选。

`run_campaign.py::NO_EVAS_AGENTIC_WRAPPER` 把反馈不可用限定为当前生成工作区，
避免否认 Evolution 显式提供的上一轮公开反馈；移除过时的“private Spectre
judge”断言，改为冻结提交后的 trusted replay。不删除合法的语言/语法说明。

## 验证与限制

`tests/test_agent_harness_evolution_extensions.py` 锁定真实 export 参数、
environment 参数与逻辑条件的区别、原 cell 不变，以及真实 r53 导出中的
prompt/access policy/evas_runtime.json 分离。对应行为先 RED 再 GREEN。
既有 three-form Docker Evolution smoke 继续验证双模型双轮、公开验证、一次
最终评分。精确运行结果见 verification log。

这是权限与信息披露的一致性修复，不证明不同镜像的全部资料完全匹配，
也不证明 Evolution 的模型效果。普通 NoEVAS 条件和 legacy 默认路径不变。
