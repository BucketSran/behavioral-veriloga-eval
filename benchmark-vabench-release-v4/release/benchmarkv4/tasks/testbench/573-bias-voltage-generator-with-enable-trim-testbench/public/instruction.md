# Bias Voltage Generator With Enable Trim Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bias Voltage Generator With Enable Trim` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bias_voltage_generator_with_enable_trim.va`:
  - Module `bias_voltage_generator_with_enable_trim` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bias_voltage_generator_with_enable_trim` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `bias_voltage_generator_with_enable_trim.tr` defaults to `1e-10` s; valid range: tr > 0; sets rise and fall smoothing for out and metric.
- `bias_voltage_generator_with_enable_trim.vth` defaults to `0.45` V; valid range: vth > 0; sets the decision threshold for clk and rst.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_CLOCKED_UPDATE`: exercise and make observable: Bias state changes are evaluated on rising clk crossings through vth and hold between clock updates. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_DISABLE_RESET`: exercise and make observable: At an update, rst above vth or vin below 0.25 V disables the generator, returning out and metric to 0 V. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_TRIM_TARGET`: exercise and make observable: When enabled, the target is 0.28 V plus 0.55 times (vin minus 0.25 V) divided by 0.65 V, clamped to 0.28 V through 0.82 V. Required traces: `time`, `clk`, `vin`, `out`.
- `P_SETTLING`: exercise and make observable: At each enabled update, out advances by 45 percent of the remaining difference to the current target rather than jumping directly. Required traces: `time`, `clk`, `vin`, `out`.
- `P_MONOTONIC_TRIM`: exercise and make observable: For otherwise equal enabled histories, a higher trim request produces a target and settled out value no lower than a smaller request. Required traces: `time`, `clk`, `vin`, `out`.
- `P_ENABLE_METRIC`: exercise and make observable: metric approaches 0.9 V while enabled and 0 V while disabled, with transition smoothing set by tr. Required traces: `time`, `clk`, `rst`, `vin`, `metric`.

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
