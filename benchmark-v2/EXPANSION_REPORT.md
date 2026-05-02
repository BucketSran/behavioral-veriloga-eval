# benchmark-v2 扩展报告

> 日期: 2026-05-02
> 作者: shenbufan (shenbf_intern26)
> 来源: 从原始92个benchmark种子出发，通过六维度扰动扩展生成

---

## 1. 概述

### 1.1 扩展目标

原始92个benchmark任务已完成闭集completion package (92/92)，但其来源混合了teacher replay和模板修复，无法充分证明机制模板、RAG检索和EVAS闭环反馈的泛化能力。

benchmark-v2的目标是通过对原始seed施加可控扰动，构建**表面形式不同但底层行为本质相同**的新任务，检验模型是真正理解电路机制还是在死记task_id和信号名。

### 1.2 扰动维度定义

| 维度 | 名称 | 操作 | 度量目标 |
|------|------|------|----------|
| P1 | 命名扰动 | 改端口名/模块名，保留领域线索词 | 字符串记忆 |
| P2 | 语义别名 | 信号名替换为领域中性词 | 功能角色推理 |
| P3 | 关键字删除 | 删除所有领域专有名词，纯功能描述 | 机制推导（无索引依赖） |
| P4 | 负约束 | 明确列出禁止使用的实现方式 | 模板滥用检测 |
| P5 | 参数扰动 | 改位宽/分频比/VDD/阈值/时间参数 | 变量绑定能力 |
| P6 | 系统组合 | 多模块机制合并为单一DUT | 结构级跨模块理解 |

### 1.3 总体统计

| 指标 | 数量 |
|------|------|
| 扰动任务总数 | 11 |
| 覆盖源seed数 | 9 |
| 覆盖机制家族 | 7 (digital-logic, phase-detector, comparator, sample-hold, stimulus, data-converter, calibration) |
| P3及以上 | 8 |
| P6系统组合 | 1 |
| P4负约束 | 9 |
| 难度分布 | easy:1, medium:9, hard:1 |

---

## 2. 任务清单总览

| # | task_id | 源seed | 家族 | 扰动维度 | 级别 | 难度 | 状态 |
|---|---------|--------|------|----------|------|------|------|
| 1 | clk_divider_p2p3p4 | clk_div_smoke | digital-logic | P2+P3+P4 | P3 | medium | dual_validated |
| 2 | clk_divider_p4p5p6 | clk_div_smoke | digital-logic | P4+P5+P6 | P6 | hard | dual_validated |
| 3 | gray_counter_4b_p1p2 | gray_counter_4b_smoke | digital-logic | P1+P2 | P2 | easy | dual_validated |
| 4 | xor_pd_p2p3p4 | xor_pd_smoke | phase-detector | P2+P3+P4 | P3 | medium | dual_validated |
| 5 | dff_rst_p2p5 | dff_rst_smoke | digital-logic | P2+P5 | P2 | medium | dual_validated |
| 6 | comparator_p2p3p4 | comparator_smoke | comparator | P2+P3+P4 | P3 | medium | dual_validated |
| 7 | sample_hold_p2p3p4 | sample_hold_smoke | sample-hold | P2+P3+P4 | P3 | medium | dual_validated |
| 8 | lfsr_p2p3p4 | lfsr_smoke | digital-logic | P2+P3+P4 | P3 | medium | dual_validated |
| 9 | clk_burst_gen_p2p3p5 | clk_burst_gen_smoke | stimulus | P2+P3+P5 | P3 | medium | dual_validated |
| 10 | pfd_updn_p2p3p4 | pfd_updn_smoke | phase-detector | P2+P3+P4 | P3 | medium | dual_validated |
| 11 | flash_adc_3b_p2p3p4 | flash_adc_3b_smoke | data-converter | P2+P3+P4 | P3 | medium | dual_validated |

---

## 3. 各任务详情

### 3.1 clk_divider_p2p3p4 — 时钟分频器 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/clk_div_smoke`
- **新模块**: `event_divider`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| CLK_IN | cadence |
| RST_N | clear |
| CLK_OUT | toggled |

**P3 关键字删除**:

| 原关键词 | 替换为 |
|----------|--------|
| clock divider | periodic binary event → slower toggling output |
| divide-by-4 | every fourth rising transition completes one full cycle |
| 50% duty-cycle | high and low durations approximately equal |
| synchronous reset | control signal restores initial internal state |

**P4 负约束**:
- 不是Gray码状态机
- 不能用 `@(timer(...))` 或 `@(delay(...))` 延迟输出
- clear必须在cadence上升沿采样，不能异步直接作用于输出

**文件**: prompt.md, checks.yaml, meta.json, gold/event_divider.va, gold/tb_event_divider_ref.scs

---

### 3.2 clk_divider_p4p5p6 — 分频器+脉冲生成器 (P4+P5+P6)

- **源seed**: `tasks/end-to-end/voltage/clk_div_smoke`
- **新模块**: `event_divider_with_pulse`
- **难度**: hard

**P4 负约束**:
- 不是Gray码状态机
- 不是PWM调制器 — tick脉冲宽度固定
- 不跳周期 — 每个完整分频周期必须产生tick
- 不能用 `@(timer(...))` 或 `@(delay(...))` 实现tick

**P5 参数**:

| 参数 | 原值 | 新值 |
|------|------|------|
| 分频比 | ÷4 | ÷5 (奇数, 2高/3低) |
| VDD | 0.9V | 1.2V |
| vth | 0.45 | 0.6 |
| tedge | 100p | 80p |
| 时钟周期 | 10n (100MHz) | 8n (125MHz) |
| stop | 300n | 400n |

**P6 系统组合**: 单输出 → 双输出。新增 `tick` 端口：每完成一个分频周期输出一个脉冲（持续恰好一个cadence周期宽度）。分频器和脉冲生成器共享计数器状态。

**文件**: prompt.md, checks.yaml, meta.json, gold/event_divider_with_pulse.va, gold/tb_event_divider_with_pulse_ref.scs

---

### 3.3 gray_counter_4b_p1p2 — Gray码计数器 (P1+P2)

- **源seed**: `tasks/end-to-end/voltage/gray_counter_4b_smoke`
- **新模块**: `adjacent_code_counter`
- **难度**: easy

**P1 命名扰动**:

| 原端口 | 新端口 |
|--------|--------|
| g3,g2,g1,g0 | qb3,qb2,qb1,qb0 |
| rstb | reset_n |

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| clk | strobe |
| en | enable |
| vdd | supply_hi |
| vss | supply_lo |

原prompt泄露的Gray码转换公式 `gray = bin ^ (bin >> 1)` 已在扰动版中删除，改为纯行为描述"相邻状态恰好变1bit"。

**文件**: prompt.md, checks.yaml, meta.json, gold/adjacent_code_counter.va, gold/tb_adjacent_code_counter_ref.scs

---

### 3.4 xor_pd_p2p3p4 — XOR鉴相器 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/xor_pd_smoke`
- **新模块**: `edge_event_comparator`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| ref | sig_a |
| div | sig_b |
| pd_out | match_out |
| vdd | supply_hi |
| vss | supply_lo |

**P3 关键字删除**: 删除"XOR/Phase Detector/phase difference/PFD"，改为"比较两个事件输入到达的先后顺序，match_out在两输入电平不同时为高"

**P4 负约束**:
- 不是PFD — 不实现UP/DN脉冲逻辑和复位反馈
- 不是Bang-Bang PD — 不用时钟采样或触发器状态机
- 输出是单信号，不是分离的UP/DN

**文件**: prompt.md, checks.yaml, meta.json, gold/edge_event_comparator.va, gold/tb_edge_event_comparator_ref.scs

---

### 3.5 dff_rst_p2p5 — D触发器 (P2+P5)

- **源seed**: `tasks/end-to-end/voltage/dff_rst_smoke`
- **新模块**: `edge_triggered_latch`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| d | sample_in |
| clk | strobe |
| rst | force_low |
| q | state |
| qb | state_n |
| vdd | supply_hi |
| vss | supply_lo |

**P5 参数**:

| 参数 | 原值 | 新值 |
|------|------|------|
| tedge | 10p | 50p |
| VDD | 1.8V | 0.9V |
| 时钟周期 | 2ns | 5ns |
| stop | 20ns | 50ns |

**文件**: prompt.md, checks.yaml, meta.json, gold/edge_triggered_latch.va, gold/tb_edge_triggered_latch_ref.scs

---

### 3.6 comparator_p2p3p4 — 比较器 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/comparator_smoke`
- **新模块**: `differential_detector`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| VINP | sense_plus |
| VINN | sense_minus |
| OUT_P | decision |
| VDD | supply_hi |
| VSS | supply_lo |

**P3 关键字删除**: 删除"comparator/differential comparison/threshold crossing"，改为"判断两个模拟节点电位的相对大小并输出二值结果"

**P4 负约束**:
- 不是StrongArm latch
- 不是动态锁存比较器
- 不添加hysteresis
- 不用时钟采样

**文件**: prompt.md, checks.yaml, meta.json, gold/differential_detector.va, gold/tb_differential_detector_ref.scs

---

### 3.7 sample_hold_p2p3p4 — 采样保持 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/sample_hold_smoke`
- **新模块**: `track_and_freeze`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| in | analog_in |
| clk | sample_cmd |
| out | held_value |
| vdd | supply_hi |
| vss | supply_lo |

**P3 关键字删除**: 删除"Sample-and-Hold/S&H/sample/hold"，改为"在命令输入上升沿捕获模拟输入的瞬时值并将输出冻结在该值直到下一个命令沿"

**P4 负约束**:
- 不是continuous follower (buffer)
- 不是integrator 或带slewing的track-and-hold
- 不添加aperture delay 或 droop行为

**文件**: prompt.md, checks.yaml, meta.json, gold/track_and_freeze.va, gold/tb_track_and_freeze_ref.scs

---

### 3.8 lfsr_p2p3p4 — LFSR伪随机源 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/lfsr_smoke`
- **新模块**: `pseudo_random_source`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| clk | advance |
| rstb | init_n |
| dpn | prbs_out |
| en | run |
| vdd | supply_hi |
| vss | supply_lo |

**P3 关键字删除**: 删除"LFSR/Linear Feedback Shift Register/PRBS/taps/polynomial/m-sequence/maximal-length"，改为"一个反馈移位链，某些位置抽头异或后注入第一位，产生周期性遍历的二进制序列"

**P4 负约束**:
- 不是CRC生成器
- 不是Gold code生成器
- 不是m-sequence以外的伪随机序列
- 反馈位置必须可参数化，不能硬编码

**文件**: prompt.md, checks.yaml, meta.json, gold/pseudo_random_source.va, gold/tb_pseudo_random_source_ref.scs

---

### 3.9 clk_burst_gen_p2p3p5 — 时钟突发生成器 (P2+P3+P5)

- **源seed**: `tasks/end-to-end/voltage/clk_burst_gen_smoke`
- **新模块**: `gated_event_passer`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| CLK | event_in |
| RST_N | clear_n |
| CLK_OUT | burst_out |

**P3 关键字删除**: 删除"burst/clock burst/gated/pass-through"，改为"周期性窗口内透传前N个输入事件，窗口其余时间强制输出低"

**P5 参数**:

| 参数 | 原值 | 新值 |
|------|------|------|
| div | 8 | 6 |
| vdd | (default) | 1.2V |
| vth | (default) | 0.6 |
| 时钟周期 | 100n | 50n |
| stop | 3000n | 2000n |

**文件**: prompt.md, checks.yaml, meta.json, gold/gated_event_passer.va, gold/tb_gated_event_passer_ref.scs

---

### 3.10 pfd_updn_p2p3p4 — PFD鉴频鉴相器 (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/pfd_updn_smoke`
- **新模块**: `edge_arrival_comparator`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| ref | early_edge |
| div | late_edge |
| up | adv |
| dn | ret |
| vdd | supply_hi |
| vss | supply_lo |

**P3 关键字删除**: 删除"PFD/Phase-Frequency Detector/UP/DN/pump/charge"，改为"两路事件输入，先到者拉高对应输出，两者都高时立即清除"

**P4 负约束**:
- 不是XOR phase detector
- 不是Bang-Bang phase detector
- 不是SR锁存器
- 复位路径必须组合逻辑，不能用时钟同步
- 两个输出不可同时为高

**文件**: prompt.md, checks.yaml, meta.json, gold/edge_arrival_comparator.va, gold/tb_edge_arrival_comparator_ref.scs

---

### 3.11 flash_adc_3b_p2p3p4 — 3-bit Flash ADC (P2+P3+P4)

- **源seed**: `tasks/end-to-end/voltage/flash_adc_3b_smoke`
- **新模块**: `level_to_code_converter`
- **难度**: medium

**P2 语义别名**:

| 原端口 | 新端口 |
|--------|--------|
| vin | analog_level |
| clk | sample_strobe |
| dout2,dout1,dout0 | qb2,qb1,qb0 |
| vdd | supply_hi |
| vss | supply_lo |
| vrefp | ref_hi |
| vrefn | ref_lo |

**P3 关键字删除**: 删除"ADC/flash/quantizer/converter/bin/thermometer/binary encoding"，改为"将连续输入电压映射到3-bit离散编码，全量程等分为8段，在采样命令上升沿更新"

**P4 负约束**:
- 不是SAR架构
- 不是流水线架构
- 输出编码必须是二进制加权，不是thermometer编码
- 不使用比较器阵列或参考阶梯 — 这是行为级模型

**文件**: prompt.md, checks.yaml, meta.json, gold/level_to_code_converter.va, gold/tb_level_to_code_converter_ref.scs

---

## 4. 扰动覆盖矩阵

```
                    P1    P2    P3    P4    P5    P6
clk_divider_p2p3p4   -     ✓     ✓     ✓     -     -
clk_divider_p4p5p6   -     -     -     ✓     ✓     ✓
gray_counter_4b_p1p2  ✓     ✓     -     -     -     -
xor_pd_p2p3p4        -     ✓     ✓     ✓     -     -
dff_rst_p2p5         -     ✓     -     -     ✓     -
comparator_p2p3p4    -     ✓     ✓     ✓     -     -
sample_hold_p2p3p4   -     ✓     ✓     ✓     -     -
lfsr_p2p3p4          -     ✓     ✓     ✓     -     -
clk_burst_gen_p2p3p5 -     ✓     ✓     -     ✓     -
pfd_updn_p2p3p4      -     ✓     ✓     ✓     -     -
flash_adc_3b_p2p3p4  -     ✓     ✓     ✓     -     -
─────────────────────────────────────────────────────
覆盖次数             1    10     8     9     4     1
```

---

## 5. 家族分布

| 机制家族 | 任务数 | 任务列表 |
|----------|--------|----------|
| digital-logic | 5 | clk_divider_p2p3p4, clk_divider_p4p5p6, gray_counter_4b_p1p2, dff_rst_p2p5, lfsr_p2p3p4 |
| phase-detector | 2 | xor_pd_p2p3p4, pfd_updn_p2p3p4 |
| comparator | 1 | comparator_p2p3p4 |
| sample-hold | 1 | sample_hold_p2p3p4 |
| stimulus | 1 | clk_burst_gen_p2p3p5 |
| data-converter | 1 | flash_adc_3b_p2p3p4 |

---

## 6. 文件结构

每个扰动任务包含标准的5个文件：

```
benchmark-v2/tasks/<task_id>/
├── prompt.md                    # 扰动后的任务规格（不泄露gold实现）
├── gold/<new_module_name>.va    # 更名后的gold DUT
├── gold/tb_*_ref.scs            # 适配后的参考testbench
├── checks.yaml                  # 行为检查定义（含must_not_include负约束）
└── meta.json                    # 任务元数据（source_seed, perturbation_axes, status等）
```

---

## 7. 验证计划

### 7.1 EVAS 本地验证 ✅ (已完成 2026-05-02)

**结果: 11/11 PASS**

```bash
cd behavioral-veriloga-eval
python benchmark-v2/run_gold_v2.py
```

| task_id | dut_compile | tb_compile | sim_correct | result |
|---------|-------------|------------|-------------|--------|
| clk_burst_gen_p2p3p5 | PASS | PASS | PASS | clk_out_hi_frac=0.173 rising_edges=13 |
| clk_divider_p2p3p4 | PASS | PASS | PASS | edge_ratio=3.75 |
| clk_divider_p4p5p6 | PASS | PASS | PASS | edge_ratio=5.00 |
| comparator_p2p3p4 | PASS | PASS | PASS | output_mean_delta=0.482 |
| dff_rst_p2p5 | PASS | PASS | PASS | checks=10 q_mismatch=0 qb_mismatch=0 |
| flash_adc_3b_p2p3p4 | PASS | PASS | PASS | codes=8/8 reversals=0 |
| gray_counter_4b_p1p2 | PASS | PASS | PASS | all_gray_ok unique_codes=16 |
| lfsr_p2p3p4 | PASS | PASS | PASS | transitions=196 hi_frac=0.474 |
| pfd_updn_p2p3p4 | PASS | PASS | PASS | up_frac=0.150 dn_frac=0.000 up_pulses=15 |
| sample_hold_p2p3p4 | PASS | PASS | PASS | edges=50 hold_ok |
| xor_pd_p2p3p4 | PASS | PASS | PASS | duty=0.491 transitions=40 |

**集成改动**: 为了让 v2 任务的 check 函数正确运行，在 `runners/simulate_evas.py` 中做了以下改动:
- `_TASK_ALIAS_CANDIDATES` 新增 11 项 v2 任务的端口别名映射（扰动后的端口名 → 源 seed 端口名）
- `CHECKS` 字典新增 11 项 v2 task_id → 对应 check 函数
- 新增 `check_gray_counter_4b_v2()` 函数：使用时间基准稳定采样(5ns)替代索引偏移采样(8 samples)，解决 v2 测试平台下过渡期误采问题

### 7.2 Spectre 交叉验证 ✅ (已完成 2026-05-02)

通过在 `thu-sui`（跳板机）上直接运行 Spectre，使用本地许可服务器 (`5280@localhost`)。

**环境配置:**
- 目标: thu-sui (166.111.78.23)，直连模式（无跳板机）
- Bridge 隧道: 正常（端口 65263）
- Spectre 版本: SPECTRE211Hotfix_crack 21.1.0
- 许可: thu-sui 本地许可服务器 `5280@localhost`（独立于集群共享许可池）

**结果: 11/11 PASS**

| task_id | Spectre | 信号数 | 备注 |
|---------|---------|--------|------|
| clk_burst_gen_p2p3p5 | PASS | 4 | event_in, clear_n, burst_out |
| clk_divider_p2p3p4 | PASS | 3 | cadence_in, toggled |
| clk_divider_p4p5p6 | PASS | 4 | cadence, toggled, tick |
| comparator_p2p3p4 | PASS | 4 | sense_plus, sense_minus, decision |
| dff_rst_p2p5 | PASS | 6 | strobe, sample_in, force_low, state, state_n |
| flash_adc_3b_p2p3p4 | PASS | 6 | analog_level, sample_strobe, qb0-2 |
| gray_counter_4b_p1p2 | PASS | 7 | strobe, reset_n, qb0-3 |
| lfsr_p2p3p4 | PASS | 4 | advance, init_n, prbs_out |
| pfd_updn_p2p3p4 | PASS | 5 | early_edge, late_edge, adv, ret |
| sample_hold_p2p3p4 | PASS | 4 | analog_in, sample_cmd, held_value |
| xor_pd_p2p3p4 | PASS | 4 | sig_a, sig_b, match_out |

### 7.3 验收标准

每个任务需满足:
1. ✅ EVAS PASS (dut_compile + tb_compile + sim_correct) — **11/11 已通过**
2. ✅ Spectre PASS (交叉验证) — **11/11 已通过**
3. 状态提升: draft → evas_pass → spectre_pass → dual_validated

---

## 8. 后续工作

- [ ] **路线A补充**: clk_div_smoke 和 gray_counter_4b_smoke 各需补至 3 个扰动任务（目标: 每 seed 3 个）
- [x] **EVAS 验证**: 跑通全部 11 个任务 ✅ (2026-05-02, 11/11 PASS)
- [x] **Spectre 验证**: 在 thu-sui 本地许可下全部通过 ✅ (2026-05-02, 11/11 PASS)
- [ ] **路线B**: 外部架构转化 — 从公开 Verilog-A 资料找 1 个新机制转成 2 个任务
