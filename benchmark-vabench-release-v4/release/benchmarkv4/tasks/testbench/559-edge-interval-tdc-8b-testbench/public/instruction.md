# Edge Interval TDC 8b Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Edge Interval TDC 8b` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `edge_interval_tdc_8b` as `XDUT` with ordered public binding: start=start, stop=stop, valid=valid, code0=code0, code1=code1, code2=code2, code3=code3, code4=code4, code5=code5, code6=code6, code7=code7.

## Public Parameter Contract

- `edge_interval_tdc_8b.vdd` defaults to `0.9` V; valid range: vdd > 0; sets the voltage-coded code and valid high level.
- `edge_interval_tdc_8b.vth` defaults to `0.45` V; valid range: 0 < vth < vdd; sets the start and stop rising-edge threshold.
- `edge_interval_tdc_8b.tr` defaults to `2e-11` s; valid range: tr > 0; sets output transition smoothing.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_START_ARMS`: exercise and make observable: Each rising start crossing begins a new interval measurement, records that edge time, and clears valid. Required traces: `time`, `start`, `stop`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_NEXT_STOP_COMPLETES`: exercise and make observable: The first rising stop crossing after an armed start completes that measurement; stop crossings while unarmed do not change the result. Required traces: `time`, `start`, `stop`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_INTERVAL_QUANTIZATION`: exercise and make observable: A completed interval is rounded to the nearest whole nanosecond and reported as an unsigned code. Required traces: `time`, `start`, `stop`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_CODE_SATURATION`: exercise and make observable: Measured interval codes are saturated to the inclusive 8-bit range 0 through 255. Required traces: `time`, `start`, `stop`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.
- `P_VALID_AND_BIT_ORDER`: exercise and make observable: valid asserts after completion; code0 is the least significant bit and code7 is the most significant bit, using 0 V and vdd logic levels. Required traces: `time`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.

The required trace names are: `time`, `start`, `stop`, `valid`, `code0`, `code1`, `code2`, `code3`, `code4`, `code5`, `code6`, `code7`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
