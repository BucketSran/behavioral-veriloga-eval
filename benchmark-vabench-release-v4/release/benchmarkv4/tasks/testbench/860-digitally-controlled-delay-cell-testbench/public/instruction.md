# Digitally Controlled Delay Cell Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Digitally Controlled Delay Cell` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `digitally_controlled_delay_cell.va`:
  - Module `digitally_controlled_delay_cell` (entry)
    - position 0: `in_clk` (input, electrical)
    - position 1: `load` (input, electrical)
    - position 2: `rst` (input, electrical)
    - position 3: `code_5` (input, electrical)
    - position 4: `code_4` (input, electrical)
    - position 5: `code_3` (input, electrical)
    - position 6: `code_2` (input, electrical)
    - position 7: `code_1` (input, electrical)
    - position 8: `code_0` (input, electrical)
    - position 9: `out_clk` (output, electrical)
    - position 10: `delay_metric` (output, electrical)
    - position 11: `valid` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `digitally_controlled_delay_cell` as `XDUT` with ordered public binding: in_clk=in_clk, load=load, rst=rst, code_5=code_5, code_4=code_4, code_3=code_3, code_2=code_2, code_1=code_1, code_0=code_0, out_clk=out_clk, delay_metric=delay_metric, valid=valid.

## Public Parameter Contract

- `digitally_controlled_delay_cell.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.delay_min` defaults to `20e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_min behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.delay_lsb` defaults to `3e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_lsb behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module digitally_controlled_delay_cell.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_CLEAR`: exercise and make observable: Reset clears the loaded code state, delayed clock, delay metric, valid indication, and pending edges. Required traces: `time`, `rst`, `load`, `out_clk`, `delay_metric`, `valid`.
- `P_CODE_CAPTURE_METRIC`: exercise and make observable: A rising load edge captures the six-bit unsigned code and the delay metric reports the normalized captured code. Required traces: `time`, `load`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `delay_metric`.
- `P_EDGE_DELAY_MAPPING`: exercise and make observable: Each input-clock edge appears at the output after delay_min plus delay_lsb times the code captured for that edge. Required traces: `time`, `in_clk`, `out_clk`, `load`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`.
- `P_PULSE_INTEGRITY_VALID`: exercise and make observable: Rising and falling edges receive equal delay, preserving pulse width, and valid asserts after the first delayed rising edge. Required traces: `time`, `rst`, `in_clk`, `out_clk`, `valid`.

The required trace names are: `time`, `in_clk`, `load`, `rst`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `out_clk`, `delay_metric`, `valid`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
