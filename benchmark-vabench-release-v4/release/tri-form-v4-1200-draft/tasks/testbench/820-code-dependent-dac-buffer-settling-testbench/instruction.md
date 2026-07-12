# Code-dependent DAC Buffer Settling Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Code-dependent DAC Buffer Settling` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `code_dependent_dac_buffer_top.va`:
  - Module `code_dependent_dac_buffer_top` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `code_3` (input, electrical)
    - position 4: `code_2` (input, electrical)
    - position 5: `code_1` (input, electrical)
    - position 6: `code_0` (input, electrical)
    - position 7: `vout` (output, electrical)
    - position 8: `target_dbg` (output, electrical)
    - position 9: `settling_metric` (output, electrical)
    - position 10: `settled` (output, electrical)
- Artifact `ideal_code_dac.va`:
  - Module `ideal_code_dac` (required_submodule)
    - position 0: `rst` (input, electrical)
    - position 1: `enable` (input, electrical)
    - position 2: `code_3` (input, electrical)
    - position 3: `code_2` (input, electrical)
    - position 4: `code_1` (input, electrical)
    - position 5: `code_0` (input, electrical)
    - position 6: `target` (output, electrical)
- Artifact `settling_buffer_state.va`:
  - Module `settling_buffer_state` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `target` (input, electrical)
    - position 4: `vout` (output, electrical)
    - position 5: `settling_metric` (output, electrical)
    - position 6: `settled` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `code_dependent_dac_buffer_top` as `XDUT` with ordered public binding: clk=clk, rst=rst, enable=enable, code_3=code_3, code_2=code_2, code_1=code_1, code_0=code_0, vout=vout, target_dbg=target_dbg, settling_metric=settling_metric, settled=settled.

## Public Parameter Contract

- `code_dependent_dac_buffer_top.vdd` defaults to `0.9`; valid range: finite; overrides vdd.
- `code_dependent_dac_buffer_top.vss` defaults to `0.0`; valid range: finite; overrides vss.
- `code_dependent_dac_buffer_top.vcm` defaults to `0.45`; valid range: finite; overrides vcm.
- `code_dependent_dac_buffer_top.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `code_dependent_dac_buffer_top.tr` defaults to `200p from (0:inf)`; valid range: finite; overrides tr.
- `code_dependent_dac_buffer_top.settle_step` defaults to `80e-3 from (0:inf)`; valid range: finite; overrides settle_step.
- `code_dependent_dac_buffer_top.settle_tol` defaults to `8e-3 from (0:inf)`; valid range: finite; overrides settle_tol.
- `ideal_code_dac.vdd` defaults to `0.9` V; valid range: finite; overrides vdd.
- `ideal_code_dac.vss` defaults to `0.0` V; valid range: finite; overrides vss.
- `ideal_code_dac.vth` defaults to `0.45` V; valid range: finite; overrides vth.
- `ideal_code_dac.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides tr.
- `settling_buffer_state.vdd` defaults to `0.9` V; valid range: finite; overrides vdd.
- `settling_buffer_state.vss` defaults to `0.0` V; valid range: finite; overrides vss.
- `settling_buffer_state.vcm` defaults to `0.45` V; valid range: finite; overrides vcm.
- `settling_buffer_state.vth` defaults to `0.45` V; valid range: finite; overrides vth.
- `settling_buffer_state.tr` defaults to `200p from (0:inf)` s; valid range: positive; overrides tr.
- `settling_buffer_state.settle_step` defaults to `80e-3 from (0:inf)` V; valid range: positive; overrides settle_step.
- `settling_buffer_state.settle_tol` defaults to `8e-3 from (0:inf)` V; valid range: positive; overrides settle_tol.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_ON_RESET_OR_WHEN_DISABLED_CLEAR`: exercise and make observable: On reset or when disabled, drive `vout` to `vcm` and drive `target_dbg`, `settling_metric`, and `settled` to `vss`. Required traces: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.
- `P_ON_EACH_ENABLED_RISING_CLK_EDGE`: exercise and make observable: Decode code 0..15 linearly from `vss` to `vdd`; on each enabled rising `clk` edge update the buffered output toward that target. Required traces: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.
- `P_APPLY_A_CODE_DEPENDENT_SETTLING_STEP`: exercise and make observable: Apply a code-dependent settling step so large code jumps take more updates to settle. Required traces: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.
- `P_EXPOSE_THE_CURRENT_TARGET_ON_TARGET`: exercise and make observable: Expose the current target on `target_dbg` and the remaining error on `settling_metric`. Required traces: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.
- `P_ASSERT_SETTLED_AFTER_THE_REMAINING_ERROR`: exercise and make observable: Assert `settled` after the remaining error stays below `settle_tol` for two enabled updates. Required traces: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.

The required trace names are: `time`, `clk`, `rst`, `enable`, `code_3`, `code_2`, `code_1`, `code_0`, `vout`, `target_dbg`, `settling_metric`, `settled`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
