# Ready/Valid Latency Counter 12b Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ready_valid_latency_counter_12b.va`:
  - Module `ready_valid_latency_counter_12b` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `valid_i` (input, electrical)
    - position 2: `ready_i` (input, electrical)
    - position 3: `done` (output, electrical)
    - position 4: `lat0` (output, electrical)
    - position 5: `lat1` (output, electrical)
    - position 6: `lat2` (output, electrical)
    - position 7: `lat3` (output, electrical)
    - position 8: `lat4` (output, electrical)
    - position 9: `lat5` (output, electrical)
    - position 10: `lat6` (output, electrical)
    - position 11: `lat7` (output, electrical)
    - position 12: `lat8` (output, electrical)
    - position 13: `lat9` (output, electrical)
    - position 14: `lat10` (output, electrical)
    - position 15: `lat11` (output, electrical)

## Public Parameter Contract

- `ready_valid_latency_counter_12b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded latency and done high level.
- `ready_valid_latency_counter_12b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock, valid, and ready decision threshold.
- `ready_valid_latency_counter_12b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_REQUEST_START`: restore: While idle, a rising clock crossing that samples valid_i high starts a measurement at count zero and clears done. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_WAIT_CYCLE_COUNT`: restore: While active, each rising clock crossing that samples ready_i low increments the pending latency by one cycle. Required traces: `time`, `clk`, `ready_i`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_READY_COMPLETION`: restore: While active, a rising clock crossing that samples ready_i high latches the current count to lat[11:0], asserts done, and returns the meter to idle. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_ZERO_LATENCY`: restore: If valid_i and ready_i are both high on the starting clock edge, the reported latency is zero. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_RESULT_HOLD_AND_ORDER`: restore: The completed result holds until a later request starts; lat0 is LSB, lat11 is MSB, and asserted outputs use vdd. Required traces: `time`, `clk`, `valid_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.

## Modeling Constraints

- AMS role: ready/valid latency measurement block for converter/readout handshakes.
- Use deterministic rising-edge active/idle and counter state.
- Sample valid_i and ready_i only at rising clock crossings.
- Use smooth voltage contributions for all outputs.
- Do not add an undeclared reset, embed stimulus timing, expose validation state, or use simulator-specific side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ready_valid_latency_counter_12b.va`.
Every supplied `.va` file is editable; do not add or omit files.
