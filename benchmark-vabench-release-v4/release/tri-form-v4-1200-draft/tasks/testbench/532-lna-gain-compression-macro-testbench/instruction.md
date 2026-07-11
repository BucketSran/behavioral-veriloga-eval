# LNA Gain Compression Macro Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LNA Gain Compression Macro` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `lna_gain_compression_macro.va`:
  - Module `lna_gain_compression_macro` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `lna_gain_compression_macro` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `lna_gain_compression_macro.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `lna_gain_compression_macro.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.
- `lna_gain_compression_macro.gain` defaults to `2.2` V/V; valid range: gain > 0; sets small-signal gain about 0.45 V common mode.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_RESET_COMMON_MODE`: exercise and make observable: Initialization sets out to 0.45 V and clears metric; an active-high reset sampled on a rising clk crossing restores the same state. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_SMALL_SIGNAL_GAIN`: exercise and make observable: For linear values from 0.14 V through 0.76 V, out equals 0.45 V plus gain times the sampled vin deviation and metric is 0.1 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_POSITIVE_COMPRESSION`: exercise and make observable: Above linear 0.76 V, excess signal is compressed by factor 0.28 and metric is 0.8 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_NEGATIVE_COMPRESSION`: exercise and make observable: Below linear 0.14 V, excess signal is compressed by factor 0.28 and metric is 0.8 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_FINAL_OUTPUT_CLAMP`: exercise and make observable: The final held output remains within 0.04 V through 0.86 V. Required traces: `time`, `out`.
- `P_CLOCKED_HOLD`: exercise and make observable: Out and metric update on rising clock crossings and hold between samples. Required traces: `time`, `clk`, `vin`, `out`, `metric`.

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
