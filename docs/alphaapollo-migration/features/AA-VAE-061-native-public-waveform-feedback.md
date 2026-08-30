# AA-VAE-061：独立公开波形工具接入 native harness

日期：2026-08-31。范围：显式 single-cell 开发 API，legacy 不变。

## 思想与代码位置

沿用 AlphaApollo 的多轮公开环境反馈，但复用 vaEVAS 现有 controller、预算、
轨迹和冻结/终评边界。不是复制数学 XML 协议，也不将 Bash 日志当作可信验证。

- `run_native_mini_swe.py::run_prepared_native_mini_swe` 新增
  `public_waveform_max_calls=None`。正整数显式启用，OneShot、No-EVAS、非隔离
  测试 sandbox 拒绝。两种 native backend/Reasoning 两种输出格式用相同工具。
- `runners/agent_harness/tools/public_waveform_tool.py` 定义零参数
  `vaevas_public_simulate`、封闭 descriptor/receipt schema、typed observation。
  controller 原有 `public_validation` admission 同时计 tool/public request；
  没有新 controller 或预算循环，不开放命令/路径参数。
- `public_waveform.py::inspect_candidate` 先检查不安全输入，再区分缺文件。
  缺文件返回可恢复观察，不启动 executor、不伪造 receipt。完整候选调用
  AA-VAE-060；语法失败交给 EVAS，绝不自行编译器式猜测。
- launcher 暂停并检查原 Docker 容器的 Paused 状态，再检查/快照/执行；
  finally 恢复并检查状态，防止后台 Bash 子进程修改源候选。隔离执行也受
  episode 剩余墙钟时间限制。原始异常与恢复/清理 incident 分别留在私有证据。
- `score_campaign.py::read_native_cell` / `read_native_waveform_evidence`
  重建工具/预算、profile/config、公开输入、候选、receipt 和 invocation joins。
  只读评分记录，不重新执行公开或最终 checker。

## 计数与权限

`public_validation_calls` 是已接纳固定动作的请求数，包括缺文件反馈。
`public_waveform_evas_invocations_confirmed` 只统计回执证实的模拟执行。
完整时 `public_waveform_evas_invocations_executed` 给出总次数；若进入执行器后
抛错且没有回执，则总次数为 null，`public_waveform_execution_count_complete=false`。
执行前失败可确认 0；执行完成但恢复生成容器失败仍保存私有回执、确认已执行。

这不是所有 EVAS 进程的全局限额：普通 Bash 仍可直接调用 EVAS，其 markers
仍只是未认证诊断。公开反馈 `task_correctness=not_evaluated`，不会升级成
最终正确性。最终分数只在提交冻结后产生，从不返回下一轮模型请求。
本切片不允许 waveform 观察直接进入共享 memory；Evolution 需要单独投影。

## 干预身份与验证边界

config hash 前声明 `extensions.public_waveform` 的干预 ID、工具名、请求限额；
之后用既有 profile 字段绑定配置，避免 profile/config 循环。扩展行仍不能混入
普通 aggregate/paired ledger。CLI/Evolution 与匹配实验协议是后续独立接线。

测试覆盖缺文件恢复/禁止不安全树、二次请求在暂停前拒绝、失败/超时/恢复异常、
post-launch 计数未知、重算 hash 后篡改 receipt 拒绝、封闭 schema 和入口条件。
免费 scripted provider 在真实 Docker 下验证 mini-swe、Reasoning tool-call/JSON
三种路径：公开反馈 → 下一轮 → freeze → 一次 EVAS final score。
CI 增加独立 smoke。具体回归数、审查和提交见 verification log。

没有新增第三方代码、依赖、模型费用、真实 corpus/训练数据、r53 或 EVAS 修改。
信任 coordinator/host/Docker；hash joins 不是签名，也不证明模型能力提升。
