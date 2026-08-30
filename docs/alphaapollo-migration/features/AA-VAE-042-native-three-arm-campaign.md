# AA-VAE-042：Native 三条件 campaign 与严格汇总

## 思想与实现地图

复用 AA-VAE-039 的 evidence reader 和既有 campaign，而不是另造调度/评分体系。
沿用 AlphaApollo 的独立轨迹思想及 coding-agent 的独立 workspace、终态和失败边界；
这里没有引入外部依赖或复制新的第三方代码。

- `benchmark-vabench-release-v4/runners/run_benchmarkv4_campaign.py`：独立
  `--episode-backend native-mini-swe` opt-in，记录 execution config 并透传。
  旧 `--agent-scaffold native` 保持 legacy sensitivity 含义。
- `operations/calibration_pilot/run_campaign.py`（v4 下）：复用 exporter 和
  prepared launcher，按条件选择 image；OneShot 不传 Bash image。每个 cell
  要求全新 runtime；已有 runtime/终评记录禁止重入。native dispatch 结果单独
  exclusive-create，不伪造 legacy `campaign_result.json`。
- `score_campaign.py`：新增 native CLI，从冻结的完整 scheduled cells 读取
  证据，兼容有 profile 的 v1 和缺席的 v2；valid infrastructure receipt 计入
  分母且无分数，缺失/破损证据阻止汇总。不会调用模型、refreeze 或重跑终评。
- `tests/test_agent_harness_native_campaign_dispatch.py`：路由、冻结配置、
  unsupported/resume/limit guard、旧失败目录重入、只读 scorer 和失败计数。
- `tests/test_agent_harness_native_campaign_smoke.py`：r53 `v4-001` DUT 与
  `v4-1001` bugfix，共六个 cell，两路并行；每条使用独立 runtime 和 provider。
  候选只由公开 artifact contract 构造，故意不完整，不读 gold 来制造成功。
- smoke 复用 `scripts/run_v4_r53_clean_room_smoke.py::public_stub_artifacts`，
  仅扩展该公开 fixture 到 bugfix；原 mixed/legacy smoke 不替换。
- CI 新增独立六-cell Docker gate，并纳入 wrapper/v2 schema 的路径触发。

## 实际发现与验收

集成发现 OneShot 的 image 参数冲突、No-EVAS 环境默认 feedback 参数问题、
独立 scorer 进程缺少 repo import root、既有失败 runtime 可能进入 force exporter。
分别修复所属参数/入口/重入边界，并保留回归；没有修改 EVAS。

真实 Docker + EVAS 0.8.7：**2 passed in 19.91s**，六个 cell 均得到结构化
`behavior_failure`。这是预期的无功能 smoke 候选结果，不是 0% 模型成绩。
每条都产生 trajectory → freeze → score sidecar；scorer CLI 运行前后全部
runtime 文件 hash 不变；公开 EVAS 调用只在 Agentic 出现。

本地 ignored evidence 根：
`benchmark-vabench-release-v4/reports/native-three-arm-20260830-p90roF/green3-pytest/test_r53_docker_all_native_thr0/`。
`smoke-evidence-index.json` SHA-256：
`a89227b666c29d1f798fb446cdeecfb377bf1515ef62642a810aa005714abe02`。
索引包含 campaign/report 摘要以及六条 artifact/trajectory/sidecar 摘要；原始
轨迹、私有终评和生成输出不进入 Git。

当前 harness + score reuse + r53 entrypoint/smoke 回归：**492 passed, 5 skipped**。
独立 campaign 审查无实质阻断；Ruff 0.12.12 / AST / whitespace 通过。
LSP 不可用，广泛历史回归因本地精简资产缺失未全绿，详见 verification log；
不把局部 GREEN 写成全仓测试成功。未来 hosted 结果必须另行绑定 commit。

## 保留的限制

native Testbench、自动 episode retry/recovery、完整 transport/tool 原文归档、
细分 provider taxonomy、正式 aggregate/claim export、真实模型/全 r53 覆盖、
Reasoning/Evolution 与 domain tools 均不由本切片完成。
已完成的六-cell 连通性不能证明新旧 backend 全量 parity、模型效果或 Spectre
一致性。EVAS sidecar 继续是 `development_only`；DUT/bugfix 仍是共享公开
stimulus + held-out checker，不声称独立隐藏刺激集。
