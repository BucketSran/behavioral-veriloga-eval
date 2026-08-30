# AA-VAE-057：合成离线检索与 native opt-in 接线

日期：2026-08-31。承接 AA-VAE-056；不是正式 RAG 实验或真实语料上线。

## 思想与边界

沿用既有 AlphaApollo 迁移中的工具注册、公开参考资料和逐轮反馈思想；
不复制数学语料、在线检索服务或 XML parser，也不新增依赖。实际实现以本仓库
controller/registry/native adapters 为基础。没有新增外部代码借用或 private 访问。

第一版仅接受操作者提供的 `synthetic_fixture` / `CC0-1.0` 合成资料；声明与 hash
可以验证契约和字节一致，不能自动证明文本无污染或法律许可真实有效。检索内容
是低信任参考数据，不是系统指令或执行权限。任意来源、真实 corpus 和线上服务
仍未启用。保留所有 reserved marker，不把 marker 本身改成 active。

## 代码对应

| 路径 | 新职责 |
| --- | --- |
| `runners/agent_harness/tools/offline_docs.py` | 严格 manifest/profile 校验，受限文件读取，不可变内存快照，确定性词法检索 |
| `runners/agent_harness/tools/offline_docs_tool.py` | 独立 `vaevas_docs_search` descriptor/handler；复用 `tool_call`，参数拒绝和 candidate 绑定 |
| `runners/agent_harness/backends/mini_swe.py` | 显式 accepted-tool 集合；默认仍只接受 Bash |
| `operations/calibration_pilot/mini_swe_vabench.py` | 模型 adapter 可显式接收工具 schema；legacy 调用不传时保持 Bash-only |
| `operations/calibration_pilot/run_native_mini_swe.py` | 可选 `docs_corpus` Python API；共同 prompt/tool-set、复合分发、私有交互和 manifest 绑定 |
| `operations/calibration_pilot/score_campaign.py` | 只读重算 corpus/registry 身份，检查检索 observation 的 profile，结果显式保留 intervention |
| `operations/calibration_pilot/result_ledger.py` | 不允许合成扩展记录静默进入已有三条件对比 |

表中 operations 路径均相对 `benchmark-vabench-release-v4/`。

接口：`OfflineDocsCorpus.from_manifest(root, manifest)` → `corpus.search(query,
top_k=3, section_filter=None)`；`corpus.profile` 返回 detached 文档。
native 函数名用下划线 `vaevas_docs_search`，逻辑上对应设计中的 docs/search
命名空间；避免把 dotted namespace 当成所有 provider 都支持的函数名。

限制：64 文档、每份 64 KiB、query 512 字符、top_k 1–5、每片段 600 字符。
profile 冻结来源/许可、排除政策、索引算法/分词/整文档分块/tie-break 和各上限。
只读取构建时快照，搜索不访问网络或后续可变文件。来源 hash/索引/profile hash
进入响应；profile 又进入 descriptor、有效能力 hash 和 launcher manifest，从而
复用既有 request → trajectory → frozen submission → final artifact 身份链。

## 接入与未接入

显式 `run_prepared_native_mini_swe(..., docs_corpus=corpus)` 支持 native mini-swe
和 Reasoning（native calls / strict JSON），适用 Agentic / Agent-No-EVAS。
OneShot 在预留 runtime 前拒绝。缺省参数不改变旧路径或工具集合。

这是开发用 Python API，不是 campaign CLI 功能；也不宣称完整 Evolution RAG。
现有 scorer 可以读取单条证据，但 aggregate/paired ledger 明确拒绝 extension
记录。正式配对实验还需冻结实际 corpus、条件/预算/版本和单独的汇总协议，不能
只因两行都标 Agentic 就计算工具收益。新工具不增 final 权限，不返回终评分数。

## 验证入口

- `tests/test_agent_harness_offline_docs.py`：来源/hash/路径/界限/确定性/快照/篡改。
- `tests/test_agent_harness_optional_tools.py`：默认拒绝；显式工具及反馈进入下一请求。
- `tests/test_agent_harness_docs_integration.py`：两 backend/三格式组合 × EVAS yes/no，
  权限预算、OneShot 拒绝、同条 trajectory/score join、禁止静默汇总。
- 同文件的 `test_r53_docker_synthetic_docs_freeze_and_evas_score`：两 backend 真实
  Docker + EVAS 0.8.7、免费 scripted provider、公开中性候选。已加入 CI。

完整命令、RED/修复和最终稳定树结果见 `logs/verification-log.md`。
测试证明工具/证据链连接性，不证明检索有用、模型更强或新 baseline 已复现。
