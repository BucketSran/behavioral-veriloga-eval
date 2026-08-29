# AA-VAE-032：Score authority report labels

## 功能标识

- ID：`AA-VAE-032`
- 名称：Score authority report labels
- 状态：已验证
- 负责人或变更任务：evaluation claim boundary hardening
- 日期：2026-08-30

## 问题

`score_campaign.summarize()` 曾把 `final_trusted_replay` 与 `final_spectre` 都输出为
`score_authority="final"`。这里的 final 只描述提交冻结后的 terminal replay 位置，却会让
EVAS 开发评分看起来与显式 Spectre formal protocol 具有同一权限。

## 契约

| `judge_kind` | `score_authority` | 可支持的 claim |
| --- | --- | --- |
| `legacy_feedback_evas` | `legacy_provisional_feedback_only` | 旧公开反馈诊断 |
| `final_trusted_replay` | `development_only` | EVAS-scoped 开发、回归与差分比较 |
| `final_spectre` | `formal` | 仅显式 Spectre final protocol |

该标签不改变 verdict；它只阻止 aggregate/report 层扩大底层 judge 的 authority。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `score_campaign.py::SCORE_AUTHORITY_BY_JUDGE_KIND` | 冻结三种 judge-kind 到 authority 的显式映射 | result/claim boundary |
| `score_campaign.py::summarize` | aggregate 使用映射，不再输出含糊 `final` | result/claim boundary |
| `test_benchmarkv4_calibration_pilot.py` | 三种 judge-kind 参数化回归 | tests |

## TDD 与验证

- RED：EVAS trusted replay 与 Spectre 两个 case 因实际值均为 `final` 失败。
- GREEN focused authority/scorer：`5 passed`。
- 完整 calibration-pilot suite：`110 passed`。
- Ruff 0.12.12、Python bytecode compilation、`git diff --check` 通过。

## Claim boundary

- 能支持：score report 的权限标签与当前 EVAS-first/Spectre-conditional 合同一致。
- 不能支持：已有 EVAS 结果成为 formal、Spectre 已运行、或 production typed sidecar 已接入。
- 不修改 r53、EVAS 0.8.7、verdict、denominator、default runner 或 Spectre trigger。
