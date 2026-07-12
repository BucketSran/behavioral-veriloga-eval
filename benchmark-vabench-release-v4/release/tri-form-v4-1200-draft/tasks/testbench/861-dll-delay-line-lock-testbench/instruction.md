# DLL Delay-line Lock Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `DLL Delay-line Lock` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `dll_top` as `XDUT` with ordered public binding: ref_clk=ref_clk, in_clk=in_clk, rst=rst, enable=enable, delayed_clk=delayed_clk, up=up, down=down, delay_4=delay_4, delay_3=delay_3, delay_2=delay_2, delay_1=delay_1, delay_0=delay_0, lock=lock.

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

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_DISABLE_CLEAR`: exercise and make observable: Reset or disabled operation restores delay_center, clears correction and lock outputs, cancels pending edges, and drives delayed_clk low. Required traces: `time`, `rst`, `enable`, `delayed_clk`, `up`, `down`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`, `lock`.
- `P_DELAY_LINE_DERIVATION`: exercise and make observable: Each delayed-clock edge derives from the matching input-clock edge using the code selected for that edge; the output is not free-running. Required traces: `time`, `in_clk`, `delayed_clk`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`.
- `P_PHASE_CORRECTION`: exercise and make observable: Completed ref/delayed comparisons request the correction direction that moves the delay code toward edge alignment and update the code once within 0 through 31. Required traces: `time`, `ref_clk`, `delayed_clk`, `up`, `down`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`.
- `P_LOCK_QUALIFICATION`: exercise and make observable: Lock asserts only after four consecutive comparisons within lock_window times unit_delay and clears after an out-of-window comparison. Required traces: `time`, `ref_clk`, `delayed_clk`, `up`, `down`, `lock`.

The required trace names are: `time`, `ref_clk`, `in_clk`, `rst`, `enable`, `delayed_clk`, `up`, `down`, `delay_4`, `delay_3`, `delay_2`, `delay_1`, `delay_0`, `lock`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
