# SAR Weighted Sum Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `SAR Weighted Sum` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

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

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `sar_weighted_sum` as `XDUT` with ordered public binding: D10=d10, D9=d9, D8=d8, D7=d7, D6=d6, D5=d5, D4=d4, D3=d3, D2=d2, D1=d1, D0=d0, VOUT=vout.

## Public Parameter Contract

- `sar_weighted_sum.vth` defaults to `0.45` V; valid range: finite real value; sets the strict decision threshold independently applied to every D input.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_THRESHOLD_DECODE`: exercise and make observable: Each D input contributes logic 1 only while its voltage is strictly above vth; a value at or below vth contributes logic 0. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_WEIGHT_ORDER`: exercise and make observable: The decoded contribution order is D10 at seven-eighths full scale, D9 at one-half, D8 at one-quarter, a 5:3 split across D7 and D6, then a binary tail from D5 through D0. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_BIPOLAR_ENDPOINTS`: exercise and make observable: All decision inputs low produce -1 V, while all decision inputs high produce one 512-unit step below +1 V on the normalized bipolar scale. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_MONOTONIC_CODE_WEIGHT`: exercise and make observable: Changing any decoded decision from low to high without lowering another decision cannot decrease VOUT. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.
- `P_CONTINUOUS_DECODE`: exercise and make observable: VOUT continuously reflects the current threshold-decoded input combination without a clock, reset, or retained code state. Required traces: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.

The required trace names are: `time`, `d10`, `d9`, `d8`, `d7`, `d6`, `d5`, `d4`, `d3`, `d2`, `d1`, `d0`, `vout`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
