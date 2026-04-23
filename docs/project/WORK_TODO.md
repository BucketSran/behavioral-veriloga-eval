# behavioral-veriloga-eval Next-Stage Roadmap

更新日期: 2026-04-19

---

## 1. 文档定位

这份 `WORK_TODO.md` 是后续阶段的正式路线图，面向“接下来还要做什么”。

它和现有文档的分工如下：

1. `docs/project/WORK_TODO.md`
   负责后续工作路线图、优先级和执行清单。
2. `tables/` 与 `tables/RUN_REGISTRY.md`
   负责论文可追踪的结果摘要与 run 记录。
3. `docs/project/PROJECT_STATUS.md`
   负责对外可读的当前阶段状态总览。

说明：
本文件包含较早阶段的历史规划文本，部分段落仍引用旧的
`coordination/...` 路径。当前有效工作流请以
`docs/project/POST_RUN_PLAYBOOK.md` 和 `README.md` 为准。

---

## 2. 当前基线

截至 2026-04-19，项目主线状态可以概括为：

1. `end-to-end` 39 个任务已闭环。
2. `spec-to-va` 18 个任务已闭环。
3. `bugfix` 8 个任务已闭环。
4. `tb-generation` 11 个任务已完成 EVAS 主验证，其中 7 个已补齐 EVAS+Spectre 执行证据。
5. benchmark / closed-loop 共有 32 行 `dual-validated`。
6. 当前没有 `verification_status != passed` 的 open row。
7. 当前有 1 条需要单独跟踪的 waveform-alignment / simulator 审计项：`cppll_freq_step_reacquire_smoke`。

因此，后续工作已经不再是“补 benchmark 功能缺口”，而是以下四类：

1. metadata 和文档治理
2. bridge / runner 工程化加固
3. 日志质量、回归保护与可复现性提升
4. 下一阶段 benchmark 扩展与结果消费

此外，需要单独补一条“`EVAS` 向 Virtuoso/Spectre 靠齐”的内核审计主线：

1. 这不是 benchmark blocker，因为当前 benchmark 主表已 closed。
2. 但 examples / 历史 gold 改写里仍能看到少量“为了绕开旧 EVAS 限制而重写模型表面”的痕迹。
3. 这类项应和 benchmark hygiene 分开管理，原则上优先修 `EVAS`，而不是继续修改 benchmark 资产来迁就 EVAS。

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
10. `7.5 下一轮 benchmark 扩展`
   已完成第二轮 `end-to-end` 主线推进。新增 `cmp_delay_smoke`、`cmp_strongarm_smoke`、`dwa_ptr_gen_no_overlap_smoke`，并在 `behavioral-veriloga-eval/results/gold-dual-suite-benchmark-expansion/` 完成 3/3 EVAS+Spectre dual-suite 验证；其中 comparator gold DUT 采用了更显式、低 warning 的 benchmark gold 风格。

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

> **[已完成]** 已完成一轮全表系统清理。

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

> **[已完成]** README 已明确文档更新顺序与职责分工。

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

### 4.4 写一份”项目当前状态总览”

> **[已完成]** `behavioral-veriloga-eval/README.md` 已补入基线状态与剩余工作性质说明。

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

> **[已完成]** `bridge_preflight.py` 已新增 `issue_codes` / `note_codes` 分类。

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

### 5.3 建立 EVAS / Spectre mismatch 审计清单

优先级：高

目标：
把”该修 EVAS”与”该修 benchmark/testbench”严格分开，避免以后再次把 EVAS 语义限制误当成 gold 资产问题。

具体动作：

1. 新建文件 `coordination/docs/project/EVAS_SPECTRE_ALIGNMENT_AUDIT.md`，按以下四节组织：

   **A. 已确认对齐（EVAS 与 Spectre 行为一致）**
   每条格式：`| 语义点 | 确认方式 | 证据目录 | 日期 |`
   包含：conditional idtmod fatal、conditional cross/above fatal、
   conditional absolute timer、conditional periodic timer、
   timer→transition→cross 时序、PLL t_next pull/push、DCO phase update。

   **B. EVAS 已收严（与 Spectre fatal 对齐，不应放开）**
   每条格式：`| 语义点 | Spectre 行为 | EVAS 行为 | 是否正确 |`
   包含：conditional idtmod（Spectre: VACOMP-2154 fatal）、
   conditional cross / above（Spectre: fatal 拒绝）。

   **C. 残余 waveform-level 差异（benchmark 已 closed，但波形未完全一致）**
   每条格式：`| case | 差异描述 | 数值 | 下一步 |`
   包含：cppll_freq_step_reacquire_smoke 的晚期 lock 脉冲尾部偏移
   （第5个上升沿早19.5ns，第6个早39ns），分析方向：lock 定义换成
   内部 streak counter 状态口而不是波形口。

   **D. 尚未双跑确认的语义点（待 probe）**
   每条格式：`| 语义点 | 预计行为 | 优先级 |`
   包含：periodic timer period shrink/expand 下的已 arm tick、
   cross/above 在粗步长 + transition 叠加时的重触发边界、
   self_output_dependent_cross 重触发、multiple_writes_same_step 可见性。

2. 对”C”里 cppll lock 差异，在同文件中写明分析假设和下一步实验命令。

产出：

1. `coordination/docs/project/EVAS_SPECTRE_ALIGNMENT_AUDIT.md`（新建）
2. 相应的 EVAS regression tests（从 D 节逐步推进）

验收标准：

1. 新同学能明确区分 “simulator-core mismatch” 与 “benchmark hygiene”。
2. A/B 节条目完整，每条都有可检索的证据路径。
3. C 节 cppll 差异已有书面分析和下一步方向。

当前状态：

1. `transition()` continuous-target 与 conditional `transition()` 这两类 EVAS 过严限制已完成一轮收敛。
2. `conditional idtmod()` 已在 2026-04-18 本地 probe 中确认 Spectre 会直接报 fatal `VACOMP-2154`，因此 EVAS 当前限制应视为对齐行为，而不是待放开的兼容缺口。
3. `conditional cross()` 与 `conditional above()` 已在 2026-04-18 conditional operator suite 中确认 Spectre 直接 fatal 拒绝，EVAS 现已同步补上编译期限制。
4. conditional absolute `timer(next_t)` 已在 2026-04-18 probe 中完成运行时对齐：EVAS 现在和 Spectre 一样，不会在首次晚使能或 disable 窗口错过目标后补触发过期 timer。
5. conditional periodic `timer(start, period)` 也已在 2026-04-18 probe 中完成运行时对齐：EVAS 现在会像 Spectre 一样跳过 missed ticks，但保持原始相位，并在重新进入 active window 后从第一个未来周期点继续。
6. `timer() -> transition() -> cross()` 独立边界时序也已在 2026-04-18 修正：EVAS 现在会在同一时刻 contributions 更新后补做一次 cross/above 后检查，并重放非 event 赋值/贡献逻辑，因此粗步长 probe 的 crossing time 已与 Spectre 一样落在 11ns 而不是 12ns。
7. `worksche/experiments/conditional_operator_suite/run_suite.py` 已补上直连 SSH 的 Spectre 执行 fallback，不再硬依赖本地 tunnel 状态文件是否仍然可用。
8. `PLL-style timer phase update` 这一条也已补齐证据：`pll_timer_phase_update_suite` 证明 EVAS 与 Spectre 在两类关键语义上保持一致：
   - 已 arm 的 absolute `timer(next_t)` 后续可被 pull-in / push-out 到新的未来目标时间；
   - 显式 `t_next = t_next + half_t` 的 DCO 写法中，单独修改 `half_t` 不会 retroactively 改动已经 arm 的下一次边沿，而是从下一次 reschedule 起生效。
9. 2026-04-19 已完成第三轮 `end-to-end` 扩展，新增 `comparator_hysteresis_smoke` 与 `pfd_deadzone_smoke`，统一 dual-suite 结果位于 `behavioral-veriloga-eval/results/gold-dual-suite-expansion-2026-04-19/`。
10. 这轮扩展没有暴露新的 EVAS/Spectre 内核不一致，但确实暴露了一个 runner 层误判：PFD 短脉冲 case 不能再用”样本点比例”近似 duty，现已改成按时间加权计算，避免 adaptive timestep 把 near-deadzone 脉宽误判成大占空比。

---

### 5.4 明确 `check_bridge_ready.sh` 的模式语义

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

### 5.5 评估 dual runner 是否进一步封装桥接调用

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

> **[已完成（首轮）]** gold testbench 旧式 `save` 限定符已统一清理，并有 `test_save_statements.py` 回归保护。

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

具体动作：

新建文件 `behavioral-veriloga-eval/runners/WARNING_TAXONOMY.md`，内容结构如下：

```
# Warning 分级规则

## Level 0 — Informational（可忽略）
- Spectre `save` format 旧式限定符（已清理，test_save_statements 保护）
- ahdl_include 路径相对化提示
- "Using default ..." 类提示

## Level 1 — Noisy but tolerated（记录，不阻塞）
- PWL 激励插值精度提示
- "Model parameter out of range" 但在合理物理范围内
- EVAS 自适应步长调整日志

## Level 2 — Suspicious（需人工确认）
- "timestep too small, forcing minimum"
- "convergence difficulty at t=..."
- dual-suite 中 EVAS 与 Spectre 结果 NRMSE > 0.1

## Level 3 — Blocking（必须修复后才能登记结果）
- "fatal error" / "VACOMP-xxxx" 编译期错误
- EVAS returncode != 0 且 tran.csv 不存在
- "segmentation fault" 或 Python traceback
- dual-suite 结果 parity=failed 且 delta 超出 task-aware 阈值
```

产出：

1. `behavioral-veriloga-eval/runners/WARNING_TAXONOMY.md`（新建）

验收标准：

1. 团队看到任何 warning 后能对照此表判断是否需要处理。
2. Level 3 条件已在 run_gold_dual_suite.py 的 `ok=False` 逻辑中有对应体现。

---

### 6.3 给关键 runner 增加最小回归测试

> **[已完成]** `test_bridge_preflight.py`、`test_run_gold_dual_suite.py`、`test_bridge_scripts.py` 已就位并接入 CI。

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

待补充的 CI 检查（在 `runner-smoke.yml` 中新增 step）：

**检查 1：results 路径存在性**
```yaml
- name: Check result paths exist
  run: |
    python - <<'EOF'
    import json, pathlib, sys
    table = pathlib.Path("coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md").read_text()
    # 扫描 results/ 列里的路径，验证目录存在
    import re
    paths = re.findall(r'results/[\w\-/]+', table)
    missing = [p for p in set(paths) if not pathlib.Path(p).exists()]
    if missing:
        print("Missing result dirs:", missing); sys.exit(1)
    EOF
```

**检查 2：task 目录完整性**
```yaml
- name: Validate task dirs have required files
  run: |
    python - <<'EOF'
    import pathlib, sys
    required = {"prompt.md", "meta.json", "checks.yaml"}
    bad = []
    for td in pathlib.Path("tasks").glob("*/*/*"):
        if td.is_dir():
            missing = required - {f.name for f in td.iterdir()}
            if missing: bad.append(f"{td}: missing {missing}")
    if bad:
        print('\n'.join(bad)); sys.exit(1)
    EOF
```

**检查 3：meta.json schema 合规**
新建 `tests/test_meta_schema.py`，对 `tasks/` 下所有 `meta.json` 运行 jsonschema 验证，确保 family / domain / scoring / expected_backend 字段都在位。

验收标准：

1. 上述三类维护错误能在 push 时被 CI 拦下。
2. `test_meta_schema.py` 已加入 `runner-smoke.yml` 的 pytest 命令。

---

### 6.5 记录结果目录 manifest

优先级：中

目标：
让每个重要 `results/` 目录更像一次可追溯实验，而不是只有一份 summary JSON。

具体动作：

**步骤 1：新建脚本 `runners/gen_manifest.py`**

```python
# 用法：python runners/gen_manifest.py <results_dir> \
#         --cmd "python runners/run_gold_dual_suite.py ..." \
#         --note "首轮扩展验证"
# 输出：<results_dir>/MANIFEST.md
```

脚本从 `summary.json`（如存在）读取任务列表和通过率，结合 `--cmd` / `--note` 参数，
生成如下格式的 `MANIFEST.md`：

```markdown
# Run Manifest

- **Date**: 2026-04-19
- **Command**: python runners/run_gold_dual_suite.py ...
- **Via wrapper**: yes
- **Tasks**: cmp_delay_smoke, cmp_strongarm_smoke, dwa_ptr_gen_no_overlap_smoke
- **EVAS pass**: 3/3
- **Dual validated**: 3/3
- **Note**: 首轮扩展验证，全部通过
```

**步骤 2：为现有 results/ 目录补 MANIFEST.md**

已有但缺少 manifest 的目录（优先补）：
- `results/gold-dual-suite-expansion-clean-2026-04-18/`
- `results/gold-dual-suite-benchmark-expansion/`
- `results/gold-dual-suite-expansion-2026-04-19/`
- `results/gold-dual-suite-cppll-initial-step-fix-v2/`

从 summary.json 和对应的 3.5 节记录恢复历史命令即可。

验收标准：

1. `gen_manifest.py` 脚本存在且可运行。
2. 上述 4 个现有目录都有 `MANIFEST.md`。
3. 后续每次运行 dual suite 时都用这个脚本生成 manifest。

---

## 7. Phase 4 - 结果消费与 benchmark 扩展

### 7.1 做 weekly summary 自动汇总

优先级：中

目标：
让项目管理和论文准备都能直接消费结果，而不需要手工数表。

具体动作：

**新建脚本 `runners/gen_weekly_summary.py`**

输入：`coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`
输出：打印到 stdout 或写入 `coordination/status/summary_<date>.md`

解析逻辑：
- 读取 Markdown 表格，识别列：`id | family | verification_status | dual_validated | date_added`
- 若 `date_added` 列不存在，从 notes 中提取日期或标记 unknown
- 统计：
  - 各 family 的任务总数
  - `verification_status = passed` 的数量
  - `dual_validated = yes` 的数量
  - 最近 7 天新增条目（通过 date_added 过滤）

输出格式：
```markdown
# Weekly Summary — 2026-04-19

## 总体状态
- 总任务数：N
- 已验证（EVAS passed）：N
- Dual validated：N

## 各 family 明细
| family | total | evas_passed | dual_validated |
|--------|-------|-------------|----------------|
| end-to-end | 39 | 39 | 32 |
| spec-to-va | 18 | 18 | 0 |
| bugfix | 8 | 8 | 7 |
| tb-generation | 11 | 11 | 9 |

## 本周新增
（自动列出 date_added 在最近 7 天的条目）
```

验收标准：

1. 脚本能从结果表生成上述报告，无需人工整理。
2. 已接入 `coordination/status/` 目录的写入路径。

---

### 7.2 生成 paper-ready 统计表

优先级：中

目标：
为论文、答辩、组会报告准备稳定的数据导出层。

具体动作：

**新建脚本 `runners/gen_paper_stats.py`**

输入：`coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md`
输出：
1. `coordination/docs/paper/PAPER_STATS.md`（Markdown 格式，可直接粘贴进论文草稿）
2. `coordination/docs/paper/paper_stats.json`（机器可读，供后续绘图脚本使用）

输出内容：

**Markdown 表 1 — family 分布（LaTeX 友好格式）**
```
| Task Family   | # Tasks | EVAS Passed | Dual-Validated |
|---------------|---------|-------------|----------------|
| end-to-end    | 39      | 39 (100%)   | 32             |
| spec-to-va    | 18      | 18 (100%)   | 0              |
| bugfix        | 8       | 8 (100%)    | 7              |
| tb-generation | 11      | 11 (100%)   | 9              |
| **Total**     | **76**  | **76**      | **48**         |
```

**Markdown 表 2 — category 分布**
按 meta.json 的 `category` 字段统计任务数量。

**JSON 格式**
```json
{
  "total_tasks": 76,
  "families": {...},
  "categories": {...},
  "dual_validated_total": 48,
  "generated_at": "2026-04-19"
}
```

验收标准：

1. 脚本可以无参数运行，自动找到结果表。
2. 输出的 Markdown 表格列宽对齐，可直接粘贴到论文草稿。
3. JSON 文件包含所有汇总字段。

---

### 7.3 做代表性 case showcase

优先级：中

目标：
从大表中挑出最能说明项目价值的样例，用于答辩、组会和论文 section。

具体动作：

**新建文件 `coordination/docs/benchmark/CASE_SHOWCASE.md`**

每条格式：
```markdown
### <case_id>
- **Family**: end-to-end / spec-to-va / bugfix / tb-generation
- **Circuit type**: comparator / PLL / data-converter / digital-logic
- **Why interesting**: <1句话说明这个 case 能验证什么能力>
- **Key check**: <最关键的评分维度>
- **Gold path**: `tasks/<family>/voltage/<case_id>/gold/`
```

建议覆盖的 showcase 条目（各类至少 1 个）：

| 覆盖维度 | 推荐 case |
|---------|----------|
| 数字逻辑基础 | `clk_divider` 或 `therm_to_bin` |
| DAC / ADC | `sar_adc_dac_8b` 或 `dac_therm_16b` |
| Comparator 状态 | `comparator_hysteresis_smoke` |
| PFD 短脉冲 | `pfd_deadzone_smoke` |
| PLL 闭环 | `adpll_lock_smoke` |
| PLL relock | `cppll_freq_step_reacquire_smoke` |
| Bugfix 典型 | `swapped_pfd_outputs_bug` 或 `wrong_edge_sample_hold_bug` |
| TB generation | `gain_step_tb` 或 `sample_hold_step_tb` |

验收标准：

1. 文件存在，包含至少 8 条完整格式的 showcase 条目。
2. 每条都有 "Why interesting" 一句话说明。

---

### 7.4 抽象 failure taxonomy

优先级：中

目标：
把这轮 benchmark 建设中暴露出的 Verilog-A 常见问题总结出来，反哺 skill 和论文叙述。

具体动作：

**新建文件 `coordination/docs/project/FAILURE_TAXONOMY.md`**

按以下结构组织，每条包含：问题描述、典型症状、已知触发 case、修复策略：

```markdown
# Verilog-A Generation Failure Taxonomy

## F1 — 端口 discipline 不兼容
**症状**: Spectre 编译报 `incompatible port discipline`
**触发 case**: 早期 PLL case 中 voltage/current 混用
**修复**: voltage domain 模块所有端口用 `electrical`，
          禁止 `ground`/`wreal` 在纯电压域模块中使用

## F2 — transition() 目标值为连续表达式
**症状**: EVAS 编译报 `transition target must be discrete`
**触发 case**: comparator gold DUT 中用 `transition(vin > 0 ? vdd : 0)`
**修复**: 先用 if-else 赋值给局部变量，再传给 transition()

## F3 — PRBS 初始化状态全零
**症状**: PRBS 输出全零，无法产生序列
**触发 case**: `prbs7_gen`，`nrz_prbs`
**修复**: initial_step 中初始化 seed = 7'h01（或任意非零值）

## F4 — save 语句旧式限定符
**症状**: Spectre warning "unsupported save qualifier :2e/:3f"
**触发 case**: 早期 gold testbench 中的 `save vout:2e`
**修复**: 移除限定符，直接写 `save vout`

## F5 — PLL 任务使用 generic parity 导致误判
**症状**: EVAS/Spectre waveform NRMSE < 阈值但评分 failed
**触发 case**: cppll 和 adpll 类任务
**修复**: PLL 类任务必须用 pll_task_aware parity（
          检查 relock_time、UP/DN 方向、vctrl 趋势，不逐点比较波形）

## F6 — duty 估算被自适应步长放大
**症状**: near-deadzone PFD 的短脉冲被误判为大占空比
**触发 case**: pfd_deadzone_smoke
**修复**: duty 计算改为按时间加权（已在 simulate_evas.py 修复）

## F7 — Gold DUT 自身违反 EVAS 限制
**症状**: benchmark 接线完成后 gold DUT compile failed
**触发 case**: cmp_delay_smoke 早期版本
**修复**: gold DUT 也要遵守 EVAS 的 transition() 目标限制
```

验收标准：

1. 文件存在，涵盖至少 F1–F7 七类。
2. 每类都有"修复策略"，可直接写进 veriloga-skills 的规则里。

---

### 7.5 下一轮 benchmark 扩展

优先级：低到中

当前状态：

1. 2026-04-18 已完成第一轮 family 扩展，`bugfix` 与 `tb-generation` 均从 4 个增至 7 个任务。
2. 本轮新增 6 个任务均已通过 gold validation；统一 clean dual-suite 结果位于 `behavioral-veriloga-eval/results/gold-dual-suite-expansion-clean-2026-04-18/`。
3. 这轮暴露出的主要工程经验是：gold testbench 中的 PWL 激励要优先使用 Spectre 更稳的单行写法，否则 EVAS 通过后仍可能在 dual-suite 阶段因为 netlist read-in 失败而返工。
4. 2026-04-18 已完成第二轮 `end-to-end` 扩展，新增 `cmp_delay_smoke`、`cmp_strongarm_smoke`、`dwa_ptr_gen_no_overlap_smoke`，统一 dual-suite 结果位于 `behavioral-veriloga-eval/results/gold-dual-suite-benchmark-expansion/`。
5. 这轮新增 comparator case 暴露出的主要工程经验是：gold DUT 自身也要遵守 EVAS 的 `transition()` 目标限制，否则 benchmark 接线完成后仍会卡在 DUT compile，而不是卡在评分逻辑。
6. 2026-04-18 已完成一轮更贴近 PLL 实际写法的语义审计：`pll_timer_phase_update_suite` 与 EVAS 单测已覆盖 absolute timer armed-edge pull-in / push-out，以及 explicit-`t_next` DCO phase update；这说明下一轮 PLL benchmark 扩展可以把重点放到 lock/relock 与评分设计，而不是继续担心这条基础 timer 语义是否对齐。
7. 2026-04-19 已完成第三轮扩展，新增 `comparator_hysteresis_smoke` 与 `pfd_deadzone_smoke`；前者把 comparator 主线推进到状态记忆/双阈值行为，后者把 phase-detector 主线推进到 near-deadzone 短脉冲区。
8. 这轮新增 PFD case 还顺手暴露并修掉了 runner 的一个真实工程问题：行为检查原先按样本点比例估算 duty，会被 EVAS 的自适应时间步放大短脉冲；现已统一改为按时间加权，后续 `pfd_*` 扩展可以直接复用。
9. 2026-04-19 已完成一轮 P0 落地：`adpll_ratio_hop_smoke`、`pfd_reset_race_smoke`、`dco_gain_step_tb`、`sample_hold_aperture_tb` 均已建好 task 目录、gold 资产和结果表登记。
10. 其中 `adpll_ratio_hop_smoke`、`pfd_reset_race_smoke` 已完成 EVAS gold-suite 行为验证；`dco_gain_step_tb`、`sample_hold_aperture_tb` 已完成 EVAS gold-suite 编译验证。根据本轮 §12.3 的 no-bridge 约束，这 4 条的 dual-suite 仍留到后续 bridge 可用时再补。
11. 2026-04-19 已完成一轮 P1 落地：新增 `strongarm_reset_priority_bug`、`gray_counter_one_bit_change_smoke`、`multimod_divider_ratio_switch_smoke`、`segmented_dac_glitch_tb`、`comparator_offset_search_smoke`，并全部完成 EVAS 侧 gold-suite 验证。
12. 同一天还对既有 `xor_pd_smoke` 与 `clk_burst_gen_smoke` 做了 EVAS gold-suite 复验，并把两条任务的本地 metadata / parity 注释收口到与结果表一致的 `passed` 状态。

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

建议按下面顺序推进，这样最贴近“让 EVAS 更像 Virtuoso/Spectre”的主目标：

1. `P0` 语义对齐 probe 先行
   - periodic `timer(start, period)` 在 period shrink / expand 下的已 arm tick 行为
   - `cross()` / `above()` 在更粗时间步长下与 `transition()` 叠加时的重复触发 / 漏触发边界
   - PLL 真实风格 `next_t_toggle` / `t_edge` 更新路径，而不只是最小 DCO probe
   - comparator / phase-detector 例子里残留的历史 `transition()` workaround 清单回扫
2. `P1` PLL / clock benchmark 扩展
   - `cppll_freq_step_reacquire_smoke`
     用参考频率 step 验证失锁后重新拉回，评分看 relock window、UP/DN 脉冲方向与 `vctrl` 趋势，而不是逐点相位。
   - `adpll_ratio_hop_smoke`
     在运行中切换 divider / control word，验证 `t_next` 重新调度、输出频率换挡与重新稳定。
   - `pfd_deadzone_tb` 或 `pfd_overlap_tb`
     专门考察 UP/DN 脉冲宽度、重叠/死区与 zero phase difference 邻域行为。
   - `dco_gain_step_tb`
     测控制量阶跃后的瞬时频率变化与边沿间隔变化，作为 PLL authoring 的基础测量 bench。
3. `P1` comparator / sample / data-converter benchmark 扩展
   - `comparator_hysteresis_smoke`
     增加迟滞路径，覆盖双阈值状态与方向相关切换。
   - `strongarm_reset_priority_bug`
     用 bugfix 任务覆盖复位优先级、预充电恢复与输出锁存方向。
   - `sample_hold_aperture_tb`
     用受控边沿偏移检查采样孔径误差，而不只是简单 step response。
   - `segmented_dac_glitch_tb`
     用 thermometer/binary 边界切换验证码跳时的瞬态行为和单调性检查。
4. `P2` comms / source / sequencing benchmark 扩展
   - `nrz_prbs_jitter_tb`
     在现有 `nrz_prbs` 基础上加入 duty / jitter / burst gap 观测。
   - `serializer_frame_alignment_smoke`
     验证并串转换时的帧边界与 bit ordering。
   - `clk_burst_rearm_tb`
     检查 burst source 的 enable/disable 窗口与重新起振相位。

截至 2026-04-19，`comparator_hysteresis_smoke` 与 `pfd_deadzone_smoke` 已经落地并完成 dual validation。`cppll_freq_step_reacquire_smoke` 也已经在 `results/gold-dual-suite-cppll-initial-step-fix-v2/` 完成正式 EVAS+Spectre 双跑，并通过当前 `pll_task_aware` parity：`relock_time_delta_s = 8.04e-11`、`pre_lock_time_delta_s = 6.72e-11`、`late_fb_freq_rel_delta = 5.07e-4`、`late_vctrl_mean_delta_v = 1.81mV`。

不过，这条 case 仍保留一条值得以后继续分析的“波形级尾差异”记录：

1. benchmark 口径下这条已经 closed，不再是 parity blocker。
2. 但晚期 `lock` 脉冲仍不是逐个完全重合：
   - EVAS 第 5 个晚期 `lock` 上升沿约比 Spectre 早 `19.5ns`（约 1 个 late ref 周期）
   - EVAS 第 6 个晚期 `lock` 上升沿约比 Spectre 早 `39ns`（约 2 个 late ref 周期）
3. 当前判断这不是主 relock 行为仍有大误差，而是 `lock` 本身属于“离散 streak counter + phase tolerance”信号，对边界样本是否落在 `lock_tol` 内非常敏感。
4. 这条 residual mismatch 应归入“EVAS/Virtuoso waveform-perfect 对齐”的后续审计项，而不是 benchmark closure 阶段继续阻塞主线。

如果后面要继续分析，最推荐优先看：

1. `lock` 的定义是否应改成更稳定的内部状态口，而不是把它当逐脉冲对齐对象。
2. `t_fb_last` / `lock_streak` 是否应完全基于内部离散状态更新，避免对过渡后输出波形的隐式依赖。
3. 是否需要给 PLL 一类 case 单独区分“benchmark parity 已闭环”和“waveform-perfect tail alignment 未闭环”两种状态。

现在最推荐继续往下做的是 `adpll_ratio_hop_smoke`、`dco_gain_step_tb`、`sample_hold_aperture_tb`，以及把这次 `cppll_freq_step_reacquire_smoke` 的 residual mismatch 归档进 EVAS/Virtuoso mismatch 审计清单。它们一方面能继续扩大 benchmark 主表，另一方面也最容易直接暴露 EVAS 与 Spectre 在锁定恢复、动态周期变化、采样孔径和测量型 bench 表面的差异。

---

### P0 任务详细规格（Codex 可直接执行）

每个任务的接入流程：
1. 建 task 目录，写 prompt.md / meta.json / checks.yaml
2. 写 gold/dut.va 和 gold/tb_*.scs
3. 本地跑 `python runners/run_gold_suite.py` 验证 EVAS 通过
4. 如有 bridge 环境，跑 `scripts/run_with_bridge.sh` 验证 dual-suite
5. 在 `BENCHMARK_RESULT_TABLE.md` 登记新行
6. 运行 `sync_task_assignment.py`

---

#### P0-1: `adpll_ratio_hop_smoke`

目录：`tasks/end-to-end/voltage/adpll_ratio_hop_smoke/`

**meta.json**
```json
{
  "id": "adpll_ratio_hop_smoke",
  "family": "end-to-end",
  "category": "pll",
  "domain": "voltage",
  "difficulty": "hard",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "pll_task_aware"
}
```

**gold/dut.va 关键逻辑**
- 参数：`ref_period`（参考周期），`N_init`（初始分频比），`Kvco`（DCO增益）
- 状态：`integer div_count`，`real t_next`，`integer ratio`（当前分频比，可被外部控制）
- `ratio` 由一个 `electrical ratio_ctrl` 端口驱动（整数 round，范围 2–16）
- 每次 `t_next` 到达：div_count++，若 div_count >= ratio 则输出翻转、div_count 复位、`t_fb_edge` 更新、重调 PFD
- DCO 以 `vctrl` 调制周期：`half_period = 0.5 / (f0 + Kvco * V(vctrl))`，`t_next += half_period`
- lock detector：streak-based（连续 5 次 |phase_err| < lock_tol 则 `V(lock) = vdd`）

**gold/tb_adpll_ratio_hop.scs 关键结构**
- tran 仿真时长：`tstop = 500 * ref_period`（约 5µs for ref=10ns）
- PWL 控制：在 t=200*ref_period 时通过 `ratio_ctrl` 端口将 ratio 从 4 切换到 6
- 同时驱动一个 `vctrl` 初始 DC 偏置
- `save vout lock vctrl ratio_ctrl`

**checks.yaml 关键检查**
```yaml
checks:
  - name: pre_hop_freq_correct
    type: output_frequency
    signal: vout
    window: [0, 200e-9]          # 前 200 个 ref 周期
    expected_ratio: 4            # vout_freq / ref_freq 应约为 1/4
    tolerance: 0.05
  - name: post_hop_freq_correct
    type: output_frequency
    signal: vout
    window: [300e-9, 500e-9]     # hop 后稳定窗口
    expected_ratio: 6
    tolerance: 0.05
  - name: lock_asserted_pre_hop
    type: signal_high_fraction
    signal: lock
    window: [150e-9, 195e-9]
    min_fraction: 0.8
  - name: lock_reacquired_post_hop
    type: signal_high_fraction
    signal: lock
    window: [400e-9, 500e-9]
    min_fraction: 0.8
```

**在 simulate_evas.py 新增的检查函数**
新增 `check_adpll_ratio_hop()` 函数，读取 `vout` 列，
用 `rising_edges()` 分别在前后窗口计算频率，验证 ratio 变化。

---

#### P0-2: `dco_gain_step_tb`

目录：`tasks/tb-generation/voltage/dco_gain_step_tb/`

**meta.json**
```json
{
  "id": "dco_gain_step_tb",
  "family": "tb-generation",
  "category": "pll",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile"],
  "parity_policy": "not_required"
}
```

注意：tb-generation 家族不要求 `sim_correct`，parity=not_required。

**gold/dut.va 关键逻辑**
- DCO 模块：参数 `f0`（中心频率），`Kvco`（Hz/V 增益）
- 端口：`electrical vctrl, vout`
- 逻辑：`half_period = 0.5 / (f0 + Kvco * V(vctrl))`，通过 `@(timer(t_next))` 驱动输出翻转

**gold/tb_dco_gain_step.scs 关键结构**
- vctrl PWL：在 t=100ns 时从 0V 阶跃到 0.5V
- tran: tstop=300ns
- 在测量脚本里：
  - 提取 t < 100ns 的边沿间隔均值 → `T_pre`
  - 提取 t > 150ns 的边沿间隔均值 → `T_post`
  - 验证 `|1/T_pre - 1/T_post| / Kvco` 接近阶跃电压 0.5V

**prompt.md 要求描述**
让 LLM 生成一个 testbench，给定 DCO DUT，
施加 vctrl 阶跃，测量阶跃前后的边沿间隔，并从中计算 Kvco。

---

#### P0-3: `sample_hold_aperture_tb`

目录：`tasks/tb-generation/voltage/sample_hold_aperture_tb/`

**meta.json**
```json
{
  "id": "sample_hold_aperture_tb",
  "family": "tb-generation",
  "category": "data-converter",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile"],
  "parity_policy": "not_required"
}
```

**gold/dut.va 关键逻辑**
- S&H 模块：端口 `vin, clk, vout`
- `@(cross(V(clk) - 0.5*vdd, +1))`：采样 `V(vin)` 到 `held`
- `V(vout) <+ transition(held, 0, 1p, 1p)`

**gold/tb_sample_hold_aperture.scs 关键结构**
- vin：1MHz 正弦波（幅度 0.4V，偏置 0.5V）
- 三段 tran：分别用 clk 上升沿在 vin 峰值、过零、谷值附近采样
- 通过 PWL 调整 clk 相位偏移（offset），各差 250ps
- 验证：`vout_i - vout_j ≈ vin(t_clk_i) - vin(t_clk_j)`

**prompt.md 要求描述**
让 LLM 生成 testbench，通过精确控制 clk 相位偏移，
测量 S&H 的孔径误差特性。

---

#### P0-4: `pfd_reset_race_smoke`

目录：`tasks/end-to-end/voltage/pfd_reset_race_smoke/`

**meta.json**
```json
{
  "id": "pfd_reset_race_smoke",
  "family": "end-to-end",
  "category": "phase-detector",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"]
}
```

**gold/dut.va 关键逻辑**
- PFD：端口 `ref, fb, up, dn`
- `@(cross(V(ref)-0.5, +1))`：up_req = 1
- `@(cross(V(fb)-0.5, +1))`：dn_req = 1
- 当 up_req && dn_req：reset_pulse 生成，延迟 Treset 后将两者清零
- 输出 UP/DN 通过 transition() 驱动

**gold/tb_pfd_reset_race.scs 关键结构**
- case A：ref 比 fb 早 0.5ns（正常锁定邻域）
- case B：ref 比 fb 早 0.05ns（near-simultaneous，接近死区）
- case C：ref 和 fb 完全同时（delta=0）
- tran: tstop = 20 * ref_period
- `save up dn ref fb`

**checks.yaml 关键检查**
```yaml
checks:
  - name: up_pulse_width_case_a
    type: pulse_width
    signal: up
    window: [0, 50e-9]
    min_width: 0.4e-9
    max_width: 2e-9   # 最多一个 reset 延时
  - name: no_stuck_up_or_dn
    type: max_steady_high
    signals: [up, dn]
    max_duration: 5e-9    # UP/DN 不应持续高超过 5ns
  - name: reset_fires_when_both_high
    type: simultaneous_high_cleared
    signals: [up, dn]
    max_overlap: 3e-9   # up 和 dn 同时高的时间应 < reset delay
```

**验收标准：**

1. P0 中至少完成 P0-1 和 P0-4（end-to-end 任务），每个都通过 EVAS + 本地 dual-suite 验证。
2. P0-2 和 P0-3（tb-generation）至少完成 gold 资产构建和 EVAS 编译验证。
3. 全部新增任务在结果表中登记完毕。

> **当前状态（2026-04-19）：P0 全部完成 EVAS 侧闭环；dual-suite 等 bridge 可用后补。**

---

### P1 任务详细规格（Codex 可直接执行）

---

#### P1-1: `strongarm_reset_priority_bug`

目录：`tasks/bugfix/voltage/strongarm_reset_priority_bug/`

**meta.json**
```json
{
  "id": "strongarm_reset_priority_bug",
  "family": "bugfix",
  "category": "comparator",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "default"
}
```

**场景描述**
Buggy DUT：StrongArm 比较器在 `rst=1` 时没有优先复位输出，clock 仍能驱动锁存翻转。
Fixed DUT：`rst=1` 无条件将 `outp`、`outn` 保持低，不受时钟影响。

**gold/dut_buggy.va 关键逻辑**
```verilog
// 缺陷：没有 rst 优先判断
@(cross(V(clk) - 0.5, +1)) begin
  if (V(inp) > V(inn)) out_p_val = vdd; else out_p_val = 0.0;
end
V(outp) <+ transition(out_p_val, 0, tr, tf);
```

**gold/dut.va（修复版）关键逻辑**
```verilog
@(cross(V(clk) - 0.5, +1)) begin
  if (V(rst) > 0.5) begin
    out_p_val = 0.0; out_n_val = 0.0;  // rst 优先
  end else begin
    if (V(inp) > V(inn)) begin
      out_p_val = vdd; out_n_val = 0.0;
    end else begin
      out_p_val = 0.0; out_n_val = vdd;
    end
  end
end
```

**gold/tb_strongarm_reset.scs 关键结构**
- 在 clk 上升沿前后，通过 PWL 驱动 rst=1，验证输出被强制低
- 随后撤 rst，验证正常比较恢复

**checks.yaml 关键检查**
```yaml
checks:
  - name: reset_overrides_output
    type: signal_low_when
    signal: outp
    condition_signal: rst
    condition_threshold: 0.5
    tolerance: 0.1
  - name: correct_compare_without_rst
    type: differential_output_correct
    inp_signal: inp
    inn_signal: inn
    outp_signal: outp
    outn_signal: outn
    window: [last_half]
```

**prompt.md 要求**
给出 buggy DUT 代码，要求 LLM 找到并修复复位优先级 bug。

---

#### P1-2: `gray_counter_one_bit_change_smoke`

目录：`tasks/end-to-end/voltage/gray_counter_one_bit_change_smoke/`

**meta.json**
```json
{
  "id": "gray_counter_one_bit_change_smoke",
  "family": "end-to-end",
  "category": "digital-logic",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "default"
}
```

**Gold DUT 关键逻辑**
- 4 位 Gray 码计数器，端口：`clk, rst, g0, g1, g2, g3`
- 每个 clk 上升沿计数加 1，输出 Gray 编码
- 关键约束：相邻两拍输出只有 1 位变化
- 用 integer `bin_count`（0–15），`gray = bin ^ (bin >> 1)` 计算编码

**checks.yaml 关键检查**
```yaml
checks:
  - name: one_bit_change_per_cycle
    type: hamming_distance_per_step
    bus_signals: [g0, g1, g2, g3]
    max_hamming: 1
    window: [after_reset]
  - name: full_cycle_16_states
    type: unique_codes_count
    bus_signals: [g0, g1, g2, g3]
    expected_count: 16
```

---

#### P1-3: `multimod_divider_ratio_switch_smoke`

目录：`tasks/end-to-end/voltage/multimod_divider_ratio_switch_smoke/`

**meta.json**
```json
{
  "id": "multimod_divider_ratio_switch_smoke",
  "family": "end-to-end",
  "category": "pll",
  "domain": "voltage",
  "difficulty": "hard",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "pll_task_aware"
}
```

**Gold DUT 关键逻辑**
- 双模分频器（÷N / ÷N+1），由外部 `modulus_ctrl` 信号控制
- `integer div_cnt`，每次到达 N 或 N+1 时输出翻转、计数器清零
- `ratio_ctrl` 端口变化时立即生效（不等当前周期结束）

**Gold TB 关键结构**
- 时钟输入 1GHz，初始 N=4
- t=100ns 切换到 N=5
- t=200ns 切回 N=4
- 验证每段输出频率（250MHz → 200MHz → 250MHz）

**checks.yaml 关键检查**
```yaml
checks:
  - name: div4_before_switch
    type: output_frequency
    signal: div_out
    window: [10e-9, 90e-9]
    expected_hz: 250e6
    tolerance: 0.03
  - name: div5_after_first_switch
    type: output_frequency
    signal: div_out
    window: [120e-9, 190e-9]
    expected_hz: 200e6
    tolerance: 0.03
  - name: div4_after_second_switch
    type: output_frequency
    signal: div_out
    window: [220e-9, 300e-9]
    expected_hz: 250e6
    tolerance: 0.03
```

---

#### P1-4: `segmented_dac_glitch_tb`

目录：`tasks/tb-generation/voltage/segmented_dac_glitch_tb/`

**meta.json**
```json
{
  "id": "segmented_dac_glitch_tb",
  "family": "tb-generation",
  "category": "data-converter",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile"],
  "parity_policy": "not_required"
}
```

**Gold DUT 关键逻辑**
- 4 位分段 DAC：高 2 位 thermometer 编码（3 个 unit），低 2 位 binary 编码
- 输出 = therm_weight × therm_count + binary_weight × binary_code
- 在码字跨越 thermometer 边界时（例如 0111→1000，即 7→8）可能产生毛刺

**Gold TB 关键结构**
- 扫描所有 16 个码字，重点观察 thermometer 边界跳变点（3→4、7→8、11→12）
- 记录每次跳变时的输出峰峰值，检查是否单调
- `save vout code`

**prompt.md 要求**
给定上述分段 DAC DUT，生成测试台，检测 thermometer 边界处的毛刺和单调性违例。

---

#### P1-5: `xor_pd_smoke`

目录：`tasks/end-to-end/voltage/xor_pd_smoke/`

**meta.json**
```json
{
  "id": "xor_pd_smoke",
  "family": "end-to-end",
  "category": "phase-detector",
  "domain": "voltage",
  "difficulty": "easy",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "default"
}
```

**Gold DUT 关键逻辑**
- XOR 相位检测器：端口 `ref, fb, pd_out`
- 当 ref 和 fb 相位差为 0 时，duty=50%；相位超前/滞后时 duty 增大/减小
- `V(pd_out) <+ transition(xor_val ? vdd : 0, 0, 1p, 1p)`
- `xor_val` 用 `(ref_state ^ fb_state)` 实现，状态由 cross() 驱动

**checks.yaml 关键检查**
```yaml
checks:
  - name: zero_phase_duty_50pct
    type: duty_cycle
    signal: pd_out
    phase_condition: zero_phase   # ref 与 fb 同频同相
    expected_duty: 0.5
    tolerance: 0.05
  - name: lead_phase_duty_gt_50
    type: duty_cycle
    signal: pd_out
    phase_condition: ref_leads_by_quarter
    min_duty: 0.7
  - name: lag_phase_duty_lt_50
    type: duty_cycle
    signal: pd_out
    phase_condition: ref_lags_by_quarter
    max_duty: 0.3
```

---

#### P1-6: `comparator_offset_search_smoke`

目录：`tasks/end-to-end/voltage/comparator_offset_search_smoke/`

**meta.json**
```json
{
  "id": "comparator_offset_search_smoke",
  "family": "end-to-end",
  "category": "comparator",
  "domain": "voltage",
  "difficulty": "medium",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "default"
}
```

**Gold DUT 关键逻辑**
- 带静态偏置的比较器：内置 `parameter real vos = 5m`（5mV offset）
- 翻转点在 `V(inp) - V(inn) = vos` 而不是 0
- `out_val = (V(inp) - V(inn) > vos) ? vdd : 0`

**Gold TB 关键结构**
- 保持 inn=0.5V，扫描 inp 从 0.45V 到 0.55V（PWL 或参数扫描）
- 记录输出翻转点，提取 vos
- `save outp inn inp`

**checks.yaml 关键检查**
```yaml
checks:
  - name: switching_point_at_offset
    type: crossing_voltage
    sweep_signal: inp
    output_signal: outp
    expected_crossing: 0.505   # inn(0.5) + vos(5m)
    tolerance: 0.003
  - name: output_low_below_offset
    type: signal_low_when
    signal: outp
    condition: inp_lt_inn_plus_vos
  - name: output_high_above_offset
    type: signal_high_when
    signal: outp
    condition: inp_gt_inn_plus_vos
```

---

#### P1-7: `clk_burst_gen_smoke`

目录：`tasks/end-to-end/voltage/clk_burst_gen_smoke/`（从 examples 升格）

**meta.json**
```json
{
  "id": "clk_burst_gen_smoke",
  "family": "end-to-end",
  "category": "calibration-source",
  "domain": "voltage",
  "difficulty": "easy",
  "expected_backend": "evas",
  "scoring": ["dut_compile", "tb_compile", "sim_correct"],
  "parity_policy": "default"
}
```

**说明**
该任务对应 `examples/clk_burst_gen/` 已有示例，目标是将其升格为正式 benchmark task：
- 直接从 examples 目录拷贝 gold DUT 和 validate 脚本
- 调整 checks.yaml 格式与 simulate_evas.py 的 `evaluate_behavior()` 对齐
- 在结果表登记

**checks.yaml 关键检查**
```yaml
checks:
  - name: burst_active_pulses
    type: rising_edges_count
    signal: clk_burst
    window: [burst_on_period]
    min_count: 4
    max_count: 6
  - name: idle_no_pulses
    type: rising_edges_count
    signal: clk_burst
    window: [burst_off_period]
    expected_count: 0
```

---

**P1 验收标准：**

1. T15–T21 中每个 task 都通过 EVAS 侧 gold-suite 验证（status=PASS）。
2. bugfix 类任务（T15）的 dut_buggy.va 和修复版 dut.va 都包含在 gold/ 目录中。
3. end-to-end 类任务（T16–T17、T20–T21）在结果表中 `verification_status=passed`。
4. tb-generation 类任务（T18）只需 dut_compile + tb_compile 通过。
5. 全部新增任务在结果表登记，运行 `sync_task_assignment.py --check` 无报错。

---

## 7.6 候选 probe / benchmark 清单

这节单独维护“下一轮可以继续增加哪些测试”的候选池，避免想法散落在聊天记录里。

管理原则：

1. `probe cases`
   优先用于 EVAS / Virtuoso / Spectre 双跑，目标是主动暴露潜在语义差异，不要求一开始就进 benchmark 主表。
2. `benchmark candidates`
   从 probe 中筛出判据清楚、结果稳定、可复现成本低的例子，再沉淀成正式 benchmark。
3. `engine micro-tests`
   更小、更偏 Verilog-A 语义或事件调度边界的专项测试，优先考虑直接进入 `EVAS/tests`，不强求包装成 benchmark 任务。

筛选标准：

1. 行为代表性强，能覆盖一类真实建模或仿真语义点。
2. EVAS 与 Spectre 都能稳定复现，或者至少值得通过双跑确认差异。
3. 通过 / 失败判据清楚，不依赖大量人工解释。
4. 一旦失配，能够较明确地指向 simulator core、benchmark 资产或测量脚本中的某一类问题。

### A. P0 候选

这些项最适合作为下一轮优先落地对象：

1. `adpll_ratio_hop_smoke`
   运行中切换 divider / ratio，验证 `timer + cross + divider state` 联动、`t_next` 重排和重新锁定。
2. `dco_gain_step_tb`
   控制量或增益阶跃后的频率响应测量，重点看瞬时边沿间隔变化和测量型 bench 表面。
3. `sample_hold_aperture_tb`
   通过受控时钟偏移检查采样孔径误差，重点看边沿采样时刻与 Spectre 的一致性。
4. `pfd_reset_race_smoke`
   REF / FB 几乎同时到达时的 UP / DN / reset 竞争，重点看事件顺序和短脉冲边界。
5. `clk_burst_gen_smoke`
   把现有 example 收成正式闭环任务，重点看 burst 起止边界和 idle-to-active 切换。
6. `xor_pd_smoke`
   把现有 XOR 相位检测任务补齐闭环，重点看 duty 映射和相位差线性区。
7. `digital_basics_smoke`
   把多模块数字基础任务补齐闭环，作为低成本 sanity probe，适合快速回归 EVAS 事件语义。

### B. 电路结构类 probe / benchmark candidates

PLL / clock：

1. `cppll_ref_glitch_reject_smoke`
   在参考时钟中插入 glitch，检查闭环抗扰和假触发边界。
2. `cppll_large_step_unlock_relock_smoke`
   比当前 reacquire 更大的频率步进，检查 unlock / relock 行为和 late lock 稳定性。
3. `cppll_startup_seed_smoke`
   扫描不同 `vctrl`、相位或分频初始种子，检查 `initial_step` 与初值敏感性。
4. `adpll_jitter_tolerance_smoke`
   对参考时钟引入抖动，检查 lock 判据和 phase error 稳定性。
5. `multimod_divider_ratio_switch_smoke`
   动态切换 modulus 或 ratio，检查计数器状态迁移与输出换挡行为。

Phase detector：

1. `bbpd_data_edge_alignment_smoke`
   Alexander BBPD 的 near-edge 判定，检查 early / late 边界。
2. `pfd_missing_pulse_recovery_smoke`
   漏脉冲后的恢复行为，检查状态机复位与脉冲重建。
3. `xor_pd_duty_linearity_smoke`
   相位差扫描，检查输出 duty 与 phase difference 的线性关系。

Comparator：

1. `comparator_offset_search_smoke`
   用偏置扫描提取翻转点，检查 crossing 判定和阈值提取稳定性。
2. `comparator_meta_window_smoke`
   超小差分输入窗口，检查边界翻转和数值稳定性。
3. `comparator_pulse_swallow_smoke`
   检查窄脉冲是否被吞掉，适合看 transition 和事件抽样边界。

Sample / hold：

1. `sample_hold_droop_smoke`
   检查保持期间的缓慢泄漏和状态保持语义。
2. `sample_hold_multi_phase_smoke`
   双相 / 非重叠采样，检查多时钟事件排序。
3. `sample_hold_clock_feedthrough_smoke`
   时钟耦合到输出的瞬态，检查边沿扰动与 hold 期间输出行为。

Calibration / data-converter / digital：

1. `dwa_wraparound_smoke`
   指针回卷边界，检查数组索引和 rotation 正确性。
2. `dwa_pointer_seed_smoke`
   不同初始指针种子下的旋转一致性。
3. `bg_cal_convergence_smoke`
   校准环收敛，检查离散状态更新与统计型输出。
4. `serializer_load_shift_race_smoke`
   `LOAD` 与 `SHIFT` 竞争，检查边沿优先级。
5. `gray_counter_one_bit_change_smoke`
   Gray 码每拍只变 1 位，检查总线输出一致性。
6. `mux_select_glitch_smoke`
   选择信号切换瞬间的冒险和毛刺。
7. `dff_async_reset_release_smoke`
   异步复位释放与时钟边沿竞争。

### C. Measurement / tb-generation 候选

1. `period_jitter_measure_tb`
   提供统一周期 / 抖动测量骨架，适合 clock / PLL 类任务。
2. `duty_cycle_measure_tb`
   统一 duty 提取，适合 XOR / PFD / clock 类任务。
3. `lock_time_measure_tb`
   统一锁定 / 重锁定时间定义，减少每个任务单独写分析脚本。
4. `phase_error_hist_tb`
   统计 phase error 分布，不只看单个 lock 时刻。
5. `threshold_sweep_tb`
   比较器 / flash ADC 通用阈值扫描平台。
6. `burst_latency_tb`
   burst stimulus 和 gated clock 的延时量测。
7. `multi_window_save_tb`
   检查保存窗口、采样窗口和分析脚本之间的一致性。

### D. Verilog-A 语义专项 engine micro-tests

这类项不一定需要单独变成 benchmark task，但非常适合进入 `EVAS/tests` 作为回归保护。

1. `initial_step_preceding_assignments`
   `@(initial_step)` 是否能看到前序连续赋值。
2. `initial_step_for_loop_arrays`
   `initial_step` 中 `for` 循环和数组初始化的一致性。
3. `final_step_stats_flush`
   `@(final_step)` 的统计收口和输出刷新。
4. `cross_direction_boundary`
   `cross(expr, +1/-1)` 在阈值边界的行为。
5. `cross_same_step_multiple_hits`
   同一步内多次 crossing 是否重复触发。
6. `above_cross_mixed_trigger`
   `above()` 和 `cross()` 混用时是否双计数。
7. `timer_self_reschedule`
   `@(timer())` 自重排和下一次触发时刻的行为。
8. `timer_cross_same_time_order`
   `timer` 与 `cross` 同时命中时的顺序。
9. `transition_rearm_overlap`
   输出仍在 transition 期间再次更新的行为。
10. `transition_initial_value`
    `transition()` 在 `t=0` 的初值和首拍行为。
11. `array_1d_2d_contrib_readback`
    1D / 2D 数组贡献和读回一致性。
12. `genvar_bus_bit_order`
    总线位序和 `genvar` 展开顺序。
13. `loop_var_scope_update`
    循环变量生命周期和 update 语句语义。
14. `self_output_dependent_cross`
    事件条件依赖本模型输出时是否重复触发。
15. `abstime_phase_accumulation`
    基于 `$abstime` 的长时间相位累积和漂移。
16. `parameter_edge_values`
    参数取 `0`、负值、极小值时的保护逻辑。
17. `stateful_threshold_history`
    历史相关阈值模型的状态保持。
18. `multiple_writes_same_step`
    同一步多个分支写同一状态时的可见性和最终值。

### E. 建议优先升格为 benchmark 的候选

1. `adpll_ratio_hop_smoke`
2. `sample_hold_aperture_tb`
3. `pfd_reset_race_smoke`
4. `multimod_divider_ratio_switch_smoke`
5. `comparator_offset_search_smoke`
6. `gray_counter_one_bit_change_smoke`

### F. 建议先做 probe、不急着进 benchmark 的候选

1. `adpll_jitter_tolerance_smoke`
2. `comparator_meta_window_smoke`
3. `cppll_ref_glitch_reject_smoke`
4. `sample_hold_clock_feedthrough_smoke`
5. `period_jitter_measure_tb`
6. `phase_error_hist_tb`

后续维护建议：

1. 每次新增 probe 时，顺手记录“主打语义点”和“预期能抓到的问题类型”。
2. 每次有 probe 跑出稳定、判据清楚的结果后，再把它提名为 benchmark candidate。
3. 每次遇到明显更偏 simulator core 的差异，优先同步进 `EVAS / Spectre mismatch audit`，不要直接在 benchmark 资产里堆 workaround。

---

## 8. 反哺 skill / 生成系统的工作

### 8.1 把修复经验写回 prompt / skill

优先级：中

目标：
减少未来再生成相同错误。

具体动作：

**更新 `veriloga-skills/veriloga/SKILL.md`（或对应规则文件）**

新增或强化以下规则条目：

1. **端口 discipline 规则**
   > 纯电压域模块的所有端口必须声明为 `electrical`。
   > 禁止在纯电压域模块中使用 `ground`、`wreal`、`voltage` 类型端口。
   > 参考：`tasks/end-to-end/voltage/*/gold/dut.va` 中的端口声明风格。

2. **transition() 目标值规则**
   > `transition()` 的目标参数必须是离散赋值变量，不能是连续表达式。
   > 错误写法：`V(vout) <+ transition(vin > 0 ? vdd : 0, 0, tr, tf)`
   > 正确写法：先 `real target; if (V(vin) > 0) target = vdd; else target = 0;`，再 `V(vout) <+ transition(target, 0, tr, tf)`

3. **PRBS 初始化规则**
   > LFSR 类模块必须在 `@(initial_step)` 中将 seed 初始化为非零值（推荐 `7'h01` 或 `8'h01`）。
   > 全零初始状态会导致 PRBS 输出永远为 0。

4. **PLL 评分规则**
   > PLL / clock 类 end-to-end 任务不使用通用波形相似度评分。
   > 必须在 meta.json 中设置 `"parity_policy": "pll_task_aware"`。
   > 评分应检查：relock_time、UP/DN 脉冲方向、vctrl 趋势，而不是逐点波形误差。

5. **tb-generation 评分规则**
   > `tb-generation` 家族的任务 scoring 中**不包含** `sim_correct`。
   > meta.json 应为：`"scoring": ["dut_compile", "tb_compile"]`，`"parity_policy": "not_required"`。

**更新位置**：
- `veriloga-skills/veriloga/SKILL.md` — 强制规则 section
- 如果有 `references/pll/` 目录，同步更新 PLL 模板注释

验收标准：

1. 上述 5 条规则都已写入 skill 文件，有代码示例。
2. 规则文件中的示例风格与当前 gold DUT 一致。

---

### 8.2 建立新增任务 authoring checklist

优先级：中

目标：
让以后新加任务不再漏掉 gold、checks、Spectre 兼容项或文档登记。

具体动作：

**新建文件 `behavioral-veriloga-eval/docs/TASK_AUTHORING_CHECKLIST.md`**

内容结构（可在每次新增任务时直接 copy 并逐项勾选）：

```markdown
# Task Authoring Checklist

## 任务 ID: ___________

### 1. 目录结构
- [ ] `tasks/<family>/voltage/<id>/prompt.md` 存在
- [ ] `tasks/<family>/voltage/<id>/meta.json` 存在，通过 schema 验证
- [ ] `tasks/<family>/voltage/<id>/checks.yaml` 存在

### 2. meta.json 字段
- [ ] `id` 与目录名一致
- [ ] `family` 在 [end-to-end, spec-to-va, bugfix, tb-generation] 之一
- [ ] `domain` = "voltage"
- [ ] `expected_backend` = "evas"
- [ ] `scoring` 字段正确（tb-generation 不含 sim_correct）
- [ ] `parity_policy` 字段正确（PLL 类用 pll_task_aware，tb-generation 用 not_required）

### 3. Gold 资产
- [ ] `gold/dut.va` 存在
- [ ] `gold/tb_*.scs` 存在
- [ ] `dut.va` 中所有端口为 `electrical`（纯电压域）
- [ ] `transition()` 目标参数为离散变量（不是条件表达式）
- [ ] `save` 语句不含旧式限定符（:2e/:3f/:6f/:d 等）
- [ ] `ahdl_include` 使用裸文件名（不含绝对路径）

### 4. EVAS 验证
- [ ] 本地运行 `python runners/run_gold_suite.py` 通过（returncode=0，tran.csv 存在）
- [ ] `simulate_evas.py` 对该任务的 checks 全部 pass

### 5. Dual validation（如适用）
- [ ] 已通过 `scripts/run_with_bridge.sh` 运行 dual-suite
- [ ] EVAS 与 Spectre 的 parity 符合 parity_policy 标准
- [ ] 结果保存到 `results/<run_name>/`
- [ ] `MANIFEST.md` 已生成

### 6. 结果登记
- [ ] 在 `coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md` 新增一行
- [ ] 运行 `python runners/sync_task_assignment.py` 无报错
- [ ] `WORK_TODO.md` 的 7.5 当前状态节已更新
```

验收标准：

1. 文件存在，checklist 可直接使用（不需要修改结构）。
2. 至少用 P0-1 任务走一遍 checklist 验证流程合理。

---

## 9. 剩余 open 项（按优先级）

### 当前仍 open

截至 2026-04-19，本阶段 open 项已清零。后续进入常规增量维护（新任务扩展 + 回归守护）。

**已知小问题（不阻塞，维护时顺手修）**

- (Fx1) ~~`xor_pd_smoke` gold DUT 文件名为 `xor_phase_detector.va`（无 `_ref` 后缀），与其余任务命名风格不一致~~ → 已于 2026-04-19 修复为 `xor_phase_detector_ref.va`，并同步 TB 的 `ahdl_include`。
- (Fx2) ~~`segmented_dac_glitch_tb` 仿真步数约 412k（~3.7s CPU）~~ → 已于 2026-04-19 将 gold TB `maxstep` 从 `20p` 放宽到 `100p`，本地 EVAS 复验通过。
- (Fx3) ~~`digital_basics_smoke/meta.json` 写为 raw/pending 但结果表已 dual-validated（2026-04-17）~~ → 已于 2026-04-19 直接修复。
- (Fx4) ~~P1 批次 5 个 meta.json 格式稀疏~~ → 已于 2026-04-19 补齐 `task_name / must_include / artifacts / tier / verification_status / evidence` 等字段。
- (Fx5) ~~P0 批次 `adpll_ratio_hop_smoke` 和 `pfd_reset_race_smoke` 的 meta.json 同时包含 `id` 与 `task_id`（冗余）~~ → 已于 2026-04-19 删除冗余 `task_id` 字段，统一用 `id`。
- (Fx6) ~~`xor_pd_smoke/meta.json` 缺 top-level `parity_policy` 字段~~ → 已于 2026-04-19 补 `"parity_policy": "default"`。

### 2026-04-19 已收口

| 项 | 产出 |
|----|------|
| `5.3` | `EVAS_SPECTRE_ALIGNMENT_AUDIT.md` 落地，含 cppll 尾部差异记录 |
| `6.2` | `runners/WARNING_TAXONOMY.md` 落地（L0–L3 四级） |
| `6.4` | CI 补入 result-path / 目录完整性 / meta schema 三类检查 |
| `6.5` | `gen_manifest.py` 落地，4 个 results 目录补 MANIFEST.md |
| `7.1` | `gen_weekly_summary.py` 落地，生成 `status/summary_2026-04-19.md` |
| `7.2` | `gen_paper_stats.py` 落地，生成 PAPER_STATS.md + paper_stats.json |
| `7.3` | `CASE_SHOWCASE.md` 落地（8 条覆盖全类型） |
| `7.4` | `FAILURE_TAXONOMY.md` 落地（F1–F7） |
| `8.1` | `veriloga-skills/veriloga/SKILL.md` 补入 5 条 benchmark authoring 规则 |
| `8.2` | `docs/TASK_AUTHORING_CHECKLIST.md` 落地（6 节 checklist）|
| `4.1` | `BENCHMARK_RESULT_TABLE.md` 中 seed 行 `pr_link` 已补齐到可追溯提交，历史 `[TODO]` 清零 |
| `5.5` | dual runner 已默认要求 wrapper 入口；`run_with_bridge.sh` 注入 `VAEVAS_BRIDGE_WRAPPER=1`，`run_gold_dual_suite.py` 直跑默认阻断并给出 remediation |
| P0-1 | `adpll_ratio_hop_smoke`：task + gold + EVAS 行为验证通过 |
| P0-2 | `dco_gain_step_tb`：task + gold + EVAS 编译验证通过 |
| P0-3 | `sample_hold_aperture_tb`：task + gold + EVAS 编译验证通过 |
| P0-4 | `pfd_reset_race_smoke`：task + gold + EVAS 行为验证通过 |
| P0-dual | `adpll_ratio_hop_smoke`、`pfd_reset_race_smoke`、`dco_gain_step_tb`、`sample_hold_aperture_tb` 已于 2026-04-19 完成 EVAS+Spectre dual-suite（`results/gold-dual-suite-p0-2026-04-19/`） |
| P1-1 | `strongarm_reset_priority_bug`：bugfix task + bug/fix gold + EVAS 行为验证通过 |
| P1-2 | `gray_counter_one_bit_change_smoke`：task + gold + EVAS 行为验证通过 |
| P1-3 | `multimod_divider_ratio_switch_smoke`：task + gold + EVAS 行为验证通过 |
| P1-4 | `segmented_dac_glitch_tb`：task + gold + EVAS 编译验证通过 |
| P1-5 | `xor_pd_smoke`：已有任务 EVAS gold-suite 复验通过，metadata 已收口到 passed |
| P1-6 | `comparator_offset_search_smoke`：task + gold + EVAS 行为验证通过 |
| P1-7 | `clk_burst_gen_smoke`：已有任务 EVAS gold-suite 复验通过，metadata 已收口到 passed |
| P2-1 | `dwa_wraparound_smoke`：task + gold + EVAS 行为验证通过 |
| P2-2 | `sample_hold_droop_smoke`：task + gold + EVAS 行为验证通过 |
| P2-3 | `bbpd_data_edge_alignment_smoke`：task + gold + EVAS 行为验证通过 |
| P2-4 | `nrz_prbs_jitter_tb`：task + gold + EVAS 编译验证通过 |
| P2-5 | `serializer_frame_alignment_smoke`：task + gold + EVAS 行为验证通过 |

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

治理层（文档/CI/脚本）已全部落地，P0/P1/P2 队列和 P0 dual-suite 均已收口；下一阶段重心是常规增量扩展与回归稳定性维护。

---

## 12. Codex 自主执行指南

本节专供 Codex（或其他 AI agent）在无人监督模式下参考，确保执行顺序正确、不破坏已有稳定面。

### 12.1 执行优先级

按下面顺序依次推进，每完成一项更新本节的状态标记：

```
[x] T1  5.3  校准并补充 EVAS_SPECTRE_ALIGNMENT_AUDIT.md（2026-04-19）
[x] T2  6.2  新建 WARNING_TAXONOMY.md（2026-04-19）
[x] T3  6.5  新建 gen_manifest.py，并为现有 4 个 results 目录补 MANIFEST.md（2026-04-19）
[x] T4  7.4  新建 FAILURE_TAXONOMY.md（2026-04-19）
[x] T5  8.2  新建 TASK_AUTHORING_CHECKLIST.md（2026-04-19）
[x] T6  7.3  新建 CASE_SHOWCASE.md（2026-04-19）
[x] T7  7.1  新建 gen_weekly_summary.py 脚本（2026-04-19）
[x] T8  7.2  新建 gen_paper_stats.py 脚本（2026-04-19）
[x] T9  6.4  新建 tests/test_meta_schema.py，更新 runner-smoke.yml（2026-04-19）
[x] T10 8.1  更新 veriloga-skills/veriloga/SKILL.md（2026-04-19）
[x] T11 7.5  实现 P0-1 adpll_ratio_hop_smoke（优先 end-to-end）（2026-04-19）
[x] T12 7.5  实现 P0-4 pfd_reset_race_smoke（2026-04-19）
[x] T13 7.5  实现 P0-2 dco_gain_step_tb（2026-04-19）
[x] T14 7.5  实现 P0-3 sample_hold_aperture_tb（2026-04-19）

--- P1 队列（已执行）---
[x] T15 7.5  实现 strongarm_reset_priority_bug（bugfix，comparator）（2026-04-19）
[x] T16 7.5  实现 gray_counter_one_bit_change_smoke（end-to-end，digital-logic）（2026-04-19）
[x] T17 7.5  实现 multimod_divider_ratio_switch_smoke（end-to-end，pll）（2026-04-19）
[x] T18 7.5  实现 segmented_dac_glitch_tb（tb-generation，data-converter）（2026-04-19）
[x] T19 7.5  实现 comparator_offset_search_smoke（end-to-end，comparator）（2026-04-19）
[x] T20 7.5  实现 xor_pd_smoke（end-to-end，phase-detector）（2026-04-19，复验收口）
[x] T21 7.5  实现 clk_burst_gen_smoke（end-to-end，calibration-source）（2026-04-19，复验收口）

--- 维护修复（建议顺手完成）---
[x] Fx1  修复 xor_pd_smoke gold DUT 文件名 → xor_phase_detector_ref.va，并同步 TB ahdl_include（2026-04-19）
[x] Fx2  segmented_dac_glitch_tb TB 里 maxstep 从 20ps 改为 100ps，缩短仿真时间（2026-04-19）
[x] Fx3  digital_basics_smoke/meta.json 更新为 tier=verified / verification_status=passed（2026-04-19，直接修复）
[x] Fx4  补全 P1 稀疏 meta.json（5 个任务：gray_counter_one_bit_change_smoke / multimod_divider_ratio_switch_smoke /
         comparator_offset_search_smoke / segmented_dac_glitch_tb / strongarm_reset_priority_bug）
         每个文件需补：task_name, must_include, must_not_include, inputs, artifacts,
         tier=verified, verification_status=passed, owner=team, created_at=2026-04-19, evidence（2026-04-19）
[x] Fx5  去掉 P0 任务 (adpll_ratio_hop_smoke / pfd_reset_race_smoke) meta.json 里的冗余 task_id 字段
         （schema 要求 id OR task_id 之一，两者并存无害但冗余）（2026-04-19）
[x] Fx6  xor_pd_smoke/meta.json 补 top-level parity_policy = "default"（当前只有 checks.parity_required，缺顶层字段）（2026-04-19）

--- P2 队列（已执行）---
[x] T22 7.5  digital_basics_smoke 已于 2026-04-05 建立并在 2026-04-17 完成 dual-suite 验证，meta.json 已由 Fx3 补全（2026-04-19）
[x] T23 7.5  实现 dwa_wraparound_smoke（end-to-end，data-converter；DWA 指针回卷边界）（2026-04-19）
[x] T24 7.5  实现 sample_hold_droop_smoke（end-to-end，sample-hold；保持期泄漏与状态保持）（2026-04-19）
[x] T25 7.5  实现 bbpd_data_edge_alignment_smoke（end-to-end，phase-detector；Alexander BBPD near-edge）（2026-04-19）
[x] T26 7.5  实现 nrz_prbs_jitter_tb（tb-generation，comms；在 nrz_prbs 基础上加 jitter/burst 观测）（2026-04-19）
[x] T27 7.5  实现 serializer_frame_alignment_smoke（end-to-end，digital-logic；帧边界与 bit ordering）（2026-04-19）
```

### 12.2 通用规则

1. **不破坏已有 gold 资产**
   任何对 `tasks/*/gold/` 下文件的修改都需要在本地重跑 `run_gold_suite.py` 确认无回退。

2. **不引入绝对路径**
   SCS 文件中的 `ahdl_include` 只用裸文件名。

3. **不在 benchmark 资产里堆 workaround**
   如果发现 EVAS 行为与 Spectre 不一致，优先记录进 `EVAS_SPECTRE_ALIGNMENT_AUDIT.md` 的 C 或 D 节，不要修改 gold DUT 绕过。

4. **新建脚本先写，再验证**
   每个 `runners/gen_*.py` 脚本完成后，在本地用 `python runners/gen_*.py --help` 和至少一次真实调用验证能跑通。

5. **每完成一个 T 项，更新 §9 剩余 open 项的状态**
   把对应行从 `未完成` 改为 `已完成（日期）`。

6. **每完成一个 benchmark task（T11–T14），运行以下验证序列**：
   ```bash
   PYTHONPATH=../EVAS python3 runners/simulate_evas.py tasks/end-to-end/voltage/<id>/ \
     gold/dut.va gold/tb_*.scs
   # 确认 status=PASS
   python3 ../coordination/scripts/sync_task_assignment.py --check
   # 确认无错误
   ```

### 12.3 已知需要跳过的操作

- **不要直跑 `python runners/run_gold_dual_suite.py`**（默认会被阻断；请用 `scripts/run_with_bridge.sh`，或显式 `--allow-direct-run` 仅用于调试）
- **不要修改任何已有 `gold/` 资产的逻辑行为**（已经过 dual-suite 验证，不能随意改）
- **不要跑 `pytest tests/test_run_gold_dual_suite.py`**（需要完整 bridge 依赖）

### 12.4 验证环境快速检查

执行任务前先确认环境：
```bash
cd /path/to/behavioral-veriloga-eval
PYTHONPATH=../EVAS python3 -c "import evas; print(evas.__version__)"   # 应有输出，不报错
python3 -m pytest tests/test_save_statements.py tests/test_pwl_statements.py -q
# 应全部 pass
python3 ../coordination/scripts/sync_task_assignment.py --check      # 应无错误
```

### 12.5 文件路径速查

| 目标 | 路径 |
|------|------|
| 结果表 | `../coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md` |
| Task schema | `schemas/task.schema.json` |
| Runner smoke CI | `.github/workflows/runner-smoke.yml` |
| EVAS 对齐审计 | `../coordination/docs/project/EVAS_SPECTRE_ALIGNMENT_AUDIT.md` |
| Warning 规则 | `runners/WARNING_TAXONOMY.md` |
| Manifest 脚本 | `runners/gen_manifest.py` |
| Paper stats 脚本 | `runners/gen_paper_stats.py` |
| Weekly summary 脚本 | `runners/gen_weekly_summary.py` |
| Failure taxonomy | `../coordination/docs/project/FAILURE_TAXONOMY.md` |
| Case showcase | `../coordination/docs/benchmark/CASE_SHOWCASE.md` |
| Authoring checklist | `docs/TASK_AUTHORING_CHECKLIST.md` |
| Skill 规则文件 | `../veriloga-skills/veriloga/SKILL.md` |
