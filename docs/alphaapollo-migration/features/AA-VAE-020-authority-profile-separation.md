# AA-VAE-020：Public/final authority profile separation

## 功能标识

- ID：`AA-VAE-020`
- 名称：Public validation and final-test authority separation
- 状态：已验证，尚未接入 production runner
- 负责人或变更任务：Phase 1 authority-profile slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 的 evolution 使用反馈改进候选；vaEVAS 必须进一步区分“可见反馈”和
  “最终评分”，否则 final score 会泄漏到下一轮 generation。
- 可信评测需要把 public validation profile 与 final trusted replay profile 分开绑定。

## vaEVAS 适配决策

- public profile 固定为 r53 + EVAS 0.8.7、in-episode、model observation、
  episode-local public memory、candidate-tree input。
- final profile 固定为 r53 + EVAS 0.8.7、post-submission-freeze-only、trusted-only、
  forbidden model observation/memory/selection/repair、frozen-submission input。
- final replay 只允许 infrastructure failure 下的同一 frozen submission、新 judge
  attempt，且禁止模型重入。
- Spectre policy 保持 conditional，不进入日常 EVAS 0.8.7 development scoring。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-public-validation-profile-v1.schema.json` | public validation authority schema | schema |
| `schemas/vaevas-final-test-profile-v1.schema.json` | final trusted replay authority schema | schema |
| `runners/agent_harness/authority_profiles.py` | profile hashes, input binding, replay guard | harness protocol |
| `tests/test_agent_harness_authority_profiles.py` | leakage, Spectre conditional, replay lineage regressions | tests |

## 数据与状态变化

- 输入：public/final authority profile documents and candidate/submission hashes。
- 输出：profile hash、profile-input identity hash、final replay classification。
- backward compatibility：不改变 scorer 或 campaign behavior。

## 验证证据

- regression tests：`tests/test_agent_harness_authority_profiles.py`。
- clean-room smoke：未执行；此切片未接 runtime。
- 未验证部分：runner-level enforcement and sidecar joins。

## Claim boundary

- 能支持：public validation 与 final trusted replay 的权限差异可机器检查。
- 不能支持：正式 campaign 已经强制使用这些 profile，或 final sidecar schema 已统一。
- 本功能不修改 EVAS，不触发 Spectre parity gate。
