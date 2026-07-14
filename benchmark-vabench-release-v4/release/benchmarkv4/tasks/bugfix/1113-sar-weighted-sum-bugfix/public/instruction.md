# SAR Weighted Sum Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `sar_weighted_sum.va`:
  - Module `sar_weighted_sum` (entry)
    - position 0: `D10` (input, electrical)
    - position 1: `D9` (input, electrical)
    - position 2: `D8` (input, electrical)
    - position 3: `D7` (input, electrical)
    - position 4: `D6` (input, electrical)
    - position 5: `D5` (input, electrical)
    - position 6: `D4` (input, electrical)
    - position 7: `D3` (input, electrical)
    - position 8: `D2` (input, electrical)
    - position 9: `D1` (input, electrical)
    - position 10: `D0` (input, electrical)
    - position 11: `VOUT` (output, electrical)

## Public Parameter Contract

- `sar_weighted_sum.vth` defaults to `0.45` V; valid range: finite real value; sets the strict decision threshold independently applied to every D input.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_THRESHOLD_DECODE`: restore: Each D input contributes logic 1 only while its voltage is strictly above vth; a value at or below vth contributes logic 0. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_WEIGHT_ORDER`: restore: The decoded contribution order is D10 at seven-eighths full scale, D9 at one-half, D8 at one-quarter, a 5:3 split across D7 and D6, then a binary tail from D5 through D0. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_BIPOLAR_ENDPOINTS`: restore: All decision inputs low produce -1 V, while all decision inputs high produce one 512-unit step below +1 V on the normalized bipolar scale. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_MONOTONIC_CODE_WEIGHT`: restore: Changing any decoded decision from low to high without lowering another decision cannot decrease VOUT. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_CONTINUOUS_DECODE`: restore: VOUT continuously reflects the current threshold-decoded input combination without a clock, reset, or retained code state. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.

## Modeling Constraints

- Use deterministic continuous voltage-domain decoding.
- Use voltage contributions only.
- Do not use current contributions, ddt(), idt(), retained validation state, or validation-only hooks.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `sar_weighted_sum.va`.
Every supplied `.va` file is editable; do not add or omit files.
