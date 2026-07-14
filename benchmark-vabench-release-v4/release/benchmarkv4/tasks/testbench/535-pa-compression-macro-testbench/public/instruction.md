# PA Compression Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `PA Compression Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `pa_compression_macro.va`:
  - Module `pa_compression_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `pa_compression_macro` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `pa_compression_macro.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `pa_compression_macro.vth` defaults to `0.45` V; valid range: 0 < vth < 0.9; sets clk and rst logic threshold.
- `pa_compression_macro.gain` defaults to `3.0`; valid range: gain > 0; sets the moderate-drive voltage gain about 0.45 V common mode.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_COMMON_MODE`: exercise and make observable: Initialization or active reset returns out to 0.45 V common mode and clears metric to 0 V. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_CLOCKED_UPDATE`: exercise and make observable: Out and metric update from the sampled signed drive vin - 0.45 V on rising clk crossings and hold between updates. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_LINEAR_REGION`: exercise and make observable: When 0.45 V + gain*(vin - 0.45 V) lies from 0.12 V through 0.78 V, out equals that target and metric is 0.1 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_SYMMETRIC_COMPRESSION`: exercise and make observable: Targets above 0.78 V or below 0.12 V are compressed with slope 0.18 about the corresponding boundary, and metric is 0.85 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_OUTPUT_CLAMP`: exercise and make observable: The compressed output remains within 0.02 V through 0.88 V with finite transition smoothing. Required traces: `time`, `out`.

The required trace names are: `time`, `clk`, `rst`, `vin`, `out`, `metric`.

## Modeling Constraints

- Submit one self-contained top-level transient `.scs` file.
- Use only the declared `./dut/...` source paths and public DUT interfaces.
- Do not redefine the DUT, drive declared DUT outputs, inspect private internals,
  access undeclared files, or emit a self-reported result.
- Missing traces, setup errors, and invalid runs do not count as behavioral kills.

## Output Contract

Return exactly one artifact named `testbench.scs`. Do not return a DUT,
checker, script, data file, waveform, or auxiliary deck.
