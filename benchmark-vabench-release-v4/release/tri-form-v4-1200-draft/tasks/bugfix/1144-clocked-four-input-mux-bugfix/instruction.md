# Clocked Four Input Mux Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `clocked_four_input_mux.va`:
  - Module `clocked_four_input_mux` (entry)
    - position 0: `dsel0` (input, electrical)
    - position 1: `dsel1` (input, electrical)
    - position 2: `din0` (input, electrical)
    - position 3: `din1` (input, electrical)
    - position 4: `din2` (input, electrical)
    - position 5: `din3` (input, electrical)
    - position 6: `clks` (input, electrical)
    - position 7: `dout` (output, electrical)

## Public Parameter Contract

- `clocked_four_input_mux.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `clocked_four_input_mux.tr` defaults to `20p`; valid range: finite; overrides tr.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_FALLING_EDGE_SAMPLE_HOLD`: restore: Only falling `clks` crossings through `vth` update `dout`; between those events the last selected input value is held. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.
- `P_SELECT_BIT_DECODE`: restore: `dsel0` is the LSB and `dsel1` is the MSB when selecting among `din0` through `din3`. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.
- `P_ALL_FOUR_INPUTS_REACHABLE`: restore: All four data inputs can be selected and forwarded to `dout` according to the two-bit select code. Required traces: `time`, `clks`, `din0`, `din1`, `din2`, `din3`, `dout`, `dsel0`, `dsel1`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `clocked_four_input_mux.va`.
Every supplied `.va` file is editable; do not add or omit files.
