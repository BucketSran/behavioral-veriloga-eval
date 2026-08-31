# AA-VAE-070：批次级恢复，不恢复未完成的模型状态

- 日期：2026-08-31；基线 `e46a9d6719893d500071f6cf5ce744d4dc7f439a`。
- [验收计划](../../../plans/batch-resume.md)；主线程独占集成、记录和 Git。
- 范围：Native campaign 与独立 Evolution batch；r53 / EVAS 0.8.7 不变。

## 为什么做、参考什么

之前 Native 的 fresh-attempt retry 只在当前进程内工作；进程退出后缺少批次级
完成记录和重调度入口。旧 legacy `--resume` 是对话恢复，不能拿来绕过 Native 的
冻结/最终评分不可重入边界。本次增加的层在 campaign 外围，不在模型内部。

参考检索日期为 2026-08-31：

- [Inspect AI Eval Sets](https://inspect.aisi.org.uk/eval-sets.html)：独立持久目录
  记录完成情况，重启只调度未完成工作。迁移这项调度思想，不迁移其动态扩展任务集
  或自动清除失败日志行为；vaEVAS 的 roster 固定，历史尝试保留。
- [Inspect AI Handling Errors](https://inspect.aisi.org.uk/handling-errors.html)：
  区分进程崩溃与已记录的样本异常，并保留完成样本。vaEVAS 更保守：没有完整证据
  不能推定“没花钱”，也不因答案错误而重试。
- [Harbor Core Concepts](https://www.harborframework.com/docs/core-concepts)：
  job 管理一组 trial，trial 负责 agent/environment/verifier。对应到现有
  campaign/cell/attempt 分层；不把外层恢复塞进 controller，也不启用重新评分。

没有直接复制第三方源代码，没有引入 Inspect/Harbor/LangGraph 依赖。它们的完整
solver/sandbox/logging 体系会与当前 harness 重叠；本切片只补 vaEVAS 必需的身份
绑定与调度适配。文件发布复用既有 `result_store` 原子写入，锁复用 OS `flock`，
并发复用标准库线程池，轨迹/评分读取复用已有校验器，不另造 agent 或评分系统。

## 代码结构与具体改动

下表中的 calibration 文件均在
`benchmark-vabench-release-v4/operations/calibration_pilot/`。

| 层 / 文件 | 新能力 | 没有改变什么 |
| --- | --- | --- |
| `runners/agent_harness/batch_resume.py` | 源码/配置/roster 冻结、排他调度锁、终态文件摘要、只追加的全分母索引 | 不创建模型、不执行评分、不判定答案优劣 |
| `attempt_sequence.py` + calibration `run_native_attempts.py` | 读取既有封存 prefix；恢复下一 fresh attempt；补齐缺失 selection；复用完成 selection | 预算不重置，沿用原 retry 分类、lineage、轨迹与 score reader |
| calibration `run_native_batch.py` + `run_campaign.py`、wrapper | 完整 roster 先校验后调度；lazy client；完成项零模型/评分调用；worker 结果按冻结顺序汇总 | legacy 默认与对话恢复不变，原 Native 单任务不允许原地重入 |
| calibration `evolution_batch.py` + `run_evolution_campaign.py` | 显式 `--batch` / 重复 `--cell` / `--resume`；每 cell 外层 attempt；完成证据复用 | 复用原 round engine/public-only reducer/final judge，不恢复部分 round 或共享记忆 |
| calibration `native_episode.py` + `run_native_evolution.py` | 抽取既有只读 final receipt 校验供两条路径共用；公开验证执行观察到的镜像 ID | 不新增 judge；不改候选选择、反馈内容或分数定义 |
| `.github/workflows/evaluator-closure.yml` | 新源文件触发 gate；真实 Docker/EVAS 完成项重开测试 | 免费脚本 provider，不进行真实模型质量实验 |

## 恢复规则

1. 使用原命令、原目录，加 `--resume`；不能改源码、模型/endpoint、roster、预算、
   watchdog 或镜像身份。镜像观察到的 ID 也是实际运行的 ID，而不是只记录可变 tag。
2. 先校验所有已存在单元，再创建客户端。任何未知运行中状态/坏证据都阻止新增调用。
3. 完成包括有效零分或终态失败，不只包括通过。已完成项原文件保持不变，不重新评分。
4. Native 只有完整、可验证、符合原 retry policy 的 pre-final attempt 可继续；
   已耗 logical model calls 和 attempt 次数沿 lineage 延续，不退还。最后终态已写而
   selection 缺失时，只补 selection，不再执行模型/工具/评分。
5. Evolution 的外层 retry 只允许配置已绑定、仅有 `setup-request.json` 和终态文件、
   且已验证零启动/零成本的 setup failure。存在 public-validation/final runtime、
   断裂链接或不明文件，也一律阻断。普通模型失败、部分 Evolution、final/cleanup/
   protocol 异常不能自动重跑。

完成项还会从冻结 campaign 重建既有 engine config，核对 rounds、budget、roster、
镜像、命令和源码；并用原 final judge 的只读校验核对 submission、profile、
episode/attempt/task 和 sidecar 内容，不能靠几个相互一致但未绑定配置的摘要放行。

目录中的 `.batch/manifest.json`、`cell-*.json`、`index-NNNNNN.json` 是本地运行
账本，不是新的模型可见 memory，也不是公开结果导出。文件摘要用于发现变化，
并不提供抵抗受信任 host 管理员主动重写整套记录的密码学认证。

## 验证与 claim boundary

测试入口：`tests/test_agent_harness_batch_resume.py`、
`test_agent_harness_attempt_sequence.py`、`test_agent_harness_native_attempts.py`、
`test_agent_harness_native_campaign_dispatch.py`、`test_agent_harness_evolution_batch.py`。
精确 RED/GREEN、集成和独立审查结论见 [verification-log](../../../logs/verification-log.md)。
本地集成和独立复审通过：attempt/native 82 项、Evolution/native episode 64 项；
另有 3 个真实 Docker 跨进程复用用例，以及 9 个任务形式/三条件/Evolution 用例。
最终全量回归 **1,226 passed / 39 skipped**；具体跳过项和命令以验证日志为准。
没有运行 hosted CI 或付费模型。

实际 Docker 用例不能标成预期失败来关闭缺口。早期 setup 失败来自 macOS 临时
目录对 Docker 不可见，并非导出代码缺陷；移除 xfail，使用仓库内已忽略的
`benchmark-vabench-release-v4/reports/` 测试输出路径后通过。Linux CI 仍使用
runner 的临时目录。未据此修改 exporter 或 EVAS。

不支持任意进程崩溃点恢复、恢复未知费用的 HTTP 请求、重新进入 final、跨机器
分布式 lease、旧输出自动纳管或 dry-run 转实跑。仅支持具备 flock/hard-link/fsync
的本地 POSIX 文件系统；失去证据时保持阻断，不删除旧记录“修复”。
guarded DeepSeek pilot 的历史费用授权/停止状态/no-resume 不变。
本切片未读取真实密钥、调用付费模型、修改封存 benchmark/EVAS 或触发 Spectre。
