# Edge Interval TDC 8b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `edge_interval_tdc_8b.va`:
  - Module `edge_interval_tdc_8b` (entry)
    - position 0: `start` (input, electrical)
    - position 1: `stop` (input, electrical)
    - position 2: `valid` (output, electrical)
    - position 3: `code0` (output, electrical)
    - position 4: `code1` (output, electrical)
    - position 5: `code2` (output, electrical)
    - position 6: `code3` (output, electrical)
    - position 7: `code4` (output, electrical)
    - position 8: `code5` (output, electrical)
    - position 9: `code6` (output, electrical)
    - position 10: `code7` (output, electrical)

## Public Parameter Contract

- `edge_interval_tdc_8b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded code and valid high level.
- `edge_interval_tdc_8b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the start and stop rising-edge threshold.
- `edge_interval_tdc_8b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_START_ARMS`: restore: Each rising start crossing begins a new interval measurement, records that edge time, and clears valid. Required traces: `time`, `start`, `stop`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_NEXT_STOP_COMPLETES`: restore: The first rising stop crossing after an armed start completes that measurement; stop crossings while unarmed do not change the result. Required traces: `time`, `start`, `stop`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_INTERVAL_QUANTIZATION`: restore: A completed interval is rounded to the nearest whole nanosecond and reported as an unsigned code. Required traces: `time`, `start`, `stop`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_CODE_SATURATION`: restore: Measured interval codes are saturated to the inclusive 8-bit range 0 through 255. Required traces: `time`, `start`, `stop`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_VALID_AND_BIT_ORDER`: restore: valid asserts after completion; code0 is the least significant bit and code7 is the most significant bit, using 0 V and vdd logic levels. Required traces: `time`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.

## Modeling Constraints

- Use deterministic event state for arming, edge times, result code, and validity.
- Use the public 1 ns code quantum without embedding any testbench stimulus times.
- Use smooth voltage contributions for all outputs.
- Do not add undeclared artifacts, validation hooks, current contributions, or simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `edge_interval_tdc_8b.va`.
Every supplied `.va` file is editable; do not add or omit files.
