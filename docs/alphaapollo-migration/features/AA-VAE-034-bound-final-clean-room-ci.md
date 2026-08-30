# AA-VAE-034：Bound-final clean-room smoke 与 CI

## 思想与来源

延续 AA-VAE-025 的可执行契约与 AA-VAE-033 的 terminal authority：接口单测证明约束，
真实 runner → submission freeze → EVAS → immutable receipt 还需独立的集成证据。
本切片复用已有 r53 三条件 smoke，没有复制新的外部代码、模型轨迹或评分数据。

## 代码与行为

| 文件 | 改动 |
| --- | --- |
| `scripts/run_v4_r53_clean_room_smoke.py` | 增加显式 `--bound-final-authority`；生成前记录 campaign 配置；使用 production scorer 的 profile/context API；检查 receipt 文件 hash 与 generation evidence 字节不变 |
| `tests/test_v4_r53_clean_room_smoke.py` | fake EVAS/subprocess adapter 覆盖 opt-in receipt，非 Docker 模式仍必须被 clean-room claim gate 拒绝 |
| `.github/workflows/evaluator-closure.yml` | production bridge/runner 修改触发 CI；真实 Docker smoke 启用 bound flag，断言 receipt 与不可回写条件 |
| `tests/test_agent_harness_ci_gate.py` | 防止触发路径、bound flag 和关键 evidence assertion 从 workflow 丢失 |

CI 外的实际运行记录、Python/EVAS 身份和文件 hash 位于 `logs/verification-log.md`。
运行产物留在本机隔离 output root，不提交候选、runtime 或生成证据到 Git。

## 能证明与不能证明

- 同一 r53 DUT 任务的 OneShot / Agent-No-EVAS / Agentic 三个独立 runtime 都经过
  freeze 和真实 EVAS 0.8.7 replay，返回可校验、`development_only` 的 sidecar receipt。
- Agent-No-EVAS 公开 EVAS 调用为 0；Agentic 的确定性脚本调用为 1。最终评分不会写回
  campaign result、checkpoint 或存在的 mini-swe trajectory。
- 使用故意不完整的公开 candidate fixture，预期为 `behavior_failure`。这不复现论文
  baseline、不比较模型质量，也不是真实模型的 reasoning/evolution 实验。
- OneShot 仍是 provider-transport 路径，其余 agent 条件使用 Docker；不能宣称三者采用
  完全相同的模型执行路径。原 smoke-local trajectory 不是新的 native typed event ledger。
- 本次仅覆盖一个 DUT 任务；跨 form、跨 attempt lineage、共享 memory 泄漏和完整结果
  denominator 仍需后续专门验证，不能据此把 Phase 5 或总计划标为完成。

## 运行环境注意

本机 Docker 使用 VM 时，`/tmp` 可能不在 daemon 的共享目录内。先前该路径下的运行因
bind mount 不可见而失败；换到允许的 `/Users/.../vaEVAS-next/` 隔离产物目录后通过。
这是部署路径限制，不是 EVAS 缺陷，未修改 EVAS、r53 或 Docker 全局配置。
