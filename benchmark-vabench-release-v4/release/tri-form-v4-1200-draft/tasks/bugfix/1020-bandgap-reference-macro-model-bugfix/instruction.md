# Bandgap Reference Macro Model Bugfix

## Task Contract

The supplied Verilog-A system violates its public circuit contract. Repair the
complete editable bundle.

## Public Verilog-A Interface

Preserve this exact artifact and module interface:

- Artifact `bandgap_reference_macro_model.va`:
  - Module `bandgap_reference_macro_model` (entry)
    - position 0: `clk` (input, electrical)
    - position 1: `rst` (input, electrical)
    - position 2: `vin` (input, electrical)
    - position 3: `out` (output, electrical)
    - position 4: `metric` (output, electrical)

## Public Parameter Contract

- `bandgap_reference_macro_model.tr` defaults to `1e-10` s; valid range: tr > 0; sets output and metric transition smoothing.
- `bandgap_reference_macro_model.vth` defaults to `0.45` V; valid range: finite real; sets the voltage-coded clk and rst threshold.
- `bandgap_reference_macro_model.vstart` defaults to `0.58` V; valid range: vstart > 0.05; sets the supply level required for startup and valid updates.
- `bandgap_reference_macro_model.vref` defaults to `0.55` V; valid range: vref >= 0; sets the nominal regulated reference target before line correction and clamping.

## Required Behavior

The repaired bundle must satisfy every public property:

- `P_RESET_AND_BROWNOUT`: restore: Reset or vin below vstart forces out and metric to 0 V. Required traces: `time`, `rst`, `vin`, `out`, `metric`.
- `P_CLOCKED_FIRST_ORDER_SETTLING`: restore: On eligible rising clock crossings, the held reference advances by 0.35 of the remaining error to the clamped line-corrected target. Required traces: `time`, `clk`, `rst`, `vin`, `out`.
- `P_TARGET_AND_OUTPUT_CLAMPS`: restore: The line-corrected target is clamped to 0 through vin minus 0.05 V, and driven out remains within 0 through 0.9 V. Required traces: `time`, `vin`, `out`.
- `P_VALIDITY_ENCODING`: restore: Metric is 0 V in reset or brownout, 0.2 V during startup below the 0.48 V validity threshold, and 0.9 V after the held reference exceeds it. Required traces: `time`, `rst`, `vin`, `out`, `metric`.
- `P_CLOCKED_HOLD`: restore: Above startup, the reference state changes only on rising clock crossings and holds between samples. Required traces: `time`, `clk`, `vin`, `out`.

## Modeling Constraints

- Use deterministic voltage-domain sampled settling with no KCL or KVL regulation loop.
- Use voltage contributions only.
- Do not use current contributions, transistor-level devices, AC/noise analysis, or validation side channels.
- Preserve the exact file set, module graph, ports, parameters, and public traces.
- Do not add debug outputs, validation state, side channels, or stimulus-specific fixes.

## Output Contract

Return the repaired bundle with exactly these paths: `bandgap_reference_macro_model.va`.
Every supplied `.va` file is editable; do not add or omit files.
