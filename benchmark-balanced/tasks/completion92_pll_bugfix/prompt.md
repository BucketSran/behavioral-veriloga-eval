Fix a Verilog-A implementation for the core function below without changing its public behavior.
Return the corrected Verilog-A artifact requested by the benchmark.

Core function family: pll.
Balanced task-form completion derived from original task: `multimod_divider_ratio_switch_smoke`.

Spectre/Verilog-A compatibility requirements:
- Use voltage-domain electrical ports where applicable.
- Keep the public interface and saved observable behavior compatible with the evaluation harness.
- Prefer explicit `transition(...)` on driven voltage outputs.
- Avoid current contributions, `ddt()`, `idt()`, simulator control blocks, and non-Spectre syntax.

Source behavioral specification:

Write a pure voltage-domain Verilog-A dual-modulus divider.

Module name: `multimod_divider_ratio_switch_ref`.

Requirements:

1. Ports: `clk_in`, `ratio_ctrl`, `div_out`
2. `ratio_ctrl < 4.5V` means divide-by-4, otherwise divide-by-5
3. The target ratio is re-sampled on every input clock edge
4. Output should emit one pulse per completed divide interval
5. Use only EVAS-compatible voltage-domain constructs

Expected behavior:
- When ratio_ctrl changes, output frequency should change accordingly
- New ratio should be applied within few cycles
Ports:
- `clk_in`: input electrical
- `ratio_ctrl`: input electrical
- `div_out`: output electrical

## Output Contract (MANDATORY)

- Return exactly two fenced code blocks:
  - first block: Verilog-A DUT (` ```verilog-a ... ``` `)
  - second block: Spectre testbench (` ```spectre ... ``` `)
- The Spectre testbench must include the DUT with `ahdl_include "<module>.va"`.
- Use a single `tran` analysis and include the required `save` signals for checker evaluation.


## Public Evaluation Contract (Non-Gold)

This section states evaluator-facing constraints that must be visible to the generated artifact.
It does not prescribe the internal implementation or reveal a gold solution.

Final EVAS transient setting:

```spectre
tran tran stop=320n maxstep=20p errpreset=conservative
```

Required public waveform columns in `tran.csv`:

- `time`, `clk_in`, `div_out`

Use plain scalar save names for these observables; do not rely on instance-qualified or aliased save names.

Timing/checking-window contract:

- Clock-like input(s) `clock` must provide enough valid edges after reset/enable for the checker to sample settled outputs.
- Sequential outputs are sampled shortly after clock edges, so drive outputs with stable held state variables and `transition()` targets rather than glitchy combinational expressions.
- Public stimulus nodes used by the reference harness include: `clk_in`, `ratio_ctrl`.
