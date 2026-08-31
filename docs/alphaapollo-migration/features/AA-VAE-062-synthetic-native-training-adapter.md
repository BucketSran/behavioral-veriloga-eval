# AA-VAE-062：合成 native 轨迹到训练格式的适配

> **2026-09-01 已退役**：metadata/hash 适配原型及专属测试已移出当前主线，
> 未接入真实训练。下文是历史设计与验证；当前 trajectory 捕获/安全导出不受影响。
> [删除前源码](https://github.com/BucketSran/behavioral-veriloga-eval/blob/5d2a39fe0dde076654e362716456b1a8cedc1547/runners/agent_harness/training_trace_adapter.py)
> 及同一提交中的 `tests/test_agent_harness_training_trace_adapter.py` 可从 Git 恢复，
> 同时需要恢复 [AA-VAE-059](AA-VAE-059-synthetic-training-export.md)。
> [清理范围](../../../plans/mainline-scope-cleanup.md)；真实训练另行立项。

日期：2026-08-31。状态：合成契约接线已验证；不导出真实数据，不启动训练。

## 思想与代码

延续 AlphaApollo 的“推理轨迹与未来训练分离”思路，复用 AA-VAE-059 的
SFT/RL source/export 契约，不新增训练框架、数据集或依赖。

- `runners/agent_harness/training_trace_adapter.py` 的
  `project_synthetic_native_trace_to_training_source` 接收内存中的 synthetic
  native 事件、来源/许可声明和 split；复用原有事件链/生命周期验证及
  `build_training_export`，只生成已有格式。
- `tests/test_agent_harness_training_trace_adapter.py` 覆盖两种格式、权限、
  事件顺序、未知 payload、可见性、上限、确定性和导出重建校验。
- 来源版本同时绑定 adapter ID 与输入轨迹完整 SHA-256。声明和 hash 不是
  真实许可、作者身份或去污染证明。

## 输出与限制

这里投影的是 controller 记录的动作/观察**元数据和 hash**，不是恢复原始
工具参数、模型回答或代码；因此只是训练格式兼容性 fixture，不是可以训练
有效 coding policy 的完整语义样本。system/user 初始消息来自显式合成 metadata。
环境观察不作为 assistant loss target；RL reward 必须另外声明为 public validation，
不会从 final score 提取。真实训练仍缺有权导出的语义内容、去重/污染审查和训练器。

仅接受 synthetic 命名空间与固定合成 release、CC0、provider/project/exposure
声明及已有 train/dev/heldout gate。未知事件/payload、损坏事件链、freeze 后重入、
私有/hidden/final 内容和超限输入拒绝。内容标记检查只是防止矛盾的保守门，
不声称它可以识别任意真实数据来源。没有文件入口、CLI、provider 请求或训练任务。

## 验证与审查

独立 executor 仅修改模块与测试，主线程统一集成。初始测试在模块不存在时 RED，
实现后原 exporter 与新增 adapter 合计 **41 passed**。独立只读审查未发现阻断问题；
主线程补完整 trace digest 的 RED→GREEN 回归，避免只绑定摘要前缀。
模型质量、训练收益、真实数据授权均未在本切片得到验证。
