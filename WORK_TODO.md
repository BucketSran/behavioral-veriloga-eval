# vaEvas 待完成工作清单

更新日期: 2026-04-18

---

## 当前状态

| 任务类型 | 总数 | 已验证 | 待验证 | 缺gold |
|----------|------|--------|--------|--------|
| end-to-end | 22 | 22 (双验证) | 0 | 0 |
| spec-to-va | 16 | 0 | 12 | 4 |
| bugfix | 4 | 0 | 2 | 2 |
| tb-generation | 4 | 待确认设计 | - | - |

**重要变更**: 所有任务现在都要求双验证(EVAS + Spectre)，commit `e44f198`。

---

## 1. 双验证任务详情

### 1.1 spec-to-va 已有gold（12个）- 待运行双验证

| 任务路径 | gold文件 | 行为检查函数 | EVAS结果 | Spectre结果 |
|----------|----------|--------------|----------|-------------|
| `adc-sar/sar_logic` | `gold/sar_logic.va`, `gold/tb_sar_logic_ref.scs` | `check_sar_logic` (待确认) | 无 | 无 |
| `adc-sar/sar_12bit` | `gold/sar_12bit.va`, `gold/tb_sar_12bit_ref.scs` | `check_sar_12bit` (待确认) | 无 | 无 |
| `adc-sar/d2b_4bit` | `gold/_va_d2b_4b.va`, `gold/tb_d2b_4bit_ref.scs` | `check_d2b_4bit` (待确认) | 无 | 无 |
| `adc-sar/pipeline_stage` | `gold/pipeline_stage.va`, `gold/tb_pipeline_stage_ref.scs` | `check_pipeline_stage` (待确认) | 无 | 无 |
| `dac/segmented_dac` | `gold/segmented_dac.va`, `gold/tb_segmented_dac_ref.scs` | `check_segmented_dac` (待确认) | 无 | 无 |
| `dac/cdac_cal` | `gold/cdac_cal.va`, `gold/tb_cdac_cal_ref.scs` | `check_cdac_cal` (待确认) | 无 | 无 |
| `digital-logic/clk_divider` | `gold/clk_divider.va`, `gold/tb_clk_divider_ref.scs` | `check_clk_divider` ✅ | 有 | 无 |
| `digital-logic/prbs7` | `gold/prbs7.va`, `gold/tb_prbs7_ref.scs` | `check_prbs7` ✅ | 有 | 无 |
| `digital-logic/therm2bin` | `gold/therm2bin.va`, `gold/tb_therm2bin_ref.scs` | `check_therm2bin` ✅ | 有 | 无 |
| `pll-clock/bbpd` | `gold/bbpd.va`, `gold/tb_bbpd_ref.scs` | `check_bbpd` ✅ | 有 | 无 |
| `pll-clock/multimod_divider` | `gold/multimod_divider.va`, `gold/tb_multimod_divider_ref.scs` | `check_multimod_divider` ✅ | 有 | 无 |
| `sar_logic_10b` | `gold/sar_logic_10b.va`, `gold/tb_sar_logic_10b_ref.scs` | `check_sar_logic` ✅ | 无 | 无 |

**执行步骤**:
```bash
# 使用 run_gold_dual_suite.py 运行双验证
python3 runners/run_gold_dual_suite.py --tasks clk_divider,prbs7,therm2bin,bbpd,multimod_divider
```

### 1.2 spec-to-va 缺gold（4个）- 需先创建gold

| 任务路径 | 需创建内容 | prompt描述 |
|----------|------------|------------|
| `amplifier-filter/sc_integrator` | `gold/dut.va`, `gold/tb_ref.scs` | 开关电容积分器 |
| `calibration/bg_cal` | `gold/dut.va`, `gold/tb_ref.scs` | 后台校准 |
| `signal-source/multitone` | 待确认目录内容 | 多音信号源 |
| `signal-source/nrz_prbs` | 待确认目录内容 | NRZ PRBS信号源 |

### 1.3 bugfix 已有gold（2个）- 待运行双验证

| 任务路径 | gold文件 | 行为检查函数 | EVAS结果 | Spectre结果 |
|----------|----------|--------------|----------|-------------|
| `bad_bus_output_loop` | `gold/dut_fixed.va`, `gold/tb_bad_bus_output_loop.scs` | `check_bad_bus_output_loop` ✅ | 无 | 无 |
| `missing_transition_outputs` | `gold/dut_fixed.va`, `gold/tb_missing_transition_outputs.scs` | `check_missing_transition_outputs` ✅ | 无 | 无 |

### 1.4 bugfix 缺gold（2个）- 需先创建gold

| 任务路径 | 需创建内容 | prompt描述 |
|----------|------------|------------|
| `mixed_domain_cdac_bug` | `gold/dut_fixed.va`, `gold/tb.scs` | `I()<+`与电压域混用bug修复 |
| `spectre_port_discipline` | `gold/dut_fixed.va`, `gold/tb.scs` | inout端口共享问题修复 |

---

## 2. 需确认行为检查函数

检查 `runners/simulate_evas.py` 中 `CHECKS` dict 是否包含以下函数：

```python
# 需确认或创建的函数
"sar_logic":      check_sar_logic,      # 已存在？
"sar_12bit":      check_sar_12bit,      # 需创建？
"pipeline_stage": check_pipeline_stage,  # 需创建？
"segmented_dac":  check_segmented_dac,  # 需创建？
"cdac_cal":       check_cdac_cal,       # 需创建？
"multitone":      check_multitone,      # 需创建？
"nrz_prbs":       check_nrz_prbs,       # 需创建？
```

**检查方法**:
```bash
grep -n "def check_" runners/simulate_evas.py | grep -E "sar_logic|sar_12bit|pipeline|segmented|cdac_cal|multitone|nrz_prbs"
```

---

## 3. tb-generation任务（待确认）

| 任务路径 | 当前状态 | 设计意图 |
|----------|----------|----------|
| `clk_div_min_tb` | 有gold目录 | 需确认是否需要双验证 |
| `comparator_offset_tb` | 有gold目录 | 需确认是否需要双验证 |
| `dac_ramp_tb` | 有gold目录 | 需确认是否需要双验证 |
| `inl_dnl_probe` | 待确认目录 | 需确认设计 |

**问题**: tb-generation任务的gold是什么？是生成的tb文件还是验证tb的代码？

---

## 4. 分支管理

| 分支 | 状态 | 操作 |
|------|------|------|
| `feat/new-benchmark-seeds-2026-04-05` | 冗余（内容已合并） | 删除 |
| PR #2 (Arcadia-1) | OPEN | 等待合并或关闭 |

---

## 5. 执行优先级

### 高优先级 (立即执行)

1. **确认行为检查函数存在**
   - 检查 simulate_evas.py
   - 创建缺失的 check_* 函数

2. **运行shenbufan任务的Spectre验证**
   - `clk_divider`, `prbs7`, `therm2bin`, `bbpd`, `multimod_divider`
   - 这些已有EVAS结果，只需补Spectre

3. **运行bugfix任务双验证**
   - `bad_bus_output_loop`, `missing_transition_outputs`

### 中优先级

1. **创建4个缺失gold的任务**
   - `sc_integrator`, `bg_cal`, `mixed_domain_cdac_bug`, `spectre_port_discipline`

2. **运行其余spec-to-va双验证**
   - `sar_logic`, `sar_12bit`, `d2b_4bit`, `pipeline_stage`, `segmented_dac`, `cdac_cal`, `sar_logic_10b`

3. **确认tb-generation设计意图**

### 低优先级

1. 分支清理
2. 文档更新 (TASK_ASSIGNMENT.md, BENCHMARK_RESULT_TABLE.md)

---

## 6. 关键文件路径

```
项目根目录: /Users/bucketsran/Documents/TsingProject/vaEvas/behavioral-veriloga-eval

关键文件:
- runners/simulate_evas.py          # EVAS运行器 + 行为检查函数
- runners/run_gold_dual_suite.py    # 双验证运行器
- schemas/task.schema.json          # 任务schema
- schemas/result.schema.json        # 结果schema
- coordination/docs/benchmark/BENCHMARK_RESULT_TABLE.md  # 结果记录表
- coordination/docs/project/TASK_ASSIGNMENT.md          # 任务分工表

任务目录结构:
tasks/
├── end-to-end/voltage/{task}/
│   ├── prompt.md
│   ├── meta.json
│   ├── checks.yaml
│   └── gold/
│       ├── dut.va
│       └── tb_ref.scs
├── spec-to-va/voltage/{category}/{task}/
├── bugfix/voltage/{task}/
├── tb-generation/voltage/{task}/
```

---

## 7. 双验证运行命令

```bash
# 单任务EVAS验证
python3 runners/simulate_evas.py tasks/spec-to-va/voltage/digital-logic/clk_divider gold/clk_divider.va gold/tb_clk_divider_ref.scs

# 批量双验证 (需要virtuoso-bridge-lite配置)
python3 runners/run_gold_dual_suite.py --tasks clk_divider,prbs7,therm2bin

# 远程服务器目录
# /home/jinzhihong/aiProject/evas/behavioral-veriloga-eval/
```

---

## 8. 注意事项

1. **Spectre验证需要virtuoso-bridge-lite**
   - 确保SSH tunnel正常
   - 确保VB_CADENCE_CSHRC环境变量设置

2. **adpll_lock_smoke已知问题**
   - Spectre idtmod兼容性问题，已记录，不影响其他任务

3. **PR #2状态**
   - 当前OPEN，等待项目负责人决定是否合并到Arcadia-1

---

## 附录: 完整任务列表

### spec-to-va (16个)
```
adc-sar/sar_logic
adc-sar/sar_12bit
adc-sar/d2b_4bit
adc-sar/pipeline_stage
dac/segmented_dac
dac/cdac_cal
digital-logic/clk_divider
digital-logic/prbs7
digital-logic/therm2bin
pll-clock/bbpd
pll-clock/multimod_divider
amplifier-filter/sc_integrator (缺gold)
calibration/bg_cal (缺gold)
signal-source/multitone (待确认)
signal-source/nrz_prbs (待确认)
sar_logic_10b
```

### bugfix (4个)
```
bad_bus_output_loop (有gold)
missing_transition_outputs (有gold)
mixed_domain_cdac_bug (缺gold)
spectre_port_discipline (缺gold)
```

### tb-generation (4个)
```
clk_div_min_tb
comparator_offset_tb
dac_ramp_tb
inl_dnl_probe
```