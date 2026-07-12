# Ready/Valid Latency Counter 12b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Ready/Valid Latency Counter 12b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ready_valid_latency_counter_12b` as `XDUT` with ordered public binding: clk=clk, valid_i=valid_i, ready_i=ready_i, done=done, lat0=lat0, lat1=lat1, lat2=lat2, lat3=lat3, lat4=lat4, lat5=lat5, lat6=lat6, lat7=lat7, lat8=lat8, lat9=lat9, lat10=lat10, lat11=lat11.

## Public Parameter Contract

- `ready_valid_latency_counter_12b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded latency and done high level.
- `ready_valid_latency_counter_12b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the clock, valid, and ready decision threshold.
- `ready_valid_latency_counter_12b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_REQUEST_START`: exercise and make observable: While idle, a rising clock crossing that samples valid_i high starts a measurement at count zero and clears done. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_WAIT_CYCLE_COUNT`: exercise and make observable: While active, each rising clock crossing that samples ready_i low increments the pending latency by one cycle. Required traces: `time`, `clk`, `ready_i`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_READY_COMPLETION`: exercise and make observable: While active, a rising clock crossing that samples ready_i high latches the current count to lat[11:0], asserts done, and returns the meter to idle. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_ZERO_LATENCY`: exercise and make observable: If valid_i and ready_i are both high on the starting clock edge, the reported latency is zero. Required traces: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.
- `P_RESULT_HOLD_AND_ORDER`: exercise and make observable: The completed result holds until a later request starts; lat0 is LSB, lat11 is MSB, and asserted outputs use vdd. Required traces: `time`, `clk`, `valid_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.

The required trace names are: `time`, `clk`, `valid_i`, `ready_i`, `done`, `lat0`, `lat1`, `lat2`, `lat3`, `lat4`, `lat5`, `lat6`, `lat7`, `lat8`, `lat9`, `lat10`, `lat11`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
