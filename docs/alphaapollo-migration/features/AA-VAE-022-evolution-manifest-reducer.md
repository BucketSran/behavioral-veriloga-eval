# AA-VAE-022：Evolution manifest and deterministic reducer

## 功能标识

- ID：`AA-VAE-022`
- 名称：Evolution manifest and deterministic round reducer
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 evolution-manifest slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo evolution 在测试时并行/多轮保存候选与验证反馈，再选择候选继续改进。
- 对 vaEVAS 的正式 benchmark，evolution 必须成为一个显式 condition，冻结 roster、
  rounds、budgets、tool registry、public/final authority、memory policy 和 selection rule。

## vaEVAS 适配决策

- 新增通用的 `vaevas-evolution-manifest-v1`；当前冻结实例由测试锁定为 r53 +
  EVAS 0.8.7 development evaluator contract。
- round snapshot 删除 completion order，只保留 public validation candidate evidence；
  snapshot hash 对候选完成顺序不敏感。
- sealed round 必须为 roster 中每个 branch 提供恰好一个 completed/timeout/failed terminal
  record；public metrics 必须完整、已声明、numeric 且 finite。
- candidate selection 先按 manifest 声明的 maximize/minimize 方向比较 public metrics，
  再用 candidate tree hash 和 candidate id tie-break；不看 completion time、model
  identity 或 final score，snapshot 重新加载时会复算 winner。
- final/trusted feedback 进入 evolution round 时 fail closed。
- global deadline 打断未封轮时，必须回退到上一个 sealed incumbent；
  `select_last_sealed_incumbent` 会验证 manifest/snapshot hash、round uniqueness、canonical
  ordering、barrier、retry contract 和 deterministic winner 后再返回最后一个 incumbent。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-evolution-manifest-v1.schema.json` | frozen evolution condition manifest | schema |
| `runners/agent_harness/evolution_manifest.py` | manifest hash, round snapshot, deterministic selection, last-sealed fallback | harness protocol |
| `tests/test_agent_harness_evolution_manifest.py` | scheduler invariance, leakage, deadline, retry regressions | tests |

## 数据与状态变化

- 输入：manifest document, branch candidate records, public validation metrics。
- 输出：round snapshot hash and selected public candidate。
- backward compatibility：不改变 production runner、score sidecar 或 existing campaign。

## 验证证据

- regression tests：`tests/test_agent_harness_evolution_manifest.py`，`29 passed`。
- clean-room smoke：未执行；此切片未接 runtime。
- 未验证部分：hosted multi-model execution, provider nondeterminism, mini-swe adapter parity。

## Claim boundary

- 能支持：evolution condition 的 frozen manifest 与 deterministic public selection contract。
- 不能支持：AlphaApollo-style backend 已经可运行，或正式 benchmark 结果可重复到逐 token。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
