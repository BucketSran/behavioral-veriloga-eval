# QTZ Differential 2level Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `qtz_differential_2level.va`:
  - Module `qtz_differential_2level` (entry)
    - position 0: `vinp` (input, electrical)
    - position 1: `vinn` (input, electrical)
    - position 2: `vrefp` (input, electrical)
    - position 3: `vrefn` (input, electrical)
    - position 4: `clk` (input, electrical)
    - position 5: `dout` (output, electrical)

## Public Parameter Contract

- `qtz_differential_2level.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `qtz_differential_2level.ttol` defaults to `5p`; valid range: finite; overrides ttol.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_SIGNED_CODE`: restore: Initialize the signed output code to `-0.5`. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_DIFFERENTIAL_MIDPOINT_DECISION`: restore: On each rising `clk`, compare `vinp-vinn` with the midpoint between `vrefn` and `vrefp`. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_BIPOLAR_TWO_LEVEL_OUTPUT`: restore: Drive `dout` to the signed `+0.5` or `-0.5` level rather than a unipolar code. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.
- `P_CLOCKED_OUTPUT_HOLD`: restore: Between rising clock decisions, hold the previous quantized output value. Required traces: `time`, `clk`, `dout`, `vinn`, `vinp`, `vrefn`, `vrefp`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `qtz_differential_2level.va`.
Every supplied `.va` file is editable; do not add or omit files.
