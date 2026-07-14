# Bandgap Reference Macro Model Testbench

## Task Contract

Write one top-level Spectre testbench that verifies the public contract of the
supplied read-only `Bandgap Reference Macro Model` DUT. The evaluator runs the same submitted bytes
against the correct DUT and five anonymous semantic negative DUTs. Your
testbench must accept the correct DUT and expose all five behavioral faults.

## Public Verilog-A Interface

- Artifact `bandgap_reference_macro_model.va`:
  - Module `bandgap_reference_macro_model` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

Stable evaluator binding:

- DUT sources use `./dut/{artifact_path}`.
- Instantiate `bandgap_reference_macro_model` as `XDUT` with ordered public binding: clk=clk, rst=rst, vin=vin, out=out, metric=metric.

## Public Parameter Contract

- `bandgap_reference_macro_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `bandgap_reference_macro_model.vth` defaults to `0.45` V; valid range: finite real; sets the voltage-coded clk and rst threshold.
- `bandgap_reference_macro_model.vstart` defaults to `0.58` V; valid range: vstart > 0.05; sets the supply level required for startup and valid updates.
- `bandgap_reference_macro_model.vref` defaults to `0.55` V; valid range: vref >= 0; sets the nominal regulated reference target before line correction and clamping.

## Required Behavior

Create stimulus and save traces sufficient for the fixed evaluator oracle to check:

- `P_RESET_AND_BROWNOUT`: exercise and make observable: Reset or vin below vstart forces out and metric to 0 V. Required traces: `time`, `rst`, `vin`, `out`, `metric`.
- `P_CLOCKED_FIRST_ORDER_SETTLING`: exercise and make observable: On eligible rising clock crossings, the held reference advances by 0.35 of the remaining error to the clamped line-corrected target. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_TARGET_AND_OUTPUT_CLAMPS`: exercise and make observable: The line-corrected target is clamped to 0 through vin minus 0.05 V, and driven out remains within 0 through 0.9 V. Required traces: `time`, `vin`, `out`.
- `P_VALIDITY_ENCODING`: exercise and make observable: Metric is 0 V in reset or brownout, 0.2 V during startup below the 0.48 V validity threshold, and 0.9 V after the held reference exceeds it. Required traces: `time`, `rst`, `vin`, `out`, `metric`.
- `P_CLOCKED_HOLD`: exercise and make observable: Above startup, the reference state changes only on rising clock crossings and holds between samples. Required traces: `time`, `clk`, `vin`, `out`.

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
