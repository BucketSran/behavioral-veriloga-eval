# AA-VAE-021：Memory snapshot and candidate lineage

## 功能标识

- ID：`AA-VAE-021`
- 名称：Memory snapshot and candidate lineage
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 evolution-state slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo evolution 会保存候选方案和验证反馈，供后续轮次改进。
- vaEVAS 需要把可共享 memory 限制为 public evidence，并记录 candidate 的 artifact
  parent 与 influence references，避免把共享反馈误当成同一份可变 workspace。

## vaEVAS 适配决策

- memory snapshot 只接受 candidate summary、public validation、public tool observation。
- final judgment、final score sidecar、private checker、trusted event 不得进入 memory。
- retry snapshot 默认重新开始，不继承 partial memory，除非显式声明 parent snapshot。
- candidate lineage 采用一个 artifact parent 加多个 influence refs；frozen candidate
  是 terminal，不可继续 mutation。
- failed mutation 保留原 tree hash 并写明失败 lineage。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-memory-snapshot-v1.schema.json` | public-only memory snapshot schema | schema |
| `schemas/vaevas-candidate-lineage-v1.schema.json` | candidate lineage schema | schema |
| `runners/agent_harness/evolution_state.py` | snapshot freeze, lineage hash, graph validation | harness state |
| `tests/test_agent_harness_evolution_state.py` | leakage, retry, frozen terminal, cycle regressions | tests |

## 数据与状态变化

- 输入：public memory entries and candidate lineage records。
- 输出：content-addressed memory snapshots and candidate lineage hashes。
- backward compatibility：不改变 existing trajectory/candidate runner。

## 验证证据

- regression tests：`tests/test_agent_harness_evolution_state.py`。
- clean-room smoke：未执行；此切片未接 runtime。
- 未验证部分：real candidate store integration and cross-cell isolation at runtime。

## Claim boundary

- 能支持：evolution memory 和 candidate provenance 的结构化、可审计契约。
- 不能支持：正式 multi-branch evolution 已运行，或 memory 策略产生性能收益。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
