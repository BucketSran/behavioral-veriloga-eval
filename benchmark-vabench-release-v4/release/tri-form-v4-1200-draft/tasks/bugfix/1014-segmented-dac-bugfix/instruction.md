# Segmented DAC Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `segmented_dac.va`:
  - Module `segmented_dac` (entry)
    - position 0: `b0` (input, electrical)
    - position 1: `b1` (input, electrical)
    - position 2: `t0` (input, electrical)
    - position 3: `t1` (input, electrical)
    - position 4: `t2` (input, electrical)
    - position 5: `vref` (input, electrical)
    - position 6: `vss` (input, electrical)
    - position 7: `aout` (output, electrical)

## Public Parameter Contract

- `segmented_dac.vth` defaults to `0.45` V; valid range: vth > 0; sets binary and thermometer control threshold.
- `segmented_dac.tr` defaults to `5e-10` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_SEGMENT_WEIGHTS`: restore: b0 and b1 contribute one and two LSB steps while each active thermometer control contributes four LSB steps. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `aout`.
- `P_CODE_MONOTONICITY`: restore: Increasing the summed segmented code does not decrease aout. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `aout`.
- `P_ENDPOINTS`: restore: The zero code maps to vss and the all-active 15-step code maps to vref. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `vref`, `vss`, `aout`.
- `P_RAIL_RELATIVE_MAPPING`: restore: Intermediate codes linearly span the vss-to-vref range. Required traces: `time`, `b0`, `b1`, `t0`, `t1`, `t2`, `vref`, `vss`, `aout`.

## Modeling Constraints

- Use deterministic continuous code-to-voltage behavior with finite transition smoothing.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), validation logic, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `segmented_dac.va`.
Every supplied `.va` file is editable; do not add or omit files.
