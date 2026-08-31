# Native 工具链历史覆盖审计归档

归档日期：2026-08-31。来源为独立审计任务
`01a05640-c83b-7223-8da0-738af106d023`；本文件是脱敏摘要，不是本轮新实验。

## 结果与来源

审计记录 284 项免费测试通过（276 项扩展、5 项配置/预算、3 项故障形态复现）。
前一组测试跨 `dee9ccfeb0` / `e46a9d6719`，审计确认所选测试文件内容未变；
期间运行时变化只有单独验证的 pilot cap 接线。后两组在 `e46a9d6719` 完成。
这些是历史测试数，不重复计入后来 AA-VAE-070 或本轮测试总数。

| 后端 | 任务 | 历史真实结果 |
| --- | --- | --- |
| native-mini-swe | DUT / v4-001 | 8 轮后提交，一次冻结/评分，development score=1.0 |
| native-reasoning | DUT / v4-001 | 第3轮输出截断且没有合法工具调用；无提交、无评分 |
| native-mini-swe | bugfix / v4-1001 | 首次请求 HTTP/2 失败，费用未知；无提交、无评分 |
| native-reasoning | bugfix / v4-1001 | 预算停止后未启动 |
| native-mini-swe | Testbench / v4-501 | 预算停止后未启动 |
| native-reasoning | Testbench / v4-501 | 预算停止后未启动 |

成功 DUT 源码为 `dee9ccfeb09cc41baf1982d1ee7882f92aef5d72`；补测源码为
`e46a9d6719893d500071f6cf5ce744d4dc7f439a`。这是一个真实工程闭环、六组合覆盖
中的 1/6，不是统一新版本的 Pass@1、论文 baseline 或 leaderboard。
runner 的 completed 不能代替有效 submission + score；未提交行的分数保持 null。

## 停止、费用与已修复问题

审计的累计保守占用为 CNY 3.577842，其中 CNY 3.182592 是未知费用请求的
完整预留，不是已确认扣款或发票。其单独5元授权尚未占用 CNY 1.422158，低于
下一请求所需预留。8月30日旧 pilot 属于另一封存账本，不能混加、抵消或重置。

预算 cap 未传入守卫的缺陷已由 `e46a9d6719` 修复，并已随 `e2498952bb` 推送
到 fork/main。截断响应缺少合法工具调用、HTTP/2 失败费用未知时，拒绝执行/继续
符合现有契约；独立复审没有据此发现 EVAS 或最终评分缺陷。增加 episode 轮数
本身不能解决这两个问题。本轮没有重新调用模型、重新评分或读取原始模型轨迹。

## 可追溯摘要

原始脱敏报告及覆盖表保留在审计任务的本地归档；源摘要哈希在本次入库时重新计算：

| 来源文件 | SHA-256 |
| --- | --- |
| 工具链覆盖验收.md | `886ce53603a8d4b3f3478b877f1e68a14ba5969886e5b4d59b109b02104a46ce` |
| coverage.json | `98d8b801b7a1f15d48fef2db9710fae04aba79e8aa33f0ac34124fc2ec8c06b2` |
| final-verification.json | `3f4ec62a4a70b4c1ed745241d2f08a2acdf2c88df663df0243ee32e6508ef318` |

这次只复核脱敏摘要和这些来源文件的哈希；底层私有运行证据的逐项验证来自原审计，
并未在此重复执行。原始响应、候选、完整轨迹、费用 journal 不进入 Git。

## 后续边界

AA-VAE-069 的 legacy/native-mini-swe 对照是另一组六单元，仍未真实启动；不能
拼接本报告的成功项完成它。任何新付费运行都需要新的冻结配置与费用授权，保留
所有历史失败和未知预留。当前免费工程工作见
[对照启动门槛计划](../../../plans/legacy-native-comparison-engineering.md)。
