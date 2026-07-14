# LDO Regulator Macro Model Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `ldo_regulator_macro_model.va`:
  - Module `ldo_regulator_macro_model` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `ldo_regulator_macro_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output transition smoothing.
- `ldo_regulator_macro_model.vth` defaults to `0.45` V; valid range: finite real; sets clk and rst logic threshold.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_INITIAL_AND_RESET_STATE`: restore: Initialization or active-high reset sets out to 0.60 V and metric to 0.9 V. Required traces: `time`, `rst`, `out`, `metric`.
- `P_LOAD_TARGET`: restore: At each eligible rising clock crossing, vin is clamped to 0 through 0.9 V and target equals 0.62 V minus 0.055 times that load. Required traces: `time`, `clk`, `rst`, `vin`, `out`, `metric`.
- `P_FIRST_ORDER_REGULATION`: restore: Out advances by 0.35 of the remaining target error on each eligible rising clock crossing. Required traces: `time`, `clk`, `vin`, `out`.
- `P_REGULATED_OUTPUT_CLAMP`: restore: The held output remains within 0.25 V through 0.75 V. Required traces: `time`, `out`.
- `P_ERROR_METRIC`: restore: Metric equals 0.9 V minus four times the absolute output-to-target error, clamped to 0 through 0.9 V. Required traces: `time`, `vin`, `out`, `metric`.
- `P_CLOCKED_HOLD`: restore: Out and metric hold between rising clock crossings except for transition smoothing. Required traces: `time`, `clk`, `vin`, `out`, `metric`.

## Modeling Constraints

- Treat vin as a bounded load or disturbance control, not as a supply rail.
- Use voltage-domain sampled settling only.
- Do not use current contributions, transistor devices, AC/noise analysis, KCL/KVL regulation loops, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `ldo_regulator_macro_model.va`.
Every supplied `.va` file is editable; do not add or omit files.
