# AA-VAE-058：有界公开波形摘要器

日期：2026-08-31。状态：独立 parser 实现；**尚未接入模型 observation**。
实现提交：`bc62c625d6`（fork/main）。

沿用 AA-VAE-056 的公开反馈压缩思想，而不是复制 hidden checker 的容差或默认值。
新增 `runners/agent_harness/tools/waveform_summary.py`，唯一输入为可信调用方选定的
输出目录，文件名固定 `tran.csv`。`summarize_waveform()` 返回 detached JSON，
`waveform_policy()` / `waveform_policy_sha256()` 明确上限及不具备的权限。

读取最多 1 MiB，扫描最多 10,000 行、32 列，返回最多 8 个信号；信号名最长 128
字符。拒绝链接、非普通文件、坏编码、异常 header、错列、非数值文本和过多列。
文件用 no-follow / nonblocking descriptor、有界读取和类型检查；父目录仍要求
可信、无并发恶意替换，不把普通文件校验称为完整 sandbox。

返回 missing / invalid / too_large / truncated / available；记录被接受字节 hash、
已扫描行数、遗漏和有限/非有限/空单元计数，min/max/mean/first/last。
单位未知时为 null；不根据列名猜电压，不引入边沿或任务阈值，不输出 pass/score。
不回显原始错误值、宿主路径或无限长错误文本。

测试位于 `tests/test_agent_harness_waveform_summary.py`。主审增加并修复了极端
正负浮点、root/ancestor symlink、FIFO、长 header/error、畸形 CSV 和遗漏标记。
精确 RED/GREEN 与独立审查结果见 verification log。

## 剩余接线门槛

这个函数只证明“这些字节可被有界解析”，不证明它们来自本候选/本次 EVAS。
本轮没有更改 PublicEvasValidator profile，也没有为任意 Bash 自动附加摘要。
AA-VAE-055 的可伪造 marker 不能作为 waveform 来源证明。后续需要专属、全新
public execution 输出和 candidate/profile/invocation/file hash receipt，然后再
让 controller 交给模型。不能读取共享旧 `tran.csv` 后补一个当前 candidate 标签。
这是明确的未完成集成项，不是把 parser 单测当成波形工具已经上线。
