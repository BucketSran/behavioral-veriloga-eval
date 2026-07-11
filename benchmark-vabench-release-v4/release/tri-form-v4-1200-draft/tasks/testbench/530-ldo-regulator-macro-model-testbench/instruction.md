# LDO Regulator Macro Model Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `LDO Regulator Macro Model` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `ldo_regulator_macro_model.va`:
  - Module `ldo_regulator_macro_model` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `ldo_regulator_macro_model` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `ldo_regulator_macro_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `ldo_regulator_macro_model.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_INITIAL_AND_RESET_STATE`: exercise and make observable: Initialization or active-high reset sets out to 0.60 V and metric to 0.9 V. Required traces: `time`, `rst`, `out`, `metric`.
- `P_LOAD_TARGET`: exercise and make observable: At each eligible rising clock crossing, vin is clamped to 0 through 0.9 V and target equals 0.62 V minus 0.055 times that load. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_FIRST_ORDER_REGULATION`: exercise and make observable: Out advances by 0.35 of the remaining target error on each eligible rising clock crossing. Required traces: `time`, `clk`, `vin`, `out`.
- `P_REGULATED_OUTPUT_CLAMP`: exercise and make observable: The held output remains within 0.25 V through 0.75 V. Required traces: `time`, `out`.
- `P_ERROR_METRIC`: exercise and make observable: Metric equals 0.9 V minus four times the absolute output-to-target error, clamped to 0 through 0.9 V. Required traces: `time`, `vin`, `out`, `metric`.
- `P_CLOCKED_HOLD`: exercise and make observable: Out and metric hold between rising clock crossings except for transition smoothing. Required traces: `time`, `clk`, `vin`, `out`, `metric`.

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
