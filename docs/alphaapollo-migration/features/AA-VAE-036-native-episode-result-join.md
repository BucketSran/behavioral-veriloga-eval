# AA-VAE-036：原生 episode 与生产最终结果串联

## 思想与范围

- 日期：2026-08-30；负责人：main coordinator；独立任务只做只读审查。
- 延续 AA-VAE-003/026/027/033/035：agent 负责产生动作，environment 管理状态，
  controller 决定何时终止，最终 scorer 只接收冻结提交。完整 episode 才是证据单位。
- 这是我们基于既定 AlphaApollo / coding-agent 边界思想做的 vaEVAS 工程适配，
  不是 AlphaApollo 原有的安全保证；没有复制新外部代码、引入依赖或许可证变更。
- 复用现有 controller、mini-swe bridge、final replay、result artifact 和原子写盘机制，
  不新增第二套 controller、candidate store 或评分协议。

## 具体代码框架

| 文件 / 符号 | 本次改动 | 没有改变什么 |
| --- | --- | --- |
| `operations/calibration_pilot/native_episode.py::run_native_episode` | opt-in Python 组合入口：冻结 profile/身份，预留 attempt，运行 controller，保留失败证据，保存 terminal result | 不创建模型、注册工具或接管默认 campaign CLI |
| `native_episode.py::_ProductionFinalJudge` | 把 controller freeze 转为既有 replay 输入；验证落盘 sidecar 的路径、字节哈希、attempt/task/submission/profile identity | 不重跑、不重新选择候选、不把最终分数变成 Observation |
| `runners/agent_harness/result_store.py::write_immutable_scored_result` | 校验 trajectory/submission/profile/sidecar join 后，复用 fsync + exclusive link 原子发布 | 通用 store 不证明执行来源；生产 caller 必须先验证真实 receipt |
| `operations/calibration_pilot/run_campaign.py::run_cell` | 旧入口也拒绝已预留的 native attempt，包括尚未评分的失败 attempt | 无 native reservation 的历史 mini-swe 路径不变 |
| `tests/test_agent_harness_native_episode.py` | 真实子进程、篡改/失败/重入、test-only public dispatcher、r53 Docker 同链路 smoke | 不发模型 API 请求，不把测试工具注册为生产工具 |
| `.github/workflows/evaluator-closure.yml` | 新模块触发 CI；镜像构建后运行 native result smoke | 保留既有 public-only 和三条件 bound-final smoke |

`operations/` 的完整前缀为 `benchmark-vabench-release-v4/`。

## 一次执行留下什么

```text
evidence/
  native-episode/
    request.json                  # 生成前冻结的身份/profile/预算；预留后不续跑
    trajectory.jsonl              # controller 原生事件；终止后只读
    outcome.json                  # 含失败分类和 cleanup incidents，不隐去失败
    scored-results/<hash>.json    # 仅完整终评证据可发布
  final_submission/               # 既有冻结提交
  bound-final-test/               # 既有一次性最终评分预留
  score-sidecars/<hash>.json      # 既有不可覆盖评分侧车
```

result 文件名使用 schema 的 `artifact_sha256`（排除自哈希字段），不是整个 JSON 文件的
字节哈希；sidecar 文件名则使用 canonical JSON 字节哈希。不能混用两种校验方式。
request/outcome 是单次写入 journal，不承诺崩溃时的原子完整性；崩溃目录保持 reserved。

生成失败：保留 trajectory/outcome，不产生分数或 scored artifact。最终 executor 能明确
分类的基础设施失败：可保留终评 artifact，但 `score=null`，绝不转成 candidate 的 0 分。
写盘失败：保留已完成的 final reservation/sidecar，拒绝重入，不能为补文件再次请求模型。

## 测试与证据

先 RED 再实现：缺失 immutable writer、缺失 composition 入口、旧入口绕过 native
reservation、已有 generation/freeze 目录仍进入新 attempt、CI 未选择新 smoke。

补充回归覆盖：profile 错配、receipt 的路径/内容/attempt/input identity 篡改、缺失
structured verdict、发布失败、模型永不收到 final verdict、公开反馈和最终结果同链路。

真实 r53 `v4-001` Docker smoke 使用公开合同构造的不完整 DUT：公开 EVAS 仿真成功，
最终 hidden checker 判定 `behavior_failure`。candidate、freeze、trajectory、profiles 和
score sidecar 被同一条结果记录绑定。网络关闭，evaluator 不挂入模型 sandbox。
命令、计数、证据目录与哈希见 `logs/verification-log.md`。

## Claim boundary 与后续缺口

可以主张 opt-in 原生 episode 到生产最终结果落盘的单任务链路已验证。
不能主张 baseline 复现、模型改进、所有 form、完整 campaign/CLI/aggregate ledger、
完整 raw model/tool trace、retry orchestration、AlphaApollo reasoning/evolution 已完成。

公开 `run_evas` dispatch 仍只存在于测试；生产 API 接受可信 coordinator 提供的
Policy/Environment，不自动接通该工具，也不支持从任意 legacy JSON 恢复原生轨迹。
现有 trajectory 主要记录 payload/argument hashes，不等于完整内容可重放档案。
backend hash 和封存 release/export provenance 由 coordinator 提供，不是运行时自动认证。
目录预留/只读位/前后哈希用于独占工作目录下的事故防护，不是敌对宿主机安全边界。

r53 和 EVAS 0.8.7 不变；最终 EVAS score 保持 `development_only`，不触发 Spectre。
