# AA-VAE-075：联合工具验收与显式 live 入口

日期：2026-09-01；基线 `025276c6fc`；r53 / EVAS 0.8.7 不变。

## 为什么不再各造一套 runner

用户希望 Reasoning、Evolution、检索和波形一起做集成验收。这里复用现有 native /
Evolution 引擎、AA-VAE-073 波形共享、AA-VAE-074 文档契约、DeepSeek transport /
spending guard 及已有 final reader，只增加一个明确命名的组合入口。
不改旧 mini-swe 默认，不把额外工具偷偷加进已冻结的旧/新六格比较。

核心思想是 AlphaApollo 的显式观察与轮次记忆，以及 coding harness 的执行/记录/
结果读取分离。这里没有复制新 agent 框架，也没有引入新的模型 SDK、向量库或依赖。

```text
prepare: task + corpus + images + source + budgets -> immutable manifest
run: exact manifest/cap assertion -> one shared provider budget
  native: docs + public waveform -> submission freeze -> final replay
  evolution: NoEVAS branches + docs -> sealed public waveform -> next round
             -> select one candidate -> submission freeze -> final replay
report: verify existing receipts -> actual feature use + all costs + final score
```

Evolution 当前组合默认同一模型的两个分支、两轮；不是异构多模型实验证据。
Reasoning 是 harness backend 名称，不表示 DeepSeek 内部 thinking 已启用。

## 代码与新增行为

以下运行脚本位于 `benchmark-vabench-release-v4/operations/calibration_pilot/`。

| 代码 | 负责什么 |
| --- | --- |
| `run_combined_tools.py::freeze_combined` | 冻结单题、backend、corpus、镜像、源码、轮次/分支/额度和已有 provider profile；不读密钥 |
| `execute_live` / `execute_fixture` | live 需精确 hash/cap/currency 和外部凭据；fixture 只使用脚本回复，仍经过同一个预算/解析边界 |
| `_execute` | 调已有 Native/Evolution API；共用费用守卫，按分支跨轮数限制调用；只对选定冻结提交 final 一次 |
| `read_combined` / `_read_budget` | 只读验证启动声明、preflight、campaign、journal、runtime tree 与原 final 证据，逐分支保留调用/费用上界 |
| `combined_tool_evidence.py::collect_feature_use` | 从实际工具结果、候选绑定的公开回执和下一轮请求计数；不输出原文/查询/波形/hidden 内容 |
| `run_native_mini_swe.py` / `score_campaign.py` | 可选 tool limit；reviewed docs 版本 join；修复同时启用 docs 与 waveform 时能力注册顺序不同导致的 hash 拒绝 |
| `evolution_batch.py` | 原 final reader 从冻结扩展重建配置；没有引入第二个评分器或重跑 final |

文档检索仍按分支本地工具结果反馈；跨分支共享的是已封存候选与绑定公开验证结果，
不是各分支任意检索片段。波形结果必须由真正的 `vaevas_public_simulate` 产生，
不能把普通 public validator 的成功当成波形成功。汇总直接复用
`_public_feedback_for_prior_candidate` 校验候选 store、profile 和真实公开输入。

## 怎么判定通过

组合验收要求检索和波形均有实际成功调用、证据完整，并能读取 final score；
Evolution 还要求已验证公开反馈出现在后续轮次请求中。final score 可以为 0：
链路可工作与模型答对题是不同命题。

`feedback_exposed_requests` 只证明反馈被放入请求，不证明模型理解、采用或因此改善。
开启标志不能代替调用证据。普通 validation、缺失回执、伪造 candidate store 都
不能让验收通过。预算截断/证据不全单独报告，不伪造任务 0 分或省略已花的费用。

费用是保守 guard upper bound，不是账户账单。实际 live 的 `paid_requests` 为
unknown；`transport_reservations` 才是已观测的可能收费尝试。锁内预留/核销复用
已有实现；未知费用保留整笔预留并停止后续请求，不能通过重建预算续跑。
每轮 model/tool cap 由 controller 管理，guard 再独立限制每分支跨所有轮次的模型
调用上限。`public-calls` 是额度上限，当前协调器每个候选只验证一次。

## 使用与剩余激活条件

从仓库根运行新脚本的 `--help`，子命令为 `prepare / inspect / run / report`。
完整参数说明见 calibration-pilot README 的 AA-VAE-075 节。
`prepare` 不等于付费授权；`run` 一次性使用精确 manifest/cap 声明，不自动重试。
该声明是防误启动措施，不是可认证的人类身份或账户级硬预算。

复用的 provider contract 有效期为 **2026-08-31 UTC**。日期过后会拒绝 live；
需要先复核并更新服务费率/模型/解码契约，再冻结全新运行，而不是改旧 manifest
或绕过时效检查。本轮不更新服务价格、不读取实际密钥、不启动付费调用。

用户后续明确授权后，veriloga-skills 四份固定参考已作为本地 reviewed-v2 语料接入，
清单与原有 `--docs-root/--docs-manifest` 用法见
[AA-VAE-074](AA-VAE-074-reviewed-local-docs.md)。Cadence 未找到，按用户要求省略。
此轮只验证语料加载/检索，没有用真实资料重新执行组合评分或付费模型实验。
外部上下文权限在 live prepare/run 两处检查；本地许可不自动赋予 API 发送权限。

## 验证记录

新增测试在 `tests/test_agent_harness_combined_tools.py` 与
`tests/test_agent_harness_combined_tool_evidence.py`。先复现并修复了混合工具
capability 顺序、Evolution extension final join、下层调用上限缺失，以及重新计算
hash 后仍应拒绝的五类启动/预算元数据篡改。保留普通验证不计波形、候选 store
缺失/篡改、私有事件缺失、费用不足、usage 未知、无重入和本地权限拒绝等回归。

CI 使用真实 Docker/EVAS、合成资料、脚本模型回复和模拟外部 HTTP；不配置密钥。
精确本地/hosted 结果及源提交以 [verification log](../../../logs/verification-log.md)
为准。工程集成通过不等于真实模型性能改善、独立工具收益、完整 r53 排名、
Spectre 等价、独立 hidden-stimulus 证据或训练数据合格。
