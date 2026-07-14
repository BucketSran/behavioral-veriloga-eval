# Digitally Controlled Delay Cell Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

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

## Public Parameter Contract

- `digitally_controlled_delay_cell.vdd` defaults to `0.9`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vdd behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.vss` defaults to `0.0`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vss behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.vth` defaults to `0.45`; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public vth behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.delay_min` defaults to `20e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_min behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.delay_lsb` defaults to `3e-12` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public delay_lsb behavior for module digitally_controlled_delay_cell.
- `digitally_controlled_delay_cell.tr` defaults to `100p from (0:inf)` s; valid range: declared Verilog-A parameter constraint or finite portable value; overrides public tr behavior for module digitally_controlled_delay_cell.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_CLEAR`: restore: Reset clears the loaded code state, delayed clock, delay metric, valid indication, and pending edges. Required traces: `time`, `rst`, `load`, `out_clk`, `delay_metric`, `valid`.
- `P_CODE_CAPTURE_METRIC`: restore: A rising load edge captures the six-bit unsigned code and the delay metric reports the normalized captured code. Required traces: `time`, `load`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`, `delay_metric`.
- `P_EDGE_DELAY_MAPPING`: restore: Each input-clock edge appears at the output after delay_min plus delay_lsb times the code captured for that edge. Required traces: `time`, `in_clk`, `out_clk`, `load`, `code_5`, `code_4`, `code_3`, `code_2`, `code_1`, `code_0`.
- `P_PULSE_INTEGRITY_VALID`: restore: Rising and falling edges receive equal delay, preserving pulse width, and valid asserts after the first delayed rising edge. Required traces: `time`, `rst`, `in_clk`, `out_clk`, `valid`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A suitable for transient simulation.
- Use public voltage contributions only and preserve the declared artifact and module interfaces.
- Do not hard-code evaluator stimulus, sample windows, checker tolerances, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `digitally_controlled_delay_cell.va`.
Every supplied `.va` file is editable; do not add or omit files.
