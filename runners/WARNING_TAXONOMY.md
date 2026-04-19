# Warning Taxonomy

更新日期: 2026-04-19

## 目标

把 runner、Spectre、bridge preflight、以及 benchmark 资产中的 warning 分成可操作的等级，避免把所有 warning 都当成同一种问题。

## 分级

### W0 — 实际阻塞型

这些 warning 已经等价于失败，必须立即处理。

典型症状：

1. netlist read-in 失败后只剩包装层 `warning` 文案
2. 结果目录未生成 `tran.csv`
3. runner summary 中出现 `status != PASS`

处理原则：

1. 直接按 `FAIL_DUT_COMPILE`、`FAIL_TB_COMPILE`、`FAIL_INFRA` 归因，不要淡化成“只是 warning”。

### W1 — parity 风险型

不会立即让运行失败，但可能让 EVAS / Spectre 对比结论失真，必须审计。

典型例子：

1. `VACOMP-1116` 一类 AHDL warning，但最终 transient 成功
2. PLL 任务中 monitor 信号存在信息性偏差
3. runner 输出指出 `parity status = needs-review`

处理原则：

1. 记录到 `EVAS_SPECTRE_ALIGNMENT_AUDIT.md`
2. benchmark 主结论可先保留，但不要当成已完全波形对齐

### W2 — benchmark hygiene 型

主要是资产写法不规范，不代表 EVAS 核心语义错误。

典型例子：

1. 旧式 `save vout:2e` / `:3f` / `:6f` / `:d`
2. PWL 续行、token 数或换行格式不稳
3. testbench 中 `ahdl_include` 使用了不应出现的路径写法

处理原则：

1. 修 benchmark / gold 资产
2. 用 `tests/test_save_statements.py`、`tests/test_pwl_statements.py` 一类检查防回归

### W3 — 环境或 bridge 状态提示型

说明环境状态不理想，但不一定影响当前结果。

典型例子：

1. `manual_tunnel_detected`
2. `daemon_disconnected`
3. `manual_tunnel_listener_pids`

处理原则：

1. 优先记录到 run manifest 或 preflight 输出
2. 若当前结果已生成且状态正常，不要把它误记成 DUT / TB 问题

### W4 — 信息性接受型

当前已知、可接受、且不需要因为它改 benchmark 资产。

典型例子：

1. Spectre 的一般性参数禁用提示，如 `SPECTRE-592`
2. 已知不影响 transient 成功和关键指标的 notices

处理原则：

1. 可以保留在 `notes`
2. 不要为清零此类提示去改 DUT 行为

## 使用规则

1. 先判断 warning 是否阻塞结果；阻塞则归 `W0`。
2. 不阻塞但会影响 EVAS / Spectre 对齐结论，则归 `W1`。
3. 仅资产写法不规范，则归 `W2`。
4. 仅环境状态提示，则归 `W3`。
5. 明确不影响结果的已知提示，则归 `W4`。

## 建议落点

1. `W0` / `W1`：写进 run summary、audit 文档、review 记录
2. `W2`：写进 benchmark 维护文档和对应回归测试
3. `W3` / `W4`：写进 `MANIFEST.md` 或 summary `notes`
