# DLL Delay-line Lock Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `dll_top.va`:
  - Module `dll_top` (entry)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `in_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `delayed_clk` (output, electrical)
    - position 5: `up` (output, electrical)
    - position 6: `down` (output, electrical)
    - position 7: `delay_4` (output, electrical)
    - position 8: `delay_3` (output, electrical)
    - position 9: `delay_2` (output, electrical)
    - position 10: `delay_1` (output, electrical)
    - position 11: `delay_0` (output, electrical)
    - position 12: `lock` (output, electrical)
- Artifact `phase_detector.va`:
  - Module `phase_detector` (required_submodule)
    - position 0: `ref_clk` (input, electrical)
    - position 1: `delayed_clk` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `enable` (input, electrical)
    - position 4: `up` (output, electrical)
    - position 5: `down` (output, electrical)
    - position 6: `decision_clk` (output, electrical)
    - position 7: `edge_error` (output, electrical)
- Artifact `delay_line.va`:
  - Module `delay_line` (required_submodule)
    - position 0: `in_clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `enable` (input, electrical)
    - position 3: `delay_4` (input, electrical)
    - position 4: `delay_3` (input, electrical)
    - position 5: `delay_2` (input, electrical)
    - position 6: `delay_1` (input, electrical)
    - position 7: `delay_0` (input, electrical)
    - position 8: `delayed_clk` (output, electrical)
- Artifact `lock_detector.va`:
  - Module `lock_detector` (required_submodule)
    - position 0: `decision_clk` (input, electrical)
    - position 1: `up` (input, electrical)
    - position 2: `down` (input, electrical)
    - position 3: `edge_error` (input, electrical)
    - position 4: `rst` (input, electrical)
    - position 5: `enable` (input, electrical)
    - position 6: `delay_4` (output, electrical)
    - position 7: `delay_3` (output, electrical)
    - position 8: `delay_2` (output, electrical)
    - position 9: `delay_1` (output, electrical)
    - position 10: `delay_0` (output, electrical)
    - position 11: `lock` (output, electrical)

## Public Parameter Contract

- `dll_top.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module dll_top.
- `dll_top.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module dll_top.
- `dll_top.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module dll_top.
- `dll_top.delay_center` defaults to `16` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_center behavior for module dll_top.
- `dll_top.unit_delay` defaults to `5e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public unit_delay behavior for module dll_top.
- `dll_top.lock_window` defaults to `1`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public lock_window behavior for module dll_top.
- `dll_top.tr` defaults to `100p` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module dll_top.
- `phase_detector.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module phase_detector.
- `phase_detector.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module phase_detector.
- `phase_detector.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module phase_detector.
- `phase_detector.unit_delay` defaults to `5e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public unit_delay behavior for module phase_detector.
- `phase_detector.tr` defaults to `100p` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module phase_detector.
- `delay_line.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module delay_line.
- `delay_line.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module delay_line.
- `delay_line.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module delay_line.
- `delay_line.unit_delay` defaults to `5e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public unit_delay behavior for module delay_line.
- `delay_line.tr` defaults to `100p` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module delay_line.
- `lock_detector.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module lock_detector.
- `lock_detector.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module lock_detector.
- `lock_detector.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module lock_detector.
- `lock_detector.delay_center` defaults to `16` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_center behavior for module lock_detector.
- `lock_detector.lock_window` defaults to `1`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public lock_window behavior for module lock_detector.
- `lock_detector.tr` defaults to `100p` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module lock_detector.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_DISABLE_CLEAR`: restore: Reset or disabled operation restores delay_center, clears correction and lock outputs, cancels pending edges, and drives delayed_clk low. Required traces: `time`, `rst`, `enable`, `delayed_clk`, `up`, `down`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`, `lock`.
- `P_DELAY_LINE_DERIVATION`: restore: Each delayed-clock edge derives from the matching input-clock edge using the code selected for that edge; the output is not free-running. Required traces: `time`, `in_clk`, `delayed_clk`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`.
- `P_PHASE_CORRECTION`: restore: Completed ref/delayed comparisons request the correction direction that moves the delay code toward edge alignment and update the code once within 0 through 31. Required traces: `time`, `ref_clk`, `delayed_clk`, `up`, `down`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`.
- `P_LOCK_QUALIFICATION`: restore: Lock asserts only after four consecutive comparisons within lock_window times unit_delay and clears after an out-of-window comparison. Required traces: `time`, `ref_clk`, `delayed_clk`, `up`, `down`, `lock`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation.
- Use public voltage contributions only and preserve the declared artifact and module interfaces.
- Do not hard-code evaluator stimulus, sample windows, checker tolerances, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `dll_top.va`, `phase_detector.va`, `delay_line.va`, `lock_detector.va`.
Every supplied `.va` file is editable; do not add or omit files.
