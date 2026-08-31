# AA-VAE-068：旧 native sensitivity 入口的 r53 兼容

## 功能标识与来源

- 日期：2026-08-31；负责人：主线程；状态：`08f2c9310f` 已发布 fork/main，
  本地验证、独立审查及两条同源 CI 通过。
- 来源：AA-VAE-067 审查留下的独立调用方缺口，不是新的 AlphaApollo 代码移植。
  继续采用代码约束工具契约、复用共同校验、明确 backend 边界的工程思想。
- 原问题：旧 `--agent-scaffold native` 的 schema 白名单只到 r52；即便补上
  r53 Testbench 名称，仅按 `v3` 后缀判 portable 仍会误加 strict 参数。

## 适配与代码

旧路径是 `native-v4-loop -> execute_tool("run_evas") -> run_public_evas`，
与默认 mini-swe 和新 native controller/Reasoning/Evolution 路径不同。
仅修前者，不替换默认 backend。

| 代码入口 | 修改及思想 |
| --- | --- |
| `operations/calibration_pilot/run_campaign.py::run_public_evas` | r53 复用 `public_execution_contract` 精确验证；再执行原有固定 argv，绝不执行 metadata shell 字符串 |
| 同文件 schema 集合与 reference 分支 | 注册 r53 DUT-v2/v3 和 reference-v1；统一 reference 集合，正确选择工作目录和公开 DUT 拷贝 |
| 同函数 portable 分支 | r53 使用已验证的显式 mode；历史 r45-r52 沿用原规则 |
| `tests/test_agent_harness_legacy_public_contract.py` | 从实际旧工具入口验证三形式 strict/portable、拒绝边界、非零退出和历史兼容 |

operations 路径均在 `benchmark-vabench-release-v4/` 下。共享校验器来自上一轮，
本轮不修改它；用延迟导入避免历史路径增加不必要的耦合。执行保留公开候选和
reference 的 confined scratch 路径；Testbench 不能请求 mutation 或 evaluator。

## 验证与边界

先复现 strict DUT schema 拒绝，再复现四个 portable DUT/bugfix 拒绝和三个
Testbench 工作目录拒绝；逐类修复到 GREEN。新增测试经实际 Python 子进程记录
argv/cwd，检查公开 reference 拷贝与结果 JSON；故障进程必须仍为 `fail`。
非法命令、schema/mode、binding、scope、case 在执行前拒绝。r52 合成兼容用例
及既有 r45-r51 合成回归保留；不需要恢复已清理的大批旧资产。

测试使用真实发布的公开契约，但假 EVAS 不编译候选：这是分发兼容证据，不是
仿真成功、硬隔离、模型改善或历史 baseline 复现。精确测试/审查/CI 见
`logs/verification-log.md`；已有 clean-room gate 只作为主线路径回归。
新增边界测试 55 项通过；与共享 parser 合并为 86 项。旧 synthetic 选择 14 项
通过；完整本地 harness/导航选择 1,125 通过、34 个 opt-in 跳过。独立审查无
必修项。缺失的历史 r52 资产由 hosted full checkout 验证，不宣称本地全仓库
全绿。Ruff 0.12.12 和编译检查通过；LSP/typecheck 不可用，不用 lint 冒充类型证明。
该源提交的 hosted 完整 checkout 回归为 1,342 通过、40 跳过，随后全部真实
Docker/clean-room 阶段通过；这补齐了历史资产环境的回归证据。不是新增模型
实验，也不把已有 mainline Docker 阶段说成旧 sensitivity 的硬隔离证明。

不改变 r53、EVAS 0.8.7、模型预算、工具集、trajectory schema、候选排名、
评分或 final non-reentry。family 102 已知动态数组能力限制不变。公开进程
`pass` 仍不等于行为正确；尚未实施公开行为指标或新的 Evolution 排序协议。
无 API 调用、真实语料、SFT/RL、Spectre 或 parity 声明。
