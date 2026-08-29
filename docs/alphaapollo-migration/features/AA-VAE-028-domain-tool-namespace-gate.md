# AA-VAE-028：Domain-tool namespace gate

## 功能标识

- ID：`AA-VAE-028`
- 名称：Domain-tool namespace gate
- 状态：占位契约已验证；五类具体工具均 deferred
- 负责人或变更任务：Phase 4 domain-tool design gate
- 日期：2026-08-30

## 为什么先保留命名空间

AlphaApollo 的 reasoning/evolution 结构和 coding-agent 的工具设计可以启发 vaEVAS，
但“其他框架存在某种工具”不构成加入 benchmark harness 的证据。新增工具可能同时改变
模型能力、观测信息、token/turn 消耗和泄漏面，进而破坏 matched comparison。

因此本功能只注册五个 `reserved` marker：它们没有 handler、模型不可见、不可调用、
不消耗运行预算，也不能读写 candidate 或进入 memory。marker 只让完整 registry 能记录
“这个扩展族被明确考虑过”，不预先批准最终 tool name、参数、输出或实现。

## 共同激活门

任一具体工具进入 active registry 前，必须单独回答：

1. 有哪些真实 trajectory failure 或可量化 workflow cost？
2. Bash、公开 EVAS 与既有 submission transport 为什么不足？
3. 数据源是否公开、许可清晰、版本固定且不会造成 benchmark contamination？
4. 工具是 read-only、candidate mutation、terminal transport，还是 evaluator authority？
5. 哪些 condition 获得能力，matched comparison 如何保持 capability 等价？
6. 消耗哪个 turn/tool/EVAS/token/wall/disk budget？
7. action、observation、candidate before/after hash 和 result 如何进入证据链？
8. 是否泄漏 checker、fault、final-test、跨任务 memory、网络或宿主路径？
9. 是否需要独立 ablation 区分 tool、backend 与 evolution 的收益？
10. 哪个最小 RED test 和 clean-room smoke 能证明 fail-closed 与副作用契约？

## 五类工具的本轮决策

| 保留族 | 当前替代能力 | 主要潜在价值 | 当前阻塞证据 | 决策 |
| --- | --- | --- | --- | --- |
| `vaevas.reserved.candidate` | sandboxed Bash + content-addressed freeze | 原子 edit/checkpoint、清晰 diff 与 rollback | 尚无失败统计证明 Bash edit 是主要瓶颈；transaction store 尚未落地 | deferred |
| `vaevas.reserved.public_validation` | 公开 EVAS 0.8.7 Bash 调用 | 结构化 diagnostics、稳定 candidate/profile binding | Phase 5 production authority adapter 尚未完成；不能先把 evaluator 包装成普通工具 | deferred |
| `vaevas.reserved.retrieval` | task public workspace 与允许的静态资料 | 数据手册/RAG 查询 | corpus、许可、版本、污染面、网络和缓存确定性尚未冻结 | deferred |
| `vaevas.reserved.submission` | `vabench-submit` | typed terminal action、减少 shell quoting 错误 | 当前 transport 已通过 clean-room smoke；收益和兼容迁移成本尚无 ablation | deferred |
| `vaevas.reserved.waveform` | Bash 读取公开 log/CSV/artifact | 压缩波形、指标和失败定位 | 允许字段、截断、数值稳定性和 EVAS 预算语义尚未冻结 | deferred |

## 代码落点

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/reserved_tools.py::reserved_domain_tool_descriptors` | 生成五个无 handler 的 fresh descriptors | capability registry |
| `runners/agent_harness/__init__.py` | 导出 marker factory | public harness API |
| `tests/test_agent_harness_reserved_tools.py` | registry identity、effective capability、fail-closed 与 final-judge exclusion | tests |

## 验证证据

- RED：测试 collection 因 `runners.agent_harness.reserved_tools` 不存在而失败。
- GREEN：reserved/tool-registry focused suite `36 passed`。
- placeholder 加入后 full `registry_sha256` 改变，但 model-visible
  `effective_capability_sha256` 与 active Bash 工具集合保持一致。
- 五个名称全部在 environment dispatch 前以 `reserved_tool` 拒绝。
- Ruff 0.12.12、Python bytecode compilation 与 `git diff --check` 通过。

## Claim boundary

- 能支持：harness 已明确保留并 fail-close 五类领域工具扩展位置；matched backend 不会因
  marker 的存在获得额外能力。
- 不能支持：任何一种领域工具已经实现、能改善模型表现、或应出现在正式 benchmark。
- final EVAS/Spectre judge 不是普通工具；本功能不改变 r53、EVAS 0.8.7、production
  submission/score authority 或 Spectre 条件门。
