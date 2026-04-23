# Table 2 低 Pass@1 根因分析

## 问题概述

| Mode | Pass@1 | 主要失败类型 |
|------|--------|-------------|
| generic-retry (裸LLM) | 8.33% (2/24) | FAIL_DUT_COMPILE 14, FAIL_TB_COMPILE 4, FAIL_SIM_CORRECTNESS 3 |
| evas-guided-repair | 29.7% (11/37) | FAIL_DUT_COMPILE 16, FAIL_TB_COMPILE 10 |

## 根因 1：LLM 混淆 Verilog-A 和 Spectre 实例化语法

**错误案例** (digital_basics_smoke):

| 正确 Spectre 语法 | LLM 生成的错误语法 |
|------------------|-------------------|
| `I_and (and_a and_b and_y) and_gate vdd=1.8` | `and_gate and0 (and_a and_b and_y) vdd=VDD` |
| 格式：`<实例名> (端口) <模块名> 参数` | 格式：`<模块名> <实例名> (端口) 参数` |

**Spectre 错误输出**:
```
ERROR (SFE-23): instance 'and_gate' referencing undefined model 'and_y'
ERROR (SFE-23): instance 'not_gate' referencing undefined model '0'
```

**原因**：LLM 把 Verilog-A 的模块实例化风格错误应用到了 Spectre TB。

---

## 根因 2：LLM 使用 Verilog 语法而非 Verilog-A

**错误案例** (clk_divider):

```verilog-a
// 错误：使用了 Verilog 的 reg 类型
reg clk_out_reg;
reg lock_reg;
reg first_period_done;
```

**Spectre 错误输出**:
```
ERROR (VACOMP-2259): "reg clk_out_reg;<<--? " syntax error
```

**原因**：Verilog-A 只有 `real` 和 `integer` 类型，没有 `reg`/`wire`。LLM 不懂这个区别。

---

## 根因 3：LLM 在 event block 内声明变量

**错误案例** (lfsr_smoke):

```verilog-a
@(cross(V(CLK) - vth, +1, ttol)) begin
    real bit30, bit20, bit0, new_bit;  // 错误：在 event block 内声明
    real temp;
    ...
end
```

**Spectre 错误输出**:
```
ERROR (VACOMP-1917): Encountered an embedded declaration statement outside a labeled block.
```

**原因**：Verilog-A 要求变量声明在模块级别或 labeled block 内，不能在普通 event block 内声明。

---

## 根因 4：LLM 使用动态索引访问信号向量

**错误案例** (prbs7):

```verilog-a
for (i = 0; i < 7; i = i + 1) begin
    if ((lfsr_reg >> i) & 1)
        V(state_out[i]) <+ transition(...);  // 错误：i 不是 genvar/常量
    else
        V(state_out[i]) <+ transition(...);
end
```

**Spectre 错误输出**:
```
ERROR (VACOMP-1192): The index that accesses bits of analog signal vector `state_out' is not a constant.
ERROR (VACOMP-2143): Encountered the `transition' analog operator embedded in a conditionally-executed statement.
```

**原因**：Verilog-A 要求信号向量索引是 genvar 或常量表达式，且 `transition()` 不能在条件语句内使用。

---

## 根因 5：EVAS repair feedback 不完整

**clk_divider evas-guided-repair 的 feedback**:

```
EVAS status: FAIL_DUT_COMPILE
EVAS notes:
- generated_dut_staged_as=clk_divider_ref.va
- spectre_strict:undefined_module=clk_divider_ref;available_modules=clk_divider
```

**问题**：EVAS 只反馈了**模块名问题**，没有反馈 `reg clk_out_reg` 的语法错误！

LLM 收到 repair prompt 后只修复了模块名，但没有修复 `reg` 类型错误。

---

## 根因 6：repair skill 规则不够明确

**evas-guided-repair 的 repair skill 包含**:
- "Use voltage-domain Verilog-A only: V() <+, transition, cross..."
- "Do not use I(), ddt, idt, idtmod, laplace_*"

**缺失的规则**:
- ❌ "Use `real` or `integer` for internal variables, never `reg`/`wire`"
- ❌ "Declare variables at module scope, not inside event blocks"
- ❌ "Signal vector indices must be genvar or constant expressions"
- ❌ "transition() must be unconditional in the analog block"

---

## 解决方案（已实施）

### 修复 1：Spectre scoring 添加语法预检

**问题**：`score_spectre_generated.py` 缺少 `spectre_strict_preflight` 调用，导致 Spectre 编译失败时没有结构化 feedback。

**修复**：在 `score_one_task` 的 `_stage_case` 之后添加语法预检：

```python
# score_spectre_generated.py
from score import spectre_strict_preflight  # 新增导入

# 在 _stage_case 之后，run_spectre_case 之前
strict_status, strict_scores, strict_notes = spectre_strict_preflight(
    family=family,
    required_axes=required_axes,
    staged_tb=staged_tb,
    staged_va_paths=include_paths,
)

if strict_status is not None:
    # 语法问题检测到 - 跳过 Spectre 运行，返回结构化失败
    # notes 包含: spectre_strict:digital_verilog_syntax=digital_reg_decl: reg keyword in clk_divider.va
    ...
```

**效果**：repair prompt 现在能收到结构化的语法错误 feedback（如 `digital_reg_decl: reg keyword`），LLM 可以针对性修复。

---

### 修复 2：repair skill 规则已存在

**检查**：`build_repair_prompt.py` 的 `_targeted_repair_skill` 函数已有完整规则（Rule 1-6）：
- Rule 1: `reg` → `integer`
- Rule 2: packed bit-select 禁止
- Rule 3: edge detection 用 `@(cross())`
- Rule 4: 声明必须在 module scope
- Rule 5: `transition()` 用法
- Rule 6: 初始化用 `@(initial_step)`

**问题**：规则存在但 Spectre scoring **从未触发**这些规则（因为没有调用 preflight）。

**修复 1 已解决此问题** - 现在 Spectre scoring 会检测语法问题并添加 notes，触发 repair skill 规则。

---

## 验证测试

```bash
python3 -c "
import sys
sys.path.insert(0, 'runners')
from score import _has_digital_verilog_syntax
from pathlib import Path

va_path = Path('generated-table2-generic-retry/kimi-k2.5/clk_divider/sample_0/clk_divider.va')
issues = _has_digital_verilog_syntax(va_path)
print('Issues:', issues)
# Output: ['digital_reg_decl: reg keyword']
"
```

---

## 下一步

1. **重新运行 Spectre scoring**：使用修复后的 `score_spectre_generated.py` 重新评分，验证 notes 包含语法问题
2. **重新运行 EVAS repair**：有了结构化 feedback，repair prompt 应能正确修复语法问题
3. **预期结果**：evas-guided-repair Pass@1 应显著提升（目标接近 100%）

- generic-retry Spectre: `results/model-spectre-eval-kimi-k2.5-table2-raw-generic-retry-dev24-2026-04-20`
- evas-guided-repair Spectre: `results/model-spectre-eval-kimi-k2.5-table2-evas-guided-repair-full86-2026-04-20`
- 生成的 VA/TB: `generated-table2-generic-retry/kimi-k2.5`, `generated-table2-evas-guided-repair/kimi-k2.5`
- repair prompts: 各任务的 `sample_0/repair_prompt.md`