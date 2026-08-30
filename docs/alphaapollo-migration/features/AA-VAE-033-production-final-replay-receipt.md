# AA-VAE-033：Production final replay receipt

## 思想与范围

沿用 AA-VAE-020/030/031 的权限分离思想：AlphaApollo 式 feedback 可以驱动下一轮，
terminal judge 则只负责冻结后的评分。此切片没有复制新的外部代码、增加依赖或模型工具，
而是把已有 production replay 接到已经验证的 generic authority/store API。

保留 legacy mini-swe 和默认 scorer；新路径由可信调用方显式提供 final profile 和
`EpisodeContext`。这不是全量 campaign 默认切换，也不伪造原生 typed trajectory。

## 代码框架与改动

| 入口 | 变化 |
| --- | --- |
| `operations/calibration_pilot/final_replay.py::build_final_test_profile` | 固定 r53/EVAS 0.8.7，记录 manifest、campaign config、evaluator tree、EVAS command/version、judge command/files/watchdog、host Python/bridge source identity |
| `final_replay.py::execute_bound_replay` | 校验真实冻结文件和执行前后身份；调用 `ProfileBoundFinalJudge` 和 `write_immutable_score_sidecar`，返回 receipt |
| `run_campaign.py::run_trusted_replay` | 显式 profile/context 进入新路径；无参数保留 legacy 执行 |
| `run_campaign.py::run_cell` / `run_cell_preserving_failure` | final reservation 后拒绝 model reentry，不通过错误恢复覆盖已有 evidence |
| `score_campaign.py::evaluate_cell` | 校验 cell identity；新路径要求 `write_back=False` 且禁止 legacy replay reuse/二次评分 |
| `result_protocol.py::normalize_trusted_replay_watchdog` | 共用现有 scorer 的 watchdog 分类，先归为 infrastructure 再封存 sidecar |
| `schemas/vabench-experiment-result.schema.json` | 为旧 v2 reader 增加可选 profile/receipt 成对字段；旧文档仍有效，profile 的完整语义由 runtime validator 校验 |

路径前缀均为 `benchmark-vabench-release-v4/`，除明确的 schema 路径外。

## 生命周期

`profile + frozen files 校验 → exclusive final reservation → 既有 replay → watchdog 分类
→ 身份复核 → typed judgment/sidecar 校验 → immutable publish → receipt`

`evidence/bound-final-test/` 是持久化停止边界，进程失败也保留。禁止自动删除它来恢复生成
或重评；明确的 infrastructure judge-retry coordinator 尚未实现。只读审计不受此限制。
返回的 receipt 包含 episode/attempt/task identity、profile/input/submission hash 和 sidecar
路径/hash。sidecar 本身内容相同可以跨独立 runtime 同 hash，不能以 hash 相同推断 attempt 相同。

## 验证与边界

行为测试位于 `tests/test_agent_harness_production_final_replay.py`：真实 subprocess adapter、
内容哈希、执行前后漂移、原地重评与 legacy bypass、缺失/畸形 verdict、watchdog 分类、resume
拒绝、旧 schema 兼容、generation evidence 不回写、相对 judge 脚本按执行 cwd 绑定。
RED/GREEN 和最终统计见 `logs/verification-log.md`。

独立审查发现原 scorer 的 watchdog stage 不在 Python/JSON schema 枚举中。共享 helper
改用已有的 `infrastructure` stage，具体超时原因留在 diagnostics 和 secondary classes，
并补上完整 experiment-result schema 回归，不只测试局部 scorer row。

当前 runtime fingerprint 覆盖声明的 host Python、bridge 文件及显式 Rust-core override，
不是完整 OS/container 或任意 Python import 的 hermetic dependency closure。campaign hash
由可信 coordinator 提供；schema/hash 不会自行证明 campaign 在首次模型调用前冻结。

保留缺口：全量 campaign CLI profile 分发、明确的基础设施 retry lineage、production public
validation adapter、native typed trajectory/result ledger、完整 denominator。r53/EVAS 不修改，
Spectre gate 不启动，EVAS receipt 仍为 `development_only`。
