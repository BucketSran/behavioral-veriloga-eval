# Limiting Amplifier Frontend Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Limiting Amplifier Frontend` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `limiting_amplifier_frontend.va`:
  - Module `limiting_amplifier_frontend` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `limiting_amplifier_frontend` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `limiting_amplifier_frontend.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `limiting_amplifier_frontend.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_RESET_COMMON_MODE`: exercise and make observable: Initialization sets out to 0.45 V and metric to 0 V; an active-high reset sampled on a rising clk crossing restores the same state. Required traces: `time`, `clk`, `rst`, `out`, `metric`.
- `P_LINEAR_REGION`: exercise and make observable: For sampled input deviation from -0.09 V through 0.09 V, out equals 0.45 V plus 1.7 times the deviation and metric is 0 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_POSITIVE_LIMITING`: exercise and make observable: Above the positive boundary, out follows 0.73 V plus 0.45 times excess deviation and metric is 0.85 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_NEGATIVE_LIMITING`: exercise and make observable: Below the negative boundary, out follows 0.17 V plus 0.45 times excess negative deviation and metric is 0.85 V. Required traces: `time`, `clk`, `vin`, `out`, `metric`.
- `P_OUTPUT_CLAMP`: exercise and make observable: The final held output remains within 0.04 V through 0.86 V. Required traces: `time`, `out`.
- `P_CLOCKED_HOLD`: exercise and make observable: Out and metric update only on rising clock crossings and hold between samples. Required traces: `time`, `clk`, `vin`, `out`, `metric`.

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
