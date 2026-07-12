# Flash Thermometer Centered Sum Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `flash_thermometer_centered_sum.va`:
  - Module `flash_thermometer_centered_sum` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `b2` (input, electrical)
    - position 3: `b3` (input, electrical)
    - position 4: `b4` (input, electrical)
    - position 5: `b5` (input, electrical)
    - position 6: `b6` (input, electrical)
    - position 7: `b7` (input, electrical)
    - position 8: `dout` (output, electrical)

## Public Parameter Contract

- `flash_thermometer_centered_sum.vth` defaults to `0.45`; valid range: finite; overrides vth.
- `flash_thermometer_centered_sum.gain` defaults to `0.1125`; valid range: finite; overrides gain.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_THERMOMETER_THRESHOLD_COUNT`: restore: Each `b0` through `b7` input above `vth` contributes exactly one count to the thermometer total. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.
- `P_CENTERED_SUM`: restore: The output subtracts the four-count midpoint so the analog sum is centered around zero asserted-input balance. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.
- `P_OUTPUT_GAIN`: restore: The centered count is multiplied by `gain` and driven on `dout` without extra scaling. Required traces: `time`, `b0`, `b1`, `b2`, `b3`, `b4`, `b5`, `b6`, `b7`, `dout`.

## Modeling Constraints

- Use deterministic voltage-domain behavioral Verilog-A.
- Do not hard-code validation stimulus, stop times, sample windows, gold internals, or simulator side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `flash_thermometer_centered_sum.va`.
Every supplied `.va` file is editable; do not add or omit files.
