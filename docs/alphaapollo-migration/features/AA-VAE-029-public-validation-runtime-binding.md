# AA-VAE-029：Public-validation runtime binding

## 功能标识

- ID：`AA-VAE-029`
- 名称：Public-validation runtime binding
- 状态：generic runtime 已验证；production adapter 待实现
- 负责人或变更任务：Phase 5 authority separation
- 日期：2026-08-30

## 问题

原有 generic harness 已区分 `PublicValidator` 与 `FinalJudge`，controller 也只在 submission
freeze 后调用 final judge。但 public-validation observation 只绑定 candidate hash，没有
记录或检查 validation profile identity。这意味着一个环境实现如果调用了错误 checker、
错误 EVAS 配置或另一个 campaign profile，反馈仍可能进入下一轮 model observation。

## 运行时契约

- campaign 在构造 controller 时提供固定的 `public_validation_profile_sha256`。
- public-validation action 只有在 profile 已绑定时才允许进入 environment dispatch。
- public-validation observation 必须返回相同的 `validation_profile_sha256`；缺失和错配都在
  model-visible event 之前 fail closed。
- capability 必须是 model-visible、read-only、candidate-bound，且
  `records_private_evidence=false`、`may_enter_model_observation=true`。
- canonical observation 与 trajectory event 都保留 profile hash，供 memory snapshot、
  evolution reducer 和最终 result artifact join 使用。
- serializer 为新文档显式输出该字段，但 v1 schema 仍接受字段缺失的历史文档；public
  validation 的强制性由当前 controller runtime gate 保证，避免破坏旧证据读取。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-observation-v1.schema.json` / `state.py::Observation` | 新增 nullable validation profile hash | wire/state |
| `schemas/vaevas-tool-descriptor-v1.schema.json` / `tool_registry.py` | 固定 public-validation evidence/effect contract | authority registry |
| `controller.py::EpisodeController` | pre-dispatch profile gate、post-step exact-match gate、trajectory evidence | controller |
| `tests/test_agent_harness_authority_runtime.py` | unbound、missing、mismatch、invalid profile 与 descriptor tests | tests |

## TDD 与验证

- RED：`5 failed`，分别暴露缺失 controller profile、Observation field、post-step mismatch gate
  和 registry evidence restriction。
- GREEN focused authority/protocol/registry/controller/meta-schema：`86 passed`。
- 完整 generic harness + meta-schema：`285 passed`。
- Ruff 0.12.12、Python bytecode compilation、`git diff --check` 通过。
- 独立 code review 首轮发现 observation-v1 required-field 兼容性问题；独立修复 commit
  `8146253c2c` 加入历史文档回归后，follow-up review 为 `APPROVE`，零剩余 finding。

## Claim boundary

- 能支持：generic controller 不会让未绑定或 profile 错配的 public-validation observation
  进入模型；trajectory 可关联 exact validation profile。
- 不能支持：现有 production `run_evas` 已经通过此 adapter、final EVAS sidecar 已绑定，或
  formal campaign 已切换到 generic controller。
- 不修改 r53 release bytes、EVAS 0.8.7、旧 mini-swe 默认 runner、最终 score authority 或
  Spectre 条件兼容门。
