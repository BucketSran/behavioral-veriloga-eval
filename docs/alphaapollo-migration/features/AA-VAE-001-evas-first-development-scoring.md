# AA-VAE-001：EVAS-first 开发评分

## 功能标识

- ID：`AA-VAE-001`
- 名称：EVAS-first development scoring
- 状态：契约已验证，runtime identity 字段待加强
- 日期：2026-08-29

## 思想来源

AlphaApollo 把环境反馈放在 agent trajectory 内部，使模型可以快速执行
`action → observation → update`。对 vaEVAS 而言，可迁移的不是数学任务或 RL
算法，而是“反馈器必须足够快，才能成为开发主循环的一部分”。

用户据此明确了 vaEVAS 的工程策略：当前使用固定 EVAS 作为开发和评测评分器；
Spectre 不进入每轮实验，只在 EVAS 自身变化或明确外部/最终协议要求时承担
compatibility audit。

这里包含两层证据：

- 公开方法启发：agent 需要环境反馈形成完整 trajectory；
- vaEVAS 工程决策：EVAS 与 Spectre 的角色和触发条件由本项目定义，不是
  AlphaApollo 的原始结论。

## vaEVAS 适配决策

- 采用：public EVAS 可在 episode 内提供反馈，strict EVAS trusted replay 对冻结
  submission 评分。
- 修改：将旧 `AGENTS.md` 中“Spectre 是每次 paper-facing final judge”的表述改为
  条件 parity gate。
- 不采用：把模型看到的 public EVAS feedback 直接当成最终 score；把 EVAS score
  伪装为 Spectre score。
- 条件门：若 EVAS code、compiler、simulator semantics、ABI、package 或 pinned
  version 变化，必须对受影响语义跑最小化 Spectre parity。

## 代码与契约落点

| 文件/符号 | 当前作用 | 本轮改动 |
| --- | --- | --- |
| `AGENTS.md` | 顶层 evaluator/judge authority 与 closure 契约 | 已修改为 EVAS-first、Spectre conditional |
| `benchmark-vabench-release-v4/operations/calibration_pilot/README.md` | 当前 runner 的 EVAS trusted-replay 协议 | 已存在，本轮只核对未修改 |
| `benchmark-vabench-release-v4/operations/calibration_pilot/run_campaign.py::run_trusted_replay` | 执行冻结 submission 的 evaluator replay | 已存在，本轮未修改 |
| `benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py` | 生成 EVAS-backed record/aggregate | 已存在，本轮未修改 |
| `benchmark-vabench-release-v4/operations/calibration_pilot/score_spectre_campaign.py` | 冻结 submission 的条件 Spectre audit | 已存在，本轮未修改 |

本轮没有改动 behavioral runtime、scorer 或 EVAS 仓库，因此这里只能声称“角色契约
已经修正并与当前代码入口一致”，不能声称新增了 scorer 功能。

## 数据与状态契约

- development/in-loop feedback：public EVAS observation；
- final development score：strict EVAS trusted replay sidecar；
- required identity：`judge_engine=evas`、EVAS version、checker revision、submission
  hash、score sidecar hash、structured verdict；
- Spectre sidecar：默认不存在；触发 conditional gate 时追加，不能覆盖 EVAS
  sidecar；
- result label：只能写 EVAS-backed，不能写 simulator-independent 或
  Spectre-backed。

## 验证证据

本轮执行：

```text
tests/test_benchmarkv4_calibration_pilot.py::test_trusted_replay_signature_binds_evas_profile
tests/test_benchmarkv4_calibration_pilot.py::test_scorer_requires_explicit_evas_for_trusted_replay
tests/test_mini_swe_vabench.py::test_mini_swe_bash_episode_runs_direct_evas_reads_output_and_submits
tests/test_mini_swe_vabench.py::test_sandbox_cannot_read_sibling_evaluator
```

结果：4 tests passed。

还未验证：

- score report 是否在所有路径显式持久化 `judge_engine=evas`；
- missing structured verdict 是否已经完全移除 legacy zero-exit implicit pass；
- EVAS 代码 diff 到 Spectre parity case 的自动影响映射。

## Claim boundary

该功能支持：

- 当前实验使用 EVAS 快速迭代和评分；
- 报告 EVAS-backed pass rate、failure taxonomy 与 agentic improvement；
- 在不修改 EVAS 时省略 Spectre 日常重放。

该功能不支持：

- 声称 EVAS 与 Spectre 对所有模型 submission 等价；
- 将 EVAS score 改名为 Spectre score；
- 在 EVAS 变化后跳过受影响语义的 Spectre parity；
- 将 public feedback call 的成功当成 hidden correctness。
