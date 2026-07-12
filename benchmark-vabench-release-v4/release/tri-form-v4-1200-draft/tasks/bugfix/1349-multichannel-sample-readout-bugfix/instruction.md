# Multi-channel Sample/Mux/Readout Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sample_mux_readout_top.va`:
  - Module `sample_mux_readout_top` (entry)
    - position 0: `ch0` (input, electrical)
    - position 1: `ch1` (input, electrical)
    - position 2: `ch2` (input, electrical)
    - position 3: `ch3` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `rst` (input, electrical)
    - position 6: `sample` (input, electrical)
    - position 7: `read` (input, electrical)
    - position 8: `out` (output, electrical)
    - position 9: `ch_sel_1` (output, electrical)
    - position 10: `ch_sel_0` (output, electrical)
    - position 11: `valid` (output, electrical)
- Artifact `sample_hold_bank.va`:
  - Module `sample_hold_bank` (required_submodule)
    - position 0: `ch0` (input, electrical)
    - position 1: `ch1` (input, electrical)
    - position 2: `ch2` (input, electrical)
    - position 3: `ch3` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `rst` (input, electrical)
    - position 6: `sample` (input, electrical)
    - position 7: `hold0` (output, electrical)
    - position 8: `hold1` (output, electrical)
    - position 9: `hold2` (output, electrical)
    - position 10: `hold3` (output, electrical)
- Artifact `mux_controller.va`:
  - Module `mux_controller` (required_submodule)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `read` (input, electrical)
    - position 3: `ch_sel_1` (output, electrical)
    - position 4: `ch_sel_0` (output, electrical)
    - position 5: `valid` (output, electrical)
- Artifact `output_driver.va`:
  - Module `output_driver` (required_submodule)
    - position 0: `hold0` (input, electrical)
    - position 1: `hold1` (input, electrical)
    - position 2: `hold2` (input, electrical)
    - position 3: `hold3` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `rst` (input, electrical)
    - position 6: `read` (input, electrical)
    - position 7: `ch_sel_1` (input, electrical)
    - position 8: `ch_sel_0` (input, electrical)
    - position 9: `out` (output, electrical)

## Public Parameter Contract

- `sample_mux_readout_top.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `sample_mux_readout_top.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `sample_mux_readout_top.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sample_mux_readout_top.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `sample_hold_bank.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `sample_hold_bank.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `mux_controller.vdd` defaults to `0.9` V; valid range: finite and consistent with the declared rail domain; overrides vdd for this module.
- `mux_controller.vss` defaults to `0.0` V; valid range: finite and consistent with the declared rail domain; overrides vss for this module.
- `mux_controller.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `mux_controller.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.
- `output_driver.vth` defaults to `0.45` V; valid range: finite and consistent with the declared rail domain; overrides vth for this module.
- `output_driver.tr` defaults to `200e-12` s; valid range: tr > 0; overrides tr for this module.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_READOUT_RESET_CLEAR`: restore: Reset clears held channels, selector, out, and valid. Required traces: `time`, `rst`, `out`, `ch_sel_1`, `ch_sel_0`, `valid`.
- `P_READOUT_SIMULTANEOUS_SAMPLE`: restore: An enabled rising clock captures all four input channels into one coherent held bank. Required traces: `time`, `ch0`, `ch1`, `ch2`, `ch3`, `clk`, `rst`, `sample`, `read`, `out`.
- `P_READOUT_CHANNEL_ORDER`: restore: Read cycles select held channels in order zero, one, two, three and wrap. Required traces: `time`, `clk`, `rst`, `read`, `ch_sel_1`, `ch_sel_0`.
- `P_READOUT_HELD_VALUE`: restore: out equals the held value of the exposed selected channel, independent of later live-input changes. Required traces: `time`, `ch0`, `ch1`, `ch2`, `ch3`, `clk`, `sample`, `read`, `out`, `ch_sel_1`, `ch_sel_0`.
- `P_READOUT_VALID_TIMING`: restore: valid is high only for read cycles; when read is low out holds and the pointer does not advance. Required traces: `time`, `clk`, `rst`, `read`, `out`, `ch_sel_1`, `ch_sel_0`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain transient behavioral Verilog-A.
- Preserve the declared multi-module architecture and exact public artifact interfaces.
- Do not use current contributions, unsupported continuous operators, validation logic, hard-coded evaluator timing, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sample_mux_readout_top.va`, `sample_hold_bank.va`, `mux_controller.va`, `output_driver.va`.
Every supplied `.va` file is editable; do not add or omit files.
