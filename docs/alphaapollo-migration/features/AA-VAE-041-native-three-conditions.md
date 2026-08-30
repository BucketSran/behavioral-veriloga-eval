# AA-VAE-041：Native DUT/bugfix 三条件入口

## 思想与代码地图

延续 AlphaApollo 的 policy/environment 分离和 coding-agent workspace 边界，
将条件差异放在明确的 adapter/capability/runtime 配置中；共用 controller、
trajectory、freeze 与 final replay，不重写一个评分器。没有新增外部依赖。

`benchmark-vabench-release-v4/operations/calibration_pilot/run_native_mini_swe.py`：

- `validate_native_cell`：仅 DUT/bugfix 的 OneShot、Agent-No-EVAS、Agentic；
  不支持的 condition/form 在调用模型前拒绝。
- `_OneShotModel` / `_OneShotPolicy`：一次逻辑生成请求，只接受结构化
  `submit_artifacts`，无 Bash、反馈循环或格式修复追问。既有 provider 内部网络
  transport retry 仍然存在，不能声称只发出一个 HTTP 请求。
- `_OneShotSubmissionEnvironment`：只写声明的文件，写入前检查符号链接；
  controller 执行 terminal submission 后仍走不可变 freeze 和 EVAS 终评。
- No-EVAS 复用 mini-swe Bash 桥，但使用配对 no-EVAS 镜像，并明确传入
  `executable_feedback=False`，既不创建公开 EVAS wrapper/profile，也不开放网络。
- Agentic 保留现有公开反馈路径。API 名字兼容；manifest 记录具体 condition、
  runtime 和实际 toolset。legacy 默认入口及旧 sensitivity flag 不变。

## 测试和修复

`tests/test_agent_harness_native_conditions.py` 覆盖三条件支持矩阵、一次调用、
无反馈工具、非法输出不追问、无 EVAS runtime 和符号链接拒绝。
与既有 launcher/absence/native-episode tests 合跑：**49 passed, 2 skipped**。
Ruff 0.12.12、语法和 whitespace 检查通过。

独立审查发现并修复两个问题：仅切换 no-EVAS 镜像但未关闭环境参数；OneShot
未在写入前拒绝中间目录符号链接。两者均有 RED→GREEN 回归。复审无代码阻断，
LSP 工具不可用，使用 Ruff、Python 编译和测试作可用诊断，不能宣称跑过 LSP。

这里不是 Reasoning/Evolution 接入，不提供 native Testbench、episode 自动重试、
完整 transport 归档或模型效果结论。真实六 cell campaign 证据另记 AA-VAE-042。
