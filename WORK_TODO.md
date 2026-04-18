# behavioral-veriloga-eval Next-Stage Roadmap

更新日期: 2026-04-18

---

## 1. 文档定位

这份 `WORK_TODO.md` 是后续阶段的正式路线图，面向“接下来还要做什么”。

它和现有文档的分工如下：

1. `WORK_TODO.md`
   负责后续工作路线图、优先级和执行清单。
2. `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`
   负责逐行事实、结果元数据和 benchmark 状态。
3. `coordination/docs/project/TASK_ASSIGNMENT.md`
   负责从结果表自动生成的汇总视图。

---

## 2. 当前基线

截至 2026-04-18，项目主线状态可以概括为：

1. `end-to-end` 24 个任务已闭环。
2. `spec-to-va` 18 个任务已闭环。
3. `bugfix` 7 个任务已闭环。
4. `tb-generation` 7 个任务已完成 EVAS 主验证，并补齐了 EVAS+Spectre 执行证据。
5. benchmark / closed-loop 共有 24 行 `dual-validated`。
6. 当前没有 `verification_status != passed` 的 open row。
7. 当前没有需要单独跟踪的 parity / simulator 例外。

因此，后续工作不再是“补 benchmark 功能缺口”，而是以下四类：

1. metadata 和文档治理
2. bridge / runner 工程化加固
3. 日志质量、回归保护与可复现性提升
4. 下一阶段 benchmark 扩展与结果消费

---

## 3. 总体优先级

### Phase 1: 必做收尾

目标：把当前项目状态从“功能完成”推进到“记录清晰、维护顺手、结论稳定”。

### Phase 2: 工程化加固

目标：降低后续跑 dual-suite 和维护 benchmark 的摩擦。

### Phase 3: 质量与自动化

目标：减少未来回归风险，提高日志整洁度和状态一致性。

### Phase 4: 下一轮扩展

目标：在不破坏当前稳定面的前提下继续扩 benchmark 覆盖面，并为论文/汇报准备消费层材料。

---

## 3.5 本轮夜间进展

截至本轮自动推进结束，下面这些项已经有实质进展：

1. `4.1 补齐 pr_link 元数据`
   已进一步完成。基于本地分支、commit 历史和 upstream PR 证据，又补齐了一批 benchmark / spec-to-va / PLL formal-benchmark 行的 `pr_link`。剩余 `[TODO]` 主要集中在 testspace PLL seed 这类尚无独立 PR provenance 的历史参考行。
2. `4.3 固化文档分层规则`
   已完成。`README.md` 已明确说明结果表、syncer 和 `WORK_TODO.md` 的更新顺序与职责分工。
3. `4.4 写一份项目当前状态总览`
   已完成。`README.md` 已加入当前 benchmark 基线与剩余工作性质说明。
4. `5.2 强化 bridge preflight 的错误分类`
   已部分完成。`bridge_preflight.py` 现在新增了 `issue_codes` / `note_codes`，能更明确地区分手动 tunnel、daemon 断开、Spectre 不可用等情况。
5. `6.3 给关键 runner 增加最小回归测试`
   已完成。已新增 `tests/test_bridge_preflight.py` 和 `tests/test_run_gold_dual_suite.py`，并完成本地 smoke 运行。
6. `6.4 把更多检查接入 CI`
   已部分完成。`behavioral-veriloga-eval/.github/workflows/runner-smoke.yml` 已新增，覆盖 runner 语法检查、最小 smoke tests，以及 gold testbench `save` 语法守护。
7. `6.1 清理 Spectre save warning`
   已完成首轮高收益收敛。现有 gold testbench 中遗留的 `save ... :2e/:3f/:6f/:d` 等旧式限定符已统一清理，并补上 `tests/test_save_statements.py` 防止回归。
8. `7.5 下一轮 benchmark 扩展`
   已完成首轮落实。新增 `inverted_comparator_logic_bug`、`swapped_pfd_outputs_bug`、`wrong_edge_sample_hold_bug`、`gain_step_tb`、`sample_hold_step_tb`、`xor_phase_tb`，并在 `behavioral-veriloga-eval/results/gold-dual-suite-expansion-clean-2026-04-18/` 完成 6/6 clean dual-suite 验证。
9. `4.2 清理过时 notes`
   已完成一轮全表收口。PLL seed / formal-benchmark / non-e2e refresh 行里仍带过渡态语气的 notes 已统一改成稳定描述，保留真正有复用价值的技术背景。

仍未在本轮完成的高优先级项：

1. `4.1 补齐 pr_link 元数据`
   仍有少量历史 seed 行保留 `[TODO]`，原因不是漏查，而是当前没有对应的独立 PR/分支 provenance 可引用。

---

## 4. Phase 1 - 必做收尾

### 4.1 补齐 `pr_link` 元数据

优先级：高

目标：
把结果表中仍为 `[TODO]` 的 `pr_link` 尽可能补齐为真实来源。

具体动作：

1. 逐行检查 benchmark 主表中的 `[TODO]` 行。
2. 逐行检查 `spec-to-va` 表中的 `[TODO]` 行。
3. 逐行检查 `pll` 相关行是否已有可引用分支、commit 或 PR。
4. 仅在本地或远端证据明确时填写；查不到就保留 `[TODO]`。

产出：

1. 更新后的 `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`

验收标准：

1. 所有可确认来源的行都已填写。
2. 剩余 `[TODO]` 都是真正无法确认，而不是漏查。

依赖：

1. 需要本地 git 历史或远端仓库信息可访问。

当前状态：

1. benchmark-backed rows 的可确认 provenance 已再次补齐一轮。
2. 目前保留的 `[TODO]` 主要是 `testspace` 下的历史 PLL seed 参考行。
3. 这些剩余项在没有独立 PR 或可稳定引用的分支前，应继续保留 `[TODO]` 而不是猜填。

---

### 4.2 清理过时 notes

优先级：高

目标：
去掉已经被最新结果覆盖的历史描述，防止后续阅读者被误导。

具体动作：

1. 扫描结果表 notes 中仍带有临时性、过渡态、待补态语气的条目。
2. 删除与当前闭环状态矛盾的旧表述。
3. 保留真正有复用价值的背景，比如：
   - 任务为什么难
   - 哪个指标被视作 informational
   - 哪个结果路径是最终证据

产出：

1. 更简洁、更稳定的结果表 notes

验收标准：

1. 不再出现“结果已 closed，但 notes 还写 pending / workaround”的情况。

当前状态：

1. 已完成一轮全表系统清理。
2. 目前结果表中的 notes 以稳定事实、关键指标和真正需要保留的技术背景为主。

---

### 4.3 固化文档分层规则

优先级：高

目标：
避免结果表、自动汇总和后续阶段计划再次轻微失步。

具体动作：

1. 在相关文档顶部或 README 中明确每份文档的职责。
2. 约定状态更新顺序：
   - 先改 benchmark result table
   - 再跑 `sync_task_assignment.py`
   - 最后更新 `WORK_TODO.md` 的路线图状态
3. 如有需要，在 `README_TASK_REPORT.md` 或协调文档里补一页维护流程说明。

产出：

1. 一套稳定的文档更新顺序

验收标准：

1. 后续更新时不用靠聊天记录记忆“该先改哪份文档”。

---

### 4.4 写一份“项目当前状态总览”

优先级：中

目标：
让新加入协作者在 5 分钟内理解项目现状。

具体动作：

1. 概括四个 family 当前覆盖情况。
2. 说明 bridge 推荐用法。
3. 说明 dual validation 的当前范围。
4. 说明真正未完成的是什么，明确“不再有 benchmark blocker”。

建议位置：

1. `behavioral-veriloga-eval/README.md` 增补
2. 或 `coordination/docs/project/` 新增总览页

验收标准：

1. 新同学无需通读整个结果表即可知道项目状态。

---

## 5. Phase 2 - 工程化加固

### 5.1 把 `run_with_bridge.sh` 固化为唯一推荐入口

优先级：高

目标：
避免继续出现手工 SSH tunnel、端口漂移和 preflight 误判带来的使用摩擦。

具体动作：

1. 在所有涉及 dual-suite 的文档中统一写法。
2. 在示例命令中只保留 wrapper 版本。
3. 将手工 `ssh -L ...` 说明降级为“调试模式”。

产出：

1. 更统一的 runner 文档
2. 更少的人为使用分叉

验收标准：

1. 新用户默认不会直接手搓 tunnel。

---

### 5.2 强化 bridge preflight 的错误分类

优先级：高

目标：
让失败信息直接指向问题层，而不是只显示一个泛化失败。

建议分类：

1. local listener missing
2. ssh jump failure
3. bridge CLI unavailable
4. Virtuoso daemon unavailable
5. Spectre unavailable
6. tunnel exists but bridge status port mismatch

具体动作：

1. 扩充 `runners/bridge_preflight.py` 输出结构。
2. 让文本模式和 JSON 模式都更稳定。
3. 在 helper 脚本里保留原始错误上下文。

验收标准：

1. 使用者看到 preflight 输出后能立刻判断该先查网络、SSH、Virtuoso 还是 Spectre。

---

### 5.3 明确 `check_bridge_ready.sh` 的模式语义

优先级：中

目标：
让这个脚本能同时服务于本地快速检查、CI、以及长任务前的自检。

具体动作：

1. 统一并记录：
   - `--json`
   - `--require-daemon`
   - 安静模式或非零退出码语义
2. 给出几组标准示例：
   - 只查 tunnel + spectre
   - 查 tunnel + daemon + spectre
   - 仅用于 wrapper 前自检

验收标准：

1. 不同场景下使用方式清晰，不再依赖口头说明。

当前状态：

1. 已完成一轮脚本工程化加固：`check_bridge_ready.sh`、`start_bridge_tunnel.sh`、`run_with_bridge.sh` 现在都支持通过环境变量覆写 `BRIDGE_REPO` / `BRIDGE_ENV`，便于测试和跨仓复用。
2. 已新增 `tests/test_bridge_scripts.py`，覆盖：
   - `check_bridge_ready.sh --json`
   - `start_bridge_tunnel.sh` 在 listener 已存在时的行为
   - `run_with_bridge.sh` 的用法错误路径
3. 上述 helper script smoke 已接入 `runner-smoke.yml`。

---

### 5.4 评估 dual runner 是否进一步封装桥接调用

优先级：中

目标：
减少使用者绕开正确工作流的概率。

可选方向：

1. 保持当前 wrapper-only 约定
2. 在 runner 帮助信息里显式提醒 wrapper
3. 再上一步，做一个更高层的 repo 命令入口

验收标准：

1. 后续团队成员默认进入正确工作流，而不是自己拼接命令。

---

## 6. Phase 3 - 质量与自动化

### 6.1 清理 Spectre `save` warning

优先级：高

目标：
降低日志噪声，让真正的问题更容易被看到。

具体动作：

1. 统计当前常见 warning 模式。
2. 找出产生 warning 的 testbench `save` 写法。
3. 尽量改成 Spectre 更稳定接受的写法。
4. 回归关键任务，确认修改不影响结果。

当前状态：

1. 已完成首轮批量清理，gold testbench 中旧式 `save` 限定符已统一移除。
2. 已新增 `tests/test_save_statements.py`，把这类写法纳入仓库级回归保护。
3. 已完成跨 family 代表性双验证 smoke，`adpll_lock_smoke`、`pipeline_stage`、`mixed_domain_cdac_bug`、`clk_div_min_tb` 均通过。
4. 后续如仍有 warning，需要再判断是否来自 `save` 以外的日志源。

验收标准：

1. warning 数显著下降。
2. benchmark 结果不回退。

---

### 6.2 建立 warning 分级规则

优先级：中

目标：
区分 benign warning 和需要阻塞回归的 warning。

建议分级：

1. informational
2. noisy but tolerated
3. suspicious
4. blocking

产出：

1. 一份 warning 处理规则说明
2. 如果合适，可写进 runner 文档或 coordination 文档

验收标准：

1. 以后看日志时，团队知道哪些 warning 可以忽略，哪些必须处理。

---

### 6.3 给关键 runner 增加最小回归测试

优先级：高

目标：
保护已经稳定下来的关键逻辑不被后续修改悄悄破坏。

建议覆盖点：

1. `bridge_preflight.py` JSON 输出结构
2. `run_gold_dual_suite.py` 的 parity policy 分派
3. `tb-generation` 中 `sim_correct` 非必需时的 `parity=not_required`
4. syncer 的最小检查路径

验收标准：

1. 核心 runner 逻辑至少有 smoke-level 自动保护。

当前状态补充：

1. 已进一步把 bridge helper scripts 纳入 smoke 保护，避免 wrapper / preflight / tunnel helper 的基本行为在后续修改中悄悄漂移。

---

### 6.4 把更多检查接入 CI

优先级：中

当前已完成：

1. `sync_task_assignment.py --check`
2. `runner-smoke.yml` 中的 runner Python 语法检查
3. `runner-smoke.yml` 中的最小 pytest smoke tests
4. `runner-smoke.yml` 中的 gold testbench `save` 语法检查
5. `runner-smoke.yml` 中的 helper script smoke tests

后续可加：

1. helper 脚本 smoke test
2. 结果表格式检查
3. 结果路径存在性检查
4. 文档职责一致性检查

验收标准：

1. 常见维护错误能在提交阶段被拦下，而不是跑大任务时才发现。

---

### 6.5 记录结果目录 manifest

优先级：中

目标：
让每个重要 `results/` 目录更像一次可追溯实验，而不是只有一份 summary JSON。

建议记录：

1. 运行日期
2. 命令
3. 任务列表
4. 是否通过 wrapper 运行
5. 关键结论

验收标准：

1. 后续写报告或追溯结果时，不需要翻聊天记录。

---

## 7. Phase 4 - 结果消费与 benchmark 扩展

### 7.1 做 weekly summary 自动汇总

优先级：中

目标：
让项目管理和论文准备都能直接消费结果，而不需要手工数表。

建议指标：

1. 每周新增多少 case
2. 新增多少 verified
3. 新增多少 dual-validated
4. family 级别通过率
5. top failure modes

验收标准：

1. 每周状态能自动汇总，不靠手工维护大段文字。

---

### 7.2 生成 paper-ready 统计表

优先级：中

目标：
为论文、答辩、组会报告准备稳定的数据导出层。

建议输出：

1. 各 family 数量与通过率
2. dual validation 覆盖率
3. category 分布
4. 代表性 case 清单

验收标准：

1. 结果表能方便导出成 paper table，而不需要每次人工整理。

---

### 7.3 做代表性 case showcase

优先级：中

目标：
从大表中挑出最能说明项目价值的样例。

建议覆盖：

1. 普通数字逻辑
2. data-converter
3. calibration / signal-source
4. PLL 闭环
5. tb-generation

验收标准：

1. 对外展示时有短名单，不必直接扔整张结果表。

---

### 7.4 抽象 failure taxonomy

优先级：中

目标：
把这轮 benchmark 建设中暴露出的 Verilog-A 常见问题总结出来，反哺 skill 和论文叙述。

可总结的方向：

1. 端口 discipline / Cadence 兼容
2. `transition()` 与连续量混用
3. PRBS 初始化与状态机边界
4. `save` 语法兼容
5. PLL 任务中 generic parity 不适用的问题

验收标准：

1. 能形成一份清晰的问题类型列表，而不仅是零散修复记录。

---

### 7.5 下一轮 benchmark 扩展

优先级：低到中

当前状态：

1. 2026-04-18 已完成第一轮 family 扩展，`bugfix` 与 `tb-generation` 均从 4 个增至 7 个任务。
2. 本轮新增 6 个任务均已通过 gold validation；统一 clean dual-suite 结果位于 `behavioral-veriloga-eval/results/gold-dual-suite-expansion-clean-2026-04-18/`。
3. 这轮暴露出的主要工程经验是：gold testbench 中的 PWL 激励要优先使用 Spectre 更稳的单行写法，否则 EVAS 通过后仍可能在 dual-suite 阶段因为 netlist read-in 失败而返工。

前提：

1. Phase 1 到 Phase 3 至少大部分完成
2. 当前结果面稳定

可扩方向：

1. 新的 `end-to-end` 纯电压域模块
2. 新的 `spec-to-va` 细粒度模块
3. 新的 `bugfix` 典型错误类型
4. 新的 `tb-generation` case
5. 更多 PLL 相关但评分语义清楚的任务

扩展约束：

1. 不要为了凑数量破坏可评分性。
2. 不要引入需要大量手工判分的 case。
3. 不要把 benchmark 从 EVAS-primary 漂移成模糊的双 simulator 混合目标。

下一轮可优先补：

1. 更贴近真实修复流的 `bugfix` 子类型，比如参数极性写反、复位优先级错误、边沿/电平敏感混淆、输出 rail 饱和遗漏。
2. 更接近测量型 bench 的 `tb-generation` 子类型，比如建立时间/保持时间、迟滞比较器、频率步进、增益扫描、锁定窗口观测。
3. 评分语义清楚的 PLL 衍生 case，但仍要坚持 task-aware parity，不把 tb-generation 家族强行改成 waveform-perfect 比赛。

验收标准：

1. 每个新增任务都有明确 gold、checks、验证路径和表格登记规则。

---

## 8. 反哺 skill / 生成系统的工作

### 8.1 把修复经验写回 prompt / skill

优先级：中

目标：
减少未来再生成相同错误。

建议回写内容：

1. Cadence 兼容端口声明规范
2. `transition()` 使用边界
3. PRBS 初始化策略
4. PLL case 的 task-aware parity 原则
5. tb-generation 中何时不要求 `sim_correct`

验收标准：

1. 后续 representative case 的首轮通过率有提升空间。

---

### 8.2 建立新增任务 authoring checklist

优先级：中

目标：
让以后新加任务不再漏掉 gold、checks、Spectre 兼容项或文档登记。

建议 checklist 内容：

1. task 目录完整性
2. gold 资产完整性
3. EVAS 验证是否通过
4. 是否需要 dual validation
5. 结果表是否登记
6. 是否需要 sync task assignment

验收标准：

1. 新任务的接入流程稳定、可复制。

---

## 9. 建议执行顺序

如果按实际推进效率排序，推荐顺序是：

1. 补 `pr_link`
2. 清理过时 notes
3. 固化文档分层规则
4. 统一 bridge wrapper 使用路径
5. 清理 Spectre warning
6. 给关键 runner 加 smoke test
7. 扩展 CI
8. 做结果 manifest / weekly summary
9. 整理 paper-ready 表格与 showcase
10. 再开始下一轮 benchmark 扩展

---

## 10. 完成判据

当下面这些条件同时满足时，可以认为“当前阶段的后续治理工作已完成”：

1. 结果表中的 `pr_link` 已尽可能补齐。
2. 文档中不再存在明显过时的 pending / temporary 表述。
3. bridge 工作流已经统一为 wrapper-first。
4. 核心 runner 至少有最小回归保护。
5. Spectre warning 噪声已显著下降，或至少完成分级说明。
6. 周期性 summary 和结果消费路径已经有稳定模板。
7. 团队能在不依赖历史聊天的情况下继续扩 benchmark。

---

## 11. 一句话版本

这个项目下一阶段最重要的，不是继续“补 case”，而是先把 metadata、bridge 工作流、日志质量、回归保护和结果消费层做扎实；等这些打稳了，再进入下一轮 benchmark 扩展。
