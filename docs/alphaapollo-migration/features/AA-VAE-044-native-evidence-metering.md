# AA-VAE-044：原生证据分层与实际计量

## 思想与代码对应

沿用 AlphaApollo 的 episode-local state / trajectory 分层思想；vaEVAS 的额外
要求是公开反馈、私有审计材料、冻结后的最终评分不能混为一份模型记忆。
不复制第三方实现，不更改 r53、EVAS 0.8.7 或 legacy 默认控制循环。

- `runners/agent_harness/evidence_export.py`：校验两个事件链、原始 JSONL
  字节与 episode/attempt 身份，按结构化白名单生成 reviewer-only ledger。
  Provider ID/model ID 使用摘要；原始 prompt、命令、回答、工具输出、终评
  payload 不进入导出。导出仍不是任意自由文本的通用脱敏器。
- `operations/calibration_pilot/run_campaign.py`（v4 下）：现有 transport 的
  opt-in observer 分开记录每个 HTTP/curl attempt；流式与非流式均保留响应
  或异常时的部分输出、摘要和截断范围，不记录认证 header。
- `mini_swe_vabench.py`：可选 private sink 保留模型裁剪之前的有界 head/tail
  输出；另记录完整已排空流的 SHA-256、字节数、EOF/read-error 与截断情况。
  不是无限制 raw archive，也不是绝对硬实时保证。默认 model-visible 返回不变。
- `run_native_mini_swe.py`：把 provider/transport/tool capture 绑定到请求和
  动作 ID；OneShot 复用相同 provider 记录机制；异常工具调用也产生终态记录。
  自动写入只读 `evidence/native-launcher/reviewer-export.json`，其文件摘要
  被 launcher result 引用，导出协议在生成前的 manifest 中冻结。
- `score_campaign.py`：从原始证据重算导出并校验引用，不能只相信新增 JSON。
  原生 token 只使用 provider 实际报告值；缺失为 null，汇总总量/中位数也为
  null，同时单列已报告小计与缺失 cell 数，不把估算或缺失冒充零成本。
  旧路径的历史兼容统计没有因此被追认成原生计量。

这些路径位于原有 controller → public environment → freeze → final sidecar
之外的证据层。Reviewer export 不得进入模型 observation 或 Evolution memory。
截断、缺失、失败、无 transport observer 的自定义 client 均应显式披露。

## 测试与验收

先新增 launcher 自动导出、缺失 usage、导出篡改和内部 transport retry 的
失败测试，再接入实现。测试入口：`test_agent_harness_evidence_export.py`、
`test_agent_harness_private_provider_capture.py`、
`test_agent_harness_private_tool_capture.py`，以及 native launcher/conditions/
campaign 的真实接口回归。精确最终结果与 Docker evidence 见 verification log。

## Claim boundary

这是审计可追溯性和计量修复，不是模型能力改进证据。真实 API/local model
质量、全 r53、跨 backend 统计结论和 Spectre parity 都需各自实验。新 attempt
恢复、Reasoning 和 Evolution 的运行接入由后续独立提交验收。
