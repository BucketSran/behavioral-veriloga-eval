# AA-VAE-018：Backend identity/profile contract

## 功能标识

- ID：`AA-VAE-018`
- 名称：Backend identity/profile contract
- 状态：已验证，尚未接入 campaign/result
- 负责人或变更任务：Phase 1 backend-profile schema slice
- 日期：2026-08-30

## 思想来源

- AlphaApollo 的 reasoning 与 evolution 是不同推理路径；后者还有 roster、round、
  feedback 和 selection 等额外条件。它们不能只靠一个自由文本 condition 名区分。
- coding-agent framework 通常把 agent/backend 与 runtime/environment 分开；backend
  负责 model request 和 action production，environment 负责 tool、workspace、budget、
  candidate 与 done。
- vaEVAS 现有 campaign 已经记录 model/provider、release、condition 和预算；本功能的
  目标是补 backend 自身身份，不复制这些运行值。

## vaEVAS 适配决策

- 新增 `vaevas-backend-profile-v1`，记录 backend profile ID/family/version、
  `single_trajectory` 或 `round_based_evolution`、proposal formats、canonical
  Action/Observation/normalizer identity、model-interface flags 与 state scope。
- backend profile 只列 `requires_campaign_contracts` 和
  `requires_environment_contracts` 的合同名字，不携带 model、temperature、token、
  wall-time、release、condition、tool descriptor、accepted tool name 或 judge 值。
- 所有 profile 必须依赖 model identity、decoding、turn/wall budget、condition、clean-room、
  proposal allowlist、trajectory、candidate store、submission freeze 和 final judge。
- evolution profile 还必须依赖 roster、round budget、feedback scope、selection 和 final
  submission policy；具体 roster/round/fanout 值仍由 campaign manifest 在首次模型调用
  前冻结。
- state 只能是 `none` 或 `episode_local`，明确禁止跨 task 和跨 condition 共享状态。
- supported/preferred proposal formats 与 model-interface support flags 必须双向一致。
- `backend_profile_sha256()` 只为已经通过 schema 的 profile 计算 canonical hash；它不
  冒充 schema validator。后续 campaign/result 应把该 hash 作为 join key。
- 不实现 backend adapter、provider client、tool registry、领域工具、controller 接入或
  campaign migration。

## 代码改动

| 文件/符号 | 改动 | 所属层 |
| --- | --- | --- |
| `schemas/vaevas-backend-profile-v1.schema.json` | strict backend identity/dependency schema | schema |
| `runners/agent_harness/backend_profile.py::backend_profile_sha256` | schema-validated profile 的 canonical content identity | protocol |
| `runners/agent_harness/__init__.py` | 导出 profile hash API | harness API |
| `tests/test_agent_harness_backend_profile.py` | 锁定 profile、ownership、scope 与 hash | tests |

## 数据与状态变化

- 输入：已通过 schema 的 backend profile JSON document。
- 中间状态：canonical JSON ordering。
- 输出：machine-checkable backend profile 与独立 SHA-256 content identity。
- 新增 schema 字段：backend identity、inference mode、proposal compatibility、model
  interface、state scope、external contract dependencies。
- backward compatibility：现有 campaign/mini-swe 不读取该 profile，行为不变。

## 验证证据

- regression tests：`tests/test_agent_harness_backend_profile.py` 覆盖 mini-swe、
  AlphaApollo reasoning/evolution、ownership rejection、state isolation、proposal
  compatibility、evolution dependencies、canonical hash 与非法 JSON value。
- clean-room smoke：未执行；profile 尚未接入 runtime。
- evidence/manifest hash：测试证明 hash 性质，没有生成正式 profile artifact。
- 未验证部分：campaign/result hash join、backend adapter identity enforcement、
  tool/validation/evolution manifests、真实 multi-model execution。

## Claim boundary

- 能支持：三类计划 backend 现在可以用同一 strict schema 表达身份、推理模式、
  proposal/state 能力与外部合同依赖。
- 不能支持：backend 已可运行、模型/预算/工具条件已经匹配、mini-swe parity、
  reasoning/evolution 收益或正式 r53 evaluation migration。
- 本功能没有修改 EVAS 代码、版本、compiler/simulator/ABI 或 packaging，不触发
  Spectre parity gate。
