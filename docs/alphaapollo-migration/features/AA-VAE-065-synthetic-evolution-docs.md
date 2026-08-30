# AA-VAE-065：synthetic 文档进入 Evolution 分支

日期：2026-08-31。只开放 `run_native_evolution(..., docs_corpus=...)` 开发 API；
没有新增 CLI、真实语料、在线检索、付费调用或默认条件。

## 代码与思想

- `run_native_evolution.py` 复用现有 `OfflineDocsTool`、registry、ReasoningPolicy、
  `_RecordedEnvironment`。各分支独立包装同一冻结 corpus，不复制 agent loop。
- 完整 profile、digest、`synthetic-frozen-docs-v1` 干预身份先进入 config，
  再计算配置 hash；registry 同时绑定 docs descriptor。初始提示只包含身份，
  文本通过 `vaevas_docs_search` 返回，不把整份语料预塞给模型。
- `offline_docs_tool.py` 对精确 Evolution 条件设置
  `may_enter_shared_memory=false`。检索观察留在本分支；原有共享内容仍为
  封闭轮次里的候选代码与公开 validation 反馈。最终结果不回流。
- `score_campaign.py::summarize` 显式拒绝 Evolution 行，即使没有 docs；
  final-result 保留 extension 身份与单 trajectory 不可混池声明。既有 ledger
  对非普通 arm/extension 的拒绝不变。

## 验证与边界

`tests/test_agent_harness_evolution_extensions.py`：两分支两轮、预算、身份、初始
提示不含 corpus、私有观察/轨迹、无共享 docs 事件、错误条件/输入及混池拒绝。
`test_agent_harness_evolution_campaign.py::test_r53_docker_synthetic_docs_evolution`
免费 scripted-provider 真 Docker：双模型双轮 docs → 候选 → 公开验证 → freeze
→ 一次 EVAS final score；CI 单独登记。88 项相关回归通过、6 opt-in 跳过，
真实 smoke 1 passed。独立代码审查 ACCEPT。

引用的思想是将工具反馈和短期记忆明确分层，而不是迁移数学 XML 或训练栈。
synthetic corpus 的格式连接不证明检索质量、真实许可/去污染或模型能力提升。
本切片不把检索事件直接共享；模型把公开知识写入候选代码属于既有候选共享。
