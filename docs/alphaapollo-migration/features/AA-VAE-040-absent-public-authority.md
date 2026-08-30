# AA-VAE-040：显式缺席的公开评测权限

## 思想与范围

沿用 AlphaApollo 的公开反馈/轨迹分离和 coding-agent 的执行权限边界，
把“本条件没有公开 EVAS”变成可验证的代码契约，而不是提示词约定。
这是 vaEVAS 自己的条件控制实现，没有复制新的外部代码或引入依赖。
No-EVAS 限制生成阶段，冻结后的 EVAS 0.8.7 终评仍然必要。

## 代码地图

- `runners/agent_harness/authority_profiles.py::episode_public_profile_sha256`：
  OneShot / Agent-No-EVAS 要求 public profile 为 `None`；Agentic 必须有真实
  profile。final profile 始终有效且必需，存在的两个 profile 必须绑定同一配置。
- `operations/calibration_pilot/native_episode.py`（v4 下）：写入显式 null
  public profile/hash，拒绝缺席权限下仍暴露 public-validation capability。
- `runners/agent_harness/controller.py`：episode start 记录权限摘要；未声明
  public authority 的 observation 在进入模型之前被拒绝，保留主失败分类。
- `trajectory.py::validate_absent_public_authority`：即使重新计算了 hash chain，
  带公开验证 hash、公开调用预算或错误开始声明的轨迹也不能作为缺席条件证据。
- `result_artifact.py` / `result_store.py`：不可变 join 接受真实缺席，仍验证
  freeze、final profile、sidecar；不能通过 null 绕过最终评分权限。
- `schemas/vaevas-result-artifact-v2.schema.json`：v2 专门表示缺席，字段必须
  存在且为 null；历史 profile-present v1 继续使用原 schema，不原地改写语义。
  native request 同样按有/无 profile 分别标 v1/v2。

## 验证和边界

`tests/test_agent_harness_absent_public_authority.py` 覆盖无 EVAS 终评、权限
矛盾、缺席能力、重哈希注入、start/step 反馈在进入 policy 前被拒绝。
连同既有 authority/controller/trajectory/native/artifact/store/CI tests：
**163 passed, 1 skipped**；Ruff 0.12.12 和 whitespace 检查通过。
独立审查无阻断，保留 OneShot 专用 toolset 需由 launcher 保证的 WATCH。

本切片证明权限/证据契约，不证明 Bash 隔离，也不使通用 native episode API
自动成为完整 OneShot runner。三条件入口和真实 Docker/campaign 证据分别另记。
r53、EVAS、legacy 默认和最终分数不可回流的边界不变。
