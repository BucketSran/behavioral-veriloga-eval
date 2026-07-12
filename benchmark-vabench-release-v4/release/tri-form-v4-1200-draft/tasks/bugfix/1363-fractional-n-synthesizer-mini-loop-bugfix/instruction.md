# Fractional-N Synthesizer Mini Loop Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `fracn_synth_top.va`:
  - Module `fracn_synth_top` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `dco_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `frac_3` (input, electrical)
    - position 5: `frac_2` (input, electrical)
    - position 6: `frac_1` (input, electrical)
    - position 7: `frac_0` (input, electrical)
    - position 8: `div_clk` (output, electrical)
    - position 9: `div_sel` (output, electrical)
    - position 10: `avg_ratio_metric` (output, electrical)
    - position 11: `valid` (output, electrical)
- Artifact `accumulator.va`:
  - Module `accumulator` (required_submodule)
    - position 0: `decision_tick` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `frac_3` (input, electrical)
    - position 4: `frac_2` (input, electrical)
    - position 5: `frac_1` (input, electrical)
    - position 6: `frac_0` (input, electrical)
    - position 7: `carry` (output, electrical)
- Artifact `multi_modulus_divider.va`:
  - Module `multi_modulus_divider` (required_submodule)
    - position 0: `dco_clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `carry` (input, electrical)
    - position 4: `div_clk` (output, electrical)
    - position 5: `div_sel` (output, electrical)
    - position 6: `decision_tick` (output, electrical)
- Artifact `ratio_monitor.va`:
  - Module `ratio_monitor` (required_submodule)
    - position 0: `decision_tick` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `div_sel` (input, electrical)
    - position 4: `avg_ratio_metric` (output, electrical)
    - position 5: `valid` (output, electrical)

## Public Parameter Contract

- `fracn_synth_top.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module fracn_synth_top.
- `fracn_synth_top.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module fracn_synth_top.
- `fracn_synth_top.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module fracn_synth_top.
- `fracn_synth_top.n_int` defaults to `8 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public n_int behavior for module fracn_synth_top.
- `fracn_synth_top.window_len` defaults to `16 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public window_len behavior for module fracn_synth_top.
- `fracn_synth_top.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module fracn_synth_top.
- `accumulator.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module accumulator.
- `accumulator.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module accumulator.
- `accumulator.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module accumulator.
- `accumulator.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module accumulator.
- `multi_modulus_divider.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module multi_modulus_divider.
- `multi_modulus_divider.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module multi_modulus_divider.
- `multi_modulus_divider.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module multi_modulus_divider.
- `multi_modulus_divider.n_int` defaults to `8 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public n_int behavior for module multi_modulus_divider.
- `multi_modulus_divider.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module multi_modulus_divider.
- `ratio_monitor.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module ratio_monitor.
- `ratio_monitor.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module ratio_monitor.
- `ratio_monitor.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module ratio_monitor.
- `ratio_monitor.n_int` defaults to `8 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public n_int behavior for module ratio_monitor.
- `ratio_monitor.window_len` defaults to `16 from [1:inf)`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public window_len behavior for module ratio_monitor.
- `ratio_monitor.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module ratio_monitor.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation clears accumulator/divider state and all public outputs. Required traces: `time`, `rst`, `enable`, `div_clk`, `div_sel`, `avg_ratio_metric`, `valid`.
- `P_FRACTIONAL_SELECTION`: restore: The fraction code drives deterministic n_int versus n_int+1 selection through accumulator carry events. Required traces: `time`, `dco_clk`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `div_sel`.
- `P_DCO_DERIVED_DIVIDER`: restore: div_clk transitions are derived only from counted rising dco_clk edges using the selected modulus. Required traces: `time`, `ref_clk`, `dco_clk`, `div_clk`, `div_sel`.
- `P_RATIO_WINDOW`: restore: At each full window, avg_ratio_metric reports n_int plus the observed fraction of larger-modulus selections and valid pulses. Required traces: `time`, `dco_clk`, `div_sel`, `avg_ratio_metric`, `valid`.
- `P_FRACTION_MONOTONICITY`: restore: Larger fraction commands produce nondecreasing average selected divide-ratio metrics over equal windows. Required traces: `time`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `avg_ratio_metric`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation.
- Use public voltage contributions only and preserve the declared artifact and module interfaces.
- Do not hard-code evaluator stimulus, sample windows, checker tolerances, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `fracn_synth_top.va`, `accumulator.va`, `multi_modulus_divider.va`, `ratio_monitor.va`.
Every supplied `.va` file is editable; do not add or omit files.
