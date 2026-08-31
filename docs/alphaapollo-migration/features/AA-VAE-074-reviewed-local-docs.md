# AA-VAE-074：受控本地文档语料

日期：2026-09-01；基线 `025276c6fc`。

## 思想与边界

把 RAG 当作冻结的信息输入，而不是一次没有记录的网络搜索。复用项目已有的
bounded lexical retriever，不引入向量数据库、联网爬虫或第二套 agent。
本次借鉴的是 AlphaApollo 的显式工具观察、以及 coding harness 的能力声明和
输入身份绑定；没有复制第三方 agent 实现或语料正文。

允许接入真实技术参考资料，但必须区分：内容能读、可以在本地模型上下文使用、
可以发送给外部 API、可以公开再分发。这四件事不能互相推导。

## 代码对应

- `runners/agent_harness/tools/offline_docs.py`：保留 synthetic v1；增加 reviewed
  v2。每份文件固定相对路径、SHA-256、来源、版本、许可/授权证据哈希、污染审查。
  `assert_model_context_allowed(external_provider=...)` 检查外部上下文权限。
- `runners/agent_harness/tools/offline_docs_tool.py`：工具 schema 根据冻结 profile
  返回正确版本；旧 v1 的 schema、描述和 prompt 保持原字节形式。
- `tests/test_agent_harness_reviewed_docs.py`：缺失授权、hash 漂移、越界/symlink、
  敏感来源 URL、污染分类、远程权限和 v1 兼容回归。
- AA-VAE-075 的入口负责在 live 请求前执行远程权限检查，并把 corpus profile
  绑定到配置和结果；普通本地 API 不自动推断客户端是不是远端服务。

元数据是可审计的操作者声明，不是自动获得版权许可、证明语料无污染或验证身份。
所有检索文本只作为不可信参考数据，文档里的指令不获得工具或评分权限。
单文档单 chunk、英文词法检索、每次最多 5 条、每条最多 600 字符等既有限制保留；
较长手册应事先按通用章节人工整理，记录原始文档版本和处理后的内容哈希。

## 推荐语料的实际状态

[Arcadia-1/veriloga-skills](https://github.com/Arcadia-1/veriloga-skills)
在本次审查时固定到
[`7c5d3f03a162ee8131103e9551eee842424360bb`](https://github.com/Arcadia-1/veriloga-skills/commit/7c5d3f03a162ee8131103e9551eee842424360bb)。
GitHub 仓库元数据 `license=null`，根目录未找到 LICENSE；暂不复制正文到本库，
也不据“开源可见”自动批准向模型服务发送。取得适用授权后，优先只选下列通用语言
资料，记录确切版本；不要整库导入。

| 固定路径（位于 `veriloga/references/`） | 原始字节 SHA-256 |
| --- | --- |
| `modules-ports-disciplines.md` | `725306a29523cb598ae2816be020591e846b02e33f79839c125c8564bab07543` |
| `analog-contributions.md` | `872e50c65d521b8c56c276ad23bc468a840fc534f513642a35012cbd21973bf5` |
| `events-state-control.md` | `d379f57902e4ddf2f40bd90d31317dc4524e11c21ec8bffb844cbb59b184f45c` |
| `operators-system-tasks.md` | `ba5d6ddde47e82c439cde8e7dd41fa73ef6a8de44763898ca0a316b18011d232` |

排除 evals、tests、examples、examples-archive、references/categories，以及
EVAS/OpenVAF 工作流；示例电路可能与 benchmark 解答重合，不能因“不含 hidden”
就宣称无污染。`SKILL.md` 即使另行审查后作为资料使用，也不能作为运行指令加载。

Cadence 文档同理：需要确切本地路径、版本和适用使用权；当前工作目录的文件名
检查未找到其原文。本次未恢复历史归档、未导入其正文、未向 API 发送文档内容。
许可证未知、授权证据缺失或外部使用未批准时，不创建可用于 live 的语料清单。

## reviewed v2 的填写要求

沿用 v1 的 `builder/exclusions/documents`，设 `schema_version=2`、
`synthetic_only=false`、`network_enabled=false`。`review` 明确记录
`review_id/reviewer/reviewed_at/purpose=general-language-reference` 和
`external_provider_allowed`。每个文档设 `source=reviewed_local_reference`，显式
`license`、空的 `contamination_categories`（完成审查后才能声明为空），以及
`provenance.origin/revision/upstream_path/rights_basis/rights_evidence_sha256`。

`rights_basis` 只能为 `license`、`owner-permission` 或 `local-license`。许可不明
不能填一个假的哈希让检查通过。正文与授权材料留在受控本地目录，Git 只保留经过
审查的元数据和工程测试。合成示例格式见上述测试文件，不是任何第三方语料的授权。

## 验证与剩余边界

独立审查发现并修复 v2 observation 仍声明 v1 schema，以及 v1 prompt/schema
被无意改变的问题；新增完整 payload 校验和旧 descriptor 哈希断言。复审通过：
35 passed / 2 optional skips（reviewed、offline docs、docs integration）。
这证明语料接入契约，不证明真实语料的检索质量、无污染或模型分数提升。
