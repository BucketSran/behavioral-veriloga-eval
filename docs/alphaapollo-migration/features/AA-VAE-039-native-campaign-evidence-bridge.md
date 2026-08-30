# AA-VAE-039：Native campaign 证据过渡接入

## 目标与借鉴思想

沿用 AlphaApollo 迁移主线中的 environment-owned trajectory，以及 coding-agent
的独立 runtime/terminal result 边界：报表必须从每条真实轨迹及其最终证据推导，
不能为了兼容旧报表而伪造另一套运行记录。本切片不移植新的外部代码或依赖。

基线 `7425d70b72`，r53 + EVAS 0.8.7 不变。复用 AA-VAE-037 的单任务 native
launcher、AA-VAE-026/036 的不可变 artifact 和原有 `score_campaign.summarize`。

## 明确的过渡条件

| 条件 | 此次执行路径 | 不变的语义 |
| --- | --- | --- |
| OneShot | legacy direct | 直接提交；无可执行反馈 |
| Agent-No-EVAS | legacy mini-swe | 独立 no-EVAS image 和 runtime overlay |
| Agentic | opt-in native mini-swe | 公开 Bash/EVAS，多轮后 freeze，终评不可回流 |

这是 `mixed-backend-connectivity-v1`，不是三个条件都迁移完成，也不是公平的
EVAS 效果或 backend 性能实验。新旧格式恢复、多动作和 deadline 差异仍见
[AA-VAE-038](AA-VAE-038-mini-swe-behavior-differential.md)。正式比较前仍需
补齐 native No-EVAS 的“没有公共验证器”契约；不能伪造启用的 EVAS profile。

## 代码变更地图

- `benchmark-vabench-release-v4/operations/calibration_pilot/score_campaign.py`
  的 `read_native_cell`：只读 launcher manifest/result、native request/outcome、
  trajectory、冻结提交和 sidecar；复用原有 cryptographic/semantic artifact
  validator，再投影为现有 score row。不会调用模型、重新 freeze 或重复终评。
  原始响应、checker 输出和异常 detail 不进入投影。
  行内保留 attempt ID、artifact 路径、文件与语义摘要；sidecar 的路径/摘要命名为
  `derived_score_sidecar_reference`，不冒充完整 producer receipt。真实回执由
  launcher 返回，保留在 smoke report 的 `bound_final_test.receipt` 中。
- 同文件 `summarize(..., scheduled_cells=...)`：可选的严格分母门，拒绝缺行、
  重复、额外行和 task/family/form/mode/arm 错配。旧调用形式保持兼容。
- `scripts/run_v4_r53_clean_room_smoke.py`：新增显式
  `--agentic-backend native-mini-swe`，要求 `--bound-final-authority`。
  generation 前冻结 backend routing、三条 cell、模型 fixture 和 watchdog 配置。
  native 结果直接接入同一报表，不生成假的 legacy `campaign_result.json`。
- `tests/test_agent_harness_native_campaign.py`：真实本地 controller/adapter
  配确定性 provider 与外部 judge fixture，覆盖只读重用、失败分类、证据破损、
  分母门；另有真实 Docker + EVAS 0.8.7 三条件测试。
- `.github/workflows/evaluator-closure.yml`：保留旧三条件 smoke，另加 mixed
  native smoke；不替换已有回归以制造“新路径全绿”。

## 失败、分母和信任边界

已完成的 native 协议失败与 provider 失败都有终态轨迹，分别保留
`protocol_failure` 和 `infrastructure_failure`，均为 `score=null`。
最终 judge 返回 infrastructure failure 时仍保留已生成的绑定 sidecar，分数为
null。缺失/破损证据会拒绝读取；smoke 把它保留为 coordinator infrastructure
incident 并阻止 PASS，不转成候选零分，也不补跑该 cell。

此 reader 是可信 coordinator 的本地证据检查器，不是签名认证、对抗恶意主机的
执行证明或通用 public trace 脱敏器。provider transport retry/SSE 原始帧仍未归档；
native 失败分类粒度、完整工具内容、cleanup 分类与跨 form 仍有后续工作。
崩溃/进程中断不自动恢复；不完整 evidence 不能形成完整报表。

架构审查保留 WATCH：reader 目前直接知道 native launcher 的私有文件布局。
这是单一有界消费者的过渡适配，不应继续膨胀成全 campaign 抽象；出现第二个
实际消费者时，再独立冻结 typed native-attempt reader 接口，而不是现在新增层次。

## 验证与使用

```sh
uv run --locked --extra agentic python scripts/run_v4_r53_clean_room_smoke.py \
  --task-id v4-001 --bound-final-authority \
  --agentic-backend native-mini-swe \
  --evas-command /absolute/path/to/evas \
  --output-root /absolute/path/to/fresh-docker-shared-output --json
```

沿用现有 pinned public/no-EVAS Docker images。输出目录必须全新，且与 Docker
daemon 共享；业务仓库内使用既有 ignored `benchmark-vabench-release-v4/reports/`
子目录。普通旧 smoke 和 campaign CLI 的默认路径不变。

确切 RED/GREEN、Docker、独立审查、回归和 fork publication 证据见
`logs/verification-log.md` 的 AA-VAE-039 记录。fixture 的预期行为失败只证明
链路，不能写成模型 baseline。本轮不实现 full native campaign CLI、Testbench、
retry、Reasoning/Evolution 或领域工具，不修改 r53/EVAS，不运行付费模型/Spectre。
