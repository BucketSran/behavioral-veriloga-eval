# AA-VAE-081：匹配的真实模型差分与工具增量条件

日期：2026-09-01

## 思想与边界

AlphaApollo 式 Reasoning/Evolution 接线此前只有“组合工具能否贯通”的验收，不能
回答没有工具时会发生什么。本轮没有再造调度器，而是在现有入口中新增显式
`baseline` 条件，使工具能力成为冻结实验变量：baseline 必须证明 RAG/波形均未被
调用，`rag-waveform` 必须证明二者被实际成功使用，Evolution 还要证明候选绑定的
公开波形反馈只在下一轮屏障后暴露。

第一项继续复用现有 legacy/native 六格差分入口；第二项由四个独立 root 组成
Reasoning/Evolution × baseline/rag-waveform。两种 estimand 分开报告，不把多分支
Evolution 的额外算力伪装成等预算纯 backend 增益，也不从 family001 外推总体质量。

## 代码落点

- `comparison_live.py`、`deepseek_budget.py`：刷新 2026-09-01 官方 DeepSeek
  模型/价格审查日期，并把完整 CNY/USD 峰谷价格表冻结到 provider profile；实际
  守卫仍按峰值保守预留。
- `run_combined_tools.py`：新增 `--intervention baseline|rag-waveform`；baseline
  不注册 docs/waveform 扩展、不向 native/Evolution 执行器传递相应能力；报告新增
  `condition_acceptance_passed`，并保留只对工具条件成立的
  `combined_acceptance_passed`。
- `combined_tool_evidence.py`：投影器接收预期工具面；关闭 public waveform 的
  Evolution 不再把“没有 receipt”误判成证据缺失，但任何意外工具尝试仍会使条件
  验收失败。
- `reporting_sources.py`：只读记录的 identity/report group 明确包含 intervention，
  防止 baseline 与工具条件在 Inspect/外部分析中静默合并。
- `plans/real-model-differential-and-incremental-study.md`：冻结两项研究的问题、矩阵、
  对比、费用权限、停止条件与最大 claim。

## TDD 与实际缺陷

先写 baseline freeze、执行参数、证据投影和只读报告回归。真实 Docker/EVAS 门随后
发现 Evolution baseline 把空扩展写为 `extensions={}`；批次证据验证器只接受省略
扩展或非空合法扩展，因此终局回读失败。修复为 baseline 完全省略该字段，保持
Evolution 既有 schema/验证器不变。该问题无法由纯 mock 的生成结果发现。

## 尚未执行的部分

没有发起真实模型 HTTP 请求，也没有读取凭据。付费执行仍需用户提供精确总费用
上限与 repo 外 owner-only 凭据文件路径。Study 2 当前每个 root 各有独立守卫，
所以四个 cap 的合计才是风险上限，报告不能只写单 root cap。
