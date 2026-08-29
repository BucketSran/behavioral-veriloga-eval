# AA-VAE-026：Scored result artifact join

## 功能标识

- ID：`AA-VAE-026`
- 名称：Scored result artifact join
- 状态：已验证，尚未接入 production campaign writer
- 负责人或变更任务：Phase 2 evidence/result closure
- 日期：2026-08-30

## 思想来源

- AlphaApollo 风格的 trajectory/evolution 需要把最终答案、反馈和评测证据放在可追溯对象里，
  而不是只保存一个最终 response。
- vaEVAS 的可信评测还需要绑定 frozen submission、public/final authority profile、EVAS
  sidecar 和 final profile input identity，防止“结果 JSON 被重新 hash 后看似合法”。

## vaEVAS 适配决策

- 采用：一个 content-addressed scored-result artifact 绑定 terminal trajectory tail、
  submission tree、final judgment、authority profile hashes 和 score sidecar hash。
- 修改：score sidecar 保持 model-invisible；artifact 只记录摘要引用，validator 接收完整
  sidecar 文档并重新校验语义 join。
- 不采用：把 final score sidecar 放入 evolution/shared memory；把 artifact builder 直接接入
  production runner。
- evaluator/claim 边界：当前 sidecar authority 仍是 EVAS 0.8.7 development-only；Spectre
  仍只在 EVAS/evaluator 协议变化或外部审计要求时触发。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `runners/agent_harness/result_artifact.py` | builder/hash/validator for scored result artifact | harness evidence |
| `schemas/vaevas-result-artifact-v1.schema.json` | artifact wire schema | schema |
| `schemas/vaevas-score-sidecar-v1.schema.json` | immutable score sidecar schema | schema |
| `tests/test_agent_harness_result_artifact.py` | sidecar binding, semantic tamper, profile substitution regressions | tests |

## 数据与状态变化

- 输入：scored `EpisodeResult`、semantic trajectory events、backend/tool/authority identities、
  immutable EVAS score sidecar。
- 中间状态：canonical artifact hash、sidecar hash、final profile input identity。
- 输出：`vaevas-result-artifact-v1` document。
- backward compatibility：不改变 mini-swe、r53、EVAS 0.8.7、真实 score sidecar 或现有 runner。

## 验证证据

- regression tests：`tests/test_agent_harness_result_artifact.py`，`11 passed`。
- complete generic harness：`tests/test_agent_harness_*.py`，`248 passed`。
- clean-room smoke：未重跑真实 Docker；本切片未接 production campaign writer。
- 未验证部分：production campaign result writer、真实 r53 result ledger、hosted run artifact upload。

## Claim boundary

- 能支持：通用 harness 可以构造并验证 terminal scored evidence 的不可变 join。
- 不能支持：历史 paper campaign 结果已经重写为该 artifact，或正式 benchmark 分数已经由该
  artifact 产出。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
