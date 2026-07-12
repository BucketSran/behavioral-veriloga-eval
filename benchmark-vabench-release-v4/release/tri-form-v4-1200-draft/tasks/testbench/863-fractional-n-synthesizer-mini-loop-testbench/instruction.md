# Fractional-N Synthesizer Mini Loop Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Fractional-N Synthesizer Mini Loop` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `fracn_synth_top` as `XDUT` with ordered public binding: ref_clk=ref_clk, dco_clk=dco_clk, rst=rst, enable=enable, frac_3=frac_3, frac_2=frac_2, frac_1=frac_1, frac_0=frac_0, div_clk=div_clk, div_sel=div_sel, avg_ratio_metric=avg_ratio_metric, valid=valid.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disabled operation clears accumulator/divider state and all public outputs. Required traces: `time`, `rst`, `enable`, `div_clk`, `div_sel`, `avg_ratio_metric`, `valid`.
- `P_FRACTIONAL_SELECTION`: exercise and make observable: The fraction code drives deterministic n_int versus n_int+1 selection through accumulator carry events. Required traces: `time`, `dco_clk`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `div_sel`.
- `P_DCO_DERIVED_DIVIDER`: exercise and make observable: div_clk transitions are derived only from counted rising dco_clk edges using the selected modulus. Required traces: `time`, `ref_clk`, `dco_clk`, `div_clk`, `div_sel`.
- `P_RATIO_WINDOW`: exercise and make observable: At each full window, avg_ratio_metric reports n_int plus the observed fraction of larger-modulus selections and valid pulses. Required traces: `time`, `dco_clk`, `div_sel`, `avg_ratio_metric`, `valid`.
- `P_FRACTION_MONOTONICITY`: exercise and make observable: Larger fraction commands produce nondecreasing average selected divide-ratio metrics over equal windows. Required traces: `time`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `avg_ratio_metric`, `valid`.

The required trace names are: `time`, `ref_clk`, `dco_clk`, `rst`, `enable`, `frac_3`, `frac_2`, `frac_1`, `frac_0`, `div_clk`, `div_sel`, `avg_ratio_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
