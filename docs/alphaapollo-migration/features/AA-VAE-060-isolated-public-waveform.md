# AA-VAE-060：公开波形的独立执行与来源绑定

日期：2026-08-31。状态：独立执行器已实现并完成本地验证；不是已启用的模型工具。
实现提交：`8b747e977c`。

## 思想与边界

延续 AlphaApollo 的显式 environment feedback 思想，但不复制其数学输出协议。
vaEVAS 自己补充执行来源边界：AA-VAE-055 的 Bash markers 可被模型伪造，
AA-VAE-058 只能证明“给定字节可被解析”。因此不能读取共享旧 CSV，再附上
当前候选标签。必须先建立独占执行与候选/调用/输出 receipt。
本切片没有新增外部代码借用、依赖、模型调用或 EVAS 修改。

## 代码到功能

- `benchmark-vabench-release-v4/operations/calibration_pilot/public_waveform.py`
  的 `IsolatedPublicWaveformExecutor` 是显式 coordinator API：冻结 r53 public
  task、campaign/profile、候选声明、固定命令、image ID 与实现/policy hash。
  `validate(candidate_tree_sha256=...)` 每次创建独立临时快照和 Docker 容器。
- `mini_swe_vabench.py` 增加默认关闭的 `submission_read_only`；原调用与序列化
  默认不变。新执行器复用原隔离/资源/有界进程输出，不再造一个 Docker runner。
- `waveform_summary.py::summarize_waveform_bytes` 与文件入口复用同一个 parser，
  解析本次 Docker 固定 reader 返回的字节，不增加 waveform provenance 权限。
- `tests/test_agent_harness_public_waveform.py` 验证绑定、拒绝路径和真实 Docker；
  `tests/test_agent_harness_ci_gate.py` 及 Evaluator Closure 增加独立 smoke gate。

## 实际执行关系

公开 task + 声明候选字节 → 新私有快照 → 只读 task/submission 挂载 →
固定 `/usr/local/bin/evas` → 本次 tmpfs 的固定 `tran.csv` → 有界摘要 + receipt。

DUT/bugfix 使用 `/tmp/vabench-visible/evas-output`；Testbench 只使用
reference DUT，输出根增加 `/reference`。不挂载原生成目录、skills、hidden
evaluator 或历史输出。临时目录是运行目录的私有同级目录，避免 macOS 系统
临时目录不在 Docker 文件共享范围内，同时避免放进模型的公开挂载。

读取最多 256 个目录项、每文件 1,000,000 bytes、每树 16 MiB；拒绝链接、FIFO、
多余候选、路径越界。snapshot hash 使用 canonical path/content-hash rows，
不使用 wrapper 自己的 framed digest。输出 reader 用隔离 Python、目录 fd、
no-follow/nonblocking 与 1 MiB 上限，CSV 统计沿用 AA-VAE-058。

receipt 绑定 attempt/task、候选、profile-input identity、image、固定命令、
public task、唯一 invocation ID 和摘要 hash。进程成功只表示模拟进程零退出，
`task_correctness=not_evaluated`；没有 task verdict、hidden threshold 或 final score。
失败/超时不复用 CSV；身份漂移或基础设施错误使实例失效。清理 incident 单列，
不覆盖原始错误；有清理 incident 的 receipt 不可用作模型反馈。

## 信任假设与下一步

可信 coordinator/host/Docker daemon 独占源工作区；hash 不是签名或宿主机防护。
不声称能防御模拟器漏洞。调用方仍须在执行前做预算 admission，并把 receipt
接入声明的 profile/trajectory/scorer；本模块本身没有模型工具注册和预算扣减。
native mini-swe/Reasoning、CLI、Evolution/memory 的接线另行实施；legacy 不变。
真实 Docker smoke 只是运行和来源边界证据，不是 baseline 复现或模型质量提升。

## 验证

最终 harness 回归 939 passed / 21 opt-in skipped；本模块 30 passed / 2 skipped。
真实 DUT/Testbench Docker smoke 2 passed，每个场景连续两次新建环境、检查真实
挂载只读/无网络、摘要有效及容器移除。导航/CI 检查 38 passed。
独立代码审查无代码问题；LSP/typecheck 未提供，不能声称通过。主线程 Ruff、
AST、bytecode compilation、YAML 与 diff 检查通过。首次真实 smoke 暴露 Docker
无法访问系统临时目录的问题，已修复为私有同级临时目录并重新通过。
