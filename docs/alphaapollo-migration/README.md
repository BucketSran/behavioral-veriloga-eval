# AlphaApollo → vaEVAS 工程迁移笔记

这个目录记录我们如何把 AlphaApollo 的公开方法论迁移到 vaEVAS 的
AI-native benchmark、agent harness、trajectory、评分与结果生成链路。

它不是 AlphaApollo 的复刻仓库，也不是聊天记录归档。每一条笔记必须回答：

1. AlphaApollo 中值得学习的思想是什么；
2. vaEVAS 的问题与边界有什么不同；
3. 采用、修改或拒绝了什么；
4. 代码改动落在哪个文件、函数或 schema；
5. 用什么测试和证据证明它生效；
6. 当前状态是设计、实现、验证还是暂缓。

## 阅读顺序

想先看一个具体运行过程，读
[单任务代码与轨迹案例](05_单任务代码与轨迹案例_2026-08-31.md)：
四轮免费 fixture，公开模拟成功而终评 0 分，对照五个组件的代码和旧/新差异。

重新梳理当前项目时，先看
[当前计划](../../plans/current-plan.md)和
[运行入口](../../benchmark-vabench-release-v4/runners/README.md)。
[夜间工程闭环审计](04_夜间工程闭环审计_2026-08-31.md)是固定旧基线记录。
[2026-08-30 快照](02_项目现状与功能缺口_2026-08-30.md)只描述其固定旧提交，
不覆盖后续已完成的实现；当前跨领域边界见 [全局路线](03_全局后续路线_2026-08-31.md)。

1. [00_迁移主线.md](00_迁移主线.md)：理解迁移目标、系统主链和不迁移的内容。
2. [01_功能迁移台账.md](01_功能迁移台账.md)：查看每项能力的代码落点、证据与缺口。
3. [features/README.md](features/README.md)：新增功能时按模板建立独立记录。

最新修复与扩展：

- [AA-VAE-078：阶段计时](features/AA-VAE-078-execution-phase-timing.md)、
  [AA-VAE-079：固定并发诊断](features/AA-VAE-079-fixed-execution-profile.md)、
  [AA-VAE-080：多路径只读报告](features/AA-VAE-080-multipath-readonly-reporting.md)：
  可复跑的免费 Docker/EVAS 吞吐诊断与 Inspect 报告互通；不迁移调度、不混合条件总分。

- [AA-VAE-073：Evolution 波形共享](features/AA-VAE-073-evolution-waveform-sharing.md)、
  [AA-VAE-074：受控真实语料契约](features/AA-VAE-074-reviewed-local-docs.md)、
  [AA-VAE-075：联合验收/live 入口](features/AA-VAE-075-combined-tools-live-entrypoint.md)：
  接通现有工具与引擎，记录实际调用/下一轮反馈；该切片没有付费实验。
  后续已按用户授权接入四份固定版本的公开资料，原文只留本地 ignored 目录；
  见 [语料激活记录](../../plans/veriloga-corpus-activation.md)。不代表已证明检索收益。

- [AA-VAE-069：旧/新 mini-swe 对照协议](features/AA-VAE-069-legacy-native-comparison-protocol.md)：
  六单元 blueprint、信息面审计与预算/结果验收；只有免费证据，真实实验尚未启动。

- AA-VAE-060/061：独立公开波形执行器和 native 显式工具，预算/候选/回执 join。
- AA-VAE-063：保留配对报告与安全 case 索引；AA-VAE-062 合成训练 adapter 已退役。
- AA-VAE-064/065：Evolution 生成信息面修复、synthetic docs 的分支本地接线。
- AA-VAE-066：config-hashed 预期信息面和证据支持的失败责任分类。
  各项代码、提交与边界统一列在最新审计页；以下保留前序独立切片说明。

- [AA-VAE-055：公开 EVAS 分层诊断](features/AA-VAE-055-public-evas-process-feedback.md)：
  已实现并免费验证；sandbox 标记明确不具备可信执行/预算/评分权限。
- [AA-VAE-056：RAG、波形、SFT/RL 并行设计](features/AA-VAE-056-rag-waveform-training-design.md)：
  三方向的设计依据；具体实施状态以下列记录为准。
- [AA-VAE-057：合成离线检索](features/AA-VAE-057-synthetic-offline-docs.md)：
  native mini-swe/Reasoning 的显式开发 API；接通反馈、预算与评分身份，不自动启用。
- [AA-VAE-058：有界波形 parser](features/AA-VAE-058-bounded-waveform-parser.md)：
  独立模块已验证；后续公开输出绑定/模型接线已由 AA-VAE-060/061 完成。
- [AA-VAE-059：合成训练导出契约](features/AA-VAE-059-synthetic-training-export.md)：
  2026-09-01 与 AA-VAE-062 一起退役，仅保留历史思想/验证和 Git 恢复点。
  当前私有 trajectory 捕获与安全导出不受影响，真实 SFT/RL 不在当前主线。

## 证据边界

允许使用的来源：

- AlphaApollo 的公开论文与公开 GitHub 仓库；
- 用户明确授权读取的历史 Codex 对话中的通用工程结论；
- vaEVAS 当前仓库的代码、测试、manifest 和公开文档；
- 用户明确允许的共享评测契约笔记。

禁止把任何私有 AlphaApollo 项目的代码、数据、prompt、trajectory、凭据或
组织内部服务细节写进本目录或 vaEVAS。

## 状态词

- `设计中`：问题与接口已定义，但没有代码证据；
- `已有基础`：仓库中存在部分能力，但尚未满足迁移契约；
- `已实现`：代码已落地，尚待充分验证；
- `已验证`：有对应测试、smoke 或冻结证据；
- `暂不迁移`：明确不属于当前 vaEVAS 主线；
- `条件启用`：只有满足特定触发条件时进入主线。
- `已退役`：实现已移出当前工作树；历史验证保留，可按记录从 Git 恢复。

严禁把“写进 AGENTS.md”记成“功能已实现”。契约、代码、测试和实验证据必须
分别记录。
