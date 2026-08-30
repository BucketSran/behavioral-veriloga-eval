# AA-VAE-037：mini-swe 原生单任务入口与私有交互证据

## 思想、复用与边界

延续 AA-VAE-003/024/036：backend 负责模型交互，environment 负责执行，controller
负责停止与终评权限，完整 episode 连同提交快照才构成可审计的结果。这是基于既有
AlphaApollo trajectory 思想与 coding-agent 环境边界的工程适配，不是复制 AlphaApollo
代码，也不意味着已实现 reasoning/evolution。没有新依赖、领域工具或训练路径。

这次 coding-agent 借鉴落实在复用固定 mini-swe 2.4.5 的 prompt、Bash tool schema、
observation formatter、已有 OpenAI-compatible client 和 Docker environment；没有重写
这些设施。新 controller 只通过已有 typed bridge 接入。旧 DefaultAgent 和旧
`--agent-scaffold native` 的含义、默认行为不变。

## 具体代码改在哪里

以下 `operations/` 的完整前缀为 `benchmark-vabench-release-v4/`。

| 位置 | 改动 | 验证 |
| --- | --- | --- |
| `operations/calibration_pilot/run_native_mini_swe.py::main` | 独立 opt-in CLI，校验 r53/campaign/policy，独占新目录，复用 exporter；dry-run 无模型、Docker、评分 | 无凭证 dry-run、重复目录拒绝、非 dry-run 组合测试 |
| 同文件 `NativeMiniSwePolicy` | 复用真实 model adapter/formatter，单 Bash action 转 typed action，公开反馈可进入下一轮 | provider 边界 fixture 比较实际消息与反馈 |
| 同文件 `_RecordedClient/_RecordedEnvironment` | 私有 JSONL 保存 decoded request/response 与有界工具输出，request/action/provider response ID 可 join | provider/tool 对齐、异常与转义凭证脱敏 |
| 同文件 `run_prepared_native_mini_swe` | 固定身份后调用已有 native episode；freeze 前 pause Docker 并 inspect；result 索引绑定文件字节哈希 | 真实 r53 Docker、EVAS public/final 和结果 artifact |
| `runners/agent_harness/controller.py`、`state.py` | 支持有 trusted deadline 的无限步；授权后到时拒绝 dispatch；完整 workspace 仍走唯一 freeze/judge | 立即到时、晚响应/异常、授权窗口到时、不完整提交 |
| `trajectory.py`、`result_artifact.py` 与 result schema | 记录 deadline，允许 scored timeout 并校验 trajectory terminal reason；judge 失败保持合法无分数轨迹 | deadline result/trajectory 回归 |
| `native_episode.py` | 透传 trusted deadline/finalizer；记录 deadline 配置 | 原有 receipt/immutable result 回归 |
| `run_campaign.py::run_cell` | 旧入口也拒绝已有 native-launcher reservation | 模型/export 前拒绝重入 |
| `tests/test_agent_harness_native_launcher.py`、CI workflow | provider fixture + 真模型适配器/Bash/EVAS 的单任务 smoke | 独立 Docker CI step；旧路径回归保留 |

## 留下哪些证据

在 AA-VAE-036 的 trajectory、冻结提交、score sidecar、scored artifact 之外，新增：

```text
prepared.json                               # CLI 的 export/campaign 文件身份
runtime/evidence/native-launcher/
  manifest.json                             # backend/model/policy/environment/source 身份
  private-events.jsonl                      # 私有 decoded provider/tool 交互哈希链
  result.json                               # trace/manifest/artifact 字节哈希及 telemetry
```

目录私有，trace 结束后只读；不记录授权 header，已知 provider credential 在异常和响应
进入持久化路径前脱敏。`artifact_file_sha256` 是完整文件字节哈希，不同于 artifact 内部
排除自身字段计算的 `artifact_sha256`。私有 trace 与 controller trace 是两条不同的链，
由 attempt/action ID 和 result 索引连接；不能把一条链冒充另一条。

provider 请求保存的是解码后的交互，不是原始 SSE 网络帧；tool output 继承既有截断，
不是无限 stdout archive。旧 client 内部最多三次 transport attempts 尚未逐次展开记录。
manifest 的少量 source hashes 也不是整个软件供应链指纹。后续 aggregate/replay 需要继续
补齐这些层次，不能把有哈希等同于完整可重放档案。

## 测试证明什么、不证明什么

- r53 `v4-001` fixture 仅由公开合同生成，经历写候选、公开 EVAS、submit、verified
  Docker pause、freeze、最终 EVAS checker，得到预期 `behavior_failure`。
- 请求边界是离线 provider fixture；没有付费 API 调用，不证明实际模型质量或 baseline
  复现。DUT 单任务成功也不能替代 Bugfix/Testbench、多条件、全 campaign 验证。
- 完整 deadline workspace 可评分并保留 `agent_timeout`；不完整 workspace 无分数。
  依赖请求/命令 timeout 与 freeze 前 pause，不保证截止瞬间的异步硬抢占。
- 新路径严格接受单一工具调用，不复现 legacy DefaultAgent 的多动作与 FormatError
  恢复行为；需要后续差分协议审计，当前不能声称新旧行为等价。
- 公开 EVAS 仍是普通 Bash feedback，不是每次调用均绑定的 typed public validator；
  test-only `run_evas` dispatcher 未启用。最终 checker 输出不回流模型。
- r53、EVAS 0.8.7 不变；最终 EVAS score 为 `development_only`，无 Spectre 等价声明。

精确 RED/GREEN、独立审查、命令、计数和证据路径见 `logs/verification-log.md`。
